"""Offline device-grant contracts; no live identity, network, model or game."""

import asyncio
import copy
import importlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from plugin.sdk.plugin import Err, Ok


@pytest.fixture
def link_modules(plugin_instance, plugin_module, monkeypatch):
    link = importlib.import_module(plugin_module.__name__ + '.neko_account_link')
    panel = importlib.import_module(plugin_module.__name__ + '.neko_account_panel')
    monkeypatch.setattr(panel, 'POLL_SECONDS', .001)
    monkeypatch.setattr(panel, 'MAX_WAIT_SECONDS', .02)
    return link, panel


def transport(link, value, *, phase='ready', lose=None):
    calls = []

    def handle(request):
        path = request.url.path
        calls.append((request.method, path))
        if path == '/api/v1/auth/neko':
            return httpx.Response(200, json={'available': True})
        if request.method == 'POST' and path.endswith('/requests'):
            if lose == 'create':
                raise httpx.ReadError('fixture unknown', request=request)
            return httpx.Response(200, json={'clientId': value['clientId'], 'username': value['username'],
                'verificationUrl': link.PORTAL + '/join?neko_request=' + value['clientId']})
        if path.endswith('/activate') and lose == 'activate':
            raise httpx.ReadError('fixture unknown', request=request)
        state = {'clientId': value['clientId'], 'username': value['username'], 'phase': phase,
                 'ready': phase == 'ready', 'gameAccountCreated': phase == 'ready', 'gameAddress': link.ADDRESS,
                 'gameVersion': link.VERSION, 'playerUuid': link.expected_uuid(value['username'])}
        assert request.headers['authorization'] == 'Bearer qnp_' + value['clientSecret']
        return httpx.Response(200, json=state)

    return httpx.MockTransport(handle), calls


def test_local_identity_is_private_stable_and_never_in_public_state(link_modules):
    link, _ = link_modules
    value = link.ensure_link()
    assert link.NAME.fullmatch(value['username'])
    assert link.ensure_link() == value
    state = json.dumps(link.public_link(value))
    for key in ('clientSecret', 'gamePassword', 'requestId'):
        assert value[key] not in state
    original = copy.deepcopy(value)
    value['clientSecret'] = 'x' * 43
    with pytest.raises(ValueError, match='neko_link_identity_conflict'):
        link.save_link(value)
    assert link.load_link() == original
    with pytest.raises(ValueError):
        link.ensure_link('ag_Different')


def test_site_without_sso_does_not_create_an_upstream_request(link_modules, run_async):
    link, _ = link_modules
    value = link.ensure_link()
    calls = []

    def handle(request):
        calls.append((request.method, request.url.path))
        return httpx.Response(404, text='Not found')

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            result = await link.advance_link(client, value)
            assert result['phase'] == 'provider_not_configured'
            assert result['selected'] is True and result['username'] == value['username']
    run_async(scenario())
    assert calls == [('GET', '/api/v1/auth/neko')]
    assert link.load_link()['request_sent'] is False


def test_background_resume_reloads_durable_submission_flags_under_the_lease(link_modules, plugin_instance, monkeypatch, run_async):
    link, panel = link_modules
    stale = link.ensure_link()
    current = copy.deepcopy(stale)
    current['request_sent'] = current['activation_sent'] = True
    link.save_link(current)
    observed = []

    async def advance(_client, value, **_):
        observed.append(copy.deepcopy(value))
        return {'phase': 'failed'}

    monkeypatch.setattr(panel, 'advance_link', advance)

    async def scenario():
        plugin_instance._neko_link_cancel = asyncio.Event()
        await plugin_instance._run_neko_link(stale)
    run_async(scenario())
    assert len(observed) == 1
    assert observed[0]['request_sent'] is True
    assert observed[0]['activation_sent'] is True


@pytest.mark.parametrize('bad', ['[]', '{}', '{"schema":"other"}'])
def test_corrupt_private_record_is_preserved_and_never_replaced(link_modules, bad):
    link, _ = link_modules
    path = link.link_path()
    path.parent.mkdir(parents=True)
    path.write_text(bad, encoding='utf-8')
    path.chmod(0o600)
    with pytest.raises(ValueError, match='private_material_unavailable'):
        link.ensure_link()
    assert path.read_text('utf-8') == bad


def test_device_grant_create_is_sent_once_then_only_original_status_is_read(link_modules, run_async):
    link, _ = link_modules
    value = link.ensure_link('ag_Offline')
    mock, calls = transport(link, value, phase='authorization_required')

    async def scenario():
        async with httpx.AsyncClient(transport=mock) as client:
            for _ in range(2):
                result = await link.advance_link(client, value)
                assert result['phase'] == 'authorization_required'
    run_async(scenario())
    assert sum(method == 'POST' for method, _ in calls) == 1
    assert link.load_link()['request_sent'] is True
    assert not link.load_link()['activation_sent']


@pytest.mark.parametrize('lost', ['create', 'activate'])
def test_lost_admission_never_replays_a_post_on_resume(link_modules, run_async, lost):
    link, _ = link_modules
    value = link.ensure_link('ag_Unknown')
    mock, calls = transport(link, value, phase='approved', lose=lost)

    async def first():
        async with httpx.AsyncClient(transport=mock) as client:
            with pytest.raises(ValueError, match='unconfirmed'):
                await link.advance_link(client, value)
    run_async(first())
    if lost == 'activate':
        assert link.load_link()['activation_sent'] is True
    before = sum(method == 'POST' for method, _ in calls)
    next_mock, next_calls = transport(link, value, phase='ready')

    async def resume():
        async with httpx.AsyncClient(transport=next_mock) as client:
            assert (await link.advance_link(client, link.load_link()))['phase'] == 'ready'
    run_async(resume())
    assert before in (1, 2)
    assert not any(method == 'POST' for method, _ in next_calls)


