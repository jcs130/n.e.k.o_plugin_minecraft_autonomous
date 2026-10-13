"""Thin Neko transport for strategic reviews owned by agent-mc-autonomy."""

import json
from dataclasses import dataclass

from agent_mc_autonomy.configuration import Settings, _text
from agent_mc_autonomy.review import ReviewPolicy, ReviewPort
from plugin.sdk.plugin import Ok, llm_tool, plugin_entry, timer_interval, ui


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


def heartbeat_text(review):
    # The host's general notification preview is 200 tokens. A full objective
    # before the facts hid inventory, the idle queue and repeated-read evidence.
    # Transport a small cue; the existing inspection tool reads framework facts.
    def brief(text, size):
        raw = str(text).encode("utf-8")
        return raw.decode() if len(raw) <= size else raw[:size - 3].decode("utf-8", errors="ignore") + "…"

    evidence = review["evidence"]
    facts = evidence["facts"]
    readings = "；".join(brief(facts.get(key, ""), size) for key, size in (
        ("queue", 90), ("body", 80), ("foodReserve", 65)))
    reads = sum(evidence.get("read_activity", {}).values())
    return ("Minecraft复盘 " + review["id"] + "。先用minecraft_autonomy_review的inspect读取完整现场，"
            "再continue/insert/revise；按实际队列和回执决策并简短解说。" + readings + f"；连续查询{reads}次。")


class NekoHeartbeat:
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
        result = self.push_message(visibility=[], ai_behavior="respond",
            parts=[{"type": "text", "text": heartbeat_text(review)}], source="minecraft_autonomous",
            target_lanlan=config.target or None, coalesce_key="minecraft_review_" + settings.identity,
            metadata={"heartbeat_id": review["id"], "sampled_at": review["evidence"]["sampled_at"], "expires_in_s": 90})
        accepted = result.get("submitted") is True
        port.delivered(review["id"], accepted)
        return Ok({"submitted": accepted, "heartbeat_id": review["id"], "trigger": review["trigger"],
                   "main_brain_acknowledged": False, "playback_verified": False})

    @llm_tool(name="minecraft_autonomy_review", timeout=10,
              description="回应Minecraft决策心跳：你是正在游戏中自主生存的主脑，负责阶段目标和策略。用通知里的heartbeat_id。"
              "每次先inspect读本次目标、身体、食物、物品、附近危险、原生队列和最近回执；通知只是短预览。"
              "正常工作用continue，不打断长动作；空闲/缺资源/受阻需改策略用insert加具体自然语言阶段目标，由独立框架规划、在安全检查点执行。"
              "已有自己插入的目标且stage_delivery.can_revise为true时，用revise修订该阶段；保留现有动作和原用户目标，不重复堆积任务。planning表示已送达，不能推断身体正忙。"
              "队列空闲或持续无进展时自己决定下一项工作，不等待观众回复；同位反复观察不算生存进展。"
              "reason写观测依据。别重复提交现有目标；受理不是完成。之后用角色口吻简短说明打算，语音由宿主处理。"
              "用户新反馈仍用minecraft_autonomy_intent并优先于旧心跳，停止只在用户明确要求时用stop。",
              parameters={"type": "object", "properties": {
                  "heartbeat_id": {"type": "string"}, "decision": {"enum": ["inspect", "continue", "insert", "revise"]},
                  "reason": {"type": "string", "maxLength": 600}, "goal": {"type": "string", "maxLength": 2000}},
                  "required": ["heartbeat_id", "decision"], "additionalProperties": False})
    async def minecraft_autonomy_review(self, heartbeat_id, decision, reason="", goal="", **_):
        raw = await self.config.dump()
        config, settings = HeartbeatSettings.parse(raw), Settings.parse(raw)
        if not config.enabled or not settings.enabled or is_stopped(self):
            return {"is_error": True, "error": "disabled_or_stopped"}
        return review_port(self, settings).decide(heartbeat_id, decision, reason, goal)
