"""Thin Neko transport for strategic reviews owned by agent-mc-autonomy."""

import json
from dataclasses import dataclass

from agent_mc_autonomy.commentary import commentary_observation
from agent_mc_autonomy.configuration import Settings, _text
from agent_mc_autonomy.host_context import HostContextPort
from agent_mc_autonomy.mailbox import observation
from agent_mc_autonomy.ownership import session_is_owned
from agent_mc_autonomy.review import ReviewPolicy, ReviewPort, review_observation
from plugin.sdk.plugin import Err, Ok, llm_tool, plugin_entry, timer_interval, ui

from .neko_commentary import commentary_delivery, commentary_plan, save_commentary
from .neko_host_context import HostContextSettings, context_request, shared_context


@dataclass(frozen=True)
class HeartbeatSettings:
    enabled: bool = False
    target: str = ""
    min_interval_seconds: int = 60
    review_interval_seconds: int = 180
    idle_presence_seconds: int = 45

    @classmethod
    def parse(cls, raw):
        section = raw.get("heartbeat", {})
        if not isinstance(section, dict):
            raise ValueError("heartbeat must be a table")
        target = _text(section, "target")
        policy = ReviewPolicy.parse(section)
        if len(target) > 80:
            raise ValueError("heartbeat.target is too long")
        return cls(policy.enabled, target, policy.min_interval_seconds, policy.review_interval_seconds, policy.idle_presence_seconds)

    def policy(self):
        return ReviewPolicy(self.enabled, self.min_interval_seconds, self.review_interval_seconds, self.idle_presence_seconds)


def review_port(plugin, settings):
    return ReviewPort(settings.data_root(plugin.data_path()) / "sessions" / settings.identity / "host")


def is_stopped(plugin):
    try:
        return json.loads(plugin.data_path("operator.json").read_text(encoding="utf-8")).get("explicit_stop", False)
    except FileNotFoundError:
        return False


def heartbeat_text(review, commentary=None):
    # The host's general notification preview is 200 tokens. A full objective
    # before the facts hid inventory, the idle queue and repeated-read evidence.
    # Transport a small cue; the existing inspection tool reads framework facts.
    def brief(text, size):
        raw = str(text).encode("utf-8")
        return raw.decode() if len(raw) <= size else raw[:size - 3].decode("utf-8", errors="ignore") + "…"

    evidence = review["evidence"]
    facts = evidence["facts"]
    user = evidence.get("current_user_goal") or {}
    intent = ("当前用户目标:" + brief(user["goal"], 50) if user.get("goal") else
              "长期目标:" + brief(evidence.get("standing_goal", ""), 50))
    readings = "；".join(brief(facts.get(key, ""), size) for key, size in (
        ("queue", 55), ("body", 50), ("foodReserve", 40)))
    reads = sum(evidence.get("read_activity", {}).values())
    failure = evidence.get("tool_failure") or {}
    native = failure.get("native_execution") or {}
    outcome = next((row for row in reversed(evidence.get("native_outcomes", [])) if not row.get("observation_only")), {})
    body = next(iter(reversed(evidence.get("body_events", []))), {})
    selected = None
    if evidence.get("runtime_error"):
        selected = ("runtime", evidence.get("phase", "failed"), evidence["runtime_error"], {})
    elif failure:
        selected = (failure.get("tool", ""), native.get("phase", "failed"), failure.get("error", ""),
                    failure.get("native_event") or failure.get("receipt") or {})
    elif outcome.get("phase") in {"blocked", "rejected", "partial"}:
        selected = (outcome.get("tool", ""), outcome["phase"], outcome.get("receipt", ""), outcome.get("original_event") or {})
    elif facts.get("bodyRestriction"):
        selected = ("bodyRestriction", "inhibited", facts["bodyRestriction"],
                    {"archive": evidence.get("fact_originals", {}).get("bodyRestriction")})
    elif body:
        selected = (body.get("type", "minecraft.body"), body.get("phase", "observed"), body.get("text", ""), body.get("original_event") or {})
    cue = ""
    if selected:
        origin, phase, problem, reference = selected
        ref = (str(reference.get("run", "")) + ":" + str(reference["cursor"]) if "cursor" in reference else
               reference.get("request_id") or reference.get("archive") or "status")
        cue = "实际反馈:" + brief(origin, 25) + "/" + brief(phase, 25) + " " + brief(problem, 75) + " 引用:" + brief(ref, 40) + "；"
        readings = ""  # Keep the causal cue within the host preview budget.
    speech = "说一个自然的小打算或感想。"
    if review.get("trigger") == "idle_presence":
        speech = "轻松聊一句自己的好奇、心情或小打算；有兴致也可轻哼原创小调。"
    if review.get("attempts", 0) > 1:
        speech = "延续刚才的话题，补齐策略判断。"
    return ("Minecraft " + review["id"] + "。先minecraft_autonomy_review inspect，再continue/insert/revise完成判断。"
            + speech + "在最终判断的spoken_text给一句行动前打算；之后可自然接话，不复述。"
            + cue + intent + "；" + readings
            + f"；连续查询{reads}次。" + (f"未行动回复{evidence['unactioned_replies']}次。" if evidence.get("unactioned_replies") else ""))


