import importlib

import httpx
import pytest


@pytest.mark.parametrize("status, payload, code", [
    (200, {"success": True, "settings": {"proactiveVisionEnabled": False}}, None),
    (200, {"success": True, "settings": {"proactiveVisionEnabled": True}}, "gameplay_screen_vision_enabled"),
    (200, {"success": True, "settings": {"proactiveVisionEnabled": 0}}, "gameplay_screen_privacy_unconfirmed"),
    (200, {"success": False, "settings": {"proactiveVisionEnabled": False}}, "gameplay_screen_privacy_unconfirmed"),
    (200, {"success": True, "settings": {}}, "gameplay_screen_privacy_unconfirmed"),
    (404, {}, "gameplay_screen_privacy_unconfirmed"),
])
def test_gameplay_admission_only_reads_the_local_privacy_switch(plugin_module, run_async, monkeypatch, status, payload, code):
    module = importlib.import_module(plugin_module.__name__ + ".neko_gameplay_context")
    requests = []

    def reply(request):
        requests.append((request.method, str(request.url)))
        return httpx.Response(status, json=payload)

    client = httpx.AsyncClient

    def local_client(**kwargs):
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
        return client(transport=httpx.MockTransport(reply), **kwargs)

    monkeypatch.setattr(module.httpx, "AsyncClient", local_client)
    raw = {"host_context": {"character_api_url": "http://127.0.0.1:51820/api/characters"}}
    result = run_async(module.gameplay_privacy_error(raw))
    assert (None if result is None else result.error["code"]) == code
    assert requests == [("GET", "http://127.0.0.1:51820/api/proactive/settings")]
