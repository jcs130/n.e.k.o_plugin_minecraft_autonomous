import asyncio
import hashlib
import importlib
import json
import threading
import time
from contextlib import nullcontext
from types import SimpleNamespace
from urllib.error import HTTPError
from uuid import uuid4

import pytest


@pytest.fixture
def resident(monkeypatch, plugin_instance):
    plugin = plugin_instance
    monkeypatch.setattr(plugin, "local_characters", lambda: (["YUI", "Another role"], "Another role"))
    session = {"endpoint": plugin.portal + "/api/v1/resident-turns/test-resident", "token": "rdt_" + "a" * 43,
               "resident": {"id": "test-resident", "characterId": str(uuid4()), "name": "测试居民", "bodyKind": "maid"}}
    mode = importlib.import_module(type(plugin).__module__ + ".neko_resident_mode")
    connection = importlib.import_module(type(plugin).__module__ + ".neko_resident_connection")
    return plugin, session, mode, connection


def offered_turn(session):
    return {
        "id": str(uuid4()), "kind": "plan", "until": time.time() * 1000 + 60_000,
        "resident": session["resident"],
        "scene": {"bodyTools": [{"tool": "observe"}], "communication": {
            "version": 1, "messages": [], "outputs": [{"mode": "native", "scope": "nearby"}],
        }},
    }


def test_desktop_device_reads_first_then_uses_the_same_start_id_on_stop(monkeypatch, run_async, resident):
    plugin, session, mode, _ = resident
    character = {**session["resident"], "bodyId": str(uuid4())}
    session["resident"] = character
    record = {"character": character["characterId"], "refreshToken": "fixture-refresh-only", "localRole": "YUI"}
    device_calls, body_calls = [], []
    controller = None

    def authorized(op, payload):
        nonlocal controller
        device_calls.append((op, payload))
        if op == "status":
            return {"character": character, "activeKind": "maid", "controller": controller,
                    "canStart": controller is None, "modes": ["maid"]}
        if op == "start":
            assert plugin._desktop_play_record()["requestId"] == payload["requestId"]
            assert plugin._desktop_play_record()["phase"] == "starting"
            controller = "this_device"
            return session
        assert op == "stop"
        controller = None
        return {"stopped": True}

    def body_post(actual_session, op, _payload):
        assert actual_session["deviceHeaders"] == {"X-QD-Device": "fixture-proof"}
        body_calls.append(op)
        return {"turn": None}

    plugin._desktop_client = SimpleNamespace(login=None, settings=lambda: record, authorized=authorized,
        headers=lambda _record: {"X-QD-Device": "fixture-proof"}, remember_role=lambda *_: None)
    monkeypatch.setattr(mode, "post", body_post)

    async def exercise():
        token = plugin.panel_token
        assert (await plugin.desktop_device("refresh", token)).value == {"status": "authorized"}
        assert [op for op, _ in device_calls] == ["status"]
        assert not body_calls
        assert "fixture-refresh-only" not in json.dumps(await plugin.connection_context())
        assert not plugin._resident_blocks_player()
        start = await plugin.desktop_device("start", token, mode="maid")
        assert start.value["phase"] == "running"
        assert plugin._resident_blocks_player()
        assert body_calls == ["begin", "poll"]
        assert (await plugin.desktop_device("start", token, mode="maid")).error["code"] == "desktop_request_pending"
        stop = await plugin.desktop_device("stop", token)
        assert stop.value == {"stopped": True, "requestId": start.value["requestId"], "controllerReleased": True}
        assert [p["requestId"] for op, p in device_calls if op in ("start", "stop")] == [start.value["requestId"]] * 2
        assert not plugin._resident_blocks_player()

    run_async(exercise())


