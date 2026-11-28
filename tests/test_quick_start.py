import time
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

from plugin.sdk.plugin import Err, Ok


def test_quick_start_saves_common_settings_then_uses_normal_start(plugin_instance, run_async, monkeypatch):
    saved = AsyncMock(return_value=Ok({"saved": True}))
    started = AsyncMock(return_value=Ok({"accepted": True}))
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    result = run_async(plugin_instance.quick_start(connection={"host": "fixture.test", "port": 25565,
        "username": "Alice", "auth": "offline", "version": "1.21.1", "connection_type": "custom"}))
    assert isinstance(result, Ok)
    patch = saved.call_args.args[0]
    assert patch["runtime"]["mode"] == "embedded"
    assert patch["autonomy"]["enabled"] is True
    assert patch["planner"]["route"] == "host"
    assert patch["heartbeat"]["enabled"] is True
    assert "auto_start" not in str(patch)
    assert "native" not in patch
    assert started.await_count == 1
    assert "Minecraft" in started.call_args.kwargs["goal"]


def test_quick_start_managed_device_is_explicit_and_bound_to_official_server(plugin_instance, run_async, monkeypatch):
    plugin = plugin_instance
    grant = SimpleNamespace(expires_at=time.time() * 1000 + 180_000, token="private-for-fixture-only")
    plugin._body_device_grant = grant
    saved = AsyncMock(return_value=Ok({"saved": True}))
    started = AsyncMock(return_value=Ok({"accepted": True}))
    monkeypatch.setattr(plugin, "save_settings", saved)
    monkeypatch.setattr(plugin, "start", started)
    official = {"host": "micro.kangqiang.site", "port": 25702, "username": "Alice"}
    wrong_panel = run_async(plugin.quick_start(connection=official, enable_device_handoff=True, uiToken="wrong"))
    assert wrong_panel.error["code"] == "body_device_pairing_required"
    wrong_server = run_async(plugin.quick_start(connection={**official, "host": "fixture.test"},
                                               enable_device_handoff=True, uiToken=plugin.panel_token))
    assert wrong_server.error["code"] == "body_device_connection_mismatch"
    assert not saved.await_count and not started.await_count
    allowed = run_async(plugin.quick_start(connection=official, enable_device_handoff=True, uiToken=plugin.panel_token))
    assert allowed.value["accepted"]
    assert started.call_args.kwargs["device_handoff"] is grant
    assert grant.token not in repr(saved.call_args)


def test_quick_start_changes_only_the_opted_in_voice_setting(plugin_instance, run_async, monkeypatch):
    original = {"native": {"reflex": {"fightBack": False}, "proximity_voice": {"enabled": True}}}
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(return_value=original))
    saved = AsyncMock(return_value=Ok({"saved": True}))
    started = AsyncMock(return_value=Ok({"accepted": True}))
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    connection = {"host": "fixture.test", "username": "Alice"}

    invalid = run_async(plugin_instance.quick_start(connection=connection, game_voice="true"))
    assert isinstance(invalid, Err)
    assert invalid.error["code"] == "invalid_game_voice_selection"
    saved.assert_not_awaited()
    started.assert_not_awaited()

    for enabled in (False, True):
        result = run_async(plugin_instance.quick_start(connection=connection, game_voice=enabled))
        assert isinstance(result, Ok)
        assert saved.call_args.args[0]["native"] == {
            "reflex": {"fightBack": False}, "proximity_voice": {"enabled": enabled},
        }
    assert original["native"]["proximity_voice"]["enabled"] is True
    assert started.await_count == 2


def test_quick_start_validation_failure_never_starts(plugin_instance, run_async, monkeypatch):
    saved = AsyncMock(return_value=Err({"code": "invalid_settings"}))
    started = AsyncMock()
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    assert isinstance(run_async(plugin_instance.quick_start(connection={"host": "bad url"})), Err)
    started.assert_not_awaited()


def test_quick_start_rejects_secrets_and_unknown_controls(plugin_instance, run_async, monkeypatch):
    saved = AsyncMock()
    started = AsyncMock()
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    assert isinstance(run_async(plugin_instance.quick_start(connection={"password": "do-not-store"})), Err)
    saved.assert_not_awaited()
    started.assert_not_awaited()


