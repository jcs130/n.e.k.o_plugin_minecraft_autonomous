import asyncio
import importlib
import json
from contextlib import nullcontext
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from agent_mc_autonomy.ownership import session_lease
from agent_mc_autonomy.review import ReviewPort
from plugin.sdk.plugin import Err


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
    assert "1—2句" in text[:130] and "不念背包" in text[:130]
    review_id = result["heartbeat_id"]
    acknowledged = run_async(plugin_instance.minecraft_autonomy_review(review_id, "continue", "继续当前工作"))
    assert acknowledged["acknowledged"] and not acknowledged["dispatched"]
    assert {k: acknowledged[k] for k in port.state()["review"]["result"]} == port.state()["review"]["result"]
    assert acknowledged["commentary"]["allowed"]


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


def test_routine_reviews_keep_strategy_but_do_not_require_spoken_readouts(plugin_instance, run_async, monkeypatch):
    port, snapshot, push = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    first = run_async(plugin_instance.game_decision_heartbeat()).value["heartbeat_id"]
    run_async(plugin_instance.minecraft_autonomy_review(first, "continue", "正常工作"))
    port.now = lambda: 10180
    snapshot["updated_at"] = datetime.fromtimestamp(10180, timezone.utc).isoformat()
    (port.directory / "status.json").write_text(json.dumps(snapshot), encoding="utf-8")
    port.observe(snapshot)
    review_id = run_async(plugin_instance.game_decision_heartbeat()).value["heartbeat_id"]
    cue = push.call_args.kwargs["parts"][0]["text"]
    assert "无需回复或口播" in cue
    assert push.call_args.kwargs["ai_behavior"] == "read"
    result = port.state()["review"]["result"]
    assert result["deferred"] and result["context_only"]
    assert not result["acknowledged"] and not result["dispatched"]
    assert port.state()["last_decision"]["heartbeat_id"] == first
    assert port.state()["review"]["id"] == review_id


def test_review_lineage_pages_are_forwarded_without_plugin_policy(plugin_instance, run_async, monkeypatch):
    port, snapshot, _ = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    review_id = run_async(plugin_instance.game_decision_heartbeat()).value["heartbeat_id"]
    page = run_async(plugin_instance.minecraft_autonomy_review(review_id, "inspect", lineage_offset=0))
    assert page["goal_lineage"] == [] and page["has_more"] is False
    assert not port.mailbox.ready()


def test_revision_routes_through_framework_without_plugin_queue_policy(plugin_instance, run_async, monkeypatch):
    port, snapshot, _ = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    first_id = run_async(plugin_instance.game_decision_heartbeat()).value["heartbeat_id"]
    first = run_async(plugin_instance.minecraft_autonomy_review(first_id, "insert", "需要工具", "做好工具再找食物"))
    port.mailbox.activate_feedback(port.mailbox.claim())
    port.now = lambda: 10180
    snapshot.update(updated_at=datetime.fromtimestamp(10180, timezone.utc).isoformat(), current_goal=port.mailbox.active_goal())
    (port.directory / "status.json").write_text(json.dumps(snapshot), encoding="utf-8")
    port.observe(snapshot)
    review_id = run_async(plugin_instance.game_decision_heartbeat()).value["heartbeat_id"]
    assert run_async(plugin_instance.minecraft_autonomy_review(review_id, "inspect"))["stage_delivery"]["can_revise"]
    args = (review_id, "revise", "已有木剑", "找食物")
    result = run_async(plugin_instance.minecraft_autonomy_review(*args))
    assert result == run_async(plugin_instance.minecraft_autonomy_review(*args))
    assert result["dispatched"] and not result["verified"]
    assert port.mailbox.claim()["payload"]["revision_of"] == first["request_id"]


def test_stop_blocks_transport_and_tool(plugin_instance, run_async, monkeypatch):
    port, snapshot, push = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    plugin_instance._operator_state(True)
    assert run_async(plugin_instance.game_decision_heartbeat()).value["reason"] == "explicit_stop"
    assert run_async(plugin_instance.minecraft_autonomy_review(port.state()["review"]["id"], "continue", "等候"))["error"] == "disabled_or_stopped"
    assert not push.called


def external_setup(plugin, monkeypatch):
    port, snapshot, push = setup(plugin, monkeypatch)
    plugin.config.dump.return_value["runtime"] = {"mode": "external", "data_directory": str(port.directory.parents[2])}
    plugin._operator_state(True)
    return port, snapshot, push