def test_unknown_desktop_start_is_durable_and_never_resubmitted(run_async, resident):
    plugin, session, _, _ = resident
    character = session["resident"]
    starts = []

    def authorized(op, payload):
        if op == "status":
            return {"character": character, "activeKind": "maid", "canStart": not starts}
        assert op == "start"
        starts.append(payload["requestId"])
        raise TimeoutError()

    plugin._desktop_client = SimpleNamespace(login=None, settings=lambda: {
        "character": character["characterId"], "refreshToken": "fixture-only", "localRole": "YUI"}, authorized=authorized)

    async def exercise():
        token = plugin.panel_token
        failure = await plugin.desktop_device("start", token, mode="maid")
        assert failure.error["code"] == "desktop_play_unconfirmed"
        assert failure.error["requestId"] == starts[0]
        assert plugin._desktop_play_record()["phase"] == "starting"
        assert plugin._desktop_play_record()["requestId"] == starts[0]
        assert plugin._resident_blocks_player()
        assert (await plugin.desktop_device("start", token, mode="maid")).error["code"] == "desktop_request_pending"
        assert (await plugin.desktop_device("stop", token)).error["code"] == "desktop_request_pending"
        assert (await plugin.desktop_device("refresh", token)).value == {"status": "authorized"}
        assert len(starts) == 1

    run_async(exercise())


def test_desktop_stop_ends_local_control_even_when_portal_is_unreachable(run_async, resident):
    plugin, session, _, _ = resident
    original = {"requestId": str(uuid4()), "characterId": session["resident"]["characterId"]}
    plugin._write_desktop_play(original, "running")
    plugin._resident_phase = "running"
    plugin._resident_session = session
    calls = []

    def authorized(op, _payload):
        calls.append(op)
        raise TimeoutError()

    plugin._desktop_client = SimpleNamespace(login=None, settings=lambda: {
        "character": original["characterId"], "refreshToken": "fixture-only"}, authorized=authorized)
    failure = run_async(plugin.desktop_device("stop", plugin.panel_token))
    assert failure.error["code"] == "desktop_play_unconfirmed"
    assert failure.error["requestId"] == original["requestId"]
    assert calls == ["status"]
    assert plugin._resident_phase == "stopped"
    assert plugin._resident_session is None
    assert plugin._resident_blocks_player()


def test_desktop_play_receipt_must_match_original_role_mode_and_id(run_async, resident):
    plugin, session, _, _ = resident
    original = {"requestId": str(uuid4()), "characterId": session["resident"]["characterId"], "mode": "maid"}
    plugin._write_desktop_play(original, "starting")
    calls = []
    expired = {**original, "status": "expired", "updatedAt": int(time.time() * 1000), "reason": "LEASE_EXPIRED"}
    replies = [HTTPError(plugin.portal, 404, "Not Found", {}, None),
               {**expired, "characterId": str(uuid4())},
               {"requestId": original["requestId"], "status": "unknown", "characterId": None, "mode": None,
                "updatedAt": None, "reason": "NO_RECEIPT"}, expired]

    def authorized(op, payload):
        calls.append((op, payload))
        reply = replies.pop(0)
        if isinstance(reply, HTTPError):
            raise reply
        return reply

    plugin._desktop_client = SimpleNamespace(login=None, authorized=authorized)

    async def exercise():
        assert (await plugin.desktop_device("verify", plugin.panel_token)).error["code"] == "desktop_receipt_unavailable"
        for _ in range(2):
            assert (await plugin.desktop_device("verify", plugin.panel_token)).error["code"] == "desktop_play_unconfirmed"
            assert plugin._resident_blocks_player()
        receipt = await plugin.desktop_device("verify", plugin.panel_token)
        assert receipt.value == {"status": "expired", "requestId": original["requestId"]}
        assert not plugin._resident_blocks_player()
        assert calls == [("play-status", {"requestId": original["requestId"]})] * 4

    run_async(exercise())


def test_desktop_refresh_reuses_original_rotation_after_network_failure(resident):
    plugin, session, _, connection = resident
    original = {"character": session["resident"]["characterId"], "role": session["resident"]["id"],
                "device": str(uuid4()), "proof": "p" * 43, "expiresAt": 0,
                "refreshToken": "qdr2_" + "r" * 43, "accessToken": "qda2_" + "a" * 43}
    row = dict(original)
    calls = []

    def save(new):
        row.clear()
        row.update(new)

    def request(url, payload, token, *, extra_headers):
        op = url.rsplit("/", 1)[-1]
        calls.append((op, payload))
        assert extra_headers == {"X-QD-Device": original["device"], "X-QD-Device-Proof": original["proof"]}
        if op == "refresh":
            if len(calls) == 1:
                raise TimeoutError()
            assert calls[0] == calls[1]
            return {**original, "expiresAt": int(time.time() * 1000) + 60_000,
                    "accessToken": "qda2_" + "b" * 43, "refreshToken": "qdr2_" + "s" * 43}
        assert op == "status" and token == "qda2_" + "b" * 43
        return {"character": session["resident"]}

    vault = SimpleNamespace(lock=nullcontext, load=lambda: dict(row), save=save)
    device = connection.DesktopDevice(plugin.portal, vault, request)
    with pytest.raises(TimeoutError):
        device.authorized("status", {})
    assert row["rotationId"] == calls[0][1]["rotationId"]
    assert device.authorized("status", {})["character"] == session["resident"]
    assert [op for op, _ in calls] == ["refresh", "refresh", "status"]
    assert "rotationId" not in row


