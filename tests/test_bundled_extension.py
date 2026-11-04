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
    explicit_engine = {"engine_module": str(tmp_path / "engine.mjs"), "engine_sha256": "a" * 64}
    composed = module.default_bundled_extension_settings({**raw, "server_extension": explicit_engine})
    assert composed["server_extension"]["engine_module"] == explicit_engine["engine_module"]
    assert composed["server_extension"]["engine_sha256"] == explicit_engine["engine_sha256"]
    disabled = module.default_bundled_extension_settings({**composed, "extension_pack": {"mode": "none"}})
    assert disabled["server_extension"]["engine_module"] == ""
    assert module.default_bundled_extension_settings({**selected, "extension_pack": {"mode": "none"}})["server_extension"]["presentation_module"] == ""
    (tmp_path / "presentation.mjs").write_bytes(b"changed")
    assert module.bundled_extension_status(raw)["available"] is False
    assert module.default_bundled_extension_settings(raw) == raw
    with pytest.raises(ValueError):
        module.extension_mode({"extension_pack": {"mode": "unexpected"}})


def test_bundled_resource_hashes_and_paths_are_checked(plugin_module, tmp_path, monkeypatch):
    module = importlib.import_module(plugin_module.__name__ + ".bundled_extension")
    monkeypatch.setattr(module, "PACK", tmp_path)
    source = b"export const createPresentationObserver=()=>({snapshot:()=>null,close(){}});"
    (tmp_path / "presentation.mjs").write_bytes(source)
    resource = b"original icon"
    (tmp_path / "icon.png").write_bytes(resource)
    metadata = {"schema": "agent-mc-server-presentation/v1", "minecraft_version": "1.21.1",
                "module_sha256": hashlib.sha256(source).hexdigest(), "version": "fixture",
                "resources": {"icon.png": {"bytes": len(resource), "sha256": hashlib.sha256(resource).hexdigest()}}}
    (tmp_path / "source.json").write_text(json.dumps(metadata), encoding="utf-8")
    assert module.bundled_extension_status({})["available"] is True
    (tmp_path / "icon.png").write_bytes(b"changed")
    assert module.bundled_extension_status({})["available"] is False
    metadata["resources"] = {"../icon.png": {"bytes": 1, "sha256": "a" * 64}}
    (tmp_path / "source.json").write_text(json.dumps(metadata), encoding="utf-8")
    assert module.bundled_extension_status({})["available"] is False


def engine_fixture(plugin_module, tmp_path, monkeypatch):
    module = importlib.import_module(plugin_module.__name__ + ".bundled_extension")
    pack = tmp_path / 'plugin/assets/server-extensions/qiandengji'
    pack.mkdir(parents=True)
    monkeypatch.setattr(module, 'PACK', pack)
    presentation = b'export const createPresentationObserver=()=>({});'
    engine = b'export class EngineWorld {}; export const createEngine=()=>null;'
    (pack / 'presentation.mjs').write_bytes(presentation)
    (pack / 'engine.mjs').write_bytes(engine)
    metadata = {'schema':'agent-mc-server-presentation/v1', 'minecraft_version':'1.21.1',
                'module_sha256':hashlib.sha256(presentation).hexdigest(),
                'engine':{'backend_relative':'extensions/qiandengji/engine.mjs',
                          'sha256':hashlib.sha256(engine).hexdigest(), 'bytes':len(engine)}}
    (pack / 'source.json').write_text(json.dumps(metadata), encoding='utf-8')
    backend = tmp_path / 'backend'
    installed = backend / metadata['engine']['backend_relative']
    installed.parent.mkdir(parents=True)
    installed.write_bytes(engine)
    raw = {'server':{'host':'micro.kangqiang.site','port':25702,'version':'1.21.1'},
           'backend':{'directory':str(backend)}, 'autonomy':{'enabled':False}}
    return module, raw, pack, installed, metadata


def test_rpg_engine_uses_explicit_connection_and_same_backend(plugin_module, tmp_path, monkeypatch):
    module, raw, pack, installed, metadata = engine_fixture(plugin_module,tmp_path,monkeypatch)
    selected = module.default_bundled_extension_settings(raw)
    assert selected['server_extension']['engine_module'] == str(installed)
    assert selected['server_extension']['engine_sha256'] == metadata['engine']['sha256']
    assert selected['autonomy']['enabled'] is False
    assert 'server_extension' not in raw
    moved = {**selected,'backend':{'directory':str(installed.parents[2] / 'new')}}
    moved_file = installed.parents[2] / 'new/extensions/qiandengji/engine.mjs'
    moved_file.parent.mkdir(parents=True)
    moved_file.write_bytes(installed.read_bytes())
    assert module.default_bundled_extension_settings(moved)['server_extension']['engine_module'] == str(moved_file)
    away = {**selected,'server':{**raw['server'],'host':'another.example'}}
    assert not module.default_bundled_extension_settings(away)['server_extension']['engine_module']
    for changed in [{'host':'another.example'}, {'port':25565}, {'version':'1.20.4'}]:
        other = {**raw,'server':{**raw['server'],**changed}}
        assert not module.default_bundled_extension_settings(other)['server_extension'].get('engine_module')
    for mode in ['none','custom']:
        manual = {**raw,'extension_pack':{'mode':mode}}
        assert not module.default_bundled_extension_settings(manual).get('server_extension',{}).get('engine_module')
    custom = {**raw,'server_extension':{'engine_module':'D:/custom/engine.mjs','engine_sha256':'b'*64}}
    assert module.default_bundled_extension_settings(custom)['server_extension']['engine_module'] == 'D:/custom/engine.mjs'


def test_saved_managed_presentation_does_not_hide_missing_gameplay_engine(plugin_module,tmp_path,monkeypatch):
    module,raw,pack,installed,metadata = engine_fixture(plugin_module,tmp_path,monkeypatch)
    old = tmp_path / 'old/plugin/assets/server-extensions/qiandengji/presentation.mjs'
    old.parent.mkdir(parents=True)
    old.write_bytes((pack/'presentation.mjs').read_bytes())
    saved = {**raw,'server_extension':{'presentation_module':str(old),'presentation_sha256':metadata['module_sha256']}}
    selected = module.default_bundled_extension_settings(saved)['server_extension']
    assert selected['presentation_module'] == str(pack/'presentation.mjs')
    assert selected['engine_module'] == str(installed)
    custom = {**raw,'server_extension':{'presentation_module':str(tmp_path/'custom.mjs'),'presentation_sha256':'a'*64}}
    assert module.default_bundled_extension_settings(custom) == custom


def test_rpg_engine_missing_tampered_or_untrusted_metadata_stays_unavailable(plugin_module,tmp_path,monkeypatch):
    module,raw,pack,installed,metadata = engine_fixture(plugin_module,tmp_path,monkeypatch)
    original = installed.read_bytes()
    installed.unlink()
    with pytest.raises(ValueError,match='准备游戏组件'):
        module.default_bundled_extension_settings(raw)
    installed.write_bytes(b'tampered')
    with pytest.raises(ValueError,match='准备游戏组件'):
        module.default_bundled_extension_settings(raw)
    installed.write_bytes(original)
    metadata['engine']['backend_relative'] = '../outside.mjs'
    (pack/'source.json').write_text(json.dumps(metadata),encoding='utf-8')
    with pytest.raises(ValueError,match='准备游戏组件'):
        module.default_bundled_extension_settings(raw)
