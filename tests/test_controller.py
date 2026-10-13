import asyncio
import dataclasses
import importlib
import json
from types import SimpleNamespace

import pytest


def packed(value):
    return {"content": [{"type": "text", "text": json.dumps(value)}]}


def action(terminal=False):
    return {"kind": "task", "id": "body-1", "phase": "completed" if terminal else "accepted",
            "terminal": terminal, "goalCompleted": False}


def choose():
    return {"content": None, "tool_calls": [{"id": "call-1", "type": "function",
            "function": {"name": "mc_do", "arguments": '{"steps":[]}'}}]}


class Bridge:
    def __init__(self):
        self.tools = [{"name": "mc_do", "inputSchema": {"type": "object"}, "_meta": {"agent-mc/v1": {"tags": ["act"]}}}]
        self.calls, self.artifacts = [], []
        self.opened = self.closed = False
        self.event_pages = []
        self.on_poll = lambda: None
        self.result = {"text": "accepted, not completed", "protocol": "agent-mc/v1", "execution": action()}

    async def open(self):
        self.opened = True

    async def close(self):
        self.closed = True

    async def resource(self, _):
        return {"contents": [{"text": "Stable core rules"}]}

    async def call(self, name, args, **kwargs):
        self.calls.append((name, args, kwargs))
        if name == "mc_connection":
            return packed({"phase": "disconnected" if args["action"] == "disconnect" else "started",
                           "lamps": [{"label": "服务器", "state": "online"}]})
        if name == "mc_events":
            self.on_poll()
            return packed({"run": "run-1", "nextCursor": len(self.calls), "events": self.event_pages.pop(0) if self.event_pages else []})
        if name == "mc_artifact":
            if args["action"] == "get":
                return {"structuredContent": {"protocol": "agent-mc/v1", "text": self.artifacts[int(args["handle"].split(":")[1]) - 1]}}
            self.artifacts.append(args["text"])
            return packed({"handle": "log:" + str(len(self.artifacts))})
        if name == "mc_protocol":
            return packed({"parts": [{"key": "world", "text": "health=20", "original": "log:health"}]} if args["action"] == "facts" else {})
        if name == "mc_do":
            value = {**self.result, "control": {"requestId": kwargs["request_id"], "barrierAfter": True, "endTurnRequested": False}}
            return {"structuredContent": value}
        if name == "mc_help":
            return {"structuredContent": {"protocol": "agent-mc/v1", "text": "Read the next section"}}
        raise AssertionError(name)


def setup(plugin_module, tmp_path, decide, stop=lambda: False):
    module = importlib.import_module(plugin_module.__name__ + ".controller")
    bridge = Bridge()
    settings = dataclasses.replace(plugin_module.Settings(), max_decisions=2)
    controller = module.Controller(bridge, decide, settings, tmp_path, lambda **_: None, stop)
    return module, bridge, controller


def test_accepted_receipt_preserves_action_and_acknowledges_barrier(plugin_module, tmp_path, run_async):
    async def decide(*_):
        return choose()
    module, bridge, controller = setup(plugin_module, tmp_path, decide)
    controller.persist(stopped=False)
    run_async(controller.turn_once("survive", "prefix", module.model_tools(bridge.tools)))
    assert controller.pending[("task", "body-1")]["terminal"] is False
    phases = [args["action"] for name, args, _ in bridge.calls if name == "mc_protocol"]
    assert phases == ["begin_turn", "facts", "ack_barrier", "end_turn"]
    call = next(row for row in bridge.calls if row[0] == "mc_do")
    assert call[2]["turn_id"] and call[2]["request_id"]
    assert json.loads((tmp_path / "receipts.jsonl").read_text())["result"]["execution"]["goalCompleted"] is False


def test_bounded_read_round_can_continue_without_unrelated_world_change(plugin_module, tmp_path, run_async):
    async def decide(*_):
        response = choose()
        response["tool_calls"][0]["function"] = {"name": "mc_help", "arguments": "{}"}
        return response
    module, bridge, controller = setup(plugin_module, tmp_path, decide)
    controller.settings = dataclasses.replace(controller.settings, max_tool_rounds=1)
    bridge.tools.append({"name": "mc_help", "inputSchema": {"type": "object"}})
    run_async(controller.turn_once("survive", "prefix", module.model_tools(bridge.tools)))
    assert controller.continuation_needed and not controller.pending
    assert len(controller.groups) == 1


