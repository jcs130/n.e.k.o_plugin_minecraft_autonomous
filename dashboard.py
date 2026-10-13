"""Public hosted UI state/actions, with bounded read-only audit sampling."""

import json
import uuid
from dataclasses import asdict

from agent_mc_autonomy.configuration import Settings
from agent_mc_autonomy.viewer import viewer_observation
from plugin.sdk.plugin import Err, Ok, plugin_entry, ui

from .model_check import check_model
from .neko_heartbeat import HeartbeatSettings, review_port
from .neko_presentation import PresentationSettings
from .neko_tools import unwrap

EDITABLE = {
    "autonomy": {"enabled", "min_decision_seconds", "idle_decision_seconds", "max_decisions", "max_tool_rounds", "context_tokens", "max_output_tokens", "model_timeout_seconds"},
    "server": {"host", "port", "username", "auth", "version"},
    "runtime": {"mode", "data_directory"},
    "backend": {"node", "directory"},
    "viewer": {"url", "auto_open", "renderer_directory", "catalog_file", "listen_port"},
    "perception": {"enabled"},
    "presentation": {"enabled", "target", "min_interval_seconds"},
    "heartbeat": {"enabled", "target", "min_interval_seconds", "review_interval_seconds"},
    "fast": {"mode", "endpoint", "model", "api_key_env", "min_confidence"},
}


def public_config(settings):
    return {
        "autonomy": {key: getattr(settings, "enabled" if key == "enabled" else key) for key in EDITABLE["autonomy"]},
        "server": {key: getattr(settings, key) for key in EDITABLE["server"]},
        "runtime": {"mode": settings.runtime_mode, "data_directory": settings.data_directory},
        "backend": {"node": settings.node, "directory": settings.backend_directory},
        "viewer": {"url": settings.external_viewer_url, "auto_open": settings.viewer_auto_open,
                   "renderer_directory": settings.viewer_renderer_directory, "catalog_file": settings.viewer_catalog_file,
                   "listen_port": settings.viewer_listen_port},
        "perception": {"enabled": settings.vision_enabled},
        "fast": asdict(settings.fast),
    }


def tail_rows(path, limit=20):
    """Fixed byte/row cap. Skip partial records during concurrent append."""
    try:
        with path.open("rb") as source:
            source.seek(0, 2)
            start = max(0, source.tell() - 131072)
            source.seek(start)
            lines = source.read(131072).splitlines(keepends=True)
    except FileNotFoundError:
        return []
    if start and lines:
        lines.pop(0)
    rows = []
    for line in lines:
        if not line.endswith(b"\n"):
            continue
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
        except (ValueError, UnicodeError):
            pass
    return rows[-limit:]


def audit_sample(directory):
    decisions, receipts = tail_rows(directory / "decisions.jsonl"), tail_rows(directory / "receipts.jsonl")
    samples = []
    for row in decisions:
        response = row.get("response") or {}
        route = response.get("model_status") or {}
        samples.append({"turn": row.get("turnId"), "status": "rejected" if "rejected" in row else "returned",
                        "tools": ", ".join(str(c.get("function", {}).get("name", ""))[:80] for c in response.get("tool_calls", [])[:1]),
                        "reply": str(response.get("content") or "")[:800], "route": route.get("route", "not_recorded"),
                        "latency_ms": route.get("latency_ms"), "usage": route.get("usage", {})})
    actions = [{"tool": str(row.get("tool", ""))[:80], "request_id": row.get("requestId"),
                "failed": bool((row.get("result") or {}).get("failed")),
                "execution": {k: ((row.get("result") or {}).get("execution") or {}).get(k) for k in ("kind", "id", "phase", "terminal")},
                "text": str((row.get("result") or {}).get("text", ""))[:1000]} for row in receipts]
    usage = [row["usage"] for row in samples if isinstance(row["usage"], dict)]
    return {"decisions": samples, "receipts": actions, "sample_scope": "last_20_records_within_128KiB_each",
            "usage_recorded": any("total_tokens" in row for row in usage),
            "sample_tokens": sum(row.get("total_tokens", 0) for row in usage if type(row.get("total_tokens", 0)) is int),
            "sample_failed_receipts": sum(row["failed"] for row in actions)}


