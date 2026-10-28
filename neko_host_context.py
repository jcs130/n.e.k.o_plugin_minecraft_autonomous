"""Explicit host profile read and main-brain context transport; no memory clone."""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

import httpx
from agent_mc_autonomy.configuration import _boolean, _text
from agent_mc_autonomy.death_memory import scope_key
from agent_mc_autonomy.host_context import HostContextPort, metadata
from agent_mc_autonomy.ownership import session_is_owned


@dataclass(frozen=True)
class HostContextSettings:
    enabled: bool = True
    character_api_url: str = ""
    memory_api_url: str = ""

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
        memory = _text(section, "memory_api_url").rstrip("/")
        if memory:
            parsed = urlparse(memory)
            if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                    or parsed.path or parsed.username or parsed.password or parsed.query or parsed.fragment):
                raise ValueError("host_context_memory_api_must_be_explicit_local_origin")
        return cls(_boolean(section, "enabled", True), url, memory)


async def character_profile(plugin, config, target, *, fresh=False, timeout=3, allow_current=False):
    if not config.character_api_url or not target and not allow_current:
        return {}
    key = (config.character_api_url, target)
    cache = getattr(plugin, "_host_profile_cache", None)
    if not fresh and cache and cache[0] == key and time.monotonic() - cache[1] < (60 if target else 2):
        return cache[2]
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False, follow_redirects=False) as client:
            response = await client.get(config.character_api_url, params={"language": "zh-CN"})
            response.raise_for_status()
            raw = response.json()
        actor = target or raw.get("当前猫娘")
        profile = raw.get("猫娘", {}).get(actor, {})
        persona = profile.get("system_prompt", "")
        if not isinstance(actor, str) or not actor or len(actor.encode("utf-8")) > 160 or not isinstance(persona, str):
            return {}
        if not persona.strip():
            # Default Neko characters use structured traits; system_prompt is
            # optional. Use only public persona fields, never model/voice data
            # or the entire _reserved object.
            traits = []
            for label in ("昵称", "日常称呼", "自称", "口癖", "口头禅", "说话风格", "性格", "核心特质", "行为特点", "爱好", "雷点", "厌恶", "隐藏设定", "一句话台词", "种族", "年龄", "性别", "性格原型"):
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
        if not fresh:
            plugin._host_profile_cache = (key, time.monotonic(), result)
        return result
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return {}


def live_character_binding(directory, identity, *, now=time.time):
    """Read an existing owned body; never create a lease, connect or call a model."""
    try:
        snapshot = json.loads((directory / "status.json").read_text(encoding="utf-8"))
        age = now() - datetime.fromisoformat(snapshot["updated_at"]).timestamp()
        scope = scope_key(snapshot.get("game_identity"))
        if (not 0 <= age <= 30 or snapshot.get("phase") != "running"
                or snapshot.get("game_connected") is not True or snapshot.get("settings_identity") != identity
                or not scope or not snapshot.get("owner_pid") or not snapshot.get("runtime_session")
                or not session_is_owned(directory)):
            return None
        return (snapshot["owner_pid"], snapshot["runtime_session"], scope)
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        return None


def publish_character_binding(profile, directory, identity, expected, *, now=time.time):
    """Refresh only public persona. Do not extend selected-memory/intent leases."""
    if expected is None or live_character_binding(directory, identity, now=now) != expected:
        return {"available": False, "reason": "no_fresh_owned_binding"}
    if not profile:
        return {"available": False, "reason": "character_unavailable"}
    return HostContextPort(directory, now=now).publish_static(profile, scope=expected[2])


