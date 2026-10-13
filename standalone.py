"""Compatibility launcher; the standalone runtime belongs to minecraft-ai-friend."""
from agent_mc_autonomy.cli import main as framework_main

from backend.install import verify_runtime


def main(argv=None):
    return framework_main(argv, entry_resolver=verify_runtime)


if __name__ == "__main__":
    raise SystemExit(main())
