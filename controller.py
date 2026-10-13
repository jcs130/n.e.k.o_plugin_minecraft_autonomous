"""Host-owned bounded decisions using the independent agent-mc/v1 execution protocol."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path

from .bridge import json_content, outcome, text_content
from .context import assemble, encode

PROTOCOL = "agent-mc/v1"
READ_PROTOCOL = {"task", "facts", "archive", "archive_runs"}
HIDDEN_TOOLS = {"mc_connection", "mc_events", "mc_trace", "mc_metrics", "mc_visual"}
DIRECT_TOOLS = {"mc_help", "mc_do", "mc_script", "mc_artifact", "mc_protocol", "mc_bag", "mc_queue", "mc_blocked", "mc_stop", "mc_escape"}


def fact_fingerprint(facts):
    # The sample timestamp is useful context, but is not a decision trigger.
    return encode([(p["key"], p["text"]) for p in facts.get("parts", []) if p["key"] != "sample"])


def model_tools(catalogue):
    def structural(value):
        if isinstance(value, list):
            return [structural(item) for item in value]
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if key in {"description", "title", "examples", "$comment", "default"}:
                    continue
                if key in {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}:
                    result[key] = {name: structural(child) for name, child in item.items()}
                else:
                    result[key] = item if key in {"const", "enum"} else structural(item)
            return result
        return value

    tools = []
    available = sorted(tool["name"] for tool in catalogue if tool["name"] not in HIDDEN_TOOLS)
    advanced = [name for name in available if name not in DIRECT_TOOLS]
    for tool in sorted(catalogue, key=lambda row: row["name"]):
        if tool["name"] not in DIRECT_TOOLS:
            continue
        schema = structural(tool["inputSchema"])
        if tool["name"] == "mc_protocol":
            schema["properties"]["action"] = {"enum": sorted(READ_PROTOCOL)}
        tools.append({"type": "function", "function": {"name": tool["name"], "description": tool.get("description", "")[:450], "parameters": schema}})
    if advanced:
        tools.append({"type": "function", "function": {"name": "mc_invoke",
                      "description": "Invoke an advanced Minecraft tool. First read its exact schema using mc_tool_help. The backend validates all arguments and returns the original execution receipt.",
                      "parameters": {"type": "object", "properties": {"name": {"enum": advanced},
                                     "arguments": {"type": "object", "additionalProperties": True}},
                                     "required": ["name", "arguments"], "additionalProperties": False}}})
    tools.append({"type": "function", "function": {"name": "mc_original",
                  "description": "Read a bounded page from an original fact or receipt artifact. Use next_offset to read more without re-inserting the full document.",
                  "parameters": {"type": "object", "properties": {"handle": {"type": "string"},
                                 "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 1000}},
                                 "required": ["handle"], "additionalProperties": False}}})
    tools.append({"type": "function", "function": {"name": "mc_tool_help",
                 "description": "Read the original tool description/schema on demand. Large nodes list JSON-pointer child paths; request a specific path for full detail.",
                 "parameters": {"type": "object", "properties": {"name": {"enum": available},
                    "path": {"type": "string", "description": "JSON pointer, e.g. /inputSchema/properties/steps"}}, "required": ["name"], "additionalProperties": False}}})
    return tools


def tool_help(catalogue, arguments):
    value = next(tool for tool in catalogue if tool["name"] == arguments["name"])
    # Expose the same host-owned control restriction in expanded documentation.
    value = json.loads(encode(value))
    if value["name"] == "mc_protocol":
        value["inputSchema"]["properties"]["action"] = {"enum": sorted(READ_PROTOCOL)}
    path = arguments.get("path", "")
    if path and not path.startswith("/"):
        raise ValueError("Tool documentation path must be a JSON pointer")
    for token in path.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    if len(encode(value).encode("utf-8")) <= 4500:
        return {"text": encode(value)}
    if isinstance(value, (dict, list)):
        pairs = value.items() if isinstance(value, dict) else enumerate(value)
        return {"text": encode({"expanded": False, "children": [
            {"path": path + "/" + str(key).replace("~", "~0").replace("/", "~1"), "type": type(item).__name__}
            for key, item in pairs]})}
    # All current scalar descriptions fit; archive_receipt retains future long ones.
    return {"text": str(value)}


def uncertain(receipt):
    evidence = (receipt.get("execution") or {}).get("evidence") or {}
    return evidence.get("outcomeUnknown") is True or evidence.get("outcomeKnown") is False or evidence.get("nativeStatus") == "unknown"


def online(status):
    # `phase: started` means engine started, not Mineflayer joined.
    return status.get("phase") == "started" and any(lamp.get("label") == "服务器" and lamp.get("state") == "online" for lamp in status.get("lamps", []))


class Controller:
    def __init__(self, bridge, decide, settings, data: Path, publish, stop_requested):
        self.bridge, self.decide, self.settings = bridge, decide, settings
        self.data, self.publish, self.stop_requested = data, publish, stop_requested
        self.pending = {}
        self.recent = []
        self.groups = []
        self.turn = None
        self.event_run = None
        self.cursor = 0
        self.last_decision = 0.0
        self.count = 0
        self.inflight_request = None
        self.last_facts = None
        self.preempted = False
        self.deferred_wake = False
        self.continuation_needed = False
        self.state_path = data / "host-state.json"

    def persist(self, **changes):
        self.data.mkdir(parents=True, exist_ok=True)
        previous = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {}
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(encode({**previous, **changes}), encoding="utf-8")
        temporary.replace(self.state_path)

    def receipt(self, value):
        if uncertain(value):
            self.persist(uncertain=True)
            raise RuntimeError("outcome_unknown: inspect the original action receipt; automatic replay is blocked")
        execution = value.get("execution")
        if execution:
            key = (execution["kind"], execution["id"])
            if execution.get("terminal") is True:
                self.pending.pop(key, None)
            else:
                self.pending[key] = execution
            self.persist(pending=list(self.pending.values()))
        self.recent.extend(e for e in value.get("events", []) if e.get("contextDelivery") != "archive-only" and not e.get("meta", {}).get("staleEpoch"))
        self.recent = self.recent[-64:]

    async def protocol(self, action, **arguments):
        return json_content(await self.bridge.call("mc_protocol", {"protocol": PROTOCOL, "action": action, **arguments}))

    async def events(self):
        page = json_content(await self.bridge.call("mc_events", {"after": self.cursor, "run": self.event_run, "limit": 64, "waitMs": 0} if self.event_run else {"after": 0, "limit": 64, "waitMs": 0}))
        if page.get("gap"):
            # Archive from the original cursor before resuming any plan; do not
            # ignore an evicted terminal/damage event and guess the task state.
            archived = await self.protocol("archive", run=page["run"], after=self.cursor, limit=64)
            page = {**archived, "run": page["run"]}
        self.event_run, self.cursor = page["run"], page["nextCursor"]
        wake, urgent = False, False
        for event in page["events"]:
            if event.get("contextDelivery") == "archive-only" or event.get("meta", {}).get("staleEpoch"):
                continue
            terminal = (event.get("execution") or {}).get("terminal") is True
            self.receipt({"events": [event], "execution": event.get("execution")})
            trigger = event.get("trigger")
            trigger = trigger.get("type") if isinstance(trigger, dict) else trigger
            wake |= terminal or trigger in {"preempt", "interrupt", "flush", "debounce"}
            urgent |= trigger in {"preempt", "interrupt"}
        return wake, urgent, page.get("hasMore", False)

    async def archive_receipt(self, request_id, name, result):
        original = encode(result)
        with (self.data / "receipts.jsonl").open("a", encoding="utf-8") as output:
            output.write(encode({"requestId": request_id, "turnId": self.turn, "tool": name, "result": result}) + "\n")
        if len(original.encode("utf-8")) <= 6000:
            return original
        # Chunks remain queryable through the existing artifact tool. JavaScript
        # measures maxLength in UTF-16; 16000 Python characters fit even with emoji.
        refs = []
        for offset in range(0, len(original), 16000):
            refs.append(json_content(await self.bridge.call("mc_artifact", {
                "action": "put", "text": original[offset:offset + 16000], "mime": "text/plain"})) ["handle"])
        return encode({"text": result.get("text", "")[:1200], "failed": result.get("failed"),
                       "control": result.get("control"), "execution": result.get("execution"),
                       "original_chunks": refs, "retrieve": "mc_original(handle,offset,limit), chunks in order"})

    async def original_page(self, arguments):
        offset, limit = arguments.get("offset", 0), arguments.get("limit", 1000)
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("Invalid original artifact page")
        raw = outcome(await self.bridge.call("mc_artifact", {"action": "get", "handle": arguments["handle"]}))
        if raw.get("failed"):
            return raw
        text = raw.get("text", "")
        end = min(len(text), offset + limit)
        return {"text": encode({"handle": arguments["handle"], "offset": offset, "text": text[offset:end],
                                "next_offset": end, "has_more": end < len(text), "total_characters": len(text)})}

    async def decide_with_events(self, messages, tools):
        task = asyncio.create_task(asyncio.wait_for(self.decide(messages, tools), self.settings.model_timeout_seconds))
        try:
            while True:
                done, _ = await asyncio.wait({task}, timeout=1)
                if self.stop_requested():
                    return None
                if done:
                    return await task
                wake, urgent, _ = await self.events()
                self.deferred_wake |= wake
                if urgent:
                    self.preempted = True
                    return None
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def turn_once(self, goal, prefix, tools):
        self.preempted = False
        self.deferred_wake = False
        self.continuation_needed = False
        self.turn = str(uuid.uuid4())
        await self.protocol("begin_turn", id=self.turn)
        try:
            for _ in range(self.settings.max_tool_rounds):
                if self.stop_requested():
                    return
                facts = await self.protocol("facts")
                self.last_facts = fact_fingerprint(facts)
                consumed = tuple(self.recent)
                self.deferred_wake = False
                messages, budget = assemble(prefix, tools, goal, facts, self.recent, self.groups,
                                            context_tokens=self.settings.context_tokens, reserved_output=self.settings.max_output_tokens)
                self.publish(context=budget)
                response = await self.decide_with_events(messages, tools)
                if self.stop_requested() or response is None:
                    return
                # Events arriving during inference belong to the next request.
                consumed_ids = {id(event) for event in consumed}
                self.recent = [event for event in self.recent if id(event) not in consumed_ids]
                calls = response.get("tool_calls") or []
                self.publish(last_message=(response.get("content") or "")[:1200])
                if not calls:
                    return
                if len(calls) != 1:
                    raise ValueError("Model must return one tool call at a time to honor runtime barriers")
                call = calls[0]
                name = call["function"]["name"]
                arguments = json.loads(call["function"]["arguments"])
                if name not in {tool["function"]["name"] for tool in tools} or not isinstance(arguments, dict):
                    raise ValueError("Model selected an unavailable Minecraft tool")
                available = {t["name"] for t in self.bridge.tools} - HIDDEN_TOOLS
                if name == "mc_invoke":
                    if arguments.get("name") not in available - DIRECT_TOOLS or not isinstance(arguments.get("arguments"), dict):
                        raise ValueError("Model selected an unavailable advanced tool")
                    name, arguments = arguments["name"], arguments["arguments"]
                if name == "mc_protocol" and arguments.get("action") not in READ_PROTOCOL:
                    raise ValueError("The host owns turn boundaries and cancellation")
                request_id = str(uuid.uuid4())
                # Journal before dispatch so a killed process cannot silently
                # restart with a new request id after an uncertain mutation.
                self.inflight_request = request_id
                self.persist(inflight_request=request_id, uncertain=True)
                if name == "mc_original":
                    raw = {"structuredContent": {"protocol": PROTOCOL, **await self.original_page(arguments)}}
                elif name == "mc_tool_help":
                    if arguments.get("name") not in available:
                        raise ValueError("Unavailable tool documentation")
                    raw = {"structuredContent": {"protocol": PROTOCOL, **tool_help(self.bridge.tools, arguments)}}
                else:
                    raw = await self.bridge.call(name, arguments, request_id=request_id, turn_id=self.turn)
                result = outcome(raw)
                # Save complete receipt before acknowledging the tool barrier.
                compact = await self.archive_receipt(request_id, name, result)
                meta = next((t for t in self.bridge.tools if t["name"] == name), {}).get("_meta", {}).get(PROTOCOL, {})
                if not raw.get("structuredContent") and {"write", "speak", "act"}.intersection(meta.get("tags", [])):
                    raise RuntimeError("outcome_unknown: mutation returned no structured execution receipt")
                self.receipt(result)
                self.inflight_request = None
                self.persist(inflight_request=None, uncertain=False)
                self.groups.append([{"role": "assistant", "content": response.get("content"), "tool_calls": calls},
                                    {"role": "tool", "tool_call_id": call["id"], "content": compact}])
                self.groups = self.groups[-8:]
                control = result.get("control") or {}
                if control.get("barrierAfter"):
                    await self.protocol("ack_barrier", id=control["requestId"])
                if control.get("endTurnRequested") or result.get("endsTurn") or self.pending:
                    return
            # A bounded documentation/read chain can continue in a fresh turn;
            # waiting for an unrelated world change here would strand the goal.
            self.continuation_needed = True
        finally:
            if not self.inflight_request:
                await self.protocol("end_turn", id=self.turn)
                self.turn = None

    async def run(self, goal):
        if self.state_path.exists():
            previous = json.loads(self.state_path.read_text(encoding="utf-8"))
            if previous.get("uncertain") or previous.get("pending") or previous.get("inflight_request"):
                raise RuntimeError("outcome_unknown: previous dispatch requires receipt reconciliation; the ledger was preserved")
        self.persist(stopped=False)
        try:
            await self.bridge.open()
            self.publish(phase="connecting")
            json_content(await self.bridge.call("mc_connection", {"action": "connect"}, timeout=120))
            deadline = time.monotonic() + 120
            while not self.stop_requested():
                status = json_content(await self.bridge.call("mc_connection", {"action": "status"}))
                if online(status):
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("Minecraft did not report an online connection within 120 seconds")
                await asyncio.sleep(1)
            if self.stop_requested():
                return
            self.publish(phase="running", game_connected=True, autonomy_running=True)
            prefix = text_content(await self.bridge.resource("mc://environment"))
            tools = model_tools(self.bridge.tools)
            wake, urgent = True, False
            last_status_check = time.monotonic()
            while not self.stop_requested() and self.count < self.settings.max_decisions:
                event_wake, event_urgent, more = await self.events()
                wake |= event_wake
                urgent |= event_urgent
                if more:
                    await asyncio.sleep(0)
                    continue
                if time.monotonic() - last_status_check >= 10:
                    status = json_content(await self.bridge.call("mc_connection", {"action": "status"}))
                    if not online(status):
                        raise RuntimeError("connection_lost: stopped decisions; inspect authentication and connection logs")
                    last_status_check = time.monotonic()
                elapsed = time.monotonic() - self.last_decision
                if not self.pending and elapsed >= self.settings.idle_decision_seconds:
                    # Poll state without a model request when nothing has changed.
                    wake |= fact_fingerprint(await self.protocol("facts")) != self.last_facts
                if (wake and (not self.pending or urgent) and elapsed >= self.settings.min_decision_seconds):
                    await self.turn_once(goal, prefix, tools)
                    self.count += 1
                    self.last_decision = time.monotonic()
                    wake, urgent = self.preempted or self.deferred_wake or self.continuation_needed, self.preempted
                    self.publish(decisions=self.count, pending=list(self.pending.values()))
                await asyncio.sleep(1)
            self.publish(phase="stopped" if self.stop_requested() else "budget_exhausted")
        finally:
            self.persist(stopped=True)  # Retain uncertainty and exact request IDs.
            try:
                status = json_content(await self.bridge.call("mc_connection", {"action": "disconnect"}, timeout=10))
                if status.get("phase") != "disconnected":
                    raise RuntimeError("Disconnect not confirmed")
                # Generic core disconnect explicitly stops its own action queue.
                # This must not be reused for Numen, whose remote body stays alive.
                self.persist(pending=[])
            except Exception:
                if self.pending or self.inflight_request:
                    self.persist(uncertain=True)
                self.publish(disconnect_confirmed=False)
            finally:
                await self.bridge.close()
                self.publish(game_connected=False, autonomy_running=False)
