"""Select a byte-checked optional resource pack; server logic lives upstream."""

import hashlib
import json
from pathlib import Path

PACK = Path(__file__).resolve().parent / "assets" / "server-extensions" / "qiandengji"
ENGINE_RELATIVE = "extensions/qiandengji/engine.mjs"


def qiandengji_connection(raw):
    """Explicit configured endpoint, never a guess from chat, account name or DNS."""
    from .qiandengji_account import ADDRESS, VERSION
    server = raw.get("server", {})
    host, port = ADDRESS.rsplit(":", 1)
    return (isinstance(server, dict) and str(server.get("host", "")).lower().rstrip(".") == host
            and server.get("port") == int(port) and server.get("version") == VERSION)


def _engine_status(raw, metadata):
    engine = metadata.get("engine")
    if not isinstance(engine, dict):
        return {"available": False}
    verified = {}
    try:
        if engine.get("backend_relative") != ENGINE_RELATIVE:
            raise ValueError("engine_path_invalid")
        original = PACK / "engine.mjs"
        if (not 0 < original.stat().st_size <= 1048576 or original.stat().st_size != engine.get("bytes")
                or hashlib.sha256(original.read_bytes()).hexdigest() != engine.get("sha256")):
            raise ValueError("engine_source_invalid")
        verified = {"sha256": engine["sha256"]}
        directory = Path(raw.get("backend", {}).get("directory", ""))
        if not directory.is_absolute():
            raise ValueError("engine_backend_required")
        module = directory / ENGINE_RELATIVE
        if (module.resolve() != directory.resolve() / ENGINE_RELATIVE or not module.is_file()
                or module.stat().st_size != engine["bytes"]
                or hashlib.sha256(module.read_bytes()).hexdigest() != engine["sha256"]):
            raise ValueError("engine_runtime_invalid")
        return {"available": True, "module": str(module), "sha256": engine["sha256"],
                "source_revision": engine.get("source_revision")}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"available": False, **verified}


def _managed_presentation(explicit, status):
    value = explicit.get("presentation_module")
    return (not value or (Path(value).parts[-4:] == ("assets", "server-extensions", "qiandengji", "presentation.mjs")
                         and explicit.get("presentation_sha256") == status.get("sha256")))


def _managed_engine(explicit, status):
    value = explicit.get("engine_module")
    return (not value or (Path(value).parts[-3:] == ("extensions", "qiandengji", "engine.mjs")
                         and explicit.get("engine_sha256") == status.get("sha256")))


def extension_mode(raw):
    section = raw.get("extension_pack", {})
    if not isinstance(section, dict) or set(section) - {"mode"} or section.get("mode", "auto") not in {"auto", "none", "custom"}:
        raise ValueError("extension_pack.mode must be auto, none or custom")
    return section.get("mode", "auto")


def bundled_extension_status(raw):
    mode = extension_mode(raw)
    try:
        source = PACK / "source.json"
        if source.stat().st_size > 16384:
            raise ValueError("pack_metadata_too_large")
        metadata = json.loads(source.read_text(encoding="utf-8"))
        module = PACK / "presentation.mjs"
        if (metadata.get("schema") != "agent-mc-server-presentation/v1" or metadata.get("minecraft_version") != "1.21.1"
                or module.stat().st_size > 262144 or hashlib.sha256(module.read_bytes()).hexdigest() != metadata.get("module_sha256")):
            raise ValueError("pack_integrity_mismatch")
        resources = metadata.get("resources", {})
        if not isinstance(resources, dict) or len(resources) > 64:
            raise ValueError("pack_resource_manifest_invalid")
        for relative, expected in resources.items():
            if (not isinstance(relative, str) or "\\" in relative or Path(relative).is_absolute()
                    or any(part in {"", ".", ".."} for part in relative.split("/")) or not isinstance(expected, dict)):
                raise ValueError("pack_resource_path_invalid")
            resource = (PACK / relative).resolve()
            if (not resource.is_relative_to(PACK.resolve()) or not resource.is_file()
                    or resource.stat().st_size > 1048576 or resource.stat().st_size != expected.get("bytes")
                    or hashlib.sha256(resource.read_bytes()).hexdigest() != expected.get("sha256")):
                raise ValueError("pack_resource_integrity_mismatch")
        return {"mode": mode, "available": True, "id": "qiandengji", "version": metadata.get("version"),
                "module": str(module), "sha256": metadata["module_sha256"], "activation": "validated_same_player_server_data",
                "engine": _engine_status(raw, metadata)}
    except (OSError, ValueError, TypeError):
        return {"mode": mode, "available": False, "reason": "optional_pack_missing_or_invalid"}


def default_bundled_extension_settings(raw):
    mode = extension_mode(raw)
    if mode == "none":
        return {**raw, "server_extension": {"presentation_module": "", "presentation_sha256": "", "engine_module": "", "engine_sha256": ""}}
    explicit = raw.get("server_extension", {})
    if not isinstance(explicit, dict):
        raise ValueError("server_extension must be a table")
    if mode == "custom":
        return raw
    status = bundled_extension_status(raw)
    if not _managed_presentation(explicit, status):
        return raw
    if not status["available"]:
        return raw
    selected = {**explicit, "presentation_module": status["module"], "presentation_sha256": status["sha256"]}
    engine = status["engine"]
    if qiandengji_connection(raw) and _managed_engine(explicit, engine):
        if not engine["available"]:
            raise ValueError("千灯纪玩法组件尚未就绪或校验失败。请点击“准备游戏组件”安装匹配版本；未启动游戏。")
        selected.update(engine_module=engine["module"], engine_sha256=engine["sha256"])
    elif not qiandengji_connection(raw) and explicit.get("engine_module") and _managed_engine(explicit, engine):
        selected.update(engine_module="", engine_sha256="")
    return {**raw, "server_extension": selected}
