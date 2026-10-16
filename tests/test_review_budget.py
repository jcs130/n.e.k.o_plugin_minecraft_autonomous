import asyncio
import importlib
import json
from copy import deepcopy
from unittest.mock import AsyncMock

import httpx
import jsonschema
import pytest
from agent_mc_autonomy.host_context import HostContextPort
from test_death_reflection import metadata, setup_death
from test_heartbeat import setup
from test_speech_output import prepare


def profile_module(plugin):
    return importlib.import_module(plugin.__class__.__module__ + ".neko_host_context")


def test_follow_current_actor_rechecks_public_identity_and_failure_is_explicit(plugin_instance, monkeypatch, run_async):
    module = profile_module(plugin_instance)
    actor = ["First"]
    client = httpx.AsyncClient

    async def handler(request):
        if actor[0] == "unavailable":
            return httpx.Response(503)
        return httpx.Response(200, json={"当前猫娘": actor[0], "猫娘": {actor[0]: {"system_prompt": "public traits"}}})

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kw: client(transport=httpx.MockTransport(handler), **kw))
    config = module.HostContextSettings(character_api_url="http://127.0.0.1:32123/api/characters")
    assert run_async(module.character_profile(plugin_instance, config, ""))["agent_name"] == "First"
    actor[0] = "Second"
    assert run_async(module.character_profile(plugin_instance, config, ""))["agent_name"] == "Second"
    actor[0] = "unavailable"
    assert run_async(module.character_profile(plugin_instance, config, "")) == {}


def test_fresh_inspection_projects_only_public_profile_without_ack(plugin_instance, monkeypatch, run_async):
    port, snapshot, _ = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    rid = port.offer()["review"]["id"]
    profile = {"agent_name": "TestRole", "persona": "curious and careful", "persona_source": "character_profile"}
    monkeypatch.setattr(profile_module(plugin_instance), "character_profile", AsyncMock(return_value=profile))
    denied = run_async(plugin_instance.minecraft_autonomy_review(rid, "continue", "Keep working"))
    assert denied["error"] == "fresh_inspection_required"
    result = run_async(plugin_instance.minecraft_autonomy_review(rid, "inspect"))
    assert result["character_binding"]["available"] and not result["acknowledged"]
    assert not result["context_request"]["persona_needed"]
    assert result["context_request"]["memory_selection"] == "not_provided"
    assert not port.state()["review"].get("result") and not port.mailbox.ready()
    host = HostContextPort(port.directory, now=port.now)
    assert host.read(999)["stable"] == profile
    assert host.read(999)["dynamic"]["current_intent"] == ""
    assert "curious and careful" not in json.dumps(result)
    before = deepcopy(port.state())
    page = run_async(plugin_instance.minecraft_autonomy_review(rid, "inspect", evidence_ref=result["evidence_ref"], detail_path=["evidence"]))
    assert page["historical"] and port.state() == before


def test_profile_read_failure_and_opt_out_do_not_reuse_stale_static_profile(plugin_instance, monkeypatch, run_async):
    port, snapshot, _ = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    rid = port.offer()["review"]["id"]
    module = profile_module(plugin_instance)
    profile = {"agent_name": "TestRole", "persona": "public", "persona_source": "character_profile"}
    monkeypatch.setattr(module, "character_profile", AsyncMock(return_value=profile))
    run_async(plugin_instance.minecraft_autonomy_review(rid, "inspect"))
    monkeypatch.setattr(module, "character_profile", AsyncMock(return_value={}))
    failed = run_async(plugin_instance.minecraft_autonomy_review(rid, "inspect"))
    assert failed["character_binding"]["reason"] == "public_profile_unavailable"
    assert not HostContextPort(port.directory, now=port.now).read(0)
    monkeypatch.setattr(plugin_instance.config, "update", AsyncMock())

    async def changing(*_):
        await plugin_instance.save_settings({"host_context": {"enabled": False}})
        return profile

    monkeypatch.setattr(module, "character_profile", changing)
    result = run_async(plugin_instance.minecraft_autonomy_review(rid, "inspect"))
    assert result["error"] == "configuration_changed_or_stopped"
    assert not (port.directory / "host-character.json").exists()


def test_late_profile_read_preserves_concurrent_final_explicit_projection(plugin_instance, monkeypatch, run_async):
    port, snapshot, _ = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    rid = port.offer()["review"]["id"]
    port.decide(rid, "inspect")
    profile = {"agent_name": "TestRole", "persona": "public", "persona_source": "character_profile"}

    async def concurrent(*_):
        accepted = port.decide(rid, "continue", "Continue", require_inspection=True,
                              host_context={"agent_name": "TestRole", "persona": "explicit main brain",
                                            "current_intent": "explicit intent", "memories": []})
        assert accepted["acknowledged"]
        return profile

    monkeypatch.setattr(profile_module(plugin_instance), "character_profile", concurrent)
    run_async(plugin_instance.minecraft_autonomy_review(rid, "inspect"))
    stored = HostContextPort(port.directory, now=port.now).read(0)
    assert stored["stable"]["persona"] == "explicit main brain"
    assert stored["dynamic"]["current_intent"] == "explicit intent"