async def character_memories(config, actor, *, timeout=3):
    """Select bounded persistent identity facts from this character's own store.

    This read-only endpoint performs no inference. Suppressed and internal
    records stay out. Preserve original IDs and source rather than inventing
    an empty successful recall or copying recent conversation transcripts.
    """
    if not config.memory_api_url or not actor:
        return None
    from urllib.parse import quote
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False, follow_redirects=False) as client:
            response = await client.get(config.memory_api_url + "/get_persona/" + quote(actor, safe=""))
            response.raise_for_status()
            raw = response.json()
        if not isinstance(raw, dict):
            return None
        rows = []
        for subject in ("relationship", "master", "neko"):
            partition = raw.get(subject, {})
            if not isinstance(partition, dict) or not isinstance(partition.get("facts", []), list):
                return None
            for row in partition.get("facts", []):
                if (not isinstance(row, dict) or row.get("suppress") or not isinstance(row.get("id"), str)
                        or not 0 < len(row["id"].encode()) <= 160 or not isinstance(row.get("text"), str)
                        or not row["text"].strip() or "\x00" in row["text"] or "\x00" in row["id"]
                        or len(row["text"].encode()) > 1800):
                    continue
                rows.append({"id": row["id"], "source": identity_memory_source(actor) + subject, "text": row["text"]})
        # Identity facts are selected independently of current game success.
        # Interleave subjects so one long partition cannot erase the others.
        selected = []
        while rows and len(selected) < 6:
            subjects = set()
            for row in rows[:]:
                if row["source"] not in subjects and len(selected) < 6:
                    if not any(old["id"] == row["id"] for old in selected):
                        selected.append(row)
                    subjects.add(row["source"])
                    rows.remove(row)
        return selected
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return None


def identity_memory_source(actor):
    actor = actor if len(actor.encode()) <= 80 else hashlib.sha256(actor.encode()).hexdigest()
    return "neko-persona:" + actor + ":"


def publish_character_memories(memories, profile, directory, identity, expected, *, now=time.time):
    """Host-selected identity facts, without renewing another producer's intent."""
    if memories is None or not profile or not memories:
        return {"published": False, "reason": "no_selected_identity_memories"}
    if expected is None or live_character_binding(directory, identity, now=now) != expected:
        return {"published": False, "reason": "no_fresh_owned_binding"}
    from agent_mc_autonomy.mailbox import Mailbox
    port = HostContextPort(directory, now=now)
    revision = Mailbox(directory).intent_revision()
    existing = port.read(revision)
    if existing and (existing["stable"]["agent_name"] != profile["agent_name"]
                     or existing["dynamic"].get("current_intent")
                     or any(not row.get("source", "").startswith(identity_memory_source(profile["agent_name"]))
                            for row in existing["dynamic"].get("memories", []))
                     or existing["stable"].get("persona_source") == "host_projection"):
        return {"published": False, "reason": "preserve_explicit_host_projection"}
    snapshot = json.loads((directory / "status.json").read_text(encoding="utf-8"))
    session = str(snapshot["owner_pid"]) + ":" + str((snapshot.get("viewer") or {}).get("session", ""))
    result = port.publish({**profile, "memories": memories}, session=session, revision=revision)
    return {"published": True, **result}


def context_request(port, now, *, enabled=True):
    if not enabled:
        return {"available": False, "needed": False, "reason": "disabled"}
    existing = HostContextPort(port.directory, now=now).read(port.mailbox.intent_revision())
    persona_needed = existing is None or not existing["stable"].get("persona")
    memory_needed = existing is None or not existing["dynamic"].get("memories_selected")
    return {**metadata(existing), "needed": persona_needed or memory_needed,
            "persona_needed": persona_needed, "memory_needed": memory_needed,
            "instructions": "先提交最终判断。context完全可选，needed仅表示可补充，非完成条件；只传你明确选择的当前关注、人格或记忆原id/source/text。公开角色资料不是记忆召回；[]仅表示明确选择为空。"}



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
    intent = supplied.get("current_intent", (previous or {}).get("dynamic", {}).get("current_intent", ""))
    # Missing fields preserve only fresh, session/intent-bound selected context;
    # an explicitly supplied [] clears memory. This is not a host memory clone.
    stable = previous["stable"] if previous else {}
    dynamic = previous["dynamic"] if previous else {}
    return {"agent_name": actor, "persona": supplied.get("persona", stable.get("persona") or profile.get("persona", "")),
            "persona_source": "host_projection" if "persona" in supplied else stable.get("persona_source", profile.get("persona_source", "host_projection")),
            "current_intent": intent, "memories": supplied.get("memories", dynamic.get("memories", [])),
            "memories_selected": "memories" in supplied or dynamic.get("memories_selected", False)}
