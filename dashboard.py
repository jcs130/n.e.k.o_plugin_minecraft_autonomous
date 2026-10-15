"""Public hosted UI state/actions, with bounded read-only audit sampling."""

import json
import uuid
from dataclasses import asdict

from agent_mc_autonomy.configuration import Settings
from agent_mc_autonomy.decision_profiles import validate_policy
from agent_mc_autonomy.host_context import HostContextPort
from agent_mc_autonomy.model_config import HttpPlannerConfig, planner_settings
from agent_mc_autonomy.readiness import installation_readiness, validation_feedback
from agent_mc_autonomy.viewer import viewer_observation
from plugin.sdk.plugin import Err, Ok, plugin_entry, ui

from .direct_planner import public_planner
from .model_check import check_model
from .neko_heartbeat import HeartbeatSettings, is_stopped, review_port
from .neko_host_context import HostContextSettings
from .neko_presentation import PresentationSettings
from .neko_tools import unwrap

try:
    from agent_mc_autonomy.operator import operator_link
except ModuleNotFoundError as error:
    if error.name != "agent_mc_autonomy.operator":
        raise
    operator_link = None

OPERATOR_UNAVAILABLE = {"available": False, "reason": "operator_capability_unavailable",
                        "guidance": "当前框架尚不支持账户入口。请安装匹配的核心与自主框架后启用；没有读取或发起 Microsoft 授权。"}

EDITABLE = {
    "autonomy": {"enabled", "min_decision_seconds", "idle_decision_seconds", "max_decisions", "max_tool_rounds", "context_tokens", "max_output_tokens", "model_timeout_seconds"},
    "server": {"host", "port", "username", "auth", "version", "connection_type"},
    "operator": {"port"},
    "decision_policy": {"enabled","routine_output_tokens","complex_output_tokens","routine_parameters","complex_parameters"},
    "runtime": {"mode", "data_directory"},
    "backend": {"node", "directory"},
    "viewer": {"url", "auto_open", "renderer_directory", "catalog_file", "bundled_appearance_catalog_file", "listen_port"},
    "perception": {"enabled"},
    "presentation": {"enabled", "target", "min_interval_seconds"},
    "heartbeat": {"enabled", "target", "min_interval_seconds", "review_interval_seconds"},
    "host_context": {"enabled", "character_api_url"},
    "fast": {"mode", "endpoint", "model", "api_key_env", "min_confidence"},
    "memory": {"mode", "endpoint", "model", "api_key_env", "timeout_ms", "provider", "library_id", "project_id", "scope_id", "search_mode", "learning_enabled", "read_preference"},
    "planner": {"route", *HttpPlannerConfig.__dataclass_fields__},
}