def test_explicit_resume_only_restores_host_participation(plugin_instance, run_async, monkeypatch):
    port, snapshot, push = external_setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    before = port.state()
    with session_lease(port.directory):
        for _ in range(2):
            result = run_async(plugin_instance.resume_observation()).value
            assert result["observer_resumed"] and not result["game_started"] and not result["task_dispatched"]
            assert not result["submitted"] and not result["main_brain_acknowledged"] and not result["playback_verified"]
    assert port.state() == before and not port.mailbox.ready() and not push.called
    assert plugin_instance._worker is None
    assert not json.loads(plugin_instance.data_path("operator.json").read_text())["explicit_stop"]
    assert run_async(plugin_instance.game_decision_heartbeat()).value["submitted"]


@pytest.mark.parametrize("fault", ["missing_lease", "other_account", "stale", "future", "failed", "disconnected", "disabled", "heartbeat_disabled", "embedded"])
def test_resume_rejects_inactive_or_disabled_runtime(plugin_instance, run_async, monkeypatch, fault):
    port, snapshot, push = external_setup(plugin_instance, monkeypatch)
    raw = plugin_instance.config.dump.return_value
    if fault in {"stale", "future"}:
        snapshot["updated_at"] = datetime.fromtimestamp(9900 if fault == "stale" else 10100, timezone.utc).isoformat()
    elif fault == "failed":
        snapshot["phase"] = "failed"
    elif fault == "disconnected":
        snapshot["game_connected"] = False
    elif fault == "disabled":
        raw["autonomy"]["enabled"] = False
    elif fault == "heartbeat_disabled":
        raw["heartbeat"]["enabled"] = False
    elif fault == "embedded":
        raw["runtime"]["mode"] = "embedded"
    (port.directory / "status.json").write_text(json.dumps(snapshot), encoding="utf-8")
    lease = nullcontext() if fault == "missing_lease" else session_lease(port.directory / "other" if fault == "other_account" else port.directory)
    with lease:
        assert isinstance(run_async(plugin_instance.resume_observation()), Err)
    assert json.loads(plugin_instance.data_path("operator.json").read_text())["explicit_stop"]
    assert not push.called and plugin_instance._worker is None and not port.mailbox.ready()


def test_stop_wins_over_inflight_observer_resume(plugin_instance, run_async, monkeypatch):
    port, _, push = external_setup(plugin_instance, monkeypatch)
    raw = plugin_instance.config.dump.return_value
    async def exercise():
        entered, release = asyncio.Event(), asyncio.Event()
        async def delayed(**_):
            entered.set()
            await release.wait()
            return raw
        monkeypatch.setattr(plugin_instance.config, "dump", delayed)
        with session_lease(port.directory):
            resuming = asyncio.create_task(plugin_instance.resume_observation())
            await entered.wait()
            stopping = asyncio.create_task(plugin_instance.stop())
            await asyncio.sleep(0)
            release.set()
            result = await resuming
            await stopping
            assert isinstance(result, Err) and result.error["code"] == "resume_cancelled"
    run_async(exercise())
    assert json.loads(plugin_instance.data_path("operator.json").read_text())["explicit_stop"]
    assert not push.called


def test_configuration_save_invalidates_inflight_observer_resume(plugin_instance, run_async, monkeypatch):
    port, _, push = external_setup(plugin_instance, monkeypatch)
    raw = plugin_instance.config.dump.return_value
    async def exercise():
        entered, release = asyncio.Event(), asyncio.Event()
        first = True
        async def delayed(**_):
            nonlocal first
            if first:
                first = False
                entered.set()
                await release.wait()
            return raw
        monkeypatch.setattr(plugin_instance.config, "dump", delayed)
        monkeypatch.setattr(plugin_instance.config, "update", AsyncMock())
        with session_lease(port.directory):
            resuming = asyncio.create_task(plugin_instance.resume_observation())
            await entered.wait()
            assert (await plugin_instance.save_settings({"server": {"username": "OtherBot"}})).value["saved"]
            release.set()
            result = await resuming
            assert isinstance(result, Err) and result.error["code"] == "resume_cancelled"
    run_async(exercise())
    assert json.loads(plugin_instance.data_path("operator.json").read_text())["explicit_stop"]
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
