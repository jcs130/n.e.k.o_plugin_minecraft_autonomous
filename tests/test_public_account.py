"""Public signup keeps one locally persisted identity; never starts gameplay."""

import asyncio
import hashlib
import importlib
import json
import sys

import pytest


def modules(plugin_module):
    root = plugin_module.__package__
    return (importlib.import_module(root + '.qiandengji_onboarding'),
            importlib.import_module(root + '.qiandengji_account'))


def test_public_signup_persists_before_exchange_and_resumes_same_role(plugin_module, monkeypatch, tmp_path):
    onboarding, account = modules(plugin_module)
    monkeypatch.setattr(onboarding, 'account_root', lambda: tmp_path)
    first = onboarding.prepare_public_identity('')
    identity = account.read_identity(str(first))[1]
    assert identity['username'].startswith('ag_')
    assert len(identity['username']) <= 12  # leaves room for the server's _eye suffix
    assert onboarding.prepare_public_identity('') == first
    assert account.read_identity(str(first))[1] == identity
    assert onboarding.public_selection({})['mode'] == 'public'
    with pytest.raises(account.AccountError, match='identity_exists_query_status'):
        onboarding.prepare_public_identity('ag_Other')


def test_public_signup_does_not_take_over_an_imported_identity(plugin_module, monkeypatch, tmp_path):
    onboarding, account = modules(plugin_module)
    monkeypatch.setattr(onboarding, 'account_root', lambda: tmp_path)
    identity = tmp_path / 'original.json'
    onboarding._select(identity, 'ag_Original')
    with pytest.raises(account.AccountError, match='identity_exists_query_status'):
        onboarding.prepare_public_identity('')


def test_public_signup_does_not_register_an_eye_role(plugin_module, monkeypatch, tmp_path):
    onboarding, account = modules(plugin_module)
    monkeypatch.setattr(onboarding, 'account_root', lambda: tmp_path)
    with pytest.raises(account.AccountError, match='reserved_observer_name'):
        onboarding.prepare_public_identity('ag_Test_eye')
    assert not list(tmp_path.iterdir())


def test_public_signup_is_an_explicit_hosted_panel_action(plugin_instance):
    from plugin.sdk.plugin.ui import UI_ACTION_META_ATTR
    handler = plugin_instance.collect_entries()['join_public_account'].handler
    assert getattr(handler, UI_ACTION_META_ATTR, {})


def test_public_signup_cannot_repurpose_an_uncertain_neko_request(plugin_module, monkeypatch, tmp_path):
    onboarding, account = modules(plugin_module)
    monkeypatch.setattr(onboarding, 'account_root', lambda: tmp_path)
    with pytest.raises(account.AccountError, match='identity_exists_query_status'):
        onboarding.prepare_public_identity('', seed={'request_sent': True})
    assert not list(tmp_path.iterdir())


def test_public_join_uses_pinned_helper_and_original_identity(plugin_module, monkeypatch, tmp_path, run_async):
    from unittest.mock import AsyncMock
    onboarding, account = modules(plugin_module)
    monkeypatch.setattr(onboarding, 'account_root', lambda: tmp_path)
    path = onboarding.prepare_public_identity('ag_Test')
    value = account.read_identity(str(path))[1]
    invoke = AsyncMock(return_value={'state': 'pending', 'username': 'ag_Test', 'gameAccountCreated': False})
    monkeypatch.setattr(account, '_invoke', invoke)
    result = run_async(account.account_action('join_public', str(path), username='ag_Test', node='owned-node'))
    assert result['ready'] is False
    assert invoke.call_args.args[0][:3] == ['join-plugin', '--portal', account.PORTAL]
    assert invoke.call_args.kwargs['node'] == 'owned-node'
    assert 'invite' not in json.dumps(invoke.call_args.args)
    assert account.read_identity(str(path))[1] == value


def test_account_helper_works_on_host_selector_loop(plugin_module, monkeypatch, tmp_path):
    _, account = modules(plugin_module)
    helper = tmp_path / 'offline-helper.py'
    helper.write_bytes(b'import json; print(json.dumps({"state":"pending"}))\n')
    monkeypatch.setattr(account, 'HELPER', helper)
    monkeypatch.setattr(account, 'HELPER_SHA256', hashlib.sha256(helper.read_bytes()).hexdigest())
    loop = asyncio.SelectorEventLoop()
    try:
        assert loop.run_until_complete(account._invoke([], node=sys.executable)) == {'state': 'pending'}
    finally:
        loop.close()


def test_cancelled_account_helper_exits_without_replay(plugin_module, monkeypatch, tmp_path, run_async):
    _, account = modules(plugin_module)
    helper = tmp_path / 'waiting-helper.py'
    helper.write_bytes(b'import time; time.sleep(10)\n')
    monkeypatch.setattr(account, 'HELPER', helper)
    monkeypatch.setattr(account, 'HELPER_SHA256', hashlib.sha256(helper.read_bytes()).hexdigest())
    original = account.subprocess.Popen
    children = []
    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(account.subprocess, 'Popen', capture)
    async def check():
        task = asyncio.create_task(account._invoke([], node=sys.executable))
        while not children:
            await asyncio.sleep(.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(children) == 1 and children[0].poll() is not None
    run_async(check())