def test_browser_authorization_binds_exact_existing_body_without_start(monkeypatch, run_async, resident):
    plugin, session, _, connection = resident
    original_tools = plugin.list_llm_tools()
    expires_at = time.time() * 1000 + 60_000
    browser_id = str(uuid4())
    opened, calls = [], []
    wrong_body = False

    def request(url, payload, *_):
        op = url.rsplit("/", 1)[-1]
        calls.append(op)
        if op == "browser-start":
            assert payload == {"bodyRead": True}
            return {"id": browser_id, "expiresAt": expires_at, "code": "123456", "secret": "rba_" + "b" * 43}
        if op == "browser-status":
            return {"state": "authorized", "expiresAt": expires_at, "onboardingToken": "rot_" + "c" * 43,
                    "playerAuthorizationExpiresAt": int(expires_at), "bodyReadExpiresAt": int(expires_at)}
        if op == "list":
            return {"availableBodies": ["maid", "numen"], "residents": [{**session["resident"], "state": "available"}]}
        if op == "character-bodies":
            assert payload is None
            return {"available": True, "characters": [{"name": "桐人", "characterId": session["resident"]["characterId"],
                    "activeKind": "numen", "status": "ready", "pendingRequestId": "request-1",
                    "targetKinds": ["mineflayer", "maid"], "generation": 7, "autonomous": True,
                    "token": "qdh_private_from_website"}]}
        if op == "request-1":
            assert payload is None and url.endswith("/" + session["resident"]["characterId"] + "/switch/request-1")
            return {"requestId":op, "characterId":session["resident"]["characterId"], "status":"completed",
                    "activeKind":"numen", "targetKind":"numen", "generation":8, "phase":"completed",
                    "reason":"ORIGINAL_RECEIPTS_CONFIRMED", "token":"qdh_private_from_website"}
        assert op == "connect"
        assert payload == {key: session["resident"][key] for key in ("id", "characterId")}
        return {**session, "resident": {**session["resident"], "characterId": str(uuid4())}} if wrong_body else session

    def open_browser(url):
        opened.append(url)
        return True

    monkeypatch.setattr(connection, "request_json", request)
    monkeypatch.setattr(connection.webbrowser, "open", open_browser)
    ui_token = plugin.panel_token

    async def exercise():
        nonlocal wrong_body
        assert (await plugin.resident_start(uiToken="invalid")).error["code"] == "resident_panel_required"
        assert (await plugin.resident_start(uiToken=ui_token)).error["code"] == "resident_binding_required"
        assert plugin.list_llm_tools() == original_tools
        assert (await plugin.resident_browser_login(op="start", uiToken=ui_token)).value == {"opened": True}
        assert (await plugin.connection_context())["browserCode"] == "123456"
        assert opened == [plugin.portal + "/resident-connect.html?flow=browser&play=1&bodyRead=1#" + browser_id]
        assert (await plugin.resident_browser_login(op="status", uiToken=ui_token)).value == {"state": "authorized"}
        args = {key: session["resident"][key] for key in ("id", "characterId")}
        assert (await plugin.connection_context())["bodyReadable"]
        await plugin.read_character_body(op="switch", uiToken=ui_token)
        await plugin.read_character_body(op="list", uiToken="wrong")
        assert (await plugin.read_character_body(op="list", uiToken=ui_token)).value == {"updated":True}
        assert (await plugin.read_character_body(op="receipt", characterId=args["characterId"],requestId="request-1",uiToken=ui_token)).value == {"updated":True}
        body_context = await plugin.connection_context()
        assert body_context["bodyView"]["characters"][0]["targetKinds"] == ["mineflayer", "maid"]
        assert body_context["bodyView"]["characters"][0]["generation"] == 7
        assert body_context["bodyReceipt"]["requestId"] == "request-1"
        assert body_context["bodyReceipt"]["generation"] == 8
        assert body_context["bodyReceipt"]["reason"] == "ORIGINAL_RECEIPTS_CONFIRMED"
        assert "qdh_private_from_website" not in json.dumps(body_context)
        await plugin.read_character_body(op="list", uiToken=ui_token)
        assert (await plugin.connection_context())["bodyReceipt"]["requestId"] == "request-1"
        await plugin.open_resident_website(page="bodies", uiToken=ui_token)
        assert opened[-1] == plugin.portal + "/resident-connect.html?flow=bodies"
        wrong_body = True
        refused = await plugin.manage_residents(op="connect", localRole="YUI", uiToken=ui_token, **args)
        assert refused.error["code"] == "resident_identity_changed"
        assert not plugin.data_path("resident-binding.json").exists()
        wrong_body = False
        plugin._resident_health = "reauthorize"
        bound = await plugin.manage_residents(op="connect", localRole="YUI", uiToken=ui_token, **args)
        assert bound.value["controlling"] is False
        state = await plugin.connection_context()
        assert state["role"] == "YUI"
        assert state["characterId"] == session["resident"]["characterId"]
        assert state["control"]["phase"] == "stopped"
        assert state["control"]["health"] == "idle"
        assert not state["bodyReadable"] and state["bodyReceipt"] is None
        assert plugin.website_login_state()["playerAuthorized"] is True
        assert plugin.website_player_grant() == "rba_" + "b" * 43
        assert plugin.website_player_grant() not in json.dumps(plugin.website_login_state())
        assert session["token"] not in json.dumps(state)
        assert plugin.list_llm_tools() == original_tools

    run_async(exercise())
    assert calls == ["browser-start", "browser-status", "list", "character-bodies", "request-1", "character-bodies", "connect", "connect"]


