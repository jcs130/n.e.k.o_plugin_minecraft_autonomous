"""N.E.K.O. privacy check and first-person game context."""

import httpx
from plugin.sdk.plugin import Err

from .neko_host_context import HostContextSettings

SELF_PLAY = ("你正在用自己绑定的身体玩《我的世界》。Worker 执行你的决定。"
             "用第一人称描述自己的行动，以这个身体的游戏观测和执行回执为准。"
             "把桌面画面、队友视角和队友行动归给各自的来源。")


async def gameplay_privacy_error(raw):
    """Read the public privacy switch before admitting a new game session."""
    try:
        profile = HostContextSettings.parse(raw)
        origin = profile.character_api_url.removesuffix("/api/characters") or "http://127.0.0.1:48911"
        async with httpx.AsyncClient(timeout=2, trust_env=False, follow_redirects=False) as client:
            response = await client.get(origin + "/api/proactive/settings")
            response.raise_for_status()
            result = response.json()
        if result.get("success") is True:
            enabled = result["settings"]["proactiveVisionEnabled"]
            if enabled is False:
                return None
            if enabled is True:
                return Err({"code": "gameplay_screen_vision_enabled",
                            "message": "请在 N.E.K.O. 主页开启「隐私模式」，结束手动屏幕共享，再开始游玩。"})
    except (httpx.HTTPError, OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return Err({"code": "gameplay_screen_privacy_unconfirmed",
                "message": "暂未核对到 N.E.K.O. 的隐私模式。请在同一台电脑打开 N.E.K.O. 并开启隐私模式后重试。"})
