import hashlib
import importlib
import json

import pytest


def test_optional_pack_integrity_and_standard_off_switch(plugin_module, tmp_path, monkeypatch):
    module = importlib.import_module(plugin_module.__name__ + ".bundled_extension")
    monkeypatch.setattr(module, "PACK", tmp_path)
    raw = {"autonomy": {"enabled": False}}
    assert module.default_bundled_extension_settings(raw) == raw
    source = b"export const createPresentationObserver=()=>({snapshot:()=>null,close(){}});"
    (tmp_path / "presentation.mjs").write_bytes(source)
    metadata = {"schema": "agent-mc-server-presentation/v1", "minecraft_version": "1.21.1",
                "module_sha256": hashlib.sha256(source).hexdigest(), "version": "fixture"}
    (tmp_path / "source.json").write_text(json.dumps(metadata), encoding="utf-8")
    selected = module.default_bundled_extension_settings(raw)
    assert selected["server_extension"]["presentation_sha256"] == metadata["module_sha256"]
    assert selected["autonomy"]["enabled"] is False
    assert module.default_bundled_extension_settings({**selected, "extension_pack": {"mode": "none"}})["server_extension"]["presentation_module"] == ""
    (tmp_path / "presentation.mjs").write_bytes(b"changed")
    assert module.bundled_extension_status(raw)["available"] is False
    assert module.default_bundled_extension_settings(raw) == raw
    with pytest.raises(ValueError):
        module.extension_mode({"extension_pack": {"mode": "unexpected"}})
