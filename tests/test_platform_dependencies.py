import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

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
