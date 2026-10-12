import asyncio
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("minecraft_bridge_test", Path(__file__).resolve().parents[1] / "bridge.py")
bridge_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge_module)


def test_mcp_failure_is_not_success():
    with pytest.raises(RuntimeError, match="disconnected"):
        bridge_module.json_content({"isError": True, "content": [{"type": "text", "text": "disconnected"}]})
    assert bridge_module.json_content({"content": [{"type": "text", "text": '{"phase":"starting"}'}]}) == {"phase": "starting"}


def test_stopped_bridge_never_submits(run_async, tmp_path):
    bridge = bridge_module.MinecraftBridge("node", tmp_path / "entry", tmp_path / "config", tmp_path / "log")
    bridge.tools = [{"name": "mc_do"}]
    with pytest.raises(RuntimeError, match="not running"):
        run_async(bridge.call("mc_do", {}))
    run_async(bridge.close())
    run_async(bridge.close())


def test_timeout_does_not_retry_action(run_async, tmp_path):
    async def exercise():
        bridge = bridge_module.MinecraftBridge("node", tmp_path / "entry", tmp_path / "config", tmp_path / "log")
        bridge.tools = [{"name": "mc_do"}]
        requests = []

        async def consume():
            request = await bridge._queue.get()
            requests.append(request)
            await asyncio.Event().wait()

        bridge._owner = asyncio.create_task(consume())
        try:
            with pytest.raises(RuntimeError, match="delivery is uncertain"):
                await bridge.call("mc_do", {}, timeout=0.01)
            assert len(requests) == 1
            assert requests[0][2].cancelled()
        finally:
            bridge._owner.cancel()
            await bridge.close()

    run_async(exercise())
