"""One autonomous runtime shared by standalone and desktop frontends."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .bridge import MinecraftBridge
from .configuration import Settings
from .controller import Controller
from .mailbox import Mailbox
from .ownership import session_lease
from .planner import Planner


def validate_start(settings: Settings, goal: str):
    if not settings.enabled:
        raise ValueError("autonomy_disabled")
    settings.require_server()
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 4000:
        raise ValueError("invalid_goal")


async def run_session(settings: Settings, entry: Path, data_root: Path, planner: Planner | None, goal: str,
                      publish, stopped, *, bridge_factory=MinecraftBridge):
    """Own the injected planner, lease, config, controller and all cleanup."""
    state = {"phase": "starting", "game_connected": False, "autonomy_running": False, "standing_goal": goal}
    directory = data_root / "sessions" / settings.identity / "host"

    def update(**values):
        state.update(values)
        state.update(updated_at=datetime.now(timezone.utc).isoformat(), owner_pid=os.getpid())
        temporary = directory / "status.tmp"
        temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        temporary.replace(directory / "status.json")
        publish(**state)

    try:
        validate_start(settings, goal)
        if stopped():
            return
        with session_lease(directory):
            commands = Mailbox(directory)
            commands.check_uncertain()
            config = directory / "client.json"
            config.write_text(json.dumps(settings.client_config(data_root), ensure_ascii=False), encoding="utf-8")
            update()
            bridge = bridge_factory(settings.node, entry, config, directory / "backend.log")
            try:
                await Controller(bridge, planner.decide if planner else None, settings, directory, update, stopped, commands).run(goal.strip())
            except asyncio.CancelledError:
                commands.stop_queued()
                update(phase="stopped")
                raise
            except Exception as error:
                update(phase="failed", error=type(error).__name__)
                raise
            finally:
                update(game_connected=False, autonomy_running=False)
    finally:
        if planner:
            await planner.aclose()
