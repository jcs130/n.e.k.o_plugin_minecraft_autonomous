import tomllib
from pathlib import Path


def test_plugin_manifest_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = root / "plugin.toml"
    assert manifest.is_file()
    metadata = tomllib.loads(manifest.read_text(encoding="utf-8"))["plugin"]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert metadata["id"] == root.name == project["name"] == "minecraft_autonomous"
    assert metadata["entry"] == "plugin.plugins.minecraft_autonomous:MinecraftAutonomousPlugin"
    assert metadata["version"] == project["version"]
    assert project["version"] == "0.6.116"
    assert project["dependencies"][0] == (
        "agent-mc-autonomy @ git+https://github.com/jcs130/minecraft-ai-friend.git@"
        "bc063992c59596c7d0e1e15a5ae718d1f33c2e56#subdirectory=packages/agent-mc-autonomy"
    )


def test_default_configuration_never_starts_autonomy() -> None:
    root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((root / "config.example.toml").read_text(encoding="utf-8"))
    assert config["plugin_runtime"]["auto_start"] is False
    assert config["autonomy"]["enabled"] is False
    assert config["autonomy"]["max_decisions"] == 0
