"""Optional Neko narration of observed changes; never drives the Minecraft body."""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime

from plugin.sdk.plugin import Ok, plugin_entry, timer_interval, ui

from .autonomy.configuration import Settings, _boolean, _integer, _text
from .neko_tools import unwrap


@dataclass(frozen=True)
class PresentationSettings:
    enabled: bool = False
    target: str = ""
    min_interval_seconds: int = 90

    @classmethod
    def parse(cls, raw):
        section = raw.get("presentation", {})
        if not isinstance(section, dict):
            raise ValueError("presentation must be a table")
        target = _text(section, "target")
        if len(target) > 80:
            raise ValueError("presentation.target is too long")
        return cls(_boolean(section, "enabled", False), target,
                   _integer(section, "min_interval_seconds", 90, 30, 900))


def presentation_event(status, now):
    """Only fresh snapshots, with a small signature excluding clocks and motion."""
    snapshot = status.get("observation", status)
    try:
        sampled = datetime.fromisoformat(snapshot["updated_at"]).timestamp()
    except (KeyError, TypeError, ValueError):
        return None
    if not 0 <= now - sampled <= 30:
        return None
    connected = snapshot.get("game_connected") is True
    if not connected and snapshot.get("phase") not in {"failed", "stopped"}:
        return None
    facts = {p["key"]: str(p.get("text", "")) for p in snapshot.get("facts", {}).get("parts", [])}
    if connected and not any(facts.get(key) for key in ("body", "gear", "queue")):
        # The connection callback can precede the first native observation.
        # Wait for evidence instead of consuming the narration interval on blanks.
        return None
    # Facts are Chinese descriptions produced by the core, never planner success claims.
    changes = {key: facts.get(key, "")[:600] for key in ("body", "gear", "foodReserve", "life")}
    signature = json.dumps({"connected": connected, "phase": snapshot.get("phase"),
                            "facts": changes, "goal": snapshot.get("current_goal"),
                            "error": snapshot.get("error")}, ensure_ascii=False, sort_keys=True)
    payload = {"sampled_at": snapshot["updated_at"], "connected": connected,
               "phase": snapshot.get("phase"), "error": snapshot.get("error"),
               "facts": {**changes, "place": facts.get("place", "")[:220],
                         "queue": facts.get("queue", "")[:400]},
               "viewer_url": status.get("viewer_url", ""),
               "viewer_binding_verified": status.get("viewer_body_binding_verified", False)}
    return hashlib.sha256(signature.encode()).hexdigest(), payload


def narration_text(payload):
    """Fit the host's small notification preview, with actual facts first."""
    facts = payload["facts"]
    def brief(text, size):
        raw = text.encode("utf-8")
        return text if len(raw) <= size else raw[:size - 3].decode("utf-8", errors="ignore") + "…"
    state = "已连接" if payload["connected"] else "已断开：" + str(payload["phase"])
    readings = "；".join(brief(facts.get(key, ""), size) for key, size in (("body", 120), ("gear", 180), ("queue", 90)))
    return ("请 {LANLAN_NAME} 向 {MASTER_NAME} 直接说一句当前游戏情况，无需再查询或派任务。"
            "下面是30秒内观测数据，受理不等于完成：" + state + "；" + readings)


class NekoPresentation:
    @timer_interval(id="observe_game_changes", seconds=10,
                    name="观察游戏进展", description="只读当前游戏快照；开启解说后仅将重要变化送给 Neko。")
    async def observe_game_changes(self, **_):
        return await self._present_game()

    @ui.action(label="解说当前游戏状态", tone="default")
    @plugin_entry(id="present_status", name="解说当前游戏状态", kind="service",
                  description="将新鲜游戏观测交给当前或指定 Neko 角色解说；不投递游戏动作。提交不代表已播报。")
    async def present_status(self, **_):
        return await self._present_game(manual=True)

    async def _present_game(self, manual=False):
        raw = await self.config.dump()
        config = PresentationSettings.parse(raw)
        settings = Settings.parse(raw)
        if not manual and not config.enabled:
            return Ok({"submitted": False, "reason": "disabled"})
        status = unwrap(await self.status())
        now = time.time()
        event = presentation_event(status, now)
        if event is None:
            return Ok({"submitted": False, "reason": "no_fresh_observation"})
        signature, payload = event
        # One state per server/account/role, kept outside the independent runtime.
        identity = hashlib.sha256((settings.identity + config.target).encode()).hexdigest()[:24]
        path = self.data_path("presentation", identity + ".json")
        with self._control_lock:
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                previous = {}
            if not manual and signature == previous.get("signature"):
                return Ok({"submitted": False, "reason": "unchanged"})
            interval = 30 if manual else config.min_interval_seconds
            if now < previous.get("retry_after", 0) or now - previous.get("submitted_at", 0) < interval:
                return Ok({"submitted": False, "reason": "rate_limited"})
            text = narration_text(payload)
            result = self.push_message(visibility=[], ai_behavior="respond",
                parts=[{"type": "text", "text": text}], source="minecraft_autonomous",
                target_lanlan=config.target or None, coalesce_key="minecraft_progress_" + identity,
                metadata={"event_signature": signature, "sampled_at": payload["sampled_at"], "expires_in_s": 30})
            accepted = result.get("submitted") is True
            saved = {"signature": signature, "submitted_at": now, "playback_verified": False} if accepted else {
                **previous, "retry_after": now + 30}
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(saved), encoding="utf-8")
            temporary.replace(path)
        return Ok({"submitted": accepted, "reason": result.get("reason"), "playback_verified": False})
