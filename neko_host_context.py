"""Explicit host profile read and main-brain context transport; no memory clone."""

import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from agent_mc_autonomy.configuration import _boolean, _text
from agent_mc_autonomy.host_context import HostContextPort, metadata


@dataclass(frozen=True)
class HostContextSettings:
    enabled: bool = True
    character_api_url: str = ""

    @classmethod
    def parse(cls, raw):
        section = raw.get("host_context", {})
        if not isinstance(section, dict):
            raise ValueError("host_context must be a table")
        url = _text(section, "character_api_url").rstrip("/")
        if url:
            parsed = urlparse(url)
            if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                    or parsed.path != "/api/characters" or parsed.username or parsed.password or parsed.query or parsed.fragment):
                raise ValueError("host_context_character_api_must_be_explicit_local_public_endpoint")
        return cls(_boolean(section, "enabled", True), url)


async def character_profile(plugin, config, target):
    if not config.character_api_url:
        return {}
    key = (config.character_api_url, target)
    cache = getattr(plugin, "_host_profile_cache", None)
    if cache and cache[0] == key and time.monotonic() - cache[1] < 60:
        return cache[2]
    try:
        async with httpx.AsyncClient(timeout=3, trust_env=False, follow_redirects=False) as client:
            response = await client.get(config.character_api_url, params={"language": "zh-CN"})
            response.raise_for_status()
            raw = response.json()
        actor = target or raw.get("当前猫娘")
        profile = raw.get("猫娘", {}).get(actor, {})
        persona = profile.get("system_prompt", "")
        if not isinstance(actor, str) or not actor or not isinstance(persona, str):
            return {}
        if not persona.strip():
            # Default Neko characters use structured traits; system_prompt is
            # optional. Use only public persona fields, never model/voice data
            # or the entire _reserved object.
            traits = []
            for label in ("性格", "核心特质", "行为特点", "口癖", "自称", "昵称", "爱好", "雷点", "厌恶", "隐藏设定", "一句话台词", "种族", "年龄", "性别", "性格原型"):
                value = profile.get(label)
                if isinstance(value, list):
                    value = "；".join(v for v in value[:8] if isinstance(v, str))
                if isinstance(value, str) and value.strip():
                    traits.append(label + ":" + value.strip().encode("utf-8")[:600].decode("utf-8", errors="ignore"))
            persona = "\n".join(traits)
        if not persona.strip():
            return {}
        # A bounded profile excerpt, explicitly not the final host request or
        # runtime-reflected persona. Never forward the whole character object.
        persona = persona.encode("utf-8")[:2400].decode("utf-8", errors="ignore")
        result = {"agent_name": actor, "persona": persona, "persona_source": "character_profile"}
        plugin._host_profile_cache = (key, time.monotonic(), result)
        return result
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return {}


def context_request(port, now, *, enabled=True):
    if not enabled:
        return {"available": False, "needed": False, "reason": "disabled"}
    existing = HostContextPort(port.directory, now=now).read(port.mailbox.intent_revision())
    persona_needed = existing is None or not existing["stable"].get("persona")
    memory_needed = existing is None or not existing["dynamic"].get("memories_selected")
    return {**metadata(existing), "needed": persona_needed or memory_needed,
            "persona_needed": persona_needed, "memory_needed": memory_needed,
            "instructions": "这是你的Minecraft身体与动作规划器。当前人格、相关记忆和关注应共享，不能另立角色。"
            "若memory_needed，使用你已有的recall_memory按当前游戏目标/用户偏好召回少量相关记忆；"
            "最终判断通过context携带current_intent及记忆原id/source/text，未命中用空列表，不编造。"
            "agent_name用你的角色名；若persona_needed，提供当前人格要点persona，标记为主脑投影；不要复制整个聊天历史。"
            "这是私有规划上下文，不是口播稿，也不是当前世界事实。"}


async def shared_context(plugin, raw, target, supplied, review, *, existing=None):
    config = HostContextSettings.parse(raw)
    if not config.enabled:
        return None
    profile = await character_profile(plugin, config, target)
    if supplied is not None and not isinstance(supplied, dict):
        raise ValueError("host_context_fields_invalid")
    supplied = supplied or {}
    if set(supplied) - {"agent_name", "persona", "current_intent", "memories"}:
        raise ValueError("host_context_fields_invalid")
    actor = target or profile.get("agent_name") or supplied.get("agent_name")
    if not actor:
        return None
    if supplied.get("agent_name") and supplied["agent_name"] != actor:
        raise ValueError("host_context_character_mismatch")
    if not supplied and not profile:
        return None
    previous = existing if existing and existing["stable"]["agent_name"] == actor else None
    evidence = review.get("evidence", {})
    intent = (supplied.get("current_intent") or (evidence.get("current_user_goal") or {}).get("goal")
              or (evidence.get("current_goal") or {}).get("goal") or evidence.get("standing_goal", ""))
    # Missing fields preserve only fresh, session/intent-bound selected context;
    # an explicitly supplied [] clears memory. This is not a host memory clone.
    stable = previous["stable"] if previous else {}
    dynamic = previous["dynamic"] if previous else {}
    return {"agent_name": actor, "persona": supplied.get("persona", profile.get("persona", stable.get("persona", ""))),
            "persona_source": "host_projection" if "persona" in supplied else profile.get("persona_source", stable.get("persona_source", "host_projection")),
            "current_intent": intent, "memories": supplied.get("memories", dynamic.get("memories", [])),
            "memories_selected": "memories" in supplied or dynamic.get("memories_selected", False)}