def test_running_actions_do_not_cause_idle_or_snapshot_replanning(plugin_module, tmp_path, run_async, monkeypatch):
    decisions, polls, stopped = [], [], False

    async def decide(*_):
        decisions.append(True)
        return choose()

    module, bridge, controller = setup(plugin_module, tmp_path, decide, lambda: stopped)
    clock = [1000]
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    original_sleep = asyncio.sleep

    async def tick(_):
        clock[0] += 61
        await original_sleep(0)

    monkeypatch.setattr(module.asyncio, "sleep", tick)

    def on_poll():
        nonlocal stopped
        polls.append(True)
        stopped = len(polls) >= 8

    bridge.on_poll = on_poll
    bridge.event_pages = [[], *[[{"cursor": n, "type": "snapshot", "trigger": "flush", "text": "unchanged"}] for n in range(7)]]
    run_async(controller.run("survive"))
    assert len(decisions) == 1
    assert bridge.closed
    state = json.loads((tmp_path / "host-state.json").read_text())
    assert state["stopped"] is True and state["pending"] == []


def test_stop_during_model_wait_blocks_late_action(plugin_module, tmp_path, run_async):
    async def exercise():
        entered = asyncio.Event()
        stopped = False

        async def slow(*_):
            entered.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                return choose()  # Misbehaving client delivers a late completion.

        _, bridge, controller = setup(plugin_module, tmp_path, slow, lambda: stopped)
        task = asyncio.create_task(controller.run("survive"))
        await entered.wait()
        stopped = True
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not any(row[0] == "mc_do" for row in bridge.calls)
        assert bridge.closed

    run_async(exercise())


def test_unknown_outcome_blocks_restart_without_replay(plugin_module, tmp_path, run_async):
    async def decide(*_):
        return choose()
    module, bridge, controller = setup(plugin_module, tmp_path, decide)
    bridge.result["execution"]["evidence"] = {"outcomeKnown": False}
    controller.persist(stopped=False)
    with pytest.raises(RuntimeError, match="outcome_unknown"):
        run_async(controller.turn_once("survive", "prefix", module.model_tools(bridge.tools)))
    assert (tmp_path / "receipts.jsonl").exists()
    _, second, restart = setup(plugin_module, tmp_path, decide)
    with pytest.raises(RuntimeError, match="outcome_unknown"):
        run_async(restart.run("survive"))
    assert not second.opened and not second.calls