def test_quick_start_refuses_an_owned_session_before_saving(plugin_instance, run_async, monkeypatch):
    monkeypatch.setattr("agent_mc_autonomy.ownership.session_is_owned", lambda _: True)
    saved = AsyncMock()
    started = AsyncMock()
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    result = run_async(plugin_instance.quick_start(connection={"host": "fixture.test", "username": "Alice"}))
    assert isinstance(result, Err)
    saved.assert_not_awaited()
    started.assert_not_awaited()


def test_quick_start_never_saves_or_starts_over_unknown_work(plugin_instance, run_async, monkeypatch):
    from agent_mc_autonomy.configuration import Settings

    raw = run_async(plugin_instance.config.dump())
    settings = Settings.parse(raw)
    host = settings.data_root(plugin_instance.data_path()) / "sessions" / settings.identity / "host"
    host.mkdir(parents=True, exist_ok=True)
    def unknown(_):
        raise RuntimeError("unknown_native_dispatch")
    monkeypatch.setattr("agent_mc_autonomy.mailbox.Mailbox.check_uncertain", unknown)
    saved = AsyncMock()
    started = AsyncMock()
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    result = run_async(plugin_instance.quick_start(connection={"host": "fixture.test", "username": "Alice"}))
    assert isinstance(result, Err)
    saved.assert_not_awaited()
    started.assert_not_awaited()


def test_first_play_defaults_follow_current_cat_and_keep_generated_account(plugin_instance, run_async, monkeypatch):
    import re

    raw = {}
    async def update(patch):
        for section, values in patch.items():
            raw.setdefault(section, {}).update(values)
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(side_effect=lambda: raw))
    monkeypatch.setattr(plugin_instance.config, "update", update)
    started = AsyncMock(return_value=Ok({"accepted": True}))
    monkeypatch.setattr(plugin_instance, "start", started)
    result = run_async(plugin_instance.quick_start(connection={"auth": "offline"}, character=""))
    assert isinstance(result, Ok)
    raw = run_async(plugin_instance.config.dump())
    assert raw["server"]["host"] == "127.0.0.1"
    nickname = raw["server"]["username"]
    assert re.fullmatch(r"Neko_[a-f0-9]{8}", nickname)
    assert raw["autonomy"]["max_decisions"] == 0
    assert raw["speech_output"]["enabled"] is True
    assert raw["speech_output"]["base_url"] == "http://127.0.0.1:48911"
    assert raw["host_context"]["character_api_url"] == "http://127.0.0.1:48911/api/characters"
    assert raw["heartbeat"]["target"] == raw["presentation"]["target"] == ""
    assert isinstance(run_async(plugin_instance.quick_start(connection={"auth": "offline"})), Ok)
    assert run_async(plugin_instance.config.dump())["server"]["username"] == nickname


def test_quick_start_retains_custom_route_endpoint_limits_and_voice_opt_out(plugin_instance, run_async, monkeypatch):
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(return_value={"speech_output": {"base_url": "http://localhost:32123", "enabled": False},
        "host_context": {"character_api_url": "http://localhost:32123/api/characters"},
        "autonomy": {"max_decisions": 7}, "planner": {"route": "direct"}}))
    saved = AsyncMock(return_value=Ok({"saved": True}))
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", AsyncMock(return_value=Ok({"accepted": True})))
    result = run_async(plugin_instance.quick_start(connection={"host": "fixture.test", "username": "Alice"},
        use_neko_model=False, narration=False))
    assert isinstance(result, Ok)
    patch = saved.call_args.args[0]
    assert patch["speech_output"] == {"enabled": False}
    assert "planner" not in patch and "max_decisions" not in patch["autonomy"]
    assert "character_api_url" not in patch["host_context"]


def test_quick_start_custom_origin_and_current_role_do_not_disable_speech(plugin_instance, run_async, monkeypatch):
    saved = AsyncMock(return_value=Ok({"saved": True}))
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", AsyncMock(return_value=Ok({"accepted": True})))
    result = run_async(plugin_instance.quick_start(connection={"host": "fixture.test", "username": "Alice"},
        character="", neko_url="http://localhost:32123"))
    assert isinstance(result, Ok)
    patch = saved.call_args.args[0]
    assert patch["speech_output"]["enabled"] is True
    assert patch["speech_output"]["base_url"] == "http://localhost:32123"
    assert patch["host_context"]["character_api_url"] == "http://localhost:32123/api/characters"


