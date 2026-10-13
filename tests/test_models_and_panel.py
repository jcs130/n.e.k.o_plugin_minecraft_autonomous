import base64
import importlib
import json
import struct
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import APIStatusError
from plugin.sdk.plugin import Err, Ok


def module(plugin_module, name):
    return importlib.import_module(plugin_module.__name__ + "." + name)


def image_raw():
    # Core's transport header, not a rendered image fixture.
    png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 128, 128)
    return {"content": [{"type": "image", "mimeType": "image/png", "data": base64.b64encode(png).decode()}]}


def answer(confidence=0.81):
    return {"type": "choice", "choice": "work", "confidence": confidence,
            "probabilities": {"survival": 0.02, "inspect": 0.1, "work": 0.88, "wait": 0}}


def model_response(content="Observed response", finish="stop"):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish,
        message=SimpleNamespace(model_dump=lambda **_: {"content": content, "tool_calls": []}))],
        usage=SimpleNamespace(model_dump=lambda **_: {"prompt_tokens": 100, "completion_tokens": 12, "total_tokens": 112}))


def gateway(create):
    return SimpleNamespace(get_client=AsyncMock(return_value=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))), aclose=AsyncMock())


def test_neko_image_slot_falls_back_without_provider_details(plugin_module, run_async):
    planner = module(plugin_module, "neko_planner")
    error = APIStatusError("private provider detail", response=httpx.Response(409, request=httpx.Request("POST", "http://unused")),
                           body={"error": {"code": "model_capability_mismatch", "message": "secret"}})
    create = AsyncMock(side_effect=[error, model_response(), model_response()])
    host = gateway(create)
    brain = planner.NekoPlanner(host, 512)
    messages = [{"role": "system", "content": "fixed"}, {"role": "user", "content": [
        {"type": "text", "text": "actual facts"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]}]
    result = run_async(brain.decide(messages, []))
    assert result["model_status"]["fallback"] == "model_capability_mismatch"
    assert result["model_status"]["usage"]["total_tokens"] == 112
    assert [c.kwargs["model"] for c in create.call_args_list] == ["vision", "decision"]
    assert create.call_args_list[0].kwargs["messages"] == messages
    assert create.call_args_list[1].kwargs["messages"][-1]["content"] == "actual facts"
    assert "secret" not in json.dumps(result)
    assert messages[-1]["content"][1]["type"] == "image_url"  # No mutation of caller history.
    run_async(brain.decide(messages, []))
    assert create.call_args_list[-1].kwargs["model"] == "decision"
    assert host.get_client.await_count == 1


def test_neko_text_and_multimodal_use_declared_aliases(plugin_module, run_async):
    planner = module(plugin_module, "neko_planner")
    create = AsyncMock(return_value=model_response())
    brain = planner.NekoPlanner(gateway(create), 1024)
    text = [{"role": "user", "content": "facts"}]
    assert run_async(brain.decide(text, []))["model_status"]["route"] == "decision"
    images = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]}]
    assert run_async(brain.decide(images, []))["model_status"]["route"] == "vision"
    assert create.call_args.kwargs["max_completion_tokens"] == 1024


def test_missing_decision_is_visible_without_dispatch_or_leaking(plugin_module, run_async):
    planner = module(plugin_module, "neko_planner")
    err = APIStatusError("secret", response=httpx.Response(403, request=httpx.Request("POST", "http://unused")),
                         body={"error": {"code": "model_usage_not_bound"}})
    brain = planner.NekoPlanner(gateway(AsyncMock(side_effect=err)), 1024)
    result = run_async(brain.decide([{"role": "user", "content": "facts"}], []))
    assert result["tool_calls"] == [] and result["model_status"]["reason"] == "model_usage_not_bound"
    assert run_async(planner.NekoPlanner(None, 1024).decide([], []))["model_status"]["route"] == "unavailable"


def test_incomplete_neko_output_uses_same_bounded_retry_contract(plugin_module, run_async):
    planner = module(plugin_module, "neko_planner")
    brain = planner.NekoPlanner(gateway(AsyncMock(return_value=model_response(finish="length"))), 512)
    with pytest.raises(planner.PlannerResponseError):
        run_async(brain.decide([], []))


