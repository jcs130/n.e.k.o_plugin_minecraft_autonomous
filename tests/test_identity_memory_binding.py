import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from agent_mc_autonomy.host_context import HostContextPort
from agent_mc_autonomy.ownership import session_lease
from test_character_binding import setup


def adapter(plugin):
    return importlib.import_module(plugin.__class__.__module__ + ".neko_host_context")


@pytest.mark.parametrize("url", ["https://example.org", "http://u:p@localhost:48932", "http://localhost/x", "http://localhost?key=x"])
def test_memory_endpoint_requires_explicit_loopback_origin(plugin_instance, url):
    with pytest.raises(ValueError):
        adapter(plugin_instance).HostContextSettings.parse({"host_context": {"memory_api_url": url}})


def test_identity_selection_uses_original_ids_and_no_chat_or_other_actor(plugin_instance, monkeypatch, run_async):
    module = adapter(plugin_instance)
    raw = {subject: {"facts": [{"id": subject + str(i), "text": subject + " fact " + str(i), "embedding": [999]}
                             for i in range(10)]} for subject in ("master", "relationship", "neko")}
    raw["neko"]["facts"].insert(0, {"id": "suppressed", "text": "private suppressed", "suppress": True})
    raw["__meta__"] = {"facts": [{"id": "internal", "text": "private internal"}]}
    response = SimpleNamespace(raise_for_status=Mock(), json=lambda: raw)
    client = SimpleNamespace(get=AsyncMock(return_value=response))
    manager = AsyncMock()
    manager.__aenter__.return_value = client
    monkeypatch.setattr(module.httpx, "AsyncClient", Mock(return_value=manager))
    config = module.HostContextSettings(memory_api_url="http://127.0.0.1:48932")
    rows = run_async(module.character_memories(config, "Test Role"))
    assert len(rows) == 6
    assert {row["source"].split(":")[-1] for row in rows} == {"master", "neko", "relationship"}
    assert all(set(row) == {"id", "source", "text"} for row in rows)
    assert not any(row["id"] in {"internal", "suppressed"} for row in rows)
    client.get.assert_awaited_once_with("http://127.0.0.1:48932/get_persona/Test%20Role")


def test_long_character_names_keep_sources_within_core_limits(plugin_instance):
    source = adapter(plugin_instance).identity_memory_source("猫" * 50)
    assert len((source + "relationship").encode()) <= 160


def test_explicit_identity_query_can_find_a_later_relevant_fact_without_loading_the_store(plugin_instance, monkeypatch, run_async):
    module = adapter(plugin_instance)
    rows = [{"id": f"n{index}", "text": "first-person 自称本喵" if index == 5 else f"unrelated fact {index}"} for index in range(12)]
    raw = {"master": {"facts": [{"id": "owner", "text": "owner fact"}]},
           "neko": {"facts": rows}, "relationship": {"facts": []}}
    response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: raw)
    client = SimpleNamespace(get=AsyncMock(return_value=response))
    manager = AsyncMock()
    manager.__aenter__.return_value = client
    monkeypatch.setattr(module.httpx, "AsyncClient", Mock(return_value=manager))
    config = module.HostContextSettings(memory_api_url="http://127.0.0.1:48932")
    selected = run_async(module.character_memories(config, "YUI", query="自称 本喵"))
    assert [row["id"] for row in selected] == ["n5"]
    assert selected[0]["text"] == rows[5]["text"]
    assert selected[0]["source"] == "neko-persona:YUI:neko"
    assert len(selected) <= 6 and sum(len(row["text"].encode()) for row in selected) <= 4000
    assert run_async(module.character_memories(config, "YUI", query="no-match")) == []


def test_identity_query_budget_keeps_original_facts_and_invalid_queries_do_not_read(plugin_instance, monkeypatch, run_async):
    module = adapter(plugin_instance)
    raw = {"master": {"facts": []}, "relationship": {"facts": []},
           "neko": {"facts": [{"id": str(i), "text": "identity " + "x" * 1500} for i in range(8)]}}
    response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: raw)
    client = SimpleNamespace(get=AsyncMock(return_value=response))
    manager = AsyncMock()
    manager.__aenter__.return_value = client
    monkeypatch.setattr(module.httpx, "AsyncClient", Mock(return_value=manager))
    config = module.HostContextSettings(memory_api_url="http://127.0.0.1:48932")
    selected = run_async(module.character_memories(config, "YUI", query="identity"))
    assert len(selected) == 2
    assert all(row["text"] == raw["neko"]["facts"][int(row["id"])]["text"] for row in selected)
    with pytest.raises(ValueError, match="invalid_identity_memory_query"):
        run_async(module.character_memories(config, "YUI", query="x" * 241))
    assert client.get.await_count == 1


def test_timer_never_reads_personal_memories_but_explicit_service_can(plugin_instance, monkeypatch, run_async):
    module, raw, _, directory, _ = setup(plugin_instance, monkeypatch)
    raw["host_context"]["memory_api_url"] = "http://127.0.0.1:48932"
    memories = [{"id": "original-id", "source": "neko-persona:YUI:neko", "text": "an existing identity fact"}]
    recall = AsyncMock(return_value=memories)
    monkeypatch.setattr(module, "character_memories", recall)
    with session_lease(directory):
        run_async(plugin_instance.refresh_character_context())
        recall.assert_not_awaited()
        assert HostContextPort(directory).read(0)["dynamic"]["memories_selected"] is False
        result = run_async(plugin_instance.load_character_identity_memory()).value
        assert result["identity_memories"]["published"]
        stored = HostContextPort(directory).read(0)
        assert stored["dynamic"]["memories"] == memories
        original = (directory / "host-context.json").read_bytes()
        run_async(plugin_instance.sync_character_context())
        assert (directory / "host-context.json").read_bytes() == original
        assert recall.await_count == 1


def test_on_demand_identity_does_not_replace_main_brain_selected_context(plugin_instance, monkeypatch, run_async):
    module, raw, _, directory, _ = setup(plugin_instance, monkeypatch)
    raw["host_context"]["memory_api_url"] = "http://127.0.0.1:48932"
    monkeypatch.setattr(module, "character_memories", AsyncMock(return_value=[
        {"id": "identity", "source": "neko-persona:YUI:neko", "text": "identity fact"}]))
    port = HostContextPort(directory)
    port.publish({"agent_name": "YUI", "persona": "explicit host persona", "current_intent": "current user focus",
                  "memories": [{"id": "chosen", "source": "recall_memory", "text": "explicit selected history"}]},
                 session="123:", revision=0)
    original = port.path.read_bytes()
    with session_lease(directory):
        result = run_async(plugin_instance.load_character_identity_memory()).value
    assert result["identity_memories"]["reason"] == "preserve_explicit_host_projection"
    assert port.path.read_bytes() == original
