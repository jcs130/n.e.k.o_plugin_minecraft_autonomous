# Death terminal receipts: source and deployment

Native task #16 was accepted during combat at 18:24:15 Beijing, then the player died. The body respawned with an empty queue, but the controller still waited on the accepted ID at 18:41 because death clearing emitted no terminal task report. This was a core executor bug, separate from the old Cortico console at port 7788.

The canonical core now emits one truthful cancellation per accepted current/frozen/queued task, retaining its ID and step outcomes. Late old-body completions remain fenced, and cancelled work is not replayed or called completed. The adapter contains no replacement queue or death-text heuristic.

- Native fix: `minecraft-ai-friend@2820afdb3d5ea0f5c995789ded24c7c27174a887`.
- Framework 0.1.27 pin: `minecraft-ai-friend@4806f7e009002aa04776a8d5ca1905554b406c88`.
- Actual engine-only archive SHA256: `59638493deb8a111a14836a3702829f89254c83e44d80febf90e15e2eb5f46da`.
- Plugin 0.5.12, normal development reload and explicit runtime restart at 19:10:54 Beijing. Server/model/Neko main/plugin-service PIDs remained 40552/43604/39124/48016.
- Official package check passed; 3,366 files, private runtime/backups excluded, exact framework/body pins confirmed. Package SHA256: `66d12fb29782073881a2111ffb7c1e784d24229ed6ee433b064e2b58ea95b892`. No tag, Release or Market publication.

Before deployment, original JSON state and read-only SQLite backups were preserved. The public stop request completed a normal disconnect: stopped true, no pending/inflight task, uncertainty false. No ledger/database record was manually deleted and the old task was not replayed. Only the explicit backend path changed in private runtime configuration; world, account, model and external renderer stayed the same. Observer delivery resumed through its public entry after the new connected session was observed.

Verification: native regression 5 passed; complete engine suite 690 passed with one optional packaged-viewer test skipped; independent clean build and actual packed consumer passed, including strict NodeNext/Bundler declarations and denied network/host imports. Framework 363 tests and isolated wheel consumer passed; adapter 53 Python and 4 Node tests, Ruff and official release/Market structure checks passed.

Initial live observations after deployment show new decisions, native task execution and collected oak logs in the actual browser stream. A natural eight-minute window is being recorded separately. This does not yet prove death-branch recovery in live play, successful food supply, continuous survival or all viewer HUD fields. No live death is intentionally triggered. Private runtime evidence is under `local/live-runtime/death-terminal-20261014/` and is excluded from source and the plugin package.

For the separately approved shutdown of the old Cortico instance and its five-minute Windows task, see [Cortico runtime audit](cortico-runtime-audit-2026-10-14.md).