def test_resident_start_scopes_tools_and_keeps_player_mode_idle(monkeypatch, run_async, resident):
    plugin, session, mode, _ = resident
    original_tools = plugin.list_llm_tools()
    turn = offered_turn(session)
    turn["resident"] = {**turn["resident"], "name": "未用于绑定的场景名称"}
    calls, messages = [], []

    def post(binding, operation, payload):
        assert binding == session
        calls.append((operation, payload))
        return {"turn": turn} if operation == "poll" else {"accepted": True}

    def submit(**message):
        messages.append(message)
        return {"submitted": True}

    monkeypatch.setattr(mode, "post", post)
    monkeypatch.setattr(plugin, "push_message", submit)
    ui_token = plugin.panel_token

    async def exercise():
        await plugin._bind("YUI", session)
        plugin._player_start_requests = 1
        assert (await plugin.resident_start(uiToken=ui_token)).error["code"] == "player_runtime_busy"
        assert not calls
        plugin._player_start_requests = 0
        assert (await plugin.resident_start(uiToken=ui_token)).is_ok()
        await asyncio.sleep(0)
        tools = {tool["name"]: tool["role"] for tool in plugin.list_llm_tools() if tool not in original_tools}
        assert tools == dict.fromkeys(mode.TOOLS, "YUI")
        assert len(messages) == 1
        assert messages[0]["target_lanlan"] == "YUI"
        assert messages[0]["visibility"] == []
        instructions, scene_json = messages[0]["parts"][0]["text"].split("\n", 1)
        assert "这是你自身的游戏回合" in instructions
        assert "第一人称" in instructions
        assert "游戏的确认回执" in instructions
        identity = {"desktopRole": "YUI", "controlledResident": "测试居民"}
        assert json.loads(instructions.split("身份对应关系：", 1)[1]) == identity
        assert json.loads(scene_json) == turn
        assert (await plugin.capabilities(id=turn["id"]))["controlledBody"] == identity
        assert (await plugin.start()).error["code"] == "resident_control_active"
        assert (await plugin.quick_start(connection={"host": "example.invalid"})).error["code"] == "resident_control_active"
        assert (await plugin._submit("goal", {}, "test")).error["code"] == "resident_control_active"
        assert (await plugin.body_action(id=turn["id"], tool="unoffered", arguments={}))["reason"] == "action_not_offered"
        wrong_scope = await plugin.communicate(id=turn["id"], text="测试", mode="native", scope="public")
        assert wrong_scope["detail"] == "scope_not_offered"
        sent = await plugin.communicate(id=turn["id"], text="测试", mode="text", scope="nearby", sourceEventId="")
        assert sent == {"accepted": True}
        assert (await plugin.resident_stop(uiToken=ui_token)).value["phase"] == "stopped"
        assert (await plugin.resident_stop(uiToken=ui_token)).is_ok()
        assert plugin.list_llm_tools() == original_tools
        assert plugin._read_resident_binding() == ("YUI", session)

    run_async(exercise())
    assert calls == [("poll", {}), ("reply", {"id": turn["id"], "answer": {"communication": {"mode": "native", "text": "测试"}}})]