class NekoHeartbeat:
    @ui.action(label="恢复 Neko 主脑参与", tone="primary")
    @plugin_entry(id="resume_observation", name="恢复外部游戏主脑反馈", kind="service",
                  description="显式恢复已运行的独立框架观测。检查同账号租约和新鲜状态，只清除 Neko 的停止标记；不启动游戏或投递任务。")
    async def resume_observation(self, **_):
        with self._control_lock:
            generation = self._generation
            if self._configuration_writes:
                return Err({"code": "resume_cancelled", "message": "配置正在保存，保持停止。"})
        try:
            raw = await self.config.dump()
            settings = Settings.parse(raw)
            if not settings.enabled or not HeartbeatSettings.parse(raw).enabled:
                return Err({"code": "disabled", "message": "先启用自主框架和主脑决策心跳。"})
            if settings.runtime_mode != "external" or not settings.data_directory:
                return Err({"code": "external_runtime_required", "message": "此入口用于已显式启动的独立框架。"})
            settings.require_server()
            port = review_port(self, settings)
            with self._control_lock:
                if generation != self._generation or self._configuration_writes:
                    return Err({"code": "resume_cancelled", "message": "恢复期间已收到停止指令或配置变更。"})
                snapshot = observation(port.directory)
                if (snapshot.get("phase") != "running" or not review_observation(snapshot, port.now())
                        or not session_is_owned(port.directory) or port.stopping()):
                    return Err({"code": "runtime_not_observed", "message": "尚无同账号的有效运行租约及新鲜联机状态，保持停止。"})
                self._operator_state(False)
            return Ok({"observer_resumed": True, "game_started": False, "task_dispatched": False,
                       "submitted": False, "main_brain_acknowledged": False, "playback_verified": False})
        except (OSError, ValueError, KeyError):
            return Err({"code": "observation_unavailable", "message": "配置或运行观测暂不可用，保持停止。"})

    @timer_interval(id="game_decision_heartbeat", seconds=10, name="转交自主框架决策请求",
                    description="仅转交独立框架生成的有效决策请求，不在插件中调度游戏。")
    async def game_decision_heartbeat(self, **_):
        return await self._review_game()

    @ui.action(label="请主脑判断当前局面", tone="default")
    @plugin_entry(id="review_game", name="转交待处理的游戏决策", kind="service",
                  description="转交自主框架待处理的复盘；保持框架限频，不启动游戏。")
    async def review_game(self, **_):
        return await self._review_game()

    async def _review_game(self):
        raw = await self.config.dump()
        config, settings = HeartbeatSettings.parse(raw), Settings.parse(raw)
        if not config.enabled or not settings.enabled:
            return Ok({"submitted": False, "reason": "disabled"})
        if is_stopped(self):
            return Ok({"submitted": False, "reason": "explicit_stop"})
        port = review_port(self, settings)
        port.configure(config.policy())
        offered = port.offer()
        if not offered["offered"]:
            return Ok({"submitted": False, "reason": offered["reason"]})
        review = offered["review"]
        # Presentation is host-specific; the framework supplies the signal and
        # still owns review creation/acknowledgement and the native work queue.
        from .neko_presentation import PresentationSettings
        # Use the original fresh snapshot for presentation: the strategic
        # envelope may abridge away the successful part of a mixed receipt.
        event = commentary_observation({**observation(port.directory), "session": review["session"]}, port.now())
        if event is None:
            port.delivered(review["id"], False)
            return Ok({"submitted": False, "reason": "no_fresh_review_evidence"})
        event["payload"]["opportunity"] = review.get("opportunity", {})
        if review["evidence"].get("death_episode"):
            event["payload"]["death_episode"] = review["evidence"]["death_episode"]
        with self._control_lock:
            path, state, note = commentary_plan(self, settings, config.target, event, port.now(),
                PresentationSettings.parse(raw).min_interval_seconds, review_id=review["id"])
        passive = not note["allowed"] and review["trigger"] == "periodic_review"
        text = ("游戏仍在自主运行。以下内部观测静默留给下次交流，无需回复或口播："
                + str(review["evidence"]["facts"].get("body", ""))[:100]
                + "；" + str(review["evidence"]["facts"].get("queue", ""))[:100] if passive else heartbeat_text(review, note))
        result = self.push_message(visibility=[], ai_behavior="read" if passive else "respond",
            parts=[{"type": "text", "text": text}], source="minecraft_autonomous",
            target_lanlan=config.target or None, coalesce_key="minecraft_review_" + settings.identity,
            metadata={"heartbeat_id": review["id"], "sampled_at": review["evidence"]["sampled_at"], "expires_in_s": 90})
        accepted = result.get("submitted") is True
        if accepted:
            with self._control_lock:
                save_commentary(path, {**state, "submitted_at": port.now(), "playback_verified": False})
        if passive:
            port.defer(review["id"], accepted)
        else:
            port.delivered(review["id"], result.get("submitted"))
        return Ok({"submitted": accepted, "heartbeat_id": review["id"], "trigger": review["trigger"],
                   "offered": True, "transport_status": "accepted" if accepted else "rejected" if result.get("submitted") is False else "unknown",
                   "context_only": passive,
                   "main_brain_acknowledged": False, "playback_verified": False})

    @llm_tool(name="minecraft_autonomy_review", timeout=10,
              description="回应Minecraft决策心跳：你是正在游戏中自主生存的主脑，负责阶段目标和策略。用通知里的heartbeat_id。"
              "每次先inspect读本次目标、身体、食物、物品、附近危险、原生队列和最近回执；通知只是短预览。"
              "你是这具Minecraft身体的主脑，不是汇报员。先inspect再完成最终判断；context_request的记忆召回仅为可选，不能挤掉最终判断。"
              "最终判断用context同步当前关注current_intent和记忆原id/source/text；未命中用[]，不编造。persona_needed时提供persona人格要点。"
              "优先读current_user_goal和standing_goal；current_goal.origin=host_review是你自己的建议阶段，不是用户要求。旧对话中的测试或练习不能覆盖当前用户目标。"
              "正常工作用continue，不打断长动作；空闲/缺资源/受阻需改策略用insert加具体自然语言阶段目标，由独立框架规划、在安全检查点执行。"
              "已有自己插入的目标且stage_delivery.can_revise为true时，用revise修订该阶段；保留现有动作和原用户目标，不重复堆积任务。planning表示已送达，不能推断身体正忙。"
              "队列空闲或持续无进展时自己决定下一项工作，不等待观众回复；同位反复观察不算生存进展。"
              "reason写观测依据。别重复提交现有目标；受理不是完成。现场和背包是内部决策资料，不是朗读稿。"
              "最终判断可附spoken_text一句同一打算，插件在普通目标投递前异步排入现有语音。按speech回执理解是否受理，受理不代表播放。之后可自然接话而不重复意图句。闲聊可分享好奇、心情或原创轻哼。inspect含待复盘死亡时，最终判断必须附death_reflection：带适用条件及事件或source run依据的教训，或因现场/背包未知等明确暂缓原因；遗漏会拒绝且可同心跳补交。旧已确认待复盘回执重新inspect后按legacy_reflection_completion补交，仅完成该事件，不重投目标或口播。"
              "用户新反馈仍用minecraft_autonomy_intent并优先于旧心跳，停止只在用户明确要求时用stop。",
              parameters={"type": "object", "properties": {
                  "heartbeat_id": {"type": "string"}, "decision": {"enum": ["inspect", "continue", "insert", "revise"]},
                  "reason": {"type": "string", "maxLength": 600}, "goal": {"type": "string", "maxLength": 2000},
                  "spoken_text": {"type": "string", "maxLength": 600, "description": "可选的一句自然意图，由本次主脑判断产生；不填控制标记。"},
                  "death_reflection": {"type": "object", "description": "inspect含待复盘死亡时最终判断必填；运行时按当前realm/account/agent和episode核验。普通判断省略。", "properties": {
                      "episode_id": {"type": "string", "minLength": 1, "maxLength": 80}, "outcome": {"enum": ["lesson", "deferred"]},
                      "lesson": {"type": "string", "maxLength": 1200}, "applicability": {"type": "string", "maxLength": 600},
                      "evidence": {"type": "string", "maxLength": 600, "description": "引用本次episode_id或source_event.run并说明事实依据。"}, "reason": {"type": "string", "maxLength": 600}},
                      "required": ["episode_id", "outcome"], "additionalProperties": False,
                      "oneOf": [{"properties": {"outcome": {"enum": ["lesson"]}}, "required": ["lesson", "applicability", "evidence"]},
                                {"properties": {"outcome": {"enum": ["deferred"]}}, "required": ["reason"]}]},
                  "context": {"type": "object", "properties": {
                      "agent_name": {"type": "string", "maxLength": 80}, "persona": {"type": "string", "maxLength": 800},
                      "current_intent": {"type": "string", "maxLength": 500},
                      "memories": {"type": "array", "maxItems": 6, "items": {"type": "object", "properties": {
                          "id": {"type": "string", "maxLength": 80}, "source": {"type": "string", "maxLength": 80},
                          "text": {"type": "string", "maxLength": 600}}, "required": ["id", "source", "text"], "additionalProperties": False}}},
                      "required": ["current_intent", "memories"], "additionalProperties": False},
                  "lineage_offset": {"type": "integer", "minimum": 0, "description": "inspect时按4条分页查询目标父链原文；平时省略。"}},
                  "required": ["heartbeat_id", "decision"], "additionalProperties": False})
    async def minecraft_autonomy_review(self, heartbeat_id, decision, reason="", goal="", lineage_offset=None, context=None, spoken_text=None, death_reflection=None, **_):
        with self._control_lock:
            generation = self._generation
        raw = await self.config.dump()
        config, settings = HeartbeatSettings.parse(raw), Settings.parse(raw)
        if not config.enabled or not settings.enabled or is_stopped(self):
            return {"is_error": True, "error": "disabled_or_stopped"}
        port = review_port(self, settings)
        try:
            projection = (await shared_context(self, raw, config.target, context, port.state().get("review", {}),
                          existing=HostContextPort(port.directory, now=port.now).read(port.mailbox.intent_revision()))
                          if decision != "inspect" else None)
        except ValueError as error:
            return {"is_error": True, "error": str(error)}
        with self._control_lock:
            if generation != self._generation or self._configuration_writes or is_stopped(self):
                return {"is_error": True, "error": "configuration_changed_or_stopped"}
            from .neko_speech import enqueue_speech
            result = port.decide(heartbeat_id, decision, reason, goal, lineage_offset=lineage_offset,
                host_context=projection, death_reflection=death_reflection,
                before_dispatch=(lambda correlation: enqueue_speech(self, raw, settings, config.target,
                    port, generation, spoken_text, correlation)) if spoken_text is not None else None)
        if result.get("is_error"):
            return result
        if decision == "inspect":
            result = {**result, "context_request": context_request(port, port.now, enabled=HostContextSettings.parse(raw).enabled),
                      "speech_contract": "Optional spoken_text in the final decision uses configured public output only. Final host text is outside plugin filtering; avoid duplicating a queued intent."}
            from .neko_commentary import load_commentary
            opportunity = port.state().get("review", {}).get("opportunity", {}).get("id", heartbeat_id)
            result["speech_delivery"] = load_commentary(port.directory / "speech-output.json").get("records", {}).get(opportunity)
        from .neko_presentation import PresentationSettings
        review = port.state().get("review", {})
        event = commentary_observation({**review.get("evidence", {}), "session": review.get("session", "")}, port.now())
        if event is None:
            return result
        event["payload"]["opportunity"] = review.get("opportunity", {})
        if review.get("evidence", {}).get("death_episode"):
            event["payload"]["death_episode"] = review["evidence"]["death_episode"]
        with self._control_lock:
            path, state, note = commentary_plan(self, settings, config.target, event, port.now(),
                PresentationSettings.parse(raw).min_interval_seconds, review_id=heartbeat_id)
            if result.get("acknowledged") and note["allowed"]:
                # This records a speaking opportunity, never synthesis/playback.
                save_commentary(path, {**state, "submitted_at": port.now(), "playback_verified": False})
        return {**result, "commentary": commentary_delivery(note)}