def test_quick_start_never_invents_microsoft_identity_or_uses_remote_tts(plugin_instance, run_async, monkeypatch):
    saved, started = AsyncMock(), AsyncMock()
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    for args in ({"connection": {"auth": "microsoft"}},
                 {"connection": {"host": "fixture.test", "username": "Alice"}, "neko_url": "https://foreign.test"}):
        assert isinstance(run_async(plugin_instance.quick_start(**args)), Err)
    saved.assert_not_awaited()
    started.assert_not_awaited()



def test_blank_custom_host_never_falls_back_to_localhost(plugin_instance, run_async, monkeypatch):
    saved, started = AsyncMock(), AsyncMock()
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    result = run_async(plugin_instance.quick_start(connection={"connection_type": "custom", "host": ""}))
    assert result.error["code"] == "server_address_required"
    saved.assert_not_awaited()
    started.assert_not_awaited()


def test_new_server_does_not_reuse_old_server_identity_or_login_file(plugin_instance, run_async, monkeypatch):
    current = {"host": "old.test", "username": "PreviouslyUsed", "port": 25600,
               "auth": "offline", "login_config_file": "old-login.json"}
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(return_value={"server": current}))
    saved = AsyncMock(return_value=Ok({"saved": True}))
    started = AsyncMock(return_value=Ok({"accepted": True}))
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    result = run_async(plugin_instance.quick_start(connection={"host": "new.test", "version": "1.21.11"}))
    assert result.value["accepted"]
    connection = saved.call_args.args[0]["server"]
    assert connection["port"] == 25565
    assert connection["username"].startswith("Neko_")
    assert connection["login_config_file"] == ""
    assert connection["version"] == "1.21.11"


def test_local_world_new_port_preserves_offline_name(plugin_instance, run_async, monkeypatch):
    current = {"host": "127.0.0.1", "username": "SameLocalName", "port": 52178, "auth": "offline"}
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(return_value={"server": current}))
    saved = AsyncMock(return_value=Ok({"saved": True}))
    started = AsyncMock(return_value=Ok({"accepted": True}))
    monkeypatch.setattr(plugin_instance, "save_settings", saved)
    monkeypatch.setattr(plugin_instance, "start", started)
    result = run_async(plugin_instance.quick_start(connection={"host": "127.0.0.1", "port": 52180}))
    assert result.value["accepted"]
    assert saved.call_args.args[0]["server"]["username"] == "SameLocalName"



def test_switching_routes_remembers_the_exact_previous_account(plugin_instance, run_async, monkeypatch):
    official = {"host": "micro.kangqiang.site", "port": 25702, "username": "PreviouslyUsed",
                "auth": "offline", "version": "1.21.1", "login_config_file": "original-login.json"}
    raw = {"server": dict(official)}

    async def update(patch):
        for name, fields in patch.items():
            raw.setdefault(name, {}).update(deepcopy(fields))

    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(side_effect=lambda: deepcopy(raw)))
    monkeypatch.setattr(plugin_instance.config, "update", AsyncMock(side_effect=update))
    monkeypatch.setattr(plugin_instance, "start", AsyncMock(return_value=Ok({"accepted": True})))
    local = {"host": "127.0.0.1", "port": 52178, "username": "LocalNeko"}
    assert run_async(plugin_instance.quick_start(connection=local)).value["accepted"]
    assert raw["server"]["login_config_file"] == ""
    assert raw["play_connections"]["qiandeng"]["username"] == "PreviouslyUsed"

    return_to_official = {key: value for key, value in official.items() if key != "login_config_file"}
    assert run_async(plugin_instance.quick_start(connection=return_to_official)).value["accepted"]
    assert raw["server"]["login_config_file"] == "original-login.json"
    assert raw["play_connections"]["vanilla"]["port"] == 52178

    assert run_async(plugin_instance.quick_start(connection={**return_to_official, "username": "AnotherAccount"})).value["accepted"]
    assert raw["server"]["login_config_file"] == ""