class Dashboard:
    @ui.action(label="检查模型接口", tone="default")
    @plugin_entry(id="check_model", name="检查已绑定模型", kind="service", timeout=30,
                  description="显式调用 Neko 模型槽做一次中性结构化测试。图像模式使用合成色块，不连接游戏，不发送聊天。",
                  input_schema={"type": "object", "properties": {"mode": {"enum": ["text", "vision"]}}, "required": ["mode"]})
    async def check_model(self, mode: str, **_):
        if mode not in {"text", "vision"}:
            return Err({"code": "invalid_model_check"})
        return Ok(await check_model(self.ctx.models, mode))

    @ui.context(id="dashboard")
    async def dashboard(self):
        try:
            raw = await self.config.dump()
            settings = Settings.parse(raw)
            result = unwrap(await self.status())
            if result.get("is_error"):
                return {"error": "configuration_or_observation_unavailable"}
            snapshot = result.get("observation", result)
            directory = settings.data_root(self.data_path()) / "sessions" / settings.identity / "host"
            state = {key: snapshot.get(key) for key in (
                "phase", "game_connected", "autonomy_running", "updated_at", "decisions", "source", "live_verified",
                "standing_goal", "current_goal", "context", "model_status", "fast_focus", "perception", "planner_error", "viewer", "viewer_window")}
            state["facts"] = [{"key": str(p.get("key", ""))[:80], "text": str(p.get("text", ""))[:900],
                               "has_more": len(str(p.get("text", ""))) > 900} for p in snapshot.get("facts", {}).get("parts", [])[:24]]
            state["pending"] = [{k: p.get(k) for k in ("kind", "id", "phase", "terminal")} for p in snapshot.get("pending", [])[:16]]
            heartbeat = HeartbeatSettings.parse(raw)
            review_state = review_port(self, settings).state()
            review = review_state.get("review", {})
            heartbeat_state = {"enabled": heartbeat.enabled, "last_decision": review_state.get("last_decision"),
                               "submitted_at": review_state.get("submitted_at"), "retry_after": review_state.get("retry_after"),
                               "review": {key: review.get(key) for key in ("id", "trigger", "attempts", "result")}}
            return {"settings": {**public_config(settings), "presentation": asdict(PresentationSettings.parse(raw)),
                                 "heartbeat": asdict(heartbeat)}, "heartbeat": heartbeat_state, "runtime": state, "audit": audit_sample(directory),
                    "model_slots": ["decision", "vision", "fast"], **viewer_observation(settings, snapshot)}
        except (OSError, ValueError, KeyError):
            return {"error": "configuration_or_observation_unavailable"}

    @ui.action(label="保存插件设置", tone="primary")
    @plugin_entry(id="save_settings", name="保存自主游玩设置", kind="service",
                  description="仅保存经过校验的插件设置；不连接游戏、不调用模型，已有运行下次显式启动生效。",
                  input_schema={"type": "object", "properties": {"settings": {"type": "object"}}, "required": ["settings"]})
    async def save_settings(self, settings: dict, **_):
        try:
            if not isinstance(settings, dict) or not settings or set(settings) - EDITABLE.keys():
                raise ValueError("unknown_settings_section")
            for section, values in settings.items():
                if not isinstance(values, dict) or set(values) - EDITABLE[section]:
                    raise ValueError("unknown_settings_field")
            original = await self.config.dump()
            merged = {**original, **{key: {**original.get(key, {}), **value} for key, value in settings.items()}}
            Settings.parse(merged)
            PresentationSettings.parse(merged)
            HeartbeatSettings.parse(merged)
            with self._control_lock:
                if set(settings) - {"viewer", "presentation", "heartbeat"} and self._worker and self._worker.snapshot().get("worker_alive"):
                    return Err({"code": "settings_runtime_active", "message": "运行参数须先显式停止嵌入式运行再保存；观战地址可单独保存，模型槽绑定可在宿主修改。"})
            await self.config.update(settings)
            if "heartbeat" in settings:
                review_port(self, Settings.parse(merged)).configure(HeartbeatSettings.parse(merged).policy())
            return Ok({"saved": True, "running_session_changed": False, "applies": "next_explicit_start_or_observer_read"})
        except (ValueError, TypeError):
            return Err({"code": "invalid_settings", "message": "配置不合法。请检查服务器、路径、预算及快决策端点；远程 System One 要求 HTTPS。"})

    @ui.action(label="投递目标", tone="primary")
    @plugin_entry(id="panel_intent", name="控制台投递目标", kind="service", description="通过同一个持久队列投递自然语言目标。",
                  input_schema={"type": "object", "properties": {"goal": {"type": "string", "minLength": 1, "maxLength": 4000},
                      "mode": {"enum": ["append", "insert", "replace"]}, "request_id": {"type": "string"}},
                      "required": ["goal", "mode", "request_id"]})
    async def panel_intent(self, goal: str, mode: str, request_id: str, **_):
        if mode == "append":
            return await self.submit_goal(goal=goal, request_id=request_id)
        if mode in {"insert", "replace"}:
            return await self.feedback(goal=goal, mode=mode, request_id=request_id)
        return Err({"code": "invalid_intent_mode"})

    @ui.action(label="开始嵌入式游玩", tone="primary")
    @plugin_entry(id="panel_start", name="控制台开始游玩", kind="service", description="按已保存配置显式开始；外部观察模式不能接管进程。",
                  input_schema={"type": "object", "properties": {"goal": {"type": "string", "minLength": 1, "maxLength": 4000}}, "required": ["goal"]})
    async def panel_start(self, goal: str, **_):
        return await self.start(goal=goal)

    @ui.action(label="停止游玩", tone="danger", confirm="停止自主框架和它的游戏连接？服务器、模型与桌面保持运行。")
    @plugin_entry(id="panel_stop", name="控制台停止游玩", kind="service", description="显式停止本框架，保留账本。")
    async def panel_stop(self, **_):
        return await self.stop(request_id=str(uuid.uuid4()))
