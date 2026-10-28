"""Static character identity is independent of optional model-driven review."""

import time

from agent_mc_autonomy.configuration import Settings
from plugin.sdk.plugin import Ok, plugin_entry, timer_interval

from .neko_heartbeat import is_stopped
from .neko_host_context import (
    HostContextSettings,
    character_memories,
    character_profile,
    live_character_binding,
    publish_character_binding,
    publish_character_memories,
)


def binding_configuration(raw):
    settings = Settings.parse(raw)
    context = HostContextSettings.parse(raw)
    target = raw.get("heartbeat", {}).get("target") or raw.get("presentation", {}).get("target") or ""
    return settings, context, target


class NekoCharacterBinding:
    @timer_interval(id="refresh_character_context", seconds=10, name="同步角色人格",
                    description="只读公开角色卡并更新本人游戏人格；不调用模型、不投递行动、不复制宿主记忆。")
    async def refresh_character_context(self, **_):
        return await self._refresh_character_context()

    @plugin_entry(id="sync_character_context", kind="service", name="同步游戏人格",
                  description="立即同步当前配置的公开人格，不触发主脑心跳或游戏动作。返回元数据，不返回人格正文。")
    async def sync_character_context(self, **_):
        return await self._refresh_character_context(force=True)

    @plugin_entry(id="load_character_identity_memory", kind="service", name="按需载入角色身份记忆",
                  description="显式选择本角色已有的少量身份记忆供游戏决策参考。只读记忆服务，不调用模型；不复制近期聊天或其他角色记忆。")
    async def load_character_identity_memory(self, **_):
        return await self._refresh_character_context(force=True, include_memories=True)

    async def _refresh_character_context(self, *, force=False, include_memories=False):
        raw = await self.config.dump()
        settings, config, target = binding_configuration(raw)
        if not settings.enabled or not config.enabled or not config.character_api_url or is_stopped(self):
            return Ok({"available": False, "reason": "disabled_or_stopped"})
        directory = settings.data_root(self.data_path()) / "sessions" / settings.identity / "host"
        expected = live_character_binding(directory, settings.identity)
        if expected is None:
            return Ok({"available": False, "reason": "no_fresh_owned_binding"})
        key = (settings.identity, str(directory), config, target, expected)
        with self._control_lock:
            generation = self._generation
            previous = getattr(self, "_character_refresh", None)
        if not force and previous and previous[0] == key and time.monotonic() - previous[1] < 120:
            return Ok({"available": True, "reason": "refresh_not_due"})
        profile = await character_profile(self, config, target, fresh=True, allow_current=True)
        memories = await character_memories(config, profile.get("agent_name")) if profile and include_memories else None
        latest = await self.config.dump()
        with self._control_lock:
            if (self._generation != generation or self._configuration_writes or is_stopped(self)
                    or binding_configuration(latest) != (settings, config, target)):
                return Ok({"available": False, "reason": "configuration_changed_or_stopped"})
            result = publish_character_binding(profile, directory, settings.identity, expected)
            if result.get("available"):
                if include_memories:
                    result["identity_memories"] = publish_character_memories(memories, profile, directory, settings.identity, expected)
                self._character_refresh = (key, time.monotonic())
        return Ok(result)
