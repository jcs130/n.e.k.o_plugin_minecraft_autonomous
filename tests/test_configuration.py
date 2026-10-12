import importlib.util
import sys
from pathlib import Path

import pytest


def load_file(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


Settings = load_file("minecraft_settings_test", "configuration.py").Settings
installer = load_file("minecraft_installer_test", "backend/install.py")


def test_remote_server_and_separate_viewer(tmp_path):
    settings = Settings.parse({"server": {"host": "play.example.org", "username": "Alice", "version": "auto"},
                               "viewer": {"url": "https://viewer.example.org/dungeon/"}})
    config = settings.client_config(tmp_path)
    assert config["world"]["host"] == "play.example.org"
    assert config["world"]["username"] == "Alice"
    assert config["world"]["local"] == {"startWithWorld": False, "serverDir": "", "cheats": False}
    assert not config["world"]["client"]["enabled"]
    assert settings.external_viewer_url.startswith("https://viewer.")
    assert settings.identity != Settings.parse({"server": {"host": "other.example.org", "username": "Alice"}}).identity


@pytest.mark.parametrize("config", [
    {"server": {"host": "http://example.org"}}, {"server": {"port": True}},
    {"server": {"port": 65536}}, {"server": {"username": "bad name"}},
    {"server": {"auth": "bypass"}}, {"autonomy": {"enabled": "false"}},
    {"viewer": {"url": "https://user:secret@viewer.example.org/"}},
    {"viewer": {"url": "javascript:alert(1)"}},
])
def test_invalid_settings_are_rejected(config):
    with pytest.raises(ValueError):
        Settings.parse(config)


def test_no_server_default_and_microsoft_identity():
    with pytest.raises(ValueError, match="server_not_configured"):
        Settings.parse({}).require_server()
    settings = Settings.parse({"server": {"auth": "microsoft", "username": "private-account-label"}})
    assert settings.auth == "microsoft"


def test_unverified_archive_and_missing_runtime_are_rejected(tmp_path):
    archive = tmp_path / "untrusted.tgz"
    archive.write_bytes(b"not the pinned release")
    with pytest.raises(ValueError, match="hash_mismatch"):
        installer.verify_archive(archive)
    with pytest.raises(ValueError, match="backend_missing"):
        installer.verify_runtime(tmp_path)