def test_resident_voice_round_trip_preserves_scope_and_reports_server_receipt(monkeypatch, run_async, resident):
    plugin, session, mode, _ = resident
    turn = offered_turn(session)
    turn["kind"] = "dialogue"
    turn["scene"]["bodyTools"] = []
    original = str(uuid4())
    transcript = "private transcript"
    turn["scene"]["communication"].update(
        messages=[{"id": original, "medium": "voice", "scope": "private", "speakerId": str(uuid4()),
                   "listenerId": str(uuid4()), "text": transcript}],
        outputs=[{"mode": "speech", "scope": "private", "sourceEventId": original}],
    )
    calls, delivered = [], []

    def post(binding, operation, payload):
        assert binding == session
        calls.append((operation, payload))
        return {"turn": turn} if operation == "poll" else {"accepted": True}

    def push_message(**message):
        delivered.append(message)
        return {"submitted": True}

    monkeypatch.setattr(mode, "post", post)
    monkeypatch.setattr(plugin, "push_message", push_message)

    async def exercise():
        await plugin._bind("YUI", session)
        assert (await plugin.resident_start(uiToken=plugin.panel_token)).is_ok()
        await asyncio.sleep(0)
        assert delivered[0]["target_lanlan"] == "YUI"
        assert delivered[0]["visibility"] == []
        model_turn = json.loads(delivered[0]["parts"][0]["text"].split("\n", 1)[1])
        assert model_turn["scene"]["communication"]["messages"] == turn["scene"]["communication"]["messages"]
        control = (await plugin.connection_context())["control"]
        assert control["voice"] == {"transcriptReceived": True, "outputModes": ["speech"], "receipt": None}
        assert transcript not in json.dumps(control) and original not in json.dumps(control)

        denied = await plugin.communicate(id=turn["id"], text="Reply", mode="speech", scope="nearby",
                                          sourceEventId=original)
        assert denied["detail"] == "scope_not_offered"
        assert len(calls) == 1
        accepted = await plugin.communicate(id=turn["id"], text="Reply", mode="speech", scope="private",
                                            sourceEventId=original)
        assert accepted == {"accepted": True}
        assert plugin._resident_status()["voice"] == {"transcriptReceived": True, "outputModes": [], "receipt": None}

        follow_up = offered_turn(session)
        follow_up["scene"]["communication"]["receipts"] = [
            {"captionRecipients": 1, "hearingVerified": True,
             "voice": {"requestId": "private voice id", "state": "sent", "text": transcript}},
            {"voice": {"state": "arbitrary server string"}},
        ]
        plugin._deliver_resident_turn(follow_up)
        assert plugin._resident_status()["voice"] == {
            "transcriptReceived": True, "outputModes": ["native"],
            "receipt": {"state": "sent", "captionRecipients": 1},
        }
        follow_up["until"] = 0
        assert plugin._resident_status()["voice"]["outputModes"] == []
        assert (await plugin.resident_stop(uiToken=plugin.panel_token)).is_ok()
        assert plugin._resident_status()["voice"] == {"transcriptReceived": False, "outputModes": [], "receipt": None}

    run_async(exercise())
    assert calls == [
        ("poll", {}),
        ("reply", {"id": turn["id"], "answer": {"communication": {
            "mode": "speech", "text": "Reply", "sourceEventId": original,
        }}}),
    ]


