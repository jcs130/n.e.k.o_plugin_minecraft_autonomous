import importlib
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from agent_mc_autonomy.review import ReviewPort


def setup(plugin, monkeypatch):
    mod = importlib.import_module(plugin.__class__.__module__ + ".neko_heartbeat")
    raw = {"autonomy": {"enabled": True}, "server": {"host": "example.invalid", "username": "TestBot"},
           "heartbeat": {"enabled": True, "target": "TestRole"}}
    monkeypatch.setattr(plugin.config, "dump", AsyncMock(return_value=raw))
    directory = mod.review_port(plugin, mod.Settings.parse(raw)).directory
    port = ReviewPort(directory, now=lambda: 10000)
    monkeypatch.setattr(mod, "review_port", lambda *_: port)
    port.configure(mod.HeartbeatSettings.parse(raw).policy())
    snapshot = {"phase": "running", "game_connected": True, "owner_pid": 123,
                "updated_at": datetime.fromtimestamp(10000, timezone.utc).isoformat(), "standing_goal": "安全生存",
                "facts": {"parts": [{"key": "body", "text": "生命20/20"}, {"key": "gear", "text": "木镐1把"},
                                    {"key": "foodReserve", "text": "口粮0个"}, {"key": "queue", "text": "空闲"}]}}
    (port.directory / "status.json").write_text(json.dumps(snapshot), encoding="utf-8")
    push = Mock(return_value={"submitted": True})
    monkeypatch.setattr(plugin, "push_message", push)
    return port, snapshot, push


def test_disabled_never_reads_game(plugin_instance, run_async, monkeypatch):
    monkeypatch.setattr(plugin_instance, "status", AsyncMock(side_effect=AssertionError("must not poll game")))
    assert run_async(plugin_instance.game_decision_heartbeat()).value["reason"] == "disabled"


def test_frontend_only_transports_framework_reviews(plugin_instance, run_async, monkeypatch):
    port, snapshot, push = setup(plugin_instance, monkeypatch)
    assert not run_async(plugin_instance.game_decision_heartbeat()).value["submitted"]
    assert not push.called  # Even fresh facts do not create a review in the adapter.
    port.observe(snapshot)  # Only the independent runtime does this.
    monkeypatch.setattr(ReviewPort, "observe", Mock(side_effect=AssertionError("frontend owns no scheduler")))
    result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result["submitted"] and not result["main_brain_acknowledged"] and not result["playback_verified"]
    event = push.call_args.kwargs
    assert event["target_lanlan"] == "TestRole" and event["ai_behavior"] == "respond"
    text = event["parts"][0]["text"]
    assert "minecraft_autonomy_review" in text and "口粮0个" in text and len(text.encode()) < 650
    review_id = result["heartbeat_id"]
    acknowledged = run_async(plugin_instance.minecraft_autonomy_review(review_id, "continue", "继续当前工作"))
    assert acknowledged["acknowledged"] and not acknowledged["dispatched"]
    assert port.state()["review"]["result"] == acknowledged


def test_review_tool_routes_once_to_framework_mailbox(plugin_instance, run_async, monkeypatch):
    port, snapshot, _ = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    review_id = run_async(plugin_instance.game_decision_heartbeat()).value["heartbeat_id"]
    args = (review_id, "insert", "缺口粮", "收集食物")
    first = run_async(plugin_instance.minecraft_autonomy_review(*args))
    assert first == run_async(plugin_instance.minecraft_autonomy_review(*args))
    assert first["dispatched"] and not first["verified"]
    assert port.mailbox.get(first["request_id"])["delivery"] == "queued"


def test_long_review_uses_small_inspection_cue_without_losing_framework_evidence(plugin_instance, run_async, monkeypatch):
    port, snapshot, push = setup(plugin_instance, monkeypatch)
    snapshot["standing_goal"] = "长期生存，获取食物和庇护所。" * 80
    snapshot["facts"]["parts"][1]["text"] = "木镐1把、工作台1个、原木34个。" * 30
    snapshot["read_activity"] = {"mc_bag": 18, "mc_scout": 8}
    (port.directory / "status.json").write_text(json.dumps(snapshot), encoding="utf-8")
    port.observe(snapshot)
    review_id = run_async(plugin_instance.game_decision_heartbeat()).value["heartbeat_id"]
    cue = push.call_args.kwargs["parts"][0]["text"]
    assert len(cue.encode("utf-8")) <= 600
    assert "先" in cue and cue.index("inspect") < cue.index("continue")
    assert "空闲" in cue and "26" in cue and "口粮0个" in cue
    detail = run_async(plugin_instance.minecraft_autonomy_review(review_id, "inspect"))
    assert "工作台1个" in detail["facts"]["gear"]
    assert detail["read_activity"] == snapshot["read_activity"]
    assert not port.state()["review"].get("result")


def test_stop_blocks_transport_and_tool(plugin_instance, run_async, monkeypatch):
    port, snapshot, push = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    plugin_instance._operator_state(True)
    assert run_async(plugin_instance.game_decision_heartbeat()).value["reason"] == "explicit_stop"
    assert run_async(plugin_instance.minecraft_autonomy_review(port.state()["review"]["id"], "continue", "等候"))["error"] == "disabled_or_stopped"
    assert not push.called


def test_narration_and_policy_configuration_are_host_adaptations(plugin_instance, run_async, monkeypatch):
    port, _, _ = setup(plugin_instance, monkeypatch)
    assert run_async(plugin_instance.observe_game_changes()).value["reason"] == "decision_heartbeat_owns_narration"
    plugin_instance._worker = SimpleNamespace(snapshot=lambda: {"worker_alive": True})
    update = AsyncMock()
    monkeypatch.setattr(plugin_instance.config, "update", update)
    assert run_async(plugin_instance.save_settings({"heartbeat": {"review_interval_seconds": 240}})).value["saved"]
    assert port.state()["policy"]["review_interval_seconds"] == 240
    assert update.await_count == 1
