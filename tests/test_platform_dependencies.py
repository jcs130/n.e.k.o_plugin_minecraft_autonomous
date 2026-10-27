import hashlib
import importlib.util
import json
import shutil
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest


def loader():
    path = Path(__file__).resolve().parents[1] / 'platform_dependencies.py'
    spec = importlib.util.spec_from_file_location('isolated_platform_dependencies', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixture_layer(tmp_path, contents=None):
    assets = tmp_path / 'assets'
    assets.mkdir()
    values = contents or {'library/__init__.py': b'fixed = True\n'}
    archive = assets / 'win32-cp311-x64.zip'
    with zipfile.ZipFile(archive, 'w') as packed:
        for name, data in values.items():
            packed.writestr(name, data)
    manifest = {'schema': 'neko-mc-platform-python/v1',
                'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'files': {k: {'size': len(v), 'sha256': hashlib.sha256(v).hexdigest()} for k, v in values.items()}}
    (assets / 'win32-cp311-x64.json').write_text(json.dumps(manifest), encoding='utf-8')
    return assets


def test_platform_cache_verifies_every_member_and_reuses_fixed_bytes(tmp_path):
    module = loader()
    assets = fixture_layer(tmp_path)
    target = module.prepare_layer(assets, tmp_path / 'cache')
    assert target.name.startswith('w-') and len(target.name) == 34
    assert module.prepare_layer(assets, tmp_path / 'cache') == target
    (target / 'library/__init__.py').write_text('tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='cache_integrity_failed'):
        module.prepare_layer(assets, tmp_path / 'cache')


@pytest.mark.parametrize('name', ['../escape.py', '/absolute.py', 'C:/escape.py', 'nested\\escape.py'])
def test_unsafe_archive_paths_never_escape_cache(tmp_path, name):
    with pytest.raises(ValueError, match='manifest_invalid'):
        loader().prepare_layer(fixture_layer(tmp_path, {name: b'bad'}), tmp_path / 'cache')
    assert not (tmp_path / 'escape.py').exists()


def test_archive_tampering_is_rejected_before_extraction(tmp_path):
    assets = fixture_layer(tmp_path)
    (assets / 'win32-cp311-x64.zip').write_bytes(b'bad')
    with pytest.raises(ValueError, match='integrity_failed'):
        loader().prepare_layer(assets, tmp_path / 'cache')
    assert not (tmp_path / 'cache').exists()


def test_extra_importable_cache_file_is_not_trusted(tmp_path):
    module = loader()
    assets = fixture_layer(tmp_path)
    target = module.prepare_layer(assets, tmp_path / 'cache')
    (target / 'json.py').write_text('injected = True', encoding='utf-8')
    with pytest.raises(ValueError, match='cache_integrity_failed'):
        module.prepare_layer(assets, tmp_path / 'cache')


def windows_sharing_error():
    error = PermissionError('temporary file sharing lock')
    error.winerror = 5
    return error


def patch_layer_rename(module, monkeypatch, rename):
    class LayerPath(type(Path())):
        def rename(self, target):
            return rename(self, target)

    monkeypatch.setattr(module, 'Path', LayerPath)


def test_temporary_windows_commit_lock_is_retried_without_reextracting(tmp_path, monkeypatch):
    module = loader()
    assets = fixture_layer(tmp_path)
    original = Path.rename
    attempts, sleeps = [], []

    def rename(source, target):
        attempts.append(source)
        if len(attempts) < 3:
            raise windows_sharing_error()
        return original(source, target)

    patch_layer_rename(module, monkeypatch, rename)
    monkeypatch.setattr(module, 'time', SimpleNamespace(sleep=sleeps.append))
    target = module.prepare_layer(assets, tmp_path / 'cache')
    assert (target / 'library/__init__.py').read_bytes() == b'fixed = True\n'
    assert len(attempts) == 3 and len(set(attempts)) == 1 and len(sleeps) == 2


def test_persistent_windows_commit_denial_stays_bounded(tmp_path, monkeypatch):
    module = loader()
    attempts = []

    def denied(source, target):
        attempts.append(source)
        raise windows_sharing_error()

    patch_layer_rename(module, monkeypatch, denied)
    monkeypatch.setattr(module, 'time', SimpleNamespace(sleep=lambda _: None))
    with pytest.raises(PermissionError):
        module.prepare_layer(fixture_layer(tmp_path), tmp_path / 'cache')
    assert len(attempts) == 6
    assert list((tmp_path / 'cache').iterdir()) == []


def test_commit_retry_never_replaces_an_invalid_concurrent_target(tmp_path, monkeypatch):
    module = loader()
    attempts = []

    def competing(source, target):
        attempts.append(source)
        (target / 'library').mkdir(parents=True)
        (target / 'library/__init__.py').write_text('tampered', encoding='utf-8')
        raise windows_sharing_error()

    patch_layer_rename(module, monkeypatch, competing)
    with pytest.raises(PermissionError):
        module.prepare_layer(fixture_layer(tmp_path), tmp_path / 'cache')
    assert len(attempts) == 1
    assert next((tmp_path / 'cache').glob('w-*/library/__init__.py')).read_text('utf-8') == 'tampered'


def test_commit_accepts_a_fully_verified_concurrent_winner(tmp_path, monkeypatch):
    module = loader()

    def competing(source, target):
        shutil.copytree(source, target)
        raise FileExistsError('another probe committed the same resource')

    patch_layer_rename(module, monkeypatch, competing)
    target = module.prepare_layer(fixture_layer(tmp_path), tmp_path / 'cache')
    assert (target / 'library/__init__.py').read_bytes() == b'fixed = True\n'
    assert not list((tmp_path / 'cache').glob('.python-*'))


def test_unclassified_commit_error_is_not_retried(tmp_path, monkeypatch):
    module = loader()
    attempts = []

    def unknown(source, target):
        attempts.append(source)
        error = OSError('unclassified rename failure')
        error.winerror = 123
        raise error

    patch_layer_rename(module, monkeypatch, unknown)
    with pytest.raises(OSError, match='unclassified'):
        module.prepare_layer(fixture_layer(tmp_path), tmp_path / 'cache')
    assert len(attempts) == 1


def test_required_native_dependencies_import_on_actual_supported_platform(plugin_module):
    import cryptography.hazmat.bindings._rust
    import pydantic_core._pydantic_core
    import rpds.rpds
    from jsonschema import Draft202012Validator
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    assert ClientSession and stdio_client
    assert Draft202012Validator({'type': 'integer'}).is_valid(1)
    assert not Draft202012Validator({'type': 'integer'}).is_valid(True)
    suffix = '.pyd' if sys.platform == 'win32' else '.so'
    for module in (rpds.rpds, pydantic_core._pydantic_core, cryptography.hazmat.bindings._rust):
        assert module.__file__.endswith(suffix)
    # The SDK test harness can preload a valid native module before the entry.
    # Do not replace that module just to force a different __file__ in a test.
    assert plugin_module.selected_layer is not None if sys.platform == 'win32' else plugin_module.selected_layer is None


def test_linux_uses_sdk_vendor_without_changing_modules(monkeypatch):
    module = loader()
    monkeypatch.setattr(sys, 'platform', 'linux')
    before = dict(sys.modules)
    assert module.activate() is None
    assert all(sys.modules.get(k) is v for k, v in before.items())
