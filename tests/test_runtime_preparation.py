"""Explicit UI resource jobs; never connect, run Node, or call a real model."""

import asyncio
import copy
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from agent_mc_autonomy.runtime_bundle import BundleError, PreparedBundle
from plugin.sdk.plugin import Err, Ok


@pytest.fixture
def setup(plugin_instance, plugin_module, monkeypatch, tmp_path):
    module = __import__(plugin_module.__package__ + ".runtime_preparation", fromlist=["unused"])
    monkeypatch.setattr(module, "supported", lambda: True)
    monkeypatch.setattr(module, "session_is_owned", lambda _: False)
    monkeypatch.setattr(module, "resolve_host_runtime", lambda raw: (raw, "missing"))
    monkeypatch.setattr(
        plugin_instance, "_resource_spec", lambda: SimpleNamespace(bytes=1024, manifest_sha256="a" * 64)
    )
    raw = {
        "server": {"host": "localhost", "username": "fixture"},
        "planner": {"route": "host"},
        "runtime": {"data_directory": str(tmp_path / "data")},
        "speech_output": {"enabled": True},
    }
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(side_effect=lambda: copy.deepcopy(raw)))

    async def update(patch):
        for key, value in patch.items():
            raw.setdefault(key, {}).update(copy.deepcopy(value))

    writer = AsyncMock(side_effect=update)
    monkeypatch.setattr(plugin_instance.config, "update", writer)
    bundle = PreparedBundle(
        tmp_path / "new-runtime",
        tmp_path / "node.exe",
        tmp_path / "backend",
        tmp_path / "renderer",
        tmp_path / "catalog.json",
        tmp_path / "appearances.json",
        "a" * 64,
    )
    return plugin_instance, module, raw, writer, bundle


def test_explicit_job_preserves_account_model_and_waits_for_separate_start(setup, monkeypatch, run_async):
    plugin, module, raw, writer, bundle = setup
    original = copy.deepcopy(raw)
    calls = []

    def prepare(spec, cache, **kwargs):
        calls.append(cache)
        kwargs["progress"]({"phase": "downloading", "downloaded_bytes": 512, "total_bytes": 1024})
        return bundle

    monkeypatch.setattr(module, "prepare_release", prepare)

    async def scenario():
        assert isinstance(await plugin.prepare_runtime(), Ok)
        await plugin._runtime_setup_task

    run_async(scenario())
    assert len(calls) == 1 and writer.await_count == 1
    for key in ["server", "planner", "speech_output"]:
        assert raw[key] == original[key]
    assert raw["runtime"]["data_directory"] == original["runtime"]["data_directory"]
    assert raw["runtime"]["bundle_manifest_sha256"] == "a" * 64
    assert plugin.runtime_setup_state()["phase"] == "ready" and plugin._worker is None


@pytest.mark.parametrize(
    "patch",
    [
        {"runtime": {"mode": "external"}},
        {"backend": {"node": "custom"}},
        {"viewer": {"url": "https://viewer.invalid"}},
        {"backend": {"provider": "java-client"}},
    ],
)
def test_never_takes_over_custom_or_external_runtime(setup, monkeypatch, run_async, patch):
    plugin, module, raw, writer, _ = setup
    raw.update(patch)
    monkeypatch.setattr(module, "prepare_release", lambda *a, **k: pytest.fail("custom runtime download"))
    assert isinstance(run_async(plugin.prepare_runtime()), Err)
    assert writer.await_count == 0 and not plugin._setup_active()


def test_active_body_blocks_preparation(setup, monkeypatch, run_async):
    plugin, module, _, writer, _ = setup
    plugin._worker = SimpleNamespace(snapshot=lambda: {"worker_alive": True})
    monkeypatch.setattr(module, "prepare_release", lambda *a, **k: pytest.fail("active runtime download"))
    assert isinstance(run_async(plugin.prepare_runtime()), Err)
    assert writer.await_count == 0


def test_duplicate_click_and_start_during_job_cannot_create_more_work(setup, monkeypatch, run_async):
    plugin, module, _, _, bundle = setup
    entered, release = threading.Event(), threading.Event()
    calls = []

    def prepare(*args, **kwargs):
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return bundle

    monkeypatch.setattr(module, "prepare_release", prepare)

    async def scenario():
        await plugin.prepare_runtime()
        assert await asyncio.to_thread(entered.wait, 5)
        assert isinstance(await plugin.prepare_runtime(), Ok)
        denied = await plugin.start()
        assert isinstance(denied, Err) and denied.error["code"] == "runtime_setup_active"
        release.set()
        await plugin._runtime_setup_task

    run_async(scenario())
    assert calls == [1] and plugin._worker is None


def test_network_failure_preserves_all_configuration_and_can_retry(setup, monkeypatch, run_async):
    plugin, module, raw, writer, bundle = setup
    original = copy.deepcopy(raw)

    def failed(*args, **kwargs):
        raise BundleError("runtime_bundle_download_network_failed")

    monkeypatch.setattr(module, "prepare_release", failed)

    async def first():
        await plugin.prepare_runtime()
        await plugin._runtime_setup_task

    run_async(first())
    assert raw == original and writer.await_count == 0
    assert plugin.runtime_setup_state()["phase"] == "failed"
    monkeypatch.setattr(module, "prepare_release", lambda *a, **k: bundle)
    run_async(first())
    assert plugin.runtime_setup_state()["phase"] == "ready" and writer.await_count == 1


def test_changed_runtime_selection_is_not_overwritten_at_completion(setup, monkeypatch, run_async):
    plugin, module, raw, writer, _ = setup

    def prepare(*args, **kwargs):
        raw["backend"] = {"node": "user-selected-node"}
        return setup[-1]

    monkeypatch.setattr(module, "prepare_release", prepare)

    async def scenario():
        await plugin.prepare_runtime()
        await plugin._runtime_setup_task

    run_async(scenario())
    assert writer.await_count == 0 and raw["backend"]["node"] == "user-selected-node"
    assert plugin.runtime_setup_state()["phase"] == "failed"


def test_shutdown_cancels_only_the_owned_resource_job(setup, monkeypatch, run_async):
    plugin, module, _, writer, _ = setup
    entered = threading.Event()

    def prepare(*args, cancelled, **kwargs):
        entered.set()
        assert cancelled.wait(5)
        raise BundleError("runtime_bundle_download_cancelled")

    monkeypatch.setattr(module, "prepare_release", prepare)

    async def scenario():
        await plugin.prepare_runtime()
        assert await asyncio.to_thread(entered.wait, 5)
        await plugin._close_runtime_setup()

    run_async(scenario())
    assert plugin.runtime_setup_state()["phase"] == "cancelled"
    assert writer.await_count == 0 and plugin._worker is None


def test_simultaneous_rpc_clicks_share_one_job_after_config_read(setup, monkeypatch, run_async):
    plugin, module, raw, _, bundle = setup
    calls = []

    async def dump():
        await asyncio.sleep(0)
        return copy.deepcopy(raw)

    monkeypatch.setattr(plugin.config, "dump", dump)

    def prepare(*args, **kwargs):
        calls.append(1)
        return bundle

    monkeypatch.setattr(module, "prepare_release", prepare)

    async def scenario():
        results = await asyncio.gather(plugin.prepare_runtime(), plugin.prepare_runtime())
        assert all(isinstance(result, Ok) for result in results)
        await plugin._runtime_setup_task

    run_async(scenario())
    assert calls == [1]
