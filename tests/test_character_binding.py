import importlib
import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from agent_mc_autonomy.host_context import HostContextPort
from agent_mc_autonomy.ownership import session_lease


def setup(plugin, monkeypatch):
    module = importlib.import_module(plugin.__class__.__module__ + ".neko_character_binding")
    raw = {"autonomy": {"enabled": True}, "server": {"host": "example.invalid", "username": "Yui"},
           "heartbeat": {"enabled": False, "target": "YUI"}, "presentation": {"enabled": False},
           "host_context": {"enabled": True, "character_api_url": "http://127.0.0.1:48931/api/characters"}}
    monkeypatch.setattr(plugin.config, "dump", AsyncMock(return_value=raw))
    settings = module.Settings.parse(raw)
    directory = settings.data_root(plugin.data_path()) / "sessions" / settings.identity / "host"
    directory.mkdir(parents=True, exist_ok=True)
    snapshot = {"updated_at": datetime.now(timezone.utc).isoformat(), "phase": "running", "game_connected": True,
                "settings_identity": settings.identity, "owner_pid": 123, "runtime_session": "session-one",
                "game_identity": {"realm": "test", "account": "account-one", "agent": "Yui"}}
    (directory / "status.json").write_text(json.dumps(snapshot), encoding="utf-8")
    profile = {"agent_name": "YUI", "persona": "自称:本喵", "persona_source": "character_profile"}
    monkeypatch.setattr(module, "character_profile", AsyncMock(return_value=profile))
    return module, raw, settings, directory, snapshot


def test_disabled_heartbeat_still_binds_persona_without_model_or_messages(plugin_instance, monkeypatch, run_async):
    module, _, settings, directory, _ = setup(plugin_instance, monkeypatch)
    with session_lease(directory):
        result = run_async(plugin_instance.sync_character_context()).value
    assert result["available"] and result["persona_source"] == "character_profile"
    assert "identity_memories" not in result
    projected = HostContextPort(directory).read(0)
    assert projected["stable"]["persona"] == "自称:本喵"
    assert projected["dynamic"] == {"current_intent": "", "memories": [], "memories_selected": False}
    assert not (directory / "host-context.json").exists()
    assert module.character_profile.await_count == 1
    assert settings.identity


@pytest.mark.parametrize("change", ["stale", "identity", "disconnected", "owner", "session"])
def test_late_profile_cannot_bind_a_stale_or_replaced_body(plugin_instance, monkeypatch, run_async, change):
    module, _, _, directory, snapshot = setup(plugin_instance, monkeypatch)

    async def changed(*_, **__):
        if change == "stale":
            snapshot["updated_at"] = datetime.fromtimestamp(time.time() - 31, timezone.utc).isoformat()
        elif change == "identity":
            snapshot["settings_identity"] = "another-account"
        elif change == "disconnected":
            snapshot["game_connected"] = False
        elif change == "owner":
            snapshot["owner_pid"] = 456
        else:
            snapshot["runtime_session"] = "session-two"
        (directory / "status.json").write_text(json.dumps(snapshot), encoding="utf-8")
        return {"agent_name": "YUI", "persona": "旧资料", "persona_source": "character_profile"}

    monkeypatch.setattr(module, "character_profile", changed)
    with session_lease(directory):
        assert not run_async(plugin_instance.sync_character_context()).value["available"]
    assert not (directory / "host-character.json").exists()


def test_binding_requires_real_held_lease(plugin_instance, monkeypatch, run_async):
    module, _, _, directory, _ = setup(plugin_instance, monkeypatch)
    assert not run_async(plugin_instance.sync_character_context()).value["available"]
    module.character_profile.assert_not_awaited()
    assert not (directory / "owner.lock").exists()


@pytest.mark.parametrize("change", ["disable", "stop", "target", "generation"])
def test_configuration_and_stop_races_reject_publication(plugin_instance, monkeypatch, run_async, change):
    module, raw, _, directory, _ = setup(plugin_instance, monkeypatch)

    async def changed(*_, **__):
        if change == "disable":
            raw["host_context"]["enabled"] = False
        elif change == "stop":
            plugin_instance._operator_state(True)
        elif change == "target":
            raw["heartbeat"]["target"] = "AnotherRole"
        else:
            plugin_instance._generation += 1
        return {"agent_name": "YUI", "persona": "旧资料", "persona_source": "character_profile"}

    monkeypatch.setattr(module, "character_profile", changed)
    with session_lease(directory):
        assert run_async(plugin_instance.sync_character_context()).value["reason"] == "configuration_changed_or_stopped"
    assert not (directory / "host-character.json").exists()


def test_refresh_keeps_stable_prefix_and_does_not_renew_selected_memories(plugin_instance, monkeypatch, run_async):
    _, _, _, directory, _ = setup(plugin_instance, monkeypatch)
    context = HostContextPort(directory)
    context.publish({"agent_name": "YUI", "persona": "", "memories": []}, session="123:", revision=0)
    original = context.path.read_bytes()
    with session_lease(directory):
        run_async(plugin_instance.sync_character_context())
        first = context.read(0)
        run_async(plugin_instance.sync_character_context())
        assert context.read(0) == first
    assert context.path.read_bytes() == original
    assert first["stable"]["persona"] == "自称:本喵"
