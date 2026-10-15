import tomllib
from pathlib import Path

from plugin.neko_plugin_cli.core.build_rules import load_build_rules, should_skip_path


def test_public_ca_only_pem_exception():
    root = Path(__file__).resolve().parents[1]
    rules = load_build_rules(tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8")))
    for name in ("credentials.pem", "CREDENTIALS.PEM", "nested/Custom.PeM", "nested/custom.pem", "vendor/unexpected.pem", "vendor/certifi/private.pem", ".superpowers/a.txt", "local/a.txt", ".env.private", "credentials.key"):
        assert should_skip_path(Path(name), is_dir=False, rules=rules), name
    for name in ("vendor/certifi/cacert.pem", "dashboard.py", "ui/panel.tsx", "vendor/certifi/core.py", "LICENSE", "assets/a.png"):
        assert not should_skip_path(Path(name), is_dir=False, rules=rules), name
