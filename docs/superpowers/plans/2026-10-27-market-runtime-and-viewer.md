# Market runtime preparation and viewer synchronization

> Execution: implement directly in this session under the user's existing authorization. Installation, configuration, start/stop and visualization acceptance use Computer Use with real screenshots.

**Goal:** Let a Windows Market user prepare the complete pinned game runtime from the plugin page, and ship the current shared renderer fixes without changing Neko or its SDK.

**Architecture:** Keep the official Market artifact and source/update transactions. The host-neutral framework owns a bounded, hash-pinned runtime ZIP downloader and extraction/preparation; the plugin owns the explicit UI action, progress and active-worker/configuration guards. Publish runtime-only resources separately so their checksum can be fixed before the official plugin is built. Reuse the existing runtime manifest, short cache and full validation.

**Tech stack:** Python 3.11/httpx, existing bundled Node 22.22.1 preparer, SDK hosted TSX, shared Minecraft 1.21.1 WebGL renderer.

**Spec:** Current human request: finish Market adaptation first; synchronize MC core and visualization fixes. Preserve the previous requirements for normal user operation, screenshots, explicit start/stop and the Neko builtin free model.

## Constraints and reviewed inputs

- Neko, SDK, official managed workflows and shared host dependencies stay unchanged.
- Market package remains the same Linux/Windows official artifact; platform-specific resources are verified and plugin-owned.
- No arbitrary download URLs, credentials, fallback model, additional body or relaxed integrity/permission/unknown-execution gates.
- A runtime preparation action never starts a game or calls a model. Custom/external runtimes are not silently replaced. Active/uncertain native work blocks runtime replacement.
- Fetch before editing/pushing and preserve unrelated commits, original worlds/data and `test_localsystem.txt`.
- Core checked at `5f8f5166ff9ac2ee65f96088af204f551e50b286` / rc.107; no new core execution changes at fetched upstream `f8a5126f`.
- Renderer update checked at `b99464bb7efce76dedb00471605019932b1e8d7e` (12 commits since the previously consumed renderer).

## Review focus

1. Clean Market install without prepared runtime: show one clear preparation action and bounded progress; no command-line or private path entry.
2. Interrupted/corrupt downloads, unexpected redirects, archive traversal/symlinks/collisions and expanded size: fail safely, keep the old ready runtime and allow an explicit retry.
3. Upgrade from a managed old runtime: retain server/account/model/personality/data and select only the fully verified new bundle; active or unknown work is never replaced.
4. Imported-to-Market takeover and subsequent update: use actual App confirmations/source records, never edit installation metadata to fake Market origin.
5. Renderer source, worker and generated assets: pin/build together, serve matching files and inspect actual WebGL; offline tests alone do not establish gameplay or full visual parity.

## Tasks

### 1. Neutral runtime download/preparation

Files: framework `runtime_bundle/download.py`, runtime-bundle tests; existing manifest/preparer are reused.

- [ ] Add fake-transport tests for a valid pinned download, wrong size/hash, timeout, redirect allowlist, malformed ZIP members, symlinks/case collisions and limits. Assert no preparer executes before complete verification.
- [ ] Implement streaming progress, staged atomic files and explicit retry; extract only validated regular members through Windows verification paths.
- [ ] Invoke only the verified bundled Node preparer, with a finite preparation timeout and bounded output. Verify resulting registration/bundle and return a `PreparedBundle`; no game/model/host startup.
- [ ] Run scoped regressions and framework source/installed-wheel checks, update the framework version/changelog and commit normally.

### 2. Pin and rebuild the shared viewer

Files: framework `core_distribution/source.json`, `viewer-source.json`, runtime source inventory; renderer builder inputs.

- [ ] Materialize a clean renderer source tree from the checked commit, preserving original versioned assets and licenses.
- [ ] Run the changed renderer suites and full shared suite; build matched 1.21.1 browser/worker assets and record source/build hashes.
- [ ] Refresh only the external renderer pin/inventory, keeping the verified rc.107 core archive and unrelated dependency versions.
- [ ] Build and fully verify a runtime-only ZIP, then pin its size/SHA256/manifest/explicit release URL before building the plugin.

### 3. Explicit plugin preparation flow

Files: plugin runtime preparation mixin/module, `__init__.py`, `dashboard.py`, `ui/panel.tsx`, `ui/installation-guidance.js`, associated tests and public release-resource metadata.

- [ ] Test the inactive/managed-runtime guard, duplicate action handling, visible progress/status, custom/external refusal, failure retry and unchanged account/model settings.
- [ ] Add `prepare_runtime` and state polling through the public SDK action/state APIs. First install shows a preparation button; compatible prepared installs need no extra configuration.
- [ ] After success select only the managed verified resource fields, retaining all other configuration; begin play only after a separate explicit start.
- [ ] Update Chinese instructions and version consistently; run plugin Python/Node/Ruff/official release structure checks and commit.

### 4. Official package and actual Market acceptance

- [ ] Build through the unchanged official Verify/Release workflow; inspect the same artifact on Windows cold and preloaded imports, Linux CI and package limits.
- [ ] Publish the runtime resource ZIP and complete offline ZIP beside the sole official `.neko-plugin`, with matching checksum records; verify the public resource URL before Market notification.
- [ ] In the real App stop the test body normally; perform supported Market takeover/install and subsequent update, confirming original config/data/model binding and source records remain correct.
- [ ] Use the plugin's preparation button from a clean resource state, record progress and final success screenshots, then start the original QA account with builtin free API and inspect fresh native events and 3D page.
- [ ] Record source/package/publication/live boundaries separately. Update the existing observation automation with current authority and remaining limitations; do not advance the old identity's full checkpoint with this maintenance.
