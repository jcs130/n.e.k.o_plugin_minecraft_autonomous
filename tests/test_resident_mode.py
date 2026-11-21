import asyncio
import hashlib
import importlib
import json
import threading
import time
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
        assert turn["id"] in messages[0]["parts"][0]["text"]
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
