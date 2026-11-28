"""Read the official Java client's most recent local world publication."""

import asyncio
import os
import re
import stat
from pathlib import Path

_LOG_TAIL_LIMIT = 128 * 1024
_START = re.compile(r"^\[[^\]]+\] \[Server thread/INFO\]: Starting integrated minecraft server version (\S+)$")
_PUBLISH = re.compile(r"^\[[^\]]+\] \[(?:Render|Server) thread/INFO\]: Started serving on (\d{1,5})$")
_STOP = re.compile(r"^\[[^\]]+\] \[Server thread/INFO\]: Stopping (?:the )?server(?:[.!])?$")


def published_world(log: Path) -> tuple[int, str] | None:
    if not stat.S_ISREG(log.stat().st_mode):
        return None
    with log.open("rb") as stream:
        size = stream.seek(0, os.SEEK_END)
        stream.seek(max(0, size - _LOG_TAIL_LIMIT))
        tail = stream.read(_LOG_TAIL_LIMIT)
    if size > _LOG_TAIL_LIMIT:
        tail = tail.partition(b"\n")[2]
    # A writer may still be appending the last line.
    if not tail.endswith(b"\n"):
        tail = tail.rpartition(b"\n")[0]
    version, port = "", 0
    for line in tail.decode("utf-8", errors="replace").splitlines():
        if start := _START.fullmatch(line):
            version, port = start[1], 0
        elif _STOP.fullmatch(line):
            version, port = "", 0
        elif published := _PUBLISH.fullmatch(line):
            port = int(published[1])
    return (port, version) if 1 <= port <= 65535 else None


async def detect_local_world() -> dict:
    home = Path(os.environ.get("APPDATA") or Path.home())
    log = home / ".minecraft" / "logs" / "latest.log"
    try:
        world = await asyncio.to_thread(published_world, log)
    except OSError:
        world = None
    if world is None:
        return {"found": False, "reason": "no_lan_world_in_default_log"}
    port, version = world
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", port), timeout=1.0)
    except (OSError, TimeoutError):
        return {"found": False, "reason": "lan_port_closed"}
    writer.close()
    return {"found": True, "host": "127.0.0.1", "port": port, "version": version}
