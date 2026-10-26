"""GUI onboarding keeps credentials out of paths, config and public results."""

import importlib
import json
from unittest.mock import AsyncMock

import pytest
from plugin.sdk.plugin import Err, Ok
from test_qiandengji_account import identity, ready


def onboarding(plugin_module, tmp_path, monkeypatch):
    m = importlib.import_module(plugin_module.__name__ + '.qiandengji_onboarding')
    monkeypatch.setattr(m, 'account_root', lambda: tmp_path / 'user-data' / 'accounts')
    return m


def test_identity_file_picker_preserves_identity_and_does_not_overwrite(plugin_module, tmp_path, monkeypatch):
    m = onboarding(plugin_module, tmp_path, monkeypatch)
    source, account = identity(tmp_path)
    result = m.store_identity(source.read_text('utf-8'))
    assert result.parent.parent == m.account_root()
    assert json.loads(result.read_text('utf-8')) == account
    assert m.store_identity(source.read_text('utf-8')) == result
    assert m.selected_identity() == result
    assert m.public_selection({}) == {'selected': True, 'username': 'ag_Test', 'imported': False}
    account['gamePassword'] = 'a-different-password'
    with pytest.raises(ValueError, match='private_material_conflict'):
        m.store_identity(json.dumps(account))
    assert json.loads(result.read_text('utf-8'))['gamePassword'] == 'private-game-password'


@pytest.mark.parametrize('text', ['{}', 'x' * 16385, '[1]', '{"gamePassword":"never echo this"}'],
                         ids=['empty', 'oversize', 'array', 'incomplete'])
def test_invalid_upload_does_not_create_private_storage(plugin_module, tmp_path, monkeypatch, text):
    m = onboarding(plugin_module, tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='invalid_private_identity'):
        m.store_identity(text)
    assert not m.account_root().exists()


def test_invite_form_reuses_original_pending_request_directory(plugin_module, tmp_path, monkeypatch):
    m = onboarding(plugin_module, tmp_path, monkeypatch)
    invite = 'https://mc.kangqiang.site/join#invite=qdi_' + 'a' * 43
    path, invite_path = m.prepare_invitation('ag_Test', invite)
    assert m.selected_identity() == path
    assert invite_path.read_text('utf-8').strip() == invite
    assert not path.exists()
    assert m.prepare_invitation('ag_Test', invite) == (path, invite_path)
    with pytest.raises(ValueError, match='identity_exists_query_status'):
        m.prepare_invitation('ag_Other', invite)
    with pytest.raises(ValueError, match='private_material_conflict'):
        m.prepare_invitation('ag_Test', invite[:-1] + 'b')


@pytest.mark.parametrize('invite', [
    'http://mc.kangqiang.site/join#invite=qdi_' + 'a' * 43,
    'https://evil.test/join#invite=qdi_' + 'a' * 43,
    'https://mc.kangqiang.site/join?x=1#invite=qdi_' + 'a' * 43,
    'https://mc.kangqiang.site/join#invite=qdi_' + 'a' * 43 + '&extra=1',
])
def test_invalid_invite_never_writes_files(plugin_module, tmp_path, monkeypatch, invite):
    m = onboarding(plugin_module, tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='invalid_private_invitation'):
        m.prepare_invitation('ag_Test', invite)
    assert not m.account_root().exists()


def test_picker_import_keeps_fresh_readiness_and_model_settings(
    plugin_instance, plugin_module, tmp_path, monkeypatch, run_async
):
    m = onboarding(plugin_module, tmp_path, monkeypatch)
    source, _ = identity(tmp_path)
    panel = importlib.import_module(plugin_module.__name__ + '.qiandengji_panel')
    invoke = AsyncMock(return_value=ready())
    account = importlib.import_module(plugin_module.__name__ + '.qiandengji_account')
    monkeypatch.setattr(account, '_invoke', invoke)
    saved = []

    async def save(settings):
        saved.append(settings)
        return Ok({'saved': True})

    monkeypatch.setattr(plugin_instance, 'save_settings', save)
    monkeypatch.setattr(panel, 'require_idle', lambda *_: None)
    result = run_async(plugin_instance.qiandengji_account('import', identity_json=source.read_text('utf-8')))
    assert isinstance(result, Ok)
    assert result.value['imported'] is True
    assert invoke.await_args.args[0] == ['status', '--identity-file', str(m.selected_identity())]
    assert set(saved[0]) == {'server', 'qiandengji'}
    assert 'private-game-password' not in json.dumps(saved)
    assert 'private-game-password' not in json.dumps(result.value)


def test_uploaded_identity_cannot_register_or_write_while_active(
    plugin_instance, plugin_module, tmp_path, monkeypatch, run_async
):
    m = onboarding(plugin_module, tmp_path, monkeypatch)
    source, _ = identity(tmp_path)
    result = run_async(plugin_instance.qiandengji_account('register', identity_json=source.read_text('utf-8')))
    assert isinstance(result, Err)
    assert not m.account_root().exists()
    panel = importlib.import_module(plugin_module.__name__ + '.qiandengji_panel')
    account = importlib.import_module(plugin_module.__name__ + '.qiandengji_account')

    def active(*_):
        raise account.AccountError('account_runtime_active')

    monkeypatch.setattr(panel, 'require_idle', active)
    result = run_async(plugin_instance.qiandengji_account('import', identity_json=source.read_text('utf-8')))
    assert isinstance(result, Err)
    assert not m.account_root().exists()


def test_retried_invitation_queries_saved_identity_instead_of_registering_again(
    plugin_instance, plugin_module, tmp_path, monkeypatch, run_async
):
    m = onboarding(plugin_module, tmp_path, monkeypatch)
    panel = importlib.import_module(plugin_module.__name__ + '.qiandengji_panel')
    invite = 'https://mc.kangqiang.site/join#invite=qdi_' + 'a' * 43
    path, _ = m.prepare_invitation('ag_Test', invite)
    source, _ = identity(tmp_path)
    path.write_bytes(source.read_bytes())
    path.chmod(0o600)
    action = AsyncMock(return_value={'ready': True, 'username': 'ag_Test'})
    monkeypatch.setattr(panel, 'account_action', action)
    result = run_async(plugin_instance.qiandengji_account('register', username='ag_Test', invite_url=invite))
    assert isinstance(result, Ok)
    assert action.await_args.args == ('status', str(path))
    assert result.value.get('imported') is not True


def test_identity_picker_schema_is_write_only_and_paths_are_optional(plugin_instance):
    entry = plugin_instance.collect_entries()['qiandengji_account']
    assert entry.meta.input_schema['required'] == ['action']
    for key in ('identity_json', 'invite_url'):
        assert entry.meta.input_schema['properties'][key]['writeOnly'] is True
