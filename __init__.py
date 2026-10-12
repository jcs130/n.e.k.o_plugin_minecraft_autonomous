"""Public-SDK foundation for an autonomous Minecraft player."""

from plugin.sdk.plugin import Err, NekoPluginBase, Ok, lifecycle, neko_plugin, plugin_entry


@neko_plugin
class MinecraftAutonomousPlugin(NekoPluginBase):
    @lifecycle(id="startup")
    async def on_startup(self, **_):
        return await self.status()

    @lifecycle(id="shutdown")
    async def on_shutdown(self, **_):
        return await self.stop()

    @plugin_entry(
        id="status",
        name="自主游玩状态 / Autonomous play status / 自律プレイ状態",
        description="报告插件接入状态；当前版本尚未接入游戏后端。",
        kind="service",
    )
    async def status(self, **_):
        return Ok(
            {
                "plugin_id": "minecraft_autonomous",
                "mode": "autonomous",
                "stage": "repository_scaffold",
                "backend_ready": False,
                "game_connected": False,
                "autonomy_running": False,
                "reason": "backend_not_integrated",
            }
        )

    @plugin_entry(
        id="start",
        name="开始自主游玩 / Start autonomous play / 自律プレイ開始",
        description="请求按目标自主游玩；当前版本会返回后端尚未接入，不执行游戏动作。",
    )
    async def start(self, goal: str = "survive", **_):
        return Err(
            {
                "code": "backend_not_integrated",
                "message": "游戏后端尚未接入。当前版本只提供仓库基础，不能开始自主游玩。",
            }
        )

    @plugin_entry(
        id="stop",
        name="停止自主游玩 / Stop autonomous play / 自律プレイ停止",
        description="保持停止状态，可重复调用；当前没有游戏后端或运行中的任务。",
    )
    async def stop(self, **_):
        return await self.status()
