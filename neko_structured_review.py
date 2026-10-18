"""Public model transport for reviews; free-form model text has no output route.

Review policy, fresh evidence and dispatch remain in the canonical ReviewPort.
This replaces the notification-triggered model turn, rather than adding another
commentary model. Only the existing explicit spoken_text transport can speak.
"""

import asyncio
import json
import math

from agent_mc_autonomy.host_context import HostContextPort
from openai import APIConnectionError, APIStatusError
from plugin.sdk.plugin import TransportError

from .neko_commentary import SPEAK, save_commentary
from .neko_recent_context import current_request, owned_runtime

REVIEW_TOOL = {"type": "function", "function": {
    "name": "submit_game_review",
    "description": "根据本次真实现场提交高层判断；reason是内部依据，spoken_text才是对外台词。",
    "parameters": {"type": "object", "properties": {
        "decision": {"enum": ["continue", "insert", "revise"]},
        "reason": {"type": "string", "maxLength": 600},
        "goal": {"type": "string", "maxLength": 2000},
        "spoken_text": {"type": "string", "maxLength": 600},
        "death_reflection": {"type": "object"}},
        "required": ["decision", "reason"], "additionalProperties": False}}}

# These canonical refusals occur before speech, mailbox or choice commitment.
# Unknown transport results and successful/accepted work must never be retried.
CORRECTABLE = frozenset({'no_active_review_stage', 'previous_intent_pending',
                         'goal_already_active', 'reason_and_stage_goal_required'})


