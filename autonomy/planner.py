"""Low-level planning inference; high-level intent arrives through the mailbox."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit


class Planner(Protocol):
    async def decide(self, messages: list[dict], tools: list[dict]) -> dict: ...

    async def aclose(self) -> None: ...


def decision(message: dict) -> dict:
    """Reject malformed provider output before the controller can dispatch it."""
    if not isinstance(message, dict) or not isinstance(message.get("content"), (str, type(None))):
        raise ValueError("brain_response_invalid")
    calls = message.get("tool_calls") or []
    if not isinstance(calls, list) or len(calls) > 1:
        raise ValueError("brain_response_invalid")
    for call in calls:
        if not isinstance(call, dict):
            raise ValueError("brain_response_invalid")
        function = call.get("function")
        if (call.get("type") != "function" or not isinstance(call.get("id"), str) or not call["id"]
                or not isinstance(function, dict) or not isinstance(function.get("name"), str)
                or not function["name"] or not isinstance(function.get("arguments"), str)):
            raise ValueError("brain_response_invalid")
    return {"content": message.get("content"), "tool_calls": calls}


@dataclass(frozen=True)
class HttpPlannerConfig:
    base_url: str
    model: str
    api_key_env: str = ""
    output_parameter: str = "max_tokens"

    @classmethod
    def parse(cls, raw: dict) -> HttpPlannerConfig:
        if (not isinstance(raw, dict) or not {"base_url", "model"} <= raw.keys()
                or set(raw) - {"base_url", "model", "api_key_env", "output_parameter"}):
            raise ValueError("brain_config_invalid")
        result = cls(**raw)
        if not all(isinstance(value, str) and value == value.strip() and not any(ord(c) < 32 for c in value)
                   for value in (result.base_url, result.model, result.api_key_env, result.output_parameter)):
            raise ValueError("brain_config_invalid")
        url = urlsplit(result.base_url)
        if (url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password
                or url.query or url.fragment or any(c.isspace() for c in result.base_url) or not result.model):
            raise ValueError("brain_endpoint_and_model_required")
        url.port  # Validate without resolving or connecting.
        if result.api_key_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", result.api_key_env):
            raise ValueError("brain_key_environment_invalid")
        if result.output_parameter not in {"max_tokens", "max_completion_tokens"}:
            raise ValueError("brain_output_parameter_invalid")
        return result

    def key(self) -> str:
        key = os.environ.get(self.api_key_env, "") if self.api_key_env else ""
        if self.api_key_env and (not key or any(ord(c) < 32 for c in key)):
            raise ValueError("brain_key_environment_missing_or_invalid")
        return key


class HttpPlanner:
    """Explicit OpenAI-compatible endpoint, without retries, discovery or fallback."""

    def __init__(self, config: HttpPlannerConfig, max_output_tokens: int, timeout: int, *, client=None):
        import httpx

        self.config, self.max_output_tokens = config, max_output_tokens
        key = config.key()
        self.headers = {"Authorization": "Bearer " + key} if key else {}
        self.client = client or httpx.AsyncClient(timeout=timeout, follow_redirects=False, trust_env=False)

    async def decide(self, messages: list[dict], tools: list[dict]) -> dict:
        import httpx

        try:
            response = await self.client.post(self.config.base_url.rstrip("/") + "/chat/completions",
                headers=self.headers, json={"model": self.config.model, "messages": messages, "tools": tools,
                    "parallel_tool_calls": False, "stream": False, self.config.output_parameter: self.max_output_tokens})
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise RuntimeError(f"brain_http_error_{error.response.status_code}") from None
        except httpx.HTTPError:
            raise RuntimeError("brain_transport_error") from None
        try:
            choice = response.json()["choices"][0]
            if not isinstance(choice, dict) or choice.get("finish_reason") not in {"stop", "tool_calls"}:
                raise ValueError("brain_response_incomplete")
            return decision(choice["message"])
        except (ValueError, TypeError, KeyError, IndexError):
            raise ValueError("brain_response_invalid_or_incomplete") from None

    async def aclose(self) -> None:
        await self.client.aclose()
