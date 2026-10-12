"""One task owns the official MCP session and its independent Node child."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path


class MinecraftBridge:
    def __init__(self, node: str, entry: Path, config: Path, log: Path, *, node_args: tuple[str, ...] = ()):
        self.node, self.entry, self.config, self.log = node, entry, config, log
        self.node_args = node_args
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=16)
        self._owner: asyncio.Task | None = None
        self._ready: asyncio.Future | None = None
        self._error: Exception | None = None
        self.tools: list[dict] = []

    async def open(self) -> None:
        if self._owner:
            raise RuntimeError("The Minecraft transport already has an owner")
        self._ready = asyncio.get_running_loop().create_future()
        self._owner = asyncio.create_task(self._serve(), name="minecraft-autonomous-mcp")
        try:
            await asyncio.wait_for(asyncio.shield(self._ready), 45)
        except BaseException:
            await self.close()
            raise

    async def _serve(self) -> None:
        # MCP's AnyIO cancel scopes must be entered/exited by the same task.
        current = None
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            self.log.parent.mkdir(parents=True, exist_ok=True)
            with self.log.open("a", encoding="utf-8") as errors:
                parameters = StdioServerParameters(command=self.node, args=[*self.node_args, str(self.entry), str(self.config)])
                async with stdio_client(parameters, errlog=errors) as (read, write), ClientSession(read, write) as session:
                    await session.initialize()
                    self.tools = [tool.model_dump(mode="json", exclude_none=True, by_alias=True) for tool in (await session.list_tools()).tools]
                    self._ready.set_result(None)
                    while True:
                        current = await self._queue.get()
                        if current is None:
                            break
                        operation, arguments, future = current
                        if future.cancelled():
                            continue
                        try:
                            if operation == "tool":
                                response = await session.call_tool(arguments[0], arguments[1])
                            else:
                                response = await session.read_resource(arguments[0])
                            if not future.done():
                                future.set_result(response.model_dump(mode="json", exclude_none=True, by_alias=True))
                        except Exception as error:
                            if not future.done():
                                future.set_exception(error)
                        current = None
        except BaseException as error:
            self._error = RuntimeError(f"Minecraft transport closed ({type(error).__name__}); inspect private backend log")
            if self._ready and not self._ready.done():
                self._ready.set_exception(self._error)
        finally:
            error = self._error or RuntimeError("Minecraft transport is stopped")
            if current and not current[2].done():
                current[2].set_exception(error)
            while not self._queue.empty():
                item = self._queue.get_nowait()
                if item and not item[2].done():
                    item[2].set_exception(error)

    async def _request(self, operation: str, *arguments, timeout: float = 45) -> dict:
        if not self._owner or self._owner.done():
            raise self._error or RuntimeError("Minecraft transport is not running")
        future = asyncio.get_running_loop().create_future()
        self._queue.put_nowait((operation, arguments, future))
        try:
            return await asyncio.wait_for(future, timeout)
        except TimeoutError as error:
            # Submission may already have reached the server. Never retry an action.
            raise RuntimeError("Minecraft request timed out; delivery is uncertain. Stop and inspect receipts before retrying.") from error

    async def call(self, name: str, arguments: dict, *, timeout: float = 45) -> dict:
        if name not in {tool["name"] for tool in self.tools}:
            raise ValueError("Unknown Minecraft tool; discover the actual tool catalogue first")
        return await self._request("tool", name, arguments, timeout=timeout)

    async def resource(self, uri: str) -> dict:
        return await self._request("resource", uri)

    async def close(self) -> None:
        owner, self._owner = self._owner, None
        if not owner:
            return
        try:
            if not owner.done():
                try:
                    self._queue.put_nowait(None)
                except asyncio.QueueFull:
                    owner.cancel()
                await asyncio.wait({owner}, timeout=5)
        finally:
            if not owner.done():
                owner.cancel()
            await asyncio.gather(owner, return_exceptions=True)


def text_content(result: dict) -> str:
    return "\n".join(part.get("text", "") for part in result.get("content", result.get("contents", [])) if "text" in part)


def json_content(result: dict) -> dict:
    if result.get("isError"):
        raise RuntimeError(text_content(result))
    value = json.loads(text_content(result))
    if not isinstance(value, dict):
        raise ValueError("Expected a structured Minecraft receipt")
    return value