async def deliver_review(plugin, raw, settings, config, port, review, generation):
    common = {"heartbeat_id": review["id"], "trigger": review["trigger"], "offered": True,
              "main_brain_acknowledged": False, "playback_verified": False,
              "transport": "neko_public_model_gateway", "free_text_output": False}
    def refused(reason):
        return {**common, "submitted": False, "reason": reason}

    with plugin._control_lock:
        if getattr(plugin, "_structured_review_busy", False):
            return refused("structured_review_busy")
        plugin._structured_review_busy = True
    gateway = None
    client_opened = False
    wait_budget = None
    try:
        gateway = plugin.ctx.models
        if gateway is None:
            return refused("structured_review_unavailable")
        profile = HostContextPort(port.directory, now=port.now).read(port.mailbox.intent_revision())
        target = config.target or (profile or {}).get("stable", {}).get("agent_name")
        bound = owned_runtime(plugin, settings, target, port, generation)
        if not profile or bound is None or profile["stable"]["agent_name"] != target:
            return refused("structured_review_persona_unavailable")

        inspection = await plugin.minecraft_autonomy_review(review["id"], "inspect")
        if inspection.get("is_error"):
            return refused("structured_review_superseded")
        request = current_request(plugin, settings, target, port, generation)
        recent = HostContextPort(port.directory, now=port.now).read_recent(request) if request else None
        # The notification transport's speech/fallback instructions do not
        # belong in this private structured exchange. Keep its game evidence.
        inspection = {k: v for k, v in inspection.items() if k not in {"speech_contract", "speech_delivery", "context_request"}}
        packet = {"review_id": review["id"], "actor": profile["stable"],
                  "selected_context": profile["dynamic"], "inspection": inspection,
                  "recent_messages": (recent or {}).get("recent_messages", [])}
        messages = [{"role": "system", "content": (
            "你是正在玩Minecraft的当前Neko角色。人格和已选记忆见下面的角色投影；未提供的记忆不要编造。"
            "根据新鲜现场作高层判断，用户新反馈优先；原生身体和队列独立运行。"
            "只调用submit_game_review提交最终判断。reason留作内部依据；可选spoken_text才会交给现有语音出口。"
            "不要把工具过程、思考内容或控制标签放入spoken_text。只读观察、受理和模型判断不等于目标完成。\n"
            + SPEAK)}, {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}]
        client = await gateway.get_client()
        client_opened = True
        for attempt in range(2):
            if owned_runtime(plugin, settings, target, port, generation) != bound:
                return refused("structured_review_superseded")
            expires = review.get('opportunity', {}).get('expires_at')
            wait_budget = (min(180, expires - port.now() - 2)
                           if type(expires) in (int, float) and math.isfinite(expires) else 25)
            if wait_budget <= 0:
                return refused('structured_review_expired')
            response = await asyncio.wait_for(client.chat.completions.create(
                model="decision", messages=messages, tools=[REVIEW_TOOL], stream=False,
                tool_choice={"type": "function", "function": {"name": "submit_game_review"}},
                parallel_tool_calls=False, max_completion_tokens=2048), timeout=wait_budget)
            if owned_runtime(plugin, settings, target, port, generation) != bound:
                return refused("structured_review_superseded")
            choice = response.choices[0]
            calls = choice.message.tool_calls or []
            if choice.finish_reason != "tool_calls" or len(calls) != 1 or calls[0].function.name != "submit_game_review":
                return refused("structured_review_invalid_response")
            call = calls[0]
            arguments = json.loads(call.function.arguments)
            allowed = set(REVIEW_TOOL["function"]["parameters"]["properties"])
            if (not isinstance(arguments, dict) or set(arguments) - allowed
                    or arguments.get("decision") not in {"continue", "insert", "revise"}
                    or not isinstance(arguments.get("reason"), str) or not arguments["reason"].strip()):
                return refused("structured_review_invalid_response")
            # Forward only the tool transaction, never free text or reasoning.
            # The canonical handler rechecks evidence/intent/stop before effects.
            port.delivered(review["id"], True)
            result = await plugin.minecraft_autonomy_review(review["id"], **arguments)
            if (attempt or result.get('is_error') is not True or result.get('error') not in CORRECTABLE
                    or not isinstance(getattr(call, 'id', None), str) or not call.id):
                break
            messages = [*messages, {"role": "assistant", "tool_calls": [{"id": call.id, "type": "function",
                "function": {"name": "submit_game_review", "arguments": call.function.arguments}}]},
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)}]
        tasks = [t for t in tuple(getattr(plugin, "_speech_output_tasks", ()))
                 if t.get_loop() is asyncio.get_running_loop()]
        if tasks:
            await asyncio.gather(*tasks)
        return {**common, "submitted": True, "main_brain_acknowledged": result.get("acknowledged") is True,
                "transport_status": "accepted", "decision": arguments["decision"],
                "correction_attempts": attempt,
                "model_wait_budget_seconds": round(wait_budget, 3),
                "decision_error": result.get('error') if result.get('error') in CORRECTABLE else
                                  "review_rejected" if result.get('is_error') else None,
                "reason": "structured_review_acknowledged" if result.get("acknowledged") else "structured_review_not_acknowledged"}
    except (APIConnectionError, APIStatusError, TransportError,
            TimeoutError, OSError, ValueError, TypeError, KeyError, IndexError, AttributeError) as error:
        category = ('deadline_exceeded' if isinstance(error, TimeoutError) else
                    'provider_http_error' if isinstance(error, APIStatusError) else
                    'provider_connection_error' if isinstance(error, APIConnectionError) else
                    'gateway_transport_error' if isinstance(error, TransportError) else 'invalid_or_unavailable_response')
        return {**refused("structured_review_unavailable"), "failure_category": category,
                "model_wait_budget_seconds": round(wait_budget, 3) if wait_budget is not None else None}
    finally:
        try:
            if client_opened and callable(getattr(gateway, "aclose", None)):
                await gateway.aclose()
        finally:
            with plugin._control_lock:
                plugin._structured_review_busy = False


def record_delivery(port, result):
    """Small categorical UI receipt, never a model transcript or audio claim."""
    save_commentary(port.directory / "structured-review.json", {
        **result, "at": port.now(), "extra_commentary_model_calls": 0})
