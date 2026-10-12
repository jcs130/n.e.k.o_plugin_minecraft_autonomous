# Minecraft Autonomous Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a standards-compliant independent repository for an autonomous
Minecraft plugin, with verified readiness reporting and no game backend yet.

**Architecture:** Generate the official external-source plugin layout. Replace the
Hello World entry with public-SDK readiness/start/stop entries that make the missing
backend explicit. Reuse the official Market workflow templates and verify locally
before creating and pushing the public repository.

**Tech Stack:** Python 3.11, N.E.K.O SDK 0.1.0, pytest, Ruff 0.12.4, GitHub Actions.

**Spec:** `docs/design.md`.

## Global Constraints

- Plugin ID: `minecraft_autonomous`; entry class: `MinecraftAutonomousPlugin`.
- Public GitHub repository: `jcs130/n.e.k.o_plugin_minecraft_autonomous`.
- Python 3.11; use the public `plugin.sdk.plugin` facade.
- Keep the official Verify/Release workflow templates intact.
- Default `plugin_runtime.auto_start = false` and `autonomy.enabled = false`.
- Existing N.E.K.O services stay stopped. Do not publish a release or Market entry.

## Review Focus

- Plugin startup must not connect or start autonomous play: test startup and status.
- A start request must not claim gameplay when no backend exists: test explicit Err.
- Repeated stop/shutdown must remain safe: test idempotence and shutdown.
- Package identity, folder, class, and version must agree: manifest/smoke tests.
- Configuration and artifacts must be portable: default-config tests and inspect ZIP
  for private paths, runtime data, secrets, and excluded development directories.

---

### Task 1: Official repository layout and product definition

**Files:** `plugin.toml`, `config.example.toml`, `pyproject.toml`, `README.md`,
`CONTRIBUTING.md`, `LICENSE`, `NOTICE`, `AGENTS.md`, `.gitignore`, `.vscode/*`,
`.github/workflows/*`, `docs/design.md`.

- [x] Generate the repository using the official CLI, with an external output path:

  ```sh
  python -m plugin.neko_plugin_cli.cli init minecraft_autonomous --type plugin \
    --output /path/to/minecraft_autonomous \
    --remote https://github.com/jcs130/n.e.k.o_plugin_minecraft_autonomous.git
  ```

- [x] Set truthful scaffold metadata and disabled autonomy configuration. Add product
  scope, contributor commands, Apache-2.0 license and template attribution. Replace
  machine-specific editor paths with `${env:NEKO_ROOT}`. Exclude tests and development
  documents from the package while retaining README, license, and runtime code.

### Task 2: Readiness entries and offline public-SDK tests

**Files:** `__init__.py`, `tests/conftest.py`, `tests/test_smoke.py`,
`tests/test_plugin.py`.

**Interfaces:** SDK startup/shutdown lifecycle; `status()`, `start(goal: str)`,
`stop()` asynchronous entries returning public `Ok`/`Err` values.

- [x] Write tests with real SDK imports and a temporary host context, with network
  connections forbidden. Assert startup/status report `backend_ready = false`,
  start returns `backend_not_integrated`, and repeated stop/shutdown stay stopped.

  ```python
  result = asyncio.run(instance.start(goal="survive"))
  assert isinstance(result, Err)
  assert result.error["code"] == "backend_not_integrated"
  ```

- [x] Run the tests against the generated Hello World module and confirm missing
  autonomous entries fail. Implement only honest scaffold entries and rerun tests.

  ```sh
  python -m pytest tests -q
  uvx ruff==0.12.4 check --ignore-noqa --config ruff.toml .
  ```

### Task 3: Verify, commit, and create the remote

**Files:** all reviewed new repository files; ignored `dist/` verification artifacts.

- [x] Run the official release and Market-structure checks without a release tag:

  ```sh
  python -m plugin.neko_plugin_cli.cli check --release --market-release \
    /path/to/minecraft_autonomous
  ```

- [ ] Inspect the generated ZIP, staged diff and secret/path scan. Commit the initial
  source using a public noreply author email. Create the public repository with no
  auto-generated README/license, then push `main` without pushing any tags.
- [ ] Verify the remote commit, repository metadata, and exact-commit Verify workflow
  result; inspect any failures and fix them within this repository. Leave Market
  submission and live-game acceptance for the functional increment.