def test_new_resident_waits_for_same_body_before_binding(monkeypatch, run_async, resident):
    plugin, session, _, _ = resident
    session["resident"]["bodyKind"] = "numen"
    ready = False
    calls = []

    async def request(operation, payload):
        calls.append(operation)
        row = {**session["resident"], "state": "available" if ready else "preparing"}
        if operation == "create":
            assert {key: payload[key] for key in ("name", "persona", "bodyKind")} == {
                "name": "测试居民", "persona": "测试托管设定", "bodyKind": "numen",
            }
            assert payload["requestId"]
            return {"resident": row}
        if operation == "list":
            return {"availableBodies": ["numen"], "residents": [row]}
        assert ready and operation == "connect"
        assert payload == {key: row[key] for key in ("id", "characterId")}
        return session

    monkeypatch.setattr(plugin, "_onboarding_request", request)

    async def exercise():
        nonlocal ready
        plugin.authorization = {"expiresAt": time.time() * 1000 + 60_000}
        pending = await plugin.manage_residents(op="create", uiToken=plugin.panel_token,
                                                localRole="YUI", bodyKind="numen", name="测试居民", persona="测试托管设定")
        assert pending.value["state"] == "preparing"
        assert plugin._read_resident_binding() == ("", None)
        ready = True
        prepared = await plugin.manage_residents(op="list", uiToken=plugin.panel_token)
        assert prepared.value["controlling"] is False
        assert plugin._read_resident_binding() == ("YUI", session)

    run_async(exercise())
    assert calls == ["create", "list", "list", "connect"]


def test_stop_waits_for_reply_and_restart_does_not_replay_it(monkeypatch, run_async, resident):
    plugin, session, mode, _ = resident
    turn = offered_turn(session)
    published, may_finish = threading.Event(), threading.Event()
    replies, messages = [], []

    def post(_, operation, payload):
        if operation == "poll":
            return {"turn": turn}
        replies.append(payload)
        published.set()
        assert may_finish.wait(4)
        raise OSError("test lost reply")

    def submit(**message):
        messages.append(message)
        return {"submitted": True}

    monkeypatch.setattr(mode, "post", post)
    monkeypatch.setattr(plugin, "push_message", submit)
    ui_token = plugin.panel_token

    async def exercise():
        await plugin._bind("YUI", session)
        assert (await plugin.resident_start(uiToken=ui_token)).is_ok()
        await asyncio.sleep(0)
        reply = asyncio.create_task(plugin.decide(id=turn["id"], answer={}))
        try:
            assert await asyncio.to_thread(published.wait, 4)
            stopped = asyncio.create_task(plugin.resident_stop(uiToken=ui_token))
            await asyncio.sleep(0)
            assert not stopped.done()
            assert plugin._resident_status()["phase"] == "stopping"
            assert (await plugin.start()).error["code"] == "resident_control_active"
        finally:
            may_finish.set()
        assert (await reply)["reason"] == "reply_unconfirmed"
        assert (await stopped).is_ok()
        saved = plugin.data_path("resident-replies", session["resident"]["characterId"] + ".json")
        assert json.loads(saved.read_bytes()) == {"turnHash": hashlib.sha256(turn["id"].encode()).hexdigest(), "retryable": False}
        assert (await plugin.resident_start(uiToken=ui_token)).is_ok()
        await asyncio.sleep(0)
        assert len(messages) == 1
        assert (await plugin.decide(id=turn["id"], answer={}))["accepted"] is False
        assert (await plugin.resident_stop(uiToken=ui_token)).is_ok()

    run_async(exercise())
    assert len(replies) == 1


def test_expired_portal_binding_requires_reauthorization(monkeypatch, run_async, resident):
    plugin, session, mode, _ = resident
    original_tools = plugin.list_llm_tools()

    def expired(*_):
        raise HTTPError(session["endpoint"], 401, "expired", {}, None)

    monkeypatch.setattr(mode, "post", expired)
    run_async(plugin._bind("YUI", session))
    result = run_async(plugin.resident_start(uiToken=plugin.panel_token))
    assert result.error["code"] == "resident_authorization_expired"
    assert plugin._resident_status()["phase"] == "stopped"
    assert plugin.list_llm_tools() == original_tools