def test_invalid_vision_response_retries_text_once(plugin_module, run_async):
    planner = module(plugin_module, "neko_planner")
    create = AsyncMock(side_effect=[model_response(finish="length"), model_response()])
    brain = planner.NekoPlanner(gateway(create), 512)
    messages = [{"role": "user", "content": [{"type": "text", "text": "current facts"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]}]
    result = run_async(brain.decide(messages, []))
    assert result["model_status"]["route"] == "decision"
    assert result["model_status"]["fallback"] == "invalid_vision_response"
    assert create.await_count == 2
    assert create.call_args.kwargs["messages"][-1]["content"] == "current facts"


def test_fast_rules_no_request_and_danger_does_not_wait(plugin_module, run_async):
    fast = module(plugin_module, "autonomy.fast")
    selector = AsyncMock(return_value=answer())
    state = {"facts": {"body": "生命 2/20，饥饿 16/20"}}
    policy = fast.FastPolicy(fast.FastSettings(mode="neko"), selector)
    assert run_async(policy.choose(state))["choice"] == "survival"
    assert selector.await_count == 0
    assert run_async(fast.FastPolicy(fast.FastSettings()).choose({"facts": {}}))["reason"] == "not_configured"


def test_jev_confidence_is_not_probability_and_low_confidence_falls_back(plugin_module, run_async):
    fast = module(plugin_module, "autonomy.fast")
    config = fast.FastSettings(mode="system_one")
    selector = AsyncMock(side_effect=[answer(), answer(.2)])
    policy = fast.FastPolicy(config, selector)
    state = {"facts": {"body": "生命 20/20"}}
    result = run_async(policy.choose(state))
    assert result["source"] == "system_one" and result["confidence"] == .81 and result["selected_probability"] == .88
    assert run_async(policy.choose(state))["reason"] == "low_confidence"


@pytest.mark.parametrize("change", [{"choice": "arbitrary_action"}, {"confidence": float("nan")},
                                  {"probabilities": {"work": 1}}, {"choice": "wait"}])
def test_invalid_fast_selection_never_authorizes_action(plugin_module, run_async, change):
    fast = module(plugin_module, "autonomy.fast")
    selector = AsyncMock(return_value={**answer(), **change})
    policy = fast.FastPolicy(fast.FastSettings(mode="neko"), selector)
    result = run_async(policy.choose({"facts": {"body": "health=20"}}))
    assert result["source"] == "rules" and result["advisory_only"]
    assert run_async(policy.choose({"facts": {}}))["reason"] == "provider_cooldown"
    assert selector.await_count == 1


def test_systemone_remote_or_local_and_private_key_errors(plugin_module, run_async, monkeypatch):
    fast = module(plugin_module, "autonomy.fast")
    monkeypatch.setenv("MC_FAST_TEST_KEY", "fake-secret")
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"model": "jev-test", "answers": {"focus": answer()}})
    config = fast.FastSettings.parse({"mode": "system_one", "endpoint": "https://api.example.test/v1/systemone", "model": "chosen", "api_key_env": "MC_FAST_TEST_KEY"})
    async def exercise():
        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        service = fast.SystemOne(config, client=client)
        result = await service.select({"facts": {"body": "healthy"}})
        assert result["choice"] == "work"
        payload = json.loads(requests[0].content)
        assert set(payload) == {"state", "model", "questions"} and payload["model"] == "chosen"
        assert requests[0].headers["Authorization"] == "Bearer fake-secret"
        monkeypatch.delenv("MC_FAST_TEST_KEY")
        with pytest.raises(ValueError, match="fast_key_unavailable"):
            await service.select({})
        assert len(requests) == 1
        await service.aclose()
    run_async(exercise())
    assert fast.FastSettings.parse({"endpoint": "http://127.0.0.1:8000/v1/systemone"}).endpoint
    with pytest.raises(ValueError, match="https"):
        fast.FastSettings.parse({"endpoint": "http://remote.test/v1/systemone"})


def test_image_budget_latest_tail_and_no_old_artifact_refresh(plugin_module, monkeypatch):
    perception = module(plugin_module, "autonomy.perception")
    context = module(plugin_module, "autonomy.context")
    frame = perception.latest_png(image_raw(), "mc_view_map")
    assert frame and not perception.latest_png(image_raw(), "mc_artifact")
    messages, budget = context.assemble("fixed", [], "goal", {"parts": []}, [], [],
        context_tokens=32768 - perception.IMAGE_RESERVE, reserved_output=1024)
    enriched, sent = perception.attach_frame(messages, frame)
    assert sent and enriched[:-1] == messages[:-1]
    assert enriched[-1]["content"][-1]["type"] == "image_url"
    assert budget["total"] + perception.IMAGE_RESERVE <= 32768
    monkeypatch.setattr(perception.time, "monotonic", lambda: frame["received_at"] + 16)
    assert perception.attach_frame(messages, frame) == (messages, False)
    assert not perception.latest_png({**image_raw(), "isError": True}, "mc_view_map")


