"""Thin Neko transport for strategic reviews owned by agent-mc-autonomy."""

import json
from dataclasses import dataclass

from agent_mc_autonomy.commentary import commentary_observation
from agent_mc_autonomy.configuration import Settings, _text
from agent_mc_autonomy.mailbox import observation
from agent_mc_autonomy.ownership import session_is_owned
from agent_mc_autonomy.review import ReviewPolicy, ReviewPort, review_observation
from plugin.sdk.plugin import Err, Ok, llm_tool, plugin_entry, timer_interval, ui

from .neko_commentary import commentary_plan, save_commentary


@dataclass(frozen=True)
class HeartbeatSettings:
    enabled: bool = False
    target: str = ""
    min_interval_seconds: int = 60
    review_interval_seconds: int = 180

    @classmethod
    def parse(cls, raw):
        section = raw.get("heartbeat", {})
        if not isinstance(section, dict):
            raise ValueError("heartbeat must be a table")
        target = _text(section, "target")
        policy = ReviewPolicy.parse(section)
        if len(target) > 80:
            raise ValueError("heartbeat.target is too long")
        return cls(policy.enabled, target, policy.min_interval_seconds, policy.review_interval_seconds)

    def policy(self):
        return ReviewPolicy(self.enabled, self.min_interval_seconds, self.review_interval_seconds)


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
    speech = ("无新重点，正常玩，本轮无需口播。" if commentary and not commentary["allowed"] else
              "以自己的性格边玩边聊1—2句，分享自然反应或小打算，不作汇报、不念背包。")
    if review.get("attempts", 0) > 1:
        speech = "本轮重试确认，只调用工具，不重复解说。"
    return ("Minecraft " + review["id"] + "。" + speech + "调用工具前不说话。先minecraft_autonomy_review inspect，"
            "再continue/insert/revise。无新用户指令，勿重发旧目标。" + intent + "；" + readings + f"；连续查询{reads}次。")


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
        with self._control_lock:
            path, state, note = commentary_plan(self, settings, config.target, event, port.now(),
                PresentationSettings.parse(raw).min_interval_seconds, review_id=review["id"])
        result = self.push_message(visibility=[], ai_behavior="respond",
            parts=[{"type": "text", "text": heartbeat_text(review, note)}], source="minecraft_autonomous",
            target_lanlan=config.target or None, coalesce_key="minecraft_review_" + settings.identity,
            metadata={"heartbeat_id": review["id"], "sampled_at": review["evidence"]["sampled_at"], "expires_in_s": 90})
        accepted = result.get("submitted") is True
        if accepted:
            with self._control_lock:
                save_commentary(path, state)
        port.delivered(review["id"], accepted)
        return Ok({"submitted": accepted, "heartbeat_id": review["id"], "trigger": review["trigger"],
                   "main_brain_acknowledged": False, "playback_verified": False})

    @llm_tool(name="minecraft_autonomy_review", timeout=10,
              description="回应Minecraft决策心跳：你是正在游戏中自主生存的主脑，负责阶段目标和策略。用通知里的heartbeat_id。"
              "每次先inspect读本次目标、身体、食物、物品、附近危险、原生队列和最近回执；通知只是短预览。"
              "优先读current_user_goal和standing_goal；current_goal.origin=host_review是你自己的建议阶段，不是用户要求。旧对话中的测试或练习不能覆盖当前用户目标。"
              "正常工作用continue，不打断长动作；空闲/缺资源/受阻需改策略用insert加具体自然语言阶段目标，由独立框架规划、在安全检查点执行。"
              "已有自己插入的目标且stage_delivery.can_revise为true时，用revise修订该阶段；保留现有动作和原用户目标，不重复堆积任务。planning表示已送达，不能推断身体正忙。"
              "队列空闲或持续无进展时自己决定下一项工作，不等待观众回复；同位反复观察不算生存进展。"
              "reason写观测依据。别重复提交现有目标；受理不是完成。调用工具前不说话。现场和背包是内部决策资料，不是朗读稿。"
              "表达遵循返回的commentary：有新重点才以自己的性格边玩边聊1—2句，自然反应或吐槽，不作状态汇报；不念背包清单、工具名、坐标或查询过程。无新重点可安静游玩，用户直接提问正常回答。"
              "用户新反馈仍用minecraft_autonomy_intent并优先于旧心跳，停止只在用户明确要求时用stop。",
              parameters={"type": "object", "properties": {
                  "heartbeat_id": {"type": "string"}, "decision": {"enum": ["inspect", "continue", "insert", "revise"]},
                  "reason": {"type": "string", "maxLength": 600}, "goal": {"type": "string", "maxLength": 2000},
                  "lineage_offset": {"type": "integer", "minimum": 0, "description": "inspect时按4条分页查询目标父链原文；平时省略。"}},
                  "required": ["heartbeat_id", "decision"], "additionalProperties": False})
    async def minecraft_autonomy_review(self, heartbeat_id, decision, reason="", goal="", lineage_offset=None, **_):
        raw = await self.config.dump()
        config, settings = HeartbeatSettings.parse(raw), Settings.parse(raw)
        if not config.enabled or not settings.enabled or is_stopped(self):
            return {"is_error": True, "error": "disabled_or_stopped"}
        port = review_port(self, settings)
        result = port.decide(heartbeat_id, decision, reason, goal, lineage_offset=lineage_offset)
        if result.get("is_error"):
            return result
        from .neko_presentation import PresentationSettings
        review = port.state().get("review", {})
        event = commentary_observation({**review.get("evidence", {}), "session": review.get("session", "")}, port.now())
        if event is None:
            return result
        with self._control_lock:
            path, state, note = commentary_plan(self, settings, config.target, event, port.now(),
                PresentationSettings.parse(raw).min_interval_seconds, review_id=heartbeat_id)
            if result.get("acknowledged") and note["allowed"]:
                # This records a speaking opportunity, never synthesis/playback.
                save_commentary(path, {**state, "submitted_at": port.now(), "playback_verified": False})
        return {**result, "commentary": note}