def test_owner_device_pairing_displays_only_approval_id(monkeypatch, resident, run_async):
    plugin, session, _, connection = resident
    until = int(time.time() * 1000) + 180_000
    character = session["resident"]["characterId"]
    plugin.authorization = {"expiresAt": until, "bodyReadExpiresAt": until}
    plugin.body_view = {"available": True, "characters": [{"characterId": character}]}
    pending = SimpleNamespace(
        pair_id="a" * 24,
        approval_url=plugin.portal + "/resident-connect.html?flow=bodies",
        expires_at=until,
        poll_secret="unit-test-private-poll",
    )
    grant = SimpleNamespace(expires_at=until, character_id=character, token="unit-test-private-device-grant")
    seen = []

    async def begin(origin):
        assert origin == plugin.portal
        seen.append("begin")
        return pending

    async def redeem(pairing):
        assert pairing is pending
        seen.append("redeem")
        return grant if seen.count("redeem") == 2 else None

    def open_browser(url):
        assert url == pending.approval_url
        seen.append("open")
        return True

    monkeypatch.setattr(plugin, "_body_device_provider",
                        lambda: SimpleNamespace(begin_device_pairing=begin, redeem_device_pairing=redeem))
    monkeypatch.setattr(connection.webbrowser, "open", open_browser)

    async def exercise():
        assert (await plugin.pair_body_device(op="start", uiToken="wrong")).error
        assert not seen
        token = plugin.panel_token
        plugin.body_view["available"] = False
        assert (await plugin.pair_body_device(op="start", uiToken=token, characterId=character)).error
        assert not seen
        plugin.body_view["available"] = True
        assert (await plugin.pair_body_device(op="start", uiToken=token, characterId="other")).error
        assert (await plugin.pair_body_device(op="start", uiToken=token, characterId=character)).value == {"state": "pending"}
        assert (await plugin.pair_body_device(op="start", uiToken=token, characterId=character)).value == {"state": "pending"}
        state = await plugin.connection_context()
        assert state["bodyDeviceAvailable"]
        assert state["bodyDevice"] == {"state": "pending", "pairId": pending.pair_id,
                                       "expiresAt": until, "characterId": character}
        assert pending.poll_secret not in json.dumps(state)
        assert (await plugin.pair_body_device(op="open", uiToken=token)).value == {"state": "pending"}
        assert (await plugin.pair_body_device(op="check", uiToken=token)).value == {"state": "pending"}
        assert (await plugin.pair_body_device(op="check", uiToken=token)).value == {"state": "paired"}
        assert plugin.desktop_body_device_grant() is grant
        state = await plugin.connection_context()
        assert state["bodyDevice"] == {"state": "paired", "characterId": character}
        assert grant.token not in json.dumps(state)
        assert not plugin.data_path("resident-binding.json").exists()

    run_async(exercise())
    assert seen == ["begin", "open", "redeem", "redeem"]


def test_owner_device_pairing_hides_private_provider_errors_and_cancels(monkeypatch, resident, run_async):
    plugin, session, _, _ = resident
    private = "unit-test-private-failed-poll"
    until = int(time.time() * 1000) + 180_000
    character = session["resident"]["characterId"]
    plugin.authorization = {"expiresAt": until, "bodyReadExpiresAt": until}
    plugin.body_view = {"available": True, "characters": [{"characterId": character}]}
    response = None

    async def begin(_):
        return SimpleNamespace(pair_id="b" * 24, approval_url=plugin.portal + "/resident-connect.html?flow=bodies",
                               expires_at=time.time() * 1000 + 180000)

    async def redeem(_):
        if response is not None:
            return response
        raise ValueError(private)

    monkeypatch.setattr(plugin, "_body_device_provider",
                        lambda: SimpleNamespace(begin_device_pairing=begin, redeem_device_pairing=redeem))

    async def exercise():
        token = plugin.panel_token
        plugin._resident_phase = "running"
        assert (await plugin.pair_body_device(op="start", uiToken=token)).error["code"] == "resident_control_active"
        plugin._resident_phase = "stopped"
        assert (await plugin.pair_body_device(op="start", uiToken=token, characterId=character)).value == {"state": "pending"}
        assert private not in (await plugin.pair_body_device(op="check", uiToken=token)).error
        assert (await plugin.connection_context())["bodyDevice"]["state"] == "pending"
        assert (await plugin.pair_body_device(op="cancel", uiToken=token)).value == {"state": "idle"}
        assert (await plugin.connection_context())["bodyDevice"] == {"state": "idle"}
        assert (await plugin.pair_body_device(op="start", uiToken=token, characterId=character)).value == {"state": "pending"}

    run_async(exercise())
    response = SimpleNamespace(character_id="another-role", expires_at=until, token=private)
    refused = run_async(plugin.pair_body_device(op="check", uiToken=plugin.panel_token))
    assert private not in refused.error and "另一角色" in refused.error
    assert plugin.desktop_body_device_grant() is None