def test_standalone_text_capability_never_sends_image(plugin_module, run_async):
    planner = module(plugin_module, "autonomy.planner")
    received = []
    def respond(request):
        received.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]})
    async def exercise():
        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        brain = planner.HttpPlanner(planner.HttpPlannerConfig("http://model.test/v1", "model"), 512, 30, client=client)
        result = await brain.decide([{"role": "user", "content": [{"type": "text", "text": "current"}, {"type": "image_url", "image_url": {"url": "secret-image"}}]}], [])
        assert result["model_status"]["route"] == "standalone_text"
        assert received[0]["messages"] == [{"role": "user", "content": "current"}]
        await brain.aclose()
    run_async(exercise())


def test_dashboard_has_bounded_actual_data_and_no_secret_config(plugin_instance, plugin_module, run_async, tmp_path, monkeypatch):
    config = {"runtime": {"mode": "external", "data_directory": str(tmp_path)},
              "server": {"host": "example.test", "username": "Alice"}, "private_provider_key": "not-for-ui"}
    monkeypatch.setattr(plugin_instance.config, "dump", AsyncMock(return_value=config))
    settings = plugin_module.Settings.parse(config)
    directory = tmp_path / "sessions" / settings.identity / "host"
    directory.mkdir(parents=True)
    (directory / "status.json").write_text(json.dumps({"phase": "running", "facts": {"parts": [{"key": "gear", "text": "x" * 2000}]}}), encoding="utf-8")
    (directory / "decisions.jsonl").write_text("\n".join(json.dumps({"turnId": str(i), "response": {"content": "reply", "model_status": {"usage": {"total_tokens": 10}}}}) for i in range(35)) + '\n{"partial":', encoding="utf-8")
    result = run_async(plugin_instance.dashboard())
    assert result["runtime"]["live_verified"] is False
    assert len(result["runtime"]["facts"][0]["text"]) == 900
    assert len(result["audit"]["decisions"]) == 20 and result["audit"]["sample_tokens"] == 200
    assert "not-for-ui" not in json.dumps(result)
    assert plugin_instance._worker is None


def test_settings_save_validates_without_starting_or_copying_provider_keys(plugin_instance, run_async, monkeypatch):
    update = AsyncMock(return_value={})
    monkeypatch.setattr(plugin_instance.config, "update", update)
    assert isinstance(run_async(plugin_instance.save_settings({"fast": {"api_key": "secret"}})), Err)
    assert isinstance(run_async(plugin_instance.save_settings({"server": {"version": "1.20.6"}})), Err)
    assert not update.await_count
    patch = {"perception": {"enabled": False}, "fast": {"mode": "rules"}}
    result = run_async(plugin_instance.save_settings(patch))
    assert isinstance(result, Ok) and not result.value["running_session_changed"]
    update.assert_awaited_once_with(patch)
    assert plugin_instance._worker is None


def test_explicit_model_diagnostic_uses_same_gateway_and_never_dispatches(plugin_instance, plugin_module, run_async):
    check = module(plugin_module, "model_check")
    create = AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(finish_reason="tool_calls",
        message=SimpleNamespace(model_dump=lambda **_: {"tool_calls": [{"id": "probe", "type": "function",
            "function": {"name": "report_probe", "arguments": '{"answer":"RED"}'}}]}))], usage=None))
    host = gateway(create)
    result = run_async(check.check_model(host, "vision"))
    assert result["vision_probe_passed"]
    assert result["game_action_dispatched"] is False
    assert create.call_args.kwargs["model"] == "vision"
    assert base64.b64decode(check.calibration_png())[:8] == b"\x89PNG\r\n\x1a\n"
    assert host.aclose.await_count == 1 and plugin_instance._worker is None
    assert isinstance(run_async(plugin_instance.check_model("other")), Err)


def test_missing_model_keeps_controller_turn_and_retry_bounded(plugin_module, tmp_path, run_async):
    from test_controller import setup
    async def decide(*_):
        return {"content": None, "tool_calls": [], "model_status": {"route": "unavailable", "reason": "model_usage_not_bound"}}
    controller_module, bridge, controller = setup(plugin_module, tmp_path, decide)
    controller.settings = replace(controller.settings, max_tool_rounds=1)
    run_async(controller.turn_once("survive", "rules", controller_module.model_tools(bridge.tools)))
    assert controller.continuation_needed and controller.planner_retry_at > 0
    assert not any(name == "mc_do" for name, _, _ in bridge.calls)
    assert bridge.calls[-1][1]["action"] == "end_turn"
