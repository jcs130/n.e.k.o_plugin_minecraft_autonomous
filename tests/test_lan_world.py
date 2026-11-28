import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock


def test_reads_latest_integrated_world_and_ignores_chat_and_partial_records(plugin_module, tmp_path):
    published_world = importlib.import_module(f"{plugin_module.__name__}.lan_world").published_world
    log = tmp_path / "latest.log"
    log.write_text(
        "[14:31:11] [Server thread/INFO]: Starting integrated minecraft server version 1.21.11\n"
        "[14:31:12] [Render thread/INFO]: Started serving on 52178\n"
        "[14:31:13] [Render thread/INFO]: [System] [CHAT] Started serving on 7777\n"
        "[14:31:14] [Render thread/INFO]: Started serving on 655", encoding="utf-8")
    assert published_world(log) == (52178, "1.21.11")
    with log.open("a", encoding="utf-8") as stream:
        stream.write("\n[14:31:15] [Server thread/INFO]: Stopping server\n")
    assert published_world(log) is None


def test_detect_entry_checks_one_loopback_port_without_joining(plugin_instance, run_async, monkeypatch, tmp_path):
    log = tmp_path / ".minecraft" / "logs" / "latest.log"
    log.parent.mkdir(parents=True)
    log.write_text("[14:31:11] [Server thread/INFO]: Starting integrated minecraft server version 1.21.1\n"
                   "[14:31:12] [Render thread/INFO]: Started serving on 52178\n", encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    writer = SimpleNamespace(close=Mock())
    open_connection = AsyncMock(return_value=(None, writer))
    monkeypatch.setattr("asyncio.open_connection", open_connection)
    result = run_async(plugin_instance.detect_lan_world())
    assert result.value == {"found": True, "host": "127.0.0.1", "port": 52178, "version": "1.21.1"}
    open_connection.assert_awaited_once_with("127.0.0.1", 52178)
    writer.close.assert_called_once()
    open_connection.side_effect = ConnectionRefusedError
    assert run_async(plugin_instance.detect_lan_world()).value == {"found": False, "reason": "lan_port_closed"}
