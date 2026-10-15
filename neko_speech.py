"""Explicit public output-only adapter; never generates text or owns body work.

Only tool-supplied spoken_text crosses this sanitizer. The host's ordinary
generated final answer is outside this plugin's public API boundary.
"""

import asyncio
import hashlib
import re
from urllib.parse import urlsplit

import httpx
from agent_mc_autonomy.configuration import _boolean, _text

from .neko_commentary import load_commentary, save_commentary


def sanitize_speech(value):
    if not isinstance(value, str) or len(value) > 600:
        return ""
    # Reserved metadata accepts whitespace/chunk splits, nested brackets and
    # future suffixes. Ordinary bracketed game names remain ordinary speech.
    prefix = r"(?:neko\s*_\s*\w+|tts\s*[_:-]\s*\w+|voice\s*[_:-]\s*\w+|speech\s*[_:-]\s*\w+|emotion|prosody|control)"
    value = re.sub(r"<\s*" + prefix + r"\b[^>]*>.*?</\s*[^>]+>", "", value, flags=re.I | re.S)
    value = re.sub(r"[\[<【]+\s*/?\s*" + prefix + r"\b[^\]>】]*(?:[\]>】]+|$)", "", value, flags=re.I | re.S)
    placeholder = (r"no[\s-]+(?:new[\s-]+)?(?:commentary|comments?)"
                   r"(?:[\s-]+(?:is[\s-]+)?needed)?(?:[\s-]+(?:for[\s-]+)?this[\s-]+round)?"
                   r"|本轮(?:无需|不需要|没有)口播|保持安静|无需回复|最终口播正文为空")
    # Normalize wrappers only for recognition, before accepting any speech.
    # Unicode whitespace can alternate with nested delimiters. Check the full
    # message before individual lines so internal newlines cannot leave a
    # speakable fragment behind. Only recognition uses this normalized view.
    wrappers = " \t\r\n[]【】<>〈〉《》()（）{}「」『』\"'‘’“”`*.!。！"
    edges = r"[\s" + re.escape(wrappers) + "]"
    def placeholder_only(text):
        normalized = re.sub("^" + edges + "+|" + edges + "+$", "", text)
        return re.fullmatch(placeholder, normalized, flags=re.I) is not None
    if placeholder_only(value):
        return ""
    value = "\n".join(line for line in value.splitlines() if not placeholder_only(line))
    value = value.strip(" \t\r\n[]【】<>")
    return value if any(c.isalnum() for c in value) else ""


def output_settings(raw, target):
    section = raw.get("speech_output", {})
    if not isinstance(section, dict):
        raise ValueError("speech_output must be a table")
    if not _boolean(section, "enabled", False):
        return None
    base = _text(section, "base_url").rstrip("/")
    url = urlsplit(base)
    if (url.scheme not in {"http", "https"} or url.hostname not in {"localhost", "127.0.0.1", "::1"}
            or url.username or url.password or url.query or url.fragment or url.path or not target):
        raise ValueError("speech_output requires an explicit local Neko base URL and heartbeat target")
    return base


def enqueue_speech(plugin, raw, settings, target, port, generation, text, correlation):
    """Reserve locally before the goal mailbox; HTTP/audio never blocks it.

    Durable reservations survive crashes as unknown and are never replayed.
    At most one output request is active per plugin; busy is an honest refusal.
    """
    base = output_settings(raw, target)
    common = {**correlation, "playback_verified": False}
    if not base:
        return {**common, "status": "disabled"}
    line = sanitize_speech(text)
    if not line:
        return {**common, "status": "empty_or_control_only"}
    path = port.directory / "speech-output.json"
    state = load_commentary(path)
    key = correlation["opportunity_id"]
    records = state.get("records", {})
    if key in records:
        return records[key]
    tasks = getattr(plugin, "_speech_output_tasks", set())
    if tasks:
        return {**common, "status": "busy"}
    receipt = {**common, "status": "reserved_unknown", "text_sha256": hashlib.sha256(line.encode()).hexdigest(),
               "offered_at": port.now(), "transport_accepted": False}
    records[key] = receipt
    save_commentary(path, {"records": dict(list(records.items())[-32:])})
    task = asyncio.create_task(_deliver(plugin, base, target, port, generation, line, receipt, path))
    plugin._speech_output_tasks = tasks
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {**receipt, "status": "enqueued", "delivery_receipt": "speech-output.json"}


def _current(plugin, port, generation, receipt):
    from .neko_heartbeat import is_stopped
    return (plugin._generation == generation and not plugin._configuration_writes and not is_stopped(plugin)
            and port.speech_current(receipt))


async def _deliver(plugin, base, target, port, generation, line, receipt, path):
    status, accepted, reason = "unknown", False, "transport_unknown"
    sent = False
    try:
        if not _current(plugin, port, generation, receipt):
            status, reason = "rejected", "stopped_or_superseded"
            return
        async with httpx.AsyncClient(timeout=3, trust_env=False, follow_redirects=False) as client:
            # Public capability discovery, never private host globals or route takeover.
            capability = await client.get(base + "/openapi.json")
            if capability.status_code != 200 or "post" not in capability.json().get("paths", {}).get("/api/game/{game_type}/speak", {}):
                status, reason = "unsupported", "public_output_endpoint_unavailable"
                return
            if not _current(plugin, port, generation, receipt):
                status, reason = "rejected", "stopped_or_superseded"
                return
            sent = True
            response = await client.post(base + "/api/game/minecraft_autonomous/speak", headers={"Origin": base}, json={
                "lanlan_name": target, "session_id": "minecraft-" + hashlib.sha256(receipt["session"].encode()).hexdigest()[:24],
                "line": line, "request_id": receipt["decision_id"], "sdk_speech_correlation_id": receipt["opportunity_id"],
                "interrupt_audio": False, "emit_turn_end": False, "wait_for_audio_completion": False,
                "mirror_text": True, "playback_gain": 1.0})
            result = response.json()
            accepted = response.status_code == 200 and result.get("ok") is True
            if accepted:
                status, reason = "accepted", "host_output_accepted"
            elif result.get("ok") is False:
                status = "rejected"
                # Bounded machine codes only; never persist raw HTTP bodies or secrets.
                code = result.get("reason", "host_output_rejected")
                reason = code if isinstance(code, str) and re.fullmatch(r"[a-z_]{1,80}", code) else "host_output_rejected"
    except asyncio.CancelledError:
        status, reason = ("unknown", "cancelled_after_submission") if sent else ("rejected", "cancelled_before_submission")
        raise
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        status, reason = ("unknown", "transport_unknown") if sent else ("unavailable", "capability_check_failed")
    finally:
        state = load_commentary(path)
        records = state.get("records", {})
        records[receipt["opportunity_id"]] = {**receipt, "status": status, "reason": reason,
            "transport_accepted": accepted, "updated_at": port.now(), "playback_verified": False}
        try:
            save_commentary(path, {"records": dict(list(records.items())[-32:])})
        except OSError:
            plugin.logger.warning("Minecraft speech receipt persistence failed; output remains unknown and must not replay.")