def test_large_receipts_are_retrievable_in_full(plugin_module, tmp_path, run_async):
    _, bridge, controller = setup(plugin_module, tmp_path, None)
    value = {"text": "原始证据🦊" * 16000}
    compact = run_async(controller.archive_receipt("r", "mc_read", value))
    assert json.loads("".join(bridge.artifacts)) == value
    assert json.loads(compact)["original_chunks"]
    assert all(len(part.encode("utf-16-le")) // 2 <= 64000 for part in bridge.artifacts)
    recovered = []
    for handle in json.loads(compact)["original_chunks"]:
        offset = 0
        while True:
            page = json.loads(run_async(controller.original_page({"handle": handle, "offset": offset}))["text"])
            assert len(page["text"].encode("utf-8")) <= 4000
            recovered.append(page["text"])
            offset = page["next_offset"]
            if not page["has_more"]:
                break
    assert json.loads("".join(recovered)) == value


def test_events_reconcile_terminal_but_ignore_archived_and_stale(plugin_module, tmp_path, run_async):
    _, bridge, controller = setup(plugin_module, tmp_path, None)
    controller.receipt({"execution": action()})
    bridge.event_pages = [[{"execution": action(True), "contextDelivery": "archive-only", "trigger": "preempt"},
                           {"execution": action(True), "meta": {"staleEpoch": True}, "trigger": "preempt"}],
                          [{"execution": action(True), "trigger": "flush"}]]
    assert run_async(controller.events()) == (False, False, False)
    assert controller.pending
    assert run_async(controller.events()) == (True, False, False)
    assert not controller.pending


def test_started_engine_without_server_lamp_is_not_online(plugin_module):
    module = importlib.import_module(plugin_module.__name__ + ".controller")
    assert not module.online({"phase": "started", "lamps": []})


def test_sample_timestamp_alone_does_not_trigger_decisions(plugin_module):
    module = importlib.import_module(plugin_module.__name__ + ".controller")
    first = {"parts": [{"key": "sample", "text": "now"}, {"key": "health", "text": "20"}]}
    later = {"parts": [{"key": "sample", "text": "later"}, {"key": "health", "text": "20"}]}
    assert module.fact_fingerprint(first) == module.fact_fingerprint(later)


def test_progressive_tool_docs_preserve_constraints(plugin_module):
    module = importlib.import_module(plugin_module.__name__ + ".controller")
    original = {"name": "mc_do", "description": "长说明" * 800, "inputSchema": {
        "type": "object", "properties": {"steps": {"type": "array", "minItems": 1, "description": "步骤文档" * 200},
                                          "description": {"type": "string", "description": "This is a real parameter"}},
        "required": ["steps"], "additionalProperties": False}}
    tool = module.model_tools([original])[0]["function"]
    assert tool["parameters"]["required"] == ["steps"]
    assert tool["parameters"]["properties"]["steps"] == {"type": "array", "minItems": 1}
    assert tool["parameters"]["properties"]["description"] == {"type": "string"}
    details = module.tool_help([original], {"name": "mc_do", "path": "/inputSchema/properties/steps"})
    assert json.loads(details["text"]) == original["inputSchema"]["properties"]["steps"]
    assert original["description"] == "长说明" * 800


def test_advanced_router_cannot_invoke_host_connection(plugin_module, tmp_path, run_async):
    async def decide(*_):
        result = choose()
        result["tool_calls"][0]["function"] = {"name": "mc_invoke", "arguments": '{"name":"mc_connection","arguments":{"action":"connect"}}'}
        return result
    module, bridge, controller = setup(plugin_module, tmp_path, decide)
    bridge.tools.append({"name": "mc_goal", "inputSchema": {"type": "object"}})
    with pytest.raises(ValueError, match="unavailable advanced tool"):
        run_async(controller.turn_once("survive", "prefix", module.model_tools(bridge.tools)))
    assert not any(row[0] in {"mc_do", "mc_connection"} for row in bridge.calls)


def test_urgent_event_discards_inflight_plan(plugin_module, tmp_path, run_async):
    async def decide(*_):
        await asyncio.Event().wait()
    module, bridge, controller = setup(plugin_module, tmp_path, decide)
    bridge.event_pages = [[{"trigger": "preempt", "type": "damage", "text": "hurt"}]]
    run_async(controller.turn_once("survive", "prefix", module.model_tools(bridge.tools)))
    assert controller.preempted
    assert controller.recent[0]["type"] == "damage"
    assert not any(row[0] == "mc_do" for row in bridge.calls)


def test_chat_arriving_during_model_wait_reaches_next_turn(plugin_module, tmp_path, run_async):
    async def exercise():
        ready = asyncio.Event()

        async def decide(*_):
            await ready.wait()
            return {"content": "Waiting", "tool_calls": []}
        module, bridge, controller = setup(plugin_module, tmp_path, decide)
        bridge.on_poll = ready.set
        bridge.event_pages = [[{"trigger": "debounce", "type": "chat", "text": "server guide"}]]
        await controller.turn_once("survive", "prefix", module.model_tools(bridge.tools))
        assert controller.deferred_wake
        assert controller.recent[0]["text"] == "server guide"
    run_async(exercise())


def test_context_tail_replaces_facts_and_budgets_all_fields(plugin_module):
    context = importlib.import_module(plugin_module.__name__ + ".context")
    tools = [{"name": "tool", "description": "文" * 1000}]
    facts = {"parts": [{"key": "health", "text": "old"}, {"key": "health", "text": "20", "original": "log:h"},
                       {"key": "chat", "text": "聊天" * 20000, "original": "log:chat"}]}
    messages, usage = context.assemble("stable", tools, "survive", facts, [], [], context_tokens=8000, reserved_output=1024)
    tail = json.loads(messages[-1]["content"])
    assert tail["current_facts"] == [facts["parts"][1]]
    assert tail["omitted_facts"] == [{"key": "chat", "original": "log:chat"}]
    assert usage["total"] <= 8000
    other, _ = context.assemble("stable", tools, "survive", {"parts": []}, [], [], context_tokens=8000, reserved_output=1024)
    assert messages[:2] == other[:2]
    assert not json.loads(other[-1]["content"])["current_facts"]
    with pytest.raises(ValueError, match="context_budget_exceeded"):
        context.assemble("stable", tools * 5, "survive", facts, [], [], context_tokens=8000, reserved_output=1024)


def test_worker_is_single_owner_and_cleans_up_before_stop_returns(plugin_module, tmp_path):
    import threading
    entered, cleanup = threading.Event(), threading.Event()

    async def factory(*_):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleanup.set()

    worker = plugin_module.Worker(factory, tmp_path / "errors.log")
    assert worker.start("survive")
    assert entered.wait(5)
    assert not worker.start("another")
    assert worker.stop(5)
    assert cleanup.is_set()
    assert not worker.snapshot()["worker_alive"]
    assert worker.stop(5)
