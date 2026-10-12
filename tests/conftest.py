"""Load the real public SDK without starting a N.E.K.O host."""

import asyncio
import importlib.util
import logging
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SDK_ROOTS = [*([Path(os.environ["NEKO_ROOT"])] if os.environ.get("NEKO_ROOT") else []), *ROOT.parents]
for candidate in SDK_ROOTS:
    if (candidate / "plugin/sdk/plugin/__init__.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise pytest.UsageError("Set NEKO_ROOT to a N.E.K.O source checkout containing plugin/sdk/plugin.")


@pytest.fixture
def run_async():
    # Windows creates an internal socket pair when the loop is initialized.
    # Initialize it before forbidding I/O, then reuse it for guarded plugin calls.
    with asyncio.Runner() as runner:
        yield runner.run


@pytest.fixture
def plugin_instance(monkeypatch, tmp_path, run_async):
    def forbidden_io(*args, **kwargs):
        raise AssertionError("The repository scaffold must not connect, launch processes, or send messages.")

    monkeypatch.setenv("NEKO_STORAGE_SELECTED_ROOT", str(tmp_path))
    monkeypatch.setattr(socket, "create_connection", forbidden_io)
    monkeypatch.setattr(socket.socket, "connect", forbidden_io)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden_io)
    monkeypatch.setattr(subprocess, "Popen", forbidden_io)

    module_name = "minecraft_autonomous_under_test"
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "__init__.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)

    ctx = SimpleNamespace(
        plugin_id="minecraft_autonomous",
        config_path=ROOT / "plugin.toml",
        metadata={},
        logger=logging.getLogger("minecraft_autonomous.tests"),
        bus=None,
        images=None,
        models=None,
        push_message=forbidden_io,
        _effective_config={},
    )
    return module.MinecraftAutonomousPlugin(ctx)