def public_config(settings):
    return {
        "autonomy": {key: getattr(settings, "enabled" if key == "enabled" else key) for key in EDITABLE["autonomy"]},
        "server": {key: getattr(settings, key, "local" if settings.host in {"", "localhost", "127.0.0.1", "::1"} else "custom") for key in EDITABLE["server"]},
        "operator": {"port": settings.console_port},
        "decision_policy": asdict(settings.decision_policy),
        "runtime": {"mode": settings.runtime_mode, "data_directory": settings.data_directory},
        "backend": {"node": settings.node, "directory": settings.backend_directory},
        "viewer": {"url": settings.external_viewer_url, "auto_open": settings.viewer_auto_open,
                   "renderer_directory": settings.viewer_renderer_directory, "catalog_file": settings.viewer_catalog_file,
                   "bundled_appearance_catalog_file": settings.viewer_bundled_appearance_catalog_file,
                   "listen_port": settings.viewer_listen_port},
        "perception": {"enabled": settings.vision_enabled},
        "fast": asdict(settings.fast),
        "memory": asdict(settings.memory),
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
    @ui.action(label="检查直连模型", tone="default")
    @plugin_entry(id="check_direct_model", name="检查显式配置的模型服务", kind="service", timeout=45,
                  description="按已保存配置显式调用一次无游戏动作的工具测试；会使用模型额度。",
                  input_schema={"type": "object", "properties": {"catalog": {"type": "boolean"}, "planner": {"type": "object"}}})
    async def check_direct_model(self, catalog: bool = False, planner: dict | None = None, **_):
        from agent_mc_autonomy.model_admin import check_model as direct_check
        from agent_mc_autonomy.model_admin import list_models
        try:
            raw = await self.config.dump()
            settings = Settings.parse(raw)
            if settings.runtime_mode == "external":
                return Err({"code": "external_runtime_use_standalone_config"})
            if planner is not None:
                if not catalog or not isinstance(planner, dict) or planner.get("route") != "direct":
                    raise ValueError("draft_catalog_only")
                config = HttpPlannerConfig.parse({k: v for k, v in planner.items() if k != "route"}, require_model=False)
            else:
                config = planner_settings(raw.get("planner", {}))
            if config is None:
                return Err({"code": "direct_model_not_selected"})
            return Ok(await (list_models(config) if catalog else direct_check(config, max_output_tokens=settings.max_output_tokens)))
        except (RuntimeError, ValueError):
            return Err({"code": "direct_model_check_failed", "message": "未通过检查。请检查密钥、OAuth 登录、模型权限和参数；游戏未启动。"})

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
            result = unwrap(await self.status(metadata_only=True))
            if result.get("is_error"):
                return {"error": "configuration_or_observation_unavailable"}
            snapshot = result.get("observation", result)
            directory = settings.data_root(self.data_path()) / "sessions" / settings.identity / "host"
            state = {key: snapshot.get(key) for key in (
                "phase", "game_connected", "autonomy_running", "updated_at", "decisions", "source", "live_verified",
                "standing_goal", "current_goal", "context", "host_context", "model_status", "fast_focus", "perception", "planner_error", "viewer", "viewer_window")}
            state["facts"] = [{"key": str(p.get("key", ""))[:80], "text": str(p.get("text", ""))[:900],
                               "has_more": len(str(p.get("text", ""))) > 900} for p in snapshot.get("facts", {}).get("parts", [])[:24]]
            state["pending"] = [{k: p.get(k) for k in ("kind", "id", "phase", "terminal")} for p in snapshot.get("pending", [])[:16]]
            heartbeat = HeartbeatSettings.parse(raw)
            review_state = review_port(self, settings).state()
            review = review_state.get("review", {})
            heartbeat_state = {"enabled": heartbeat.enabled, "explicit_stop": is_stopped(self), "last_decision": review_state.get("last_decision"),
                               "submitted_at": review_state.get("submitted_at"), "retry_after": review_state.get("retry_after"),
                               "review": {key: review.get(key) for key in ("id", "trigger", "attempts", "result")}}
            return {"settings": {**public_config(settings), "presentation": asdict(PresentationSettings.parse(raw)),
                                 "heartbeat": asdict(heartbeat), "host_context": asdict(HostContextSettings.parse(raw)), "planner": public_planner(raw.get("planner", {}))}, "heartbeat": heartbeat_state, "runtime": state, "audit": audit_sample(directory),
                    "model_slots": ["decision", "vision", "fast"],
                    "installation": installation_readiness(settings, self.cache_path()),
                    "operator": operator_link(settings, settings.data_root(self.data_path())) if operator_link else OPERATOR_UNAVAILABLE,
                    **viewer_observation(settings, snapshot)}
        except (OSError, ValueError, KeyError):
            return {"error": "configuration_or_observation_unavailable"}

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
            if operator_link is None and ("operator" in settings or "connection_type" in settings.get("server", {})):
                return Err({"code": "operator_capability_unavailable", "message": OPERATOR_UNAVAILABLE["guidance"]})
            original = await self.config.dump()
            merged = {**original, **{key: {**original.get(key, {}), **value} for key, value in settings.items()}}
            parsed = Settings.parse(merged)
            direct = planner_settings(merged.get("planner", {}))
            if direct:
                direct.validate_budget(parsed.max_output_tokens)
                validate_policy(parsed.decision_policy,direct,parsed.max_output_tokens)
            PresentationSettings.parse(merged)
            HeartbeatSettings.parse(merged)
            HostContextSettings.parse(merged)
            with self._control_lock:
                if set(settings) - {"viewer", "presentation", "heartbeat", "host_context"} and self._worker and self._worker.snapshot().get("worker_alive"):
                    return Err({"code": "settings_runtime_active", "message": "运行参数须先显式停止嵌入式运行再保存；观战地址可单独保存，模型槽绑定可在宿主修改。"})
                fence = bool(set(settings) & {"server", "runtime", "autonomy", "heartbeat", "host_context"})
                if fence:
                    self._generation += 1
                    self._configuration_writes += 1
            try:
                await self.config.update(settings)
                if set(settings) & {"host_context", "heartbeat"}:
                    port = review_port(self, parsed)
                    with self._control_lock:
                        HostContextPort(port.directory).invalidate()
                        self._host_profile_cache = None
            finally:
                if fence:
                    with self._control_lock:
                        self._generation += 1
                        self._configuration_writes -= 1
            if "heartbeat" in settings:
                review_port(self, Settings.parse(merged)).configure(HeartbeatSettings.parse(merged).policy())
            return Ok({"saved": True, "running_session_changed": False, "applies": "next_explicit_start_or_observer_read"})
        except (ValueError, TypeError) as error:
            return Err(validation_feedback(error))

    @ui.action(label="保存插件设置", tone="primary")
    @plugin_entry(id="save_settings_hosted", name="托管面板保存设置", kind="service",
                  description="通过可序列化反馈保存设置；校验拒绝保留草稿，不启动运行。",
                  input_schema={"type": "object", "properties": {"settings": {"type": "object"}}, "required": ["settings"]})
    async def save_settings_hosted(self, settings: dict, **_):
        result = await self.save_settings(settings)
        if isinstance(result, Err):
            # The host stringifies Err payloads. Expected rejection must travel
            # through a successful dispatch so the panel receives field metadata.
            return Ok({"success": False, "error": result.error})
        return result

    @ui.action(label="投递目标", tone="primary")
    @plugin_entry(id="panel_intent", name="控制台投递目标", kind="service", description="通过同一个持久队列投递自然语言目标。",
                  input_schema={"type": "object", "properties": {"goal": {"type": "string", "minLength": 1, "maxLength": 4000},
                      "mode": {"enum": ["append", "insert", "replace"]}, "request_id": {"type": "string"}},
                      "required": ["goal", "mode", "request_id"]})
    async def panel_intent(self, goal: str, mode: str, request_id: str, **_):
        if mode == "append":
            return await self._submit("goal", {"goal": goal, "origin": "user"}, request_id)
        if mode in {"insert", "replace"}:
            return await self._submit("feedback", {"goal": goal, "mode": mode, "origin": "user"}, request_id)
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