def test_wrong_game_identity_or_redirect_never_becomes_ready(link_modules, run_async):
    link, _ = link_modules
    value = link.ensure_link('ag_Exact')

    def wrong(request):
        if request.url.path.endswith('/auth/neko'):
            return httpx.Response(200, json={'available': True})
        return httpx.Response(200, json={'clientId': value['clientId'], 'username': value['username'],
            'verificationUrl': 'https://attacker.example/?token=bad'})
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(wrong)) as client:
            with pytest.raises(ValueError, match='response_mismatch'):
                await link.advance_link(client, value)
    run_async(scenario())
    assert link.load_link()['phase'] != 'configured'


def test_expired_authorization_renews_only_on_explicit_request_and_keeps_identity(link_modules, run_async):
    link, _ = link_modules
    value = link.ensure_link('ag_Renew')
    value['request_sent'] = True
    link.save_link(value)
    original = copy.deepcopy(value)
    calls = []

    def handle(request):
        calls.append(request.method)
        base = {'clientId': value['clientId'], 'username': value['username']}
        return httpx.Response(200, json={**base, 'phase': 'expired' if request.method == 'GET' else 'authorization_required', 'renewable': True})
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            assert (await link.advance_link(client, value))['renewable'] is True
            assert calls == ['GET']
            assert (await link.advance_link(client, value, renew=True))['phase'] == 'authorization_required'
    run_async(scenario())
    assert calls == ['GET', 'GET', 'POST']
    for key in link.IMMUTABLE:
        assert link.load_link()[key] == original[key]


@pytest.mark.parametrize('blocked', ['worker', 'identity', 'external', 'manual_login'])
def test_original_identity_or_active_runtime_is_not_replaced(link_modules, plugin_instance, monkeypatch, run_async, blocked):
    link, panel = link_modules
    raw = {'runtime': {'mode': 'external'}} if blocked == 'external' else {}
    if blocked == 'worker':
        plugin_instance._worker = SimpleNamespace(snapshot=lambda: {'worker_alive': True})
    if blocked == 'identity':
        monkeypatch.setattr(panel, 'selected_identity', lambda: '/private/original.json')
    if blocked == 'manual_login':
        raw = {'server': {'host': 'micro.kangqiang.site', 'username': 'ag_Original', 'login_config_file': '/original/login.json'}}
    monkeypatch.setattr(plugin_instance.config, 'dump', AsyncMock(return_value=raw))
    result = run_async(plugin_instance.connect_neko_account())
    assert isinstance(result, Err)
    assert not link.link_path().exists()


@pytest.mark.parametrize('committed', [False, True])
def test_ui_job_prepares_login_without_start_or_replaying_an_unconfirmed_save(
    link_modules, plugin_instance, monkeypatch, run_async, committed
):
    link, panel = link_modules
    value = link.ensure_link('ag_Login')
    mock, _ = transport(link, value)
    original_client = httpx.AsyncClient
    monkeypatch.setattr(panel.httpx, 'AsyncClient', lambda **_: original_client(transport=mock))
    raw = {}

    async def update(patch):
        for key, fields in patch.items():
            raw.setdefault(key, {}).update(copy.deepcopy(fields))
    monkeypatch.setattr(plugin_instance.config, 'dump', AsyncMock(side_effect=lambda: copy.deepcopy(raw)))
    monkeypatch.setattr(plugin_instance.config, 'update', AsyncMock(side_effect=update))
    plugin_instance._operator_state(True)
    original_login = plugin_instance.configure_server_login

    async def unconfirmed(*args, **kwargs):
        if committed:
            assert isinstance(await original_login(*args, **kwargs), Ok)
        return Err({'code': 'settings_save_unconfirmed'})
    writer = AsyncMock(side_effect=unconfirmed)
    monkeypatch.setattr(plugin_instance, 'configure_server_login', writer)

    async def scenario():
        assert isinstance(await plugin_instance.connect_neko_account(), Ok)
        await plugin_instance._neko_link_task
        assert plugin_instance.neko_account_state()['phase'] == 'neko_link_configuration_unconfirmed'
        assert isinstance(await plugin_instance.connect_neko_account(), Ok)
        await plugin_instance._neko_link_task
    run_async(scenario())
    assert writer.await_count == 1
    assert plugin_instance._worker is None
    assert json.loads(plugin_instance.data_path('operator.json').read_bytes())['explicit_stop'] is True
    if committed:
        assert plugin_instance.neko_account_state()['configured'] is True
        assert raw['server']['username'] == 'ag_Login'
    assert value['gamePassword'] not in json.dumps(raw)


def test_shutdown_cancels_queries_and_preserves_the_original_request(link_modules, plugin_instance, monkeypatch, run_async):
    link, panel = link_modules
    value = link.ensure_link('ag_Paused')
    mock, calls = transport(link, value, phase='authorization_required')
    original_client = httpx.AsyncClient
    monkeypatch.setattr(panel.httpx, 'AsyncClient', lambda **_: original_client(transport=mock))
    monkeypatch.setattr(panel, 'MAX_WAIT_SECONDS', 60)

    async def scenario():
        await plugin_instance.connect_neko_account()
        while not link.load_link()['request_sent']:
            await asyncio.sleep(.001)
        await plugin_instance._close_neko_link()
    run_async(scenario())
    assert plugin_instance._neko_link_task.done()
    assert link.load_link()['clientId'] == value['clientId']
    assert sum(method == 'POST' for method, _ in calls) <= 1
    assert plugin_instance._worker is None