@pytest.mark.parametrize("outcome", ["lesson", "deferred"])
def test_compact_same_brain_final_contract_and_optional_local_token_budget(plugin_instance, monkeypatch, run_async, outcome):
    _, port, review, _ = setup_death(plugin_instance, monkeypatch)
    inspected = run_async(plugin_instance.minecraft_autonomy_review(review["id"], "inspect"))
    assert len(json.dumps(inspected, ensure_ascii=False).encode()) < 14000
    contract = inspected["completion_contract"]
    assert contract["required"]["heartbeat_id"] == review["id"]
    assert contract["death_reflection"]["required"]["evidence_ref"] == inspected["evidence_ref"]
    reflection = {"evidence_ref": inspected["evidence_ref"], "outcome": outcome}
    if outcome == "lesson":
        reflection.update(lesson="复活后重查资源", applicability="重返旧路线前")
    else:
        reflection["reason"] = "死因不明，暂不推断教训"
    payload = {"heartbeat_id": review["id"], "decision": "continue", "reason": "重生后背包为空",
               "death_reflection": reflection}
    jsonschema.validate(payload, metadata(plugin_instance).parameters)
    # Optional local tokenizer; no model/provider calls. The persisted regression
    # still tests the actual SDK schema and final path when this is not installed.
    try:
        import tiktoken
    except ImportError:
        pass
    else:
        assert len(tiktoken.get_encoding("o200k_base").encode(json.dumps(payload, ensure_ascii=False))) < 260
    accepted = run_async(plugin_instance.minecraft_autonomy_review(**payload))
    assert accepted["acknowledged"] and not accepted["reflection_pending"]
    assert port.state()["review"]["reflection"]["outcome"] == outcome


@pytest.mark.parametrize("public,expected", [
    ({"speech_id": "speech-123", "audio_queued": True, "audio_completed": False},
     {"speech_id": "speech-123", "audio_queued": True, "audio_completed": False}),
    ({"speech_id": "x" * 161, "audio_queued": 1, "audio_completed": "yes"}, {}),
    ({"speech_id": "private text\nsecret"}, {}),
    ({}, {}),
    ({"speech_id": "speech:done", "audio_queued": True, "audio_completed": True},
     {"speech_id": "speech:done", "audio_queued": True, "audio_completed": True}),
])
def test_public_speech_metadata_is_bounded_and_queue_is_not_playback(plugin_instance, monkeypatch, run_async, public, expected):
    module, port, _, review, _ = prepare(plugin_instance, monkeypatch)
    client = httpx.AsyncClient

    async def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"paths": {"/api/game/{game_type}/speak": {"post": {}}}})
        return httpx.Response(200, json={"ok": True, "private_text": "not stored", **public})

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kw: client(transport=httpx.MockTransport(handler), **kw))

    async def scenario():
        result = await plugin_instance.minecraft_autonomy_review(review["id"], "continue", "Working", spoken_text="附近真安静。")
        assert result["speech"]["status"] == "enqueued"
        await asyncio.gather(*plugin_instance._speech_output_tasks)

    run_async(scenario())
    receipt = json.loads((port.directory / "speech-output.json").read_text(encoding="utf-8"))["records"][review["id"]]
    assert {key: receipt[key] for key in ("speech_id", "audio_queued", "audio_completed") if key in receipt} == expected
    assert receipt["playback_verified"] is False  # Endpoint report is not independent playback proof.
    assert "not stored" not in json.dumps(receipt) and "附近真安静" not in json.dumps(receipt, ensure_ascii=False)


def test_sdk_minimal_ordinary_final_and_control_only_cues(plugin_instance, monkeypatch, run_async):
    port, snapshot, _ = setup(plugin_instance, monkeypatch)
    port.observe(snapshot)
    rid = port.offer()["review"]["id"]
    inspected = run_async(plugin_instance.minecraft_autonomy_review(rid, "inspect"))
    assert "先提交最终判断" in inspected["speech_contract"]
    assert "未排入则用正常最终回复" in inspected["speech_contract"]
    assert "非完成条件" in inspected["context_request"]["instructions"]
    assert set(inspected["completion_contract"]["required"]) == {"heartbeat_id", "decision", "reason"}
    payload = {"heartbeat_id": rid, "decision": "insert", "reason": "口粮为空，先补充食物", "goal": "在附近寻找可采集的食物"}
    jsonschema.validate(payload, metadata(plugin_instance).parameters)
    result = run_async(plugin_instance.minecraft_autonomy_review(**payload))
    assert result["acknowledged"] and result["delivery"] == "queued" and not result["verified"]
    assert "speech" not in result and not getattr(plugin_instance, "_speech_output_tasks", None)
    assert "已排入语音，无需另写口播" in result["commentary"]["instruction"]
    assert "例：" not in metadata(plugin_instance).description
