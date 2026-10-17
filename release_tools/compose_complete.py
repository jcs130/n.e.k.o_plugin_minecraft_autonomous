"""Maintainer-only outer installer; the plugin itself uses the official SDK packer."""

import argparse
import html
import re
import zipfile
from pathlib import Path

from agent_mc_autonomy.runtime_bundle.build import compose_delivery


def compose(runtime: Path, plugin: Path, output: Path, instructions: Path) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.neko-plugin", plugin.name):
        raise ValueError("Use the official ASCII plugin artifact filename")
    result = compose_delivery(runtime, plugin, output, instructions)
    page = Path(__file__).with_name("start-here.html").read_text(encoding="utf-8")
    # This small wrapper only guides normal official import. It never writes
    # into a Neko installation, discovers credentials, or starts host/game/model.
    launcher = ('@echo off\r\nsetlocal\r\ncall "%~dp0prepare.cmd"\r\n'
        'if errorlevel 1 (\r\n  echo Preparation failed. Keep this window and check the error above.\r\n'
        '  if /i not "%~1"=="--no-open" pause\r\n  exit /b 1\r\n)\r\n'
        'if /i "%~1"=="--no-open" exit /b 0\r\n'
        'start "" "%~dp0start-here.html"\r\n'
        'echo Resources ready. Follow the opened guide to import the plugin in Neko.\r\nexit /b 0\r\n')
    with zipfile.ZipFile(result, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("一键安装.cmd", launcher.encode("ascii"))
        archive.writestr("install.cmd", launcher.encode("ascii"))
        archive.writestr("start-here.html", page.replace("@PLUGIN_FILE@", html.escape(plugin.name, quote=True)))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("runtime", "plugin", "output", "instructions"):
        parser.add_argument("--" + name, type=Path, required=True)
    print(compose(**vars(parser.parse_args())))
