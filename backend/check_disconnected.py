"""Exercise the real Python-to-Node MCP bridge with networking denied."""

import argparse
import asyncio
import importlib.util
import json
import tempfile
from pathlib import Path


async def check(directory: Path, node: str) -> dict:
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("minecraft_check_bridge", root / "bridge.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="neko-minecraft-offline-") as temporary:
        data = Path(temporary)
        config = data / "client.json"
        config.write_text(json.dumps({"dataDir": str(data / "data"), "consolePort": 0, "metricsPort": 0,
                                      "world": {"host": "example.test", "username": "OfflineCheck", "viewerPort": 0}}), encoding="utf-8")
        bridge = module.MinecraftBridge(node, directory.resolve() / "node_modules/agent-mc-world/bin/minecraft-agent-mcp.mjs",
                                        config, data / "backend.log", node_args=("--import", (root / "backend/deny-network.mjs").as_uri()))
        try:
            await bridge.open()
            names = {tool["name"] for tool in bridge.tools}
            assert {"mc_connection", "mc_do", "mc_events", "mc_script", "mc_queue", "mc_visual"} <= names
            assert not any(name.startswith("mymc_") for name in names)
            status = module.json_content(await bridge.call("mc_connection", {"action": "status"}))
            assert status["phase"] == "disconnected" and status["facts"] is None
            environment = module.text_content(await bridge.resource("mc://environment"))
            assert "mc_help" in environment
            refused = await bridge.call("mc_bag", {})
            assert refused.get("isError") is True
            assert "disconnected" in module.text_content(refused)
            invalid = await bridge.call("mc_connection", {"action": "not-an-action"})
            assert invalid.get("isError") is True
            return {"ok": True, "protocol": "MCP stdio", "profile": status["profile"], "tools": len(names),
                    "phase": status["phase"], "game_connected": False, "network_denied": True,
                    "cortico_installed": (directory / "node_modules/cortico").exists()}
        finally:
            await bridge.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--node", default="node")
    arguments = parser.parse_args()
    print(json.dumps(asyncio.run(check(arguments.directory, arguments.node)), indent=2))
