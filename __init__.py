"""Explicitly started N.E.K.O decisions and one independent Minecraft body."""

import asyncio
import json
import threading

from plugin.sdk.plugin import Err, NekoPluginBase, Ok, TransportError, lifecycle, neko_plugin, plugin_entry

from .backend.install import verify_runtime
from .bridge import MinecraftBridge
from .configuration import Settings
from .controller import Controller
from .worker import Worker


@neko_plugin
class MinecraftAutonomousPlugin(NekoPluginBase):
    def __init__(self, ctx):
        super().__init__(ctx)
        self._control_lock = threading.RLock()
        self._generation = 0
        self._worker = None

    def _operator_state(self, stopped):
        path = self.data_path("operator.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"explicit_stop": stopped}), encoding="utf-8")
        temporary.replace(path)

    @lifecycle(id="startup")
    async def on_startup(self, **_):
        return await self.status()

    @lifecycle(id="shutdown")
    async def on_shutdown(self, **_):
        return await self.stop()

    @plugin_entry(
        id="status",
        name="自主游玩状态 / Autonomous play status / 自律プレイ状態",
        description="只读报告后端、Minecraft 连接、当前动作与自主决策状态。",
        kind="service",
    )
    async def status(self, **_):
        state = {"phase": "stopped", "game_connected": False, "autonomy_running": False, "worker_alive": False}
        with self._control_lock:
            if self._worker:
                state.update(self._worker.snapshot())
        ready, reason, viewer = False, "backend_missing", ""
        try:
            settings = Settings.parse(await self.config.dump())
            viewer = settings.external_viewer_url
            verify_runtime(settings.runtime_directory(self.cache_path()))
            ready, reason = True, "ready_for_explicit_start"
        except (OSError, ValueError, KeyError):
            pass
        except TransportError:
            reason = "configuration_unavailable"
        return Ok({"plugin_id": "minecraft_autonomous", "mode": "autonomous", "stage": "development",
                   "minecraft_version": "1.21.1", "backend_ready": ready, "reason": reason,
                   "viewer_url": viewer, "viewer_body_binding_verified": False, **state})

    @plugin_entry(
        id="start",
        name="开始自主游玩 / Start autonomous play / 自律プレイ開始",
        description="按目标启动 Minecraft 1.21.1 自主游玩；需要启用配置、安装后端并绑定 decision 模型。返回受理状态，连接结果请查 status。",
    )
    async def start(self, goal: str = "survive", **_):
        with self._control_lock:
            if self._worker and self._worker.snapshot()["worker_alive"]:
                return Ok(self._worker.snapshot())
            self._generation += 1
            generation = self._generation
        try:
            if not isinstance(goal, str) or not goal.strip() or len(goal) > 4000:
                raise ValueError("invalid_goal: goal must contain 1..4000 characters")
            settings = Settings.parse(await self.config.dump())
            if not settings.enabled:
                return Err({"code": "autonomy_disabled", "message": "先在配置中启用 autonomy；插件不会自动进入游戏。"})
            settings.require_server()
            entry = verify_runtime(settings.runtime_directory(self.cache_path()))
            if self.ctx.models is None:
                return Err({"code": "model_gateway_unavailable", "message": "需要支持公共模型接口的 N.E.K.O，并绑定 decision 模型。"})
            data = self.data_path("sessions", settings.identity, "host")
            config_path = data / "client.json"

            async def play(goal, publish, stopped):
                try:
                    client = await self.ctx.models.get_client()

                    async def decide(messages, tools):
                        response = await client.chat.completions.create(
                            model="decision", messages=messages, tools=tools, parallel_tool_calls=False,
                            max_completion_tokens=settings.max_output_tokens,
                        )
                        message = response.choices[0].message
                        return {"content": message.content, "tool_calls": [call.model_dump(exclude_none=True)
                                                                         for call in message.tool_calls or []]}

                    bridge = MinecraftBridge(settings.node, entry, config_path, data / "backend.log")
                    if not stopped():
                        await Controller(bridge, decide, settings, data, publish, stopped).run(goal)
                finally:
                    await self.ctx.models.aclose()

            with self._control_lock:
                if generation != self._generation:
                    return Err({"code": "start_cancelled", "message": "启动期间已收到停止指令。"})
                data.mkdir(parents=True, exist_ok=True)
                config_path.write_text(json.dumps(settings.client_config(self.data_path()), ensure_ascii=False), encoding="utf-8")
                self._operator_state(False)
                self._worker = Worker(play, data / "host-error.log")
                self._worker.start(goal.strip())
                return Ok({"accepted": True, **self._worker.snapshot()})
        except (OSError, ValueError, KeyError) as error:
            return Err({"code": "configuration_error", "message": str(error)})
        except TransportError:
            return Err({"code": "configuration_unavailable", "message": "宿主配置接口暂不可用，未启动游戏。"})

    @plugin_entry(
        id="stop",
        name="停止自主游玩 / Stop autonomous play / 自律プレイ停止",
        description="停止决策并断开插件拥有的 Minecraft 连接，保留账本；可重复调用。",
        timeout=30,
    )
    async def stop(self, **_):
        with self._control_lock:
            self._generation += 1
            self._operator_state(True)
            worker = self._worker
        stopped = await asyncio.to_thread(worker.stop) if worker else True
        if not stopped:
            return Err({"code": "stop_pending", "message": "停止指令已生效，资源仍在清理；新的启动会被拒绝。"})
        return await self.status()
