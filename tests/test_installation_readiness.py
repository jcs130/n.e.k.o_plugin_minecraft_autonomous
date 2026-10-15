import json
from unittest.mock import AsyncMock

import pytest
from plugin.sdk.plugin import Err


@pytest.mark.parametrize("patch,field", [
    ({"server": {"host": "secret.invalid", "connection_type": "local"}}, "server.connection_type"),
    ({"server": {"username": "SECRET!"}}, "server.username"),
    ({"server": {"port": 0}}, "server.port"),
    ({"operator": {"port": 80}}, "operator.port"),
    ({"viewer": {"renderer_directory": "SECRET"}}, "viewer.renderer_directory"),
])
def test_rejected_save_preserves_state(plugin_instance, run_async, monkeypatch, patch, field):
    original = {"server": {"username": "MyAccount"}}
    dump = AsyncMock(return_value=original)
    update = AsyncMock()
    monkeypatch.setattr(plugin_instance.config, "dump", dump)
    monkeypatch.setattr(plugin_instance.config, "update", update)
    generation = plugin_instance._generation
    result = run_async(plugin_instance.save_settings(patch))
    assert isinstance(result, Err)
    assert result.error["field"] == field
    assert "SECRET" not in json.dumps(result.error)
    assert update.await_count == 0 and plugin_instance._generation == generation
    assert plugin_instance._configuration_writes == 0 and plugin_instance._worker is None
    assert original == {"server": {"username": "MyAccount"}}


def test_dashboard_metadata_does_not_hash_backend(plugin_instance, plugin_module, run_async, monkeypatch):
    def forbid(*args, **kwargs):
        raise AssertionError("dashboard must not hash full runtime")
    monkeypatch.setattr(plugin_module, "verify_runtime", forbid)
    result = run_async(plugin_instance.dashboard())
    assert result["installation"]["scope"] == "metadata_only_not_runtime_or_render_verification"
    assert result["installation"]["viewer"] == "text_only"
    assert plugin_instance._worker is None
