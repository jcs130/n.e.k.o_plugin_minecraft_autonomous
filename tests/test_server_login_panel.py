import json
from unittest.mock import AsyncMock

import pytest
from agent_mc_autonomy.configuration import Settings
from plugin.sdk.plugin import Err, Ok


@pytest.fixture(autouse=True)
def memory_config(plugin_instance, monkeypatch):
    raw = {}

    async def update(patch):
        for key, value in patch.items():
            if not value or value.get('__replace__') is True:
                raw[key] = {k: v for k, v in value.items() if k != '__replace__'}
            else:
                raw[key] = {**raw.get(key, {}), **value}
        return raw

    monkeypatch.setattr(plugin_instance.config, 'dump', AsyncMock(side_effect=lambda: raw))
    monkeypatch.setattr(plugin_instance.config, 'update', update)


def test_password_is_private_and_blank_refresh_never_erases_it(plugin_instance, run_async):
    connection = {'host': 'fixture.test', 'username': 'Alice', 'port': 25565, 'auth': 'offline'}
    result = run_async(plugin_instance.configure_server_login(connection=connection, enabled=True, password='fixture-only-secret'))
    assert isinstance(result, Ok)
    raw = run_async(plugin_instance.config.dump())
    assert 'fixture-only-secret' not in json.dumps(raw)
    settings = Settings.parse(raw)
    assert settings.login_config_file and settings.username == 'Alice'
    result = run_async(plugin_instance.configure_server_login(enabled=True, password=''))
    assert isinstance(result, Ok)
    assert 'fixture-only-secret' not in str(result)
    assert Settings.parse(run_async(plugin_instance.config.dump())).login_config_file == settings.login_config_file
    result = run_async(plugin_instance.configure_server_login(enabled=False))
    assert isinstance(result, Ok)
    assert Settings.parse(run_async(plugin_instance.config.dump())).login_config_file == ''


def test_password_form_never_changes_a_running_worker_or_external_body(plugin_instance, run_async, monkeypatch):
    from types import SimpleNamespace
    saved = AsyncMock()
    monkeypatch.setattr(plugin_instance, 'save_settings', saved)
    plugin_instance._worker = SimpleNamespace(snapshot=lambda: {'worker_alive': True})
    result = run_async(plugin_instance.configure_server_login(enabled=True, password='fixture-only-secret'))
    assert isinstance(result, Err)
    saved.assert_not_awaited()
    plugin_instance._worker = None
    run_async(plugin_instance.config.update({'runtime': {'mode': 'external'}}))
    assert isinstance(run_async(plugin_instance.configure_server_login(enabled=True, password='fixture-only-secret')), Err)
    saved.assert_not_awaited()


def test_changed_account_requires_its_own_password(plugin_instance, run_async):
    assert isinstance(run_async(plugin_instance.configure_server_login(
        connection={'host': 'fixture.test', 'username': 'Alice'}, enabled=True, password='fixture-only-secret')), Ok)
    rejected = run_async(plugin_instance.configure_server_login(connection={'username': 'Bob'}, enabled=True))
    assert isinstance(rejected, Err)
    assert 'fixture-only-secret' not in str(rejected)
    assert Settings.parse(run_async(plugin_instance.config.dump())).username == 'Alice'


def test_secret_form_rejects_control_characters_without_echo(plugin_instance, run_async):
    result = run_async(plugin_instance.configure_server_login(connection={'host': 'fixture.test', 'username': 'Alice'},
        enabled=True, password='private\nvalue'))
    assert isinstance(result, Err)
    assert 'private' not in str(result)


def test_native_default_selection_replaces_old_overrides(plugin_instance, run_async):
    assert isinstance(run_async(plugin_instance.save_settings({'native': {'combat': {'enabled': False}}})), Ok)
    assert isinstance(run_async(plugin_instance.save_settings({'native': {'journey': {'enabled': False}}})), Ok)
    raw = run_async(plugin_instance.config.dump())
    assert raw['native'] == {'journey': {'enabled': False}}
    assert isinstance(run_async(plugin_instance.save_settings({'native': {}})), Ok)
    assert run_async(plugin_instance.config.dump())['native'] == {}


def test_bounded_perception_settings_save_without_enabling_mineral_vision(plugin_instance, run_async):
    native = {'perception': {'entityView': 'camera', 'entityRange': 32, 'nearbyOccludedRange': 0}}
    assert isinstance(run_async(plugin_instance.save_settings({'native': native})), Ok)
    raw = run_async(plugin_instance.config.dump())
    assert raw['native'] == native
    assert Settings.parse(raw).mineral_vision is False
    rejected = run_async(plugin_instance.save_settings({'native': {'perception': {'nearbyOccludedRange': 17}}}))
    assert isinstance(rejected, Err)
    assert run_async(plugin_instance.config.dump())['native'] == native
