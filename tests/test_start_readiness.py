"""Expected first-install states stay actionable without starting a body."""

import copy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from plugin.sdk.plugin import Err, Ok


@pytest.fixture
def saved_config(plugin_instance, plugin_module, monkeypatch):
    from importlib import import_module

    module = import_module(plugin_module.__name__ + '.runtime_preparation')
    monkeypatch.setattr(module, 'supported', lambda: True)
    raw = {}

    async def update(patch):
        for section, fields in patch.items():
            raw.setdefault(section, {}).update(copy.deepcopy(fields))

    writer = AsyncMock(side_effect=update)
    monkeypatch.setattr(plugin_instance.config, 'dump', AsyncMock(side_effect=lambda: copy.deepcopy(raw)))
    monkeypatch.setattr(plugin_instance.config, 'update', writer)
    return raw, writer


@pytest.mark.parametrize('backend,action', [({}, 'prepare_runtime'), ({'node': 'node'}, 'use_prepared_runtime'),
                                         ({'directory': 'missing-user-backend'}, 'use_prepared_runtime')])
def test_quick_start_missing_backend_returns_preparation_state(plugin_instance, saved_config, run_async, backend, action):
    raw, _ = saved_config
    raw['backend'] = backend
    result = run_async(plugin_instance.quick_start(connection={'host': 'fixture.test', 'username': 'Fixture'}))
    assert isinstance(result, Ok)
    assert result.value['success'] is False
    error = result.value['error']
    assert error['code'] == 'runtime_setup_required' and error['next_action'] == action
    assert '组件' in error['message'] and 'README' not in error['message']
    assert plugin_instance._worker is None
    assert not plugin_instance.data_path('operator.json').exists()


def test_direct_start_missing_components_does_not_query_account(plugin_instance, plugin_module, saved_config, run_async, monkeypatch):
    raw, _ = saved_config
    raw.update(autonomy={'enabled': True}, server={'host': 'fixture.test', 'username': 'Fixture'})
    account = AsyncMock(side_effect=AssertionError('unprepared start must not query an account'))
    monkeypatch.setattr(plugin_module, 'qiandengji_preflight', account)
    result = run_async(plugin_instance.start())
    assert isinstance(result, Err) and result.error['code'] == 'runtime_setup_required'
    account.assert_not_awaited()
    assert plugin_instance._worker is None


def test_integrity_failure_is_not_converted_to_missing_components(plugin_instance, run_async, monkeypatch):
    monkeypatch.setattr(plugin_instance, 'save_settings', AsyncMock(return_value=Ok({'saved': True})))
    monkeypatch.setattr(plugin_instance, 'start', AsyncMock(return_value=Err({'code': 'configuration_error',
        'message': 'backend_build_mismatch: source inventory changed'})))
    result = run_async(plugin_instance.quick_start(connection={'host': 'fixture.test', 'username': 'Fixture'}))
    assert isinstance(result, Err) and result.error['code'] == 'configuration_error'


def custom_config():
    return {'server': {'host': 'fixture.test', 'username': 'Fixture'}, 'planner': {'route': 'host'},
            'autonomy': {'enabled': False, 'max_decisions': 7},
            'backend': {'node': 'custom-node', 'directory': 'missing-user-backend'},
            'viewer': {'renderer_directory': 'custom-renderer', 'catalog_file': 'custom-catalog',
                       'bundled_appearance_catalog_file': 'custom-appearance', 'auto_open': False},
            'runtime': {'mode': 'embedded', 'data_directory': 'my-data'}}


def test_explicit_component_selection_preserves_identity_model_and_stop(plugin_instance, saved_config, run_async):
    raw, writer = saved_config
    raw.update(custom_config())
    original = copy.deepcopy(raw)
    plugin_instance._operator_state(True)
    result = run_async(plugin_instance.use_prepared_runtime())
    assert isinstance(result, Ok) and result.value['saved'] is True
    assert writer.await_count == 1
    for section in ['server', 'planner', 'autonomy']:
        assert raw[section] == original[section]
    assert raw['backend'] == {'node': '', 'directory': ''}
    for field in ['renderer_directory', 'catalog_file', 'bundled_appearance_catalog_file']:
        assert raw['viewer'][field] == ''
    assert raw['viewer']['auto_open'] is False and raw['runtime']['data_directory'] == 'my-data'
    assert json.loads(plugin_instance.data_path('operator.json').read_bytes())['explicit_stop'] is True
    assert plugin_instance._worker is None and not plugin_instance._setup_active()


@pytest.mark.parametrize('patch', [{'runtime': {'mode': 'external'}}, {'backend': {'provider': 'java-client'}},
                                 {'viewer': {'url': 'https://viewer.invalid'}}])
def test_component_selection_does_not_take_over_other_runtimes(plugin_instance, saved_config, run_async, patch):
    raw, writer = saved_config
    raw.update(custom_config())
    for key, fields in patch.items():
        raw[key].update(fields)
    original = copy.deepcopy(raw)
    result = run_async(plugin_instance.use_prepared_runtime())
    assert isinstance(result, Err) and raw == original
    writer.assert_not_awaited()


@pytest.mark.parametrize('state', [{'pending': {'task': 'unsettled'}}, {'uncertain': True}, {'inflight_request': 'unknown'}])
def test_component_selection_keeps_unsettled_state_closed(plugin_instance, saved_config, run_async, state):
    from agent_mc_autonomy.configuration import Settings

    raw, writer = saved_config
    raw.update(custom_config())
    # Use the fixture's private directory rather than the relative custom-data example.
    raw['runtime']['data_directory'] = str(plugin_instance.data_path())
    settings = Settings.parse(raw)
    host = settings.data_root(plugin_instance.data_path()) / 'sessions' / settings.identity / 'host'
    host.mkdir(parents=True)
    (host / 'host-state.json').write_text(json.dumps(state), encoding='utf-8')
    assert isinstance(run_async(plugin_instance.use_prepared_runtime()), Err)
    writer.assert_not_awaited()
    assert json.loads((host / 'host-state.json').read_bytes()) == state


@pytest.mark.parametrize('active', ['worker', 'lease', 'setup'])
def test_component_selection_refuses_current_work(plugin_instance, plugin_module, saved_config, run_async, monkeypatch, active):
    from importlib import import_module

    raw, writer = saved_config
    raw.update(custom_config())
    module = import_module(plugin_module.__name__ + '.runtime_preparation')
    if active == 'worker':
        plugin_instance._worker = SimpleNamespace(snapshot=lambda: {'worker_alive': True})
    elif active == 'lease':
        monkeypatch.setattr(module, 'session_is_owned', lambda _: True)
    else:
        monkeypatch.setattr(plugin_instance, '_setup_active', lambda: True)
    assert isinstance(run_async(plugin_instance.use_prepared_runtime()), Err)
    writer.assert_not_awaited()


def test_unsupported_platform_keeps_custom_paths(plugin_instance, plugin_module, saved_config, run_async, monkeypatch):
    from importlib import import_module

    raw, writer = saved_config
    raw.update(custom_config())
    original = copy.deepcopy(raw)
    module = import_module(plugin_module.__name__ + '.runtime_preparation')
    monkeypatch.setattr(module, 'supported', lambda: False)
    assert isinstance(run_async(plugin_instance.use_prepared_runtime()), Err)
    assert raw == original
    assert plugin_instance.runtime_start_error(raw, 'backend_missing')['next_action'] == 'open_advanced_settings'
    writer.assert_not_awaited()
