import importlib
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

from plugin.sdk.plugin import Ok


def snapshot(now, health="生命 20/20"):
    return {"phase": "running", "game_connected": True,
            "updated_at": datetime.fromtimestamp(now, timezone.utc).isoformat(),
            "facts": {"parts": [{"key": "body", "text": health}, {"key": "gear", "text": "木板×4"}]}}


def configure(plugin_instance, monkeypatch, now, *, enabled=True):
    module = importlib.import_module(plugin_instance.__class__.__module__ + ".neko_presentation")
    monkeypatch.setattr(module.time, "time", lambda: now)
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(return_value={
        "presentation": {"enabled": enabled, "target": "TestRole"}}))
    monkeypatch.setattr(plugin_instance, "status", AsyncMock(return_value=Ok(snapshot(now))))
    push = Mock(return_value={"submitted": True})
    monkeypatch.setattr(plugin_instance, "push_message", push)
    return module, push


def test_disabled_timer_has_no_model_or_game_io(plugin_instance, run_async):
    assert run_async(plugin_instance.observe_game_changes()).value["reason"] == "disabled"


def test_fresh_progress_uses_public_role_aware_push_and_deduplicates(plugin_instance, run_async, monkeypatch):
    module, push = configure(plugin_instance, monkeypatch, 10000)
    first = run_async(plugin_instance.observe_game_changes()).value
    assert first["submitted"] and first["playback_verified"] is False
    kwargs = push.call_args.kwargs
    assert kwargs["target_lanlan"] == "TestRole" and kwargs["ai_behavior"] == "respond"
    assert kwargs["visibility"] == [] and "{LANLAN_NAME}" in kwargs["parts"][0]["text"]
    assert "生命 20/20" in kwargs["parts"][0]["text"]
    monkeypatch.setattr(module.time, "time", lambda: 10010)
    plugin_instance.status.return_value = Ok({**snapshot(10010), "decisions": 200})
    assert run_async(plugin_instance.observe_game_changes()).value["reason"] == "unchanged"
    plugin_instance.status.return_value = Ok(snapshot(10010, "生命 12/20"))
    assert run_async(plugin_instance.observe_game_changes()).value["reason"] == "rate_limited"
    monkeypatch.setattr(module.time, "time", lambda: 10100)
    plugin_instance.status.return_value = Ok(snapshot(10100, "生命 12/20"))
    assert run_async(plugin_instance.observe_game_changes()).value["submitted"]
    assert push.call_count == 2
    assert json.loads(next(plugin_instance.data_path("presentation").glob("*.json")).read_text())["playback_verified"] is False


def test_stale_snapshot_and_not_observed_never_narrate(plugin_instance, run_async, monkeypatch):
    _, push = configure(plugin_instance, monkeypatch, 10000)
    connected_without_facts = {**snapshot(10000), "facts": {"parts": []}}
    for status in (snapshot(9900), {"phase": "not_observed"}, snapshot(10040), connected_without_facts):
        plugin_instance.status.return_value = Ok(status)
        assert run_async(plugin_instance.present_status()).value["reason"] == "no_fresh_observation"
    assert not push.called


def test_notification_is_bounded_before_the_host_summary_and_explicit_refresh_is_throttled(plugin_instance, run_async, monkeypatch):
    module, push = configure(plugin_instance, monkeypatch, 10000)
    status = snapshot(10000)
    status["facts"]["parts"] += [{"key": "gear", "text": "木板×18；" * 1000}, {"key": "queue", "text": "正在移动" * 1000}]
    plugin_instance.status.return_value = Ok(status)
    assert run_async(plugin_instance.present_status()).value["submitted"]
    text = push.call_args.kwargs["parts"][0]["text"]
    assert len(text.encode("utf-8")) < 650
    assert "生命 20/20" in text and "木板×18" not in text and "正在移动" in text
    assert "1—2句" in text and "背包清单" in text
    assert run_async(plugin_instance.present_status()).value["reason"] == "rate_limited"
    monkeypatch.setattr(module.time, "time", lambda: 10031)
    plugin_instance.status.return_value = Ok(snapshot(10031))
    assert run_async(plugin_instance.present_status()).value["submitted"]


def test_submission_rejection_keeps_event_retryable_but_bounded(plugin_instance, run_async, monkeypatch):
    module, push = configure(plugin_instance, monkeypatch, 10000)
    push.return_value = {"submitted": False, "reason": "backpressure"}
    assert not run_async(plugin_instance.observe_game_changes()).value["submitted"]
    assert run_async(plugin_instance.present_status()).value["reason"] == "rate_limited"
    monkeypatch.setattr(module.time, "time", lambda: 10031)
    plugin_instance.status.return_value = Ok(snapshot(10031))
    push.return_value = {"submitted": True}
    assert run_async(plugin_instance.observe_game_changes()).value["submitted"]
    assert push.call_count == 2


def test_inventory_count_changes_do_not_trigger_automatic_speech(plugin_instance, run_async, monkeypatch):
    module, push = configure(plugin_instance, monkeypatch, 10000)
    first = snapshot(10000)
    first["facts"]["parts"][1]["text"] = "包里有：白桦木板×12、木斧 耐久20/59×1。"
    plugin_instance.status.return_value = Ok(first)
    assert run_async(plugin_instance.observe_game_changes()).value["submitted"]
    monkeypatch.setattr(module.time, "time", lambda: 10100)
    later = snapshot(10100)
    later["facts"]["parts"][1]["text"] = "包里有：白桦木板×20、木斧 耐久12/59×1。"
    plugin_instance.status.return_value = Ok(later)
    assert run_async(plugin_instance.observe_game_changes()).value["reason"] == "unchanged"
    assert push.call_count == 1


def test_new_critical_danger_bypasses_interval_once(plugin_instance, run_async, monkeypatch):
    module, push = configure(plugin_instance, monkeypatch, 10000)
    assert run_async(plugin_instance.observe_game_changes()).value["submitted"]
    monkeypatch.setattr(module.time, "time", lambda: 10010)
    plugin_instance.status.return_value = Ok(snapshot(10010, "生命 4/20"))
    assert run_async(plugin_instance.observe_game_changes()).value["submitted"]
    monkeypatch.setattr(module.time, "time", lambda: 10011)
    plugin_instance.status.return_value = Ok(snapshot(10011, "生命 3/20"))
    assert not run_async(plugin_instance.observe_game_changes()).value["submitted"]
    assert push.call_count == 2
