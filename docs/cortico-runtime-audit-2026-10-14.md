# Cortico runtime audit, 2026-10-14

The user identified `http://127.0.0.1:7788/#/world`. This is a real **Cortico / 可缇mini** console, not merely an old label in the Minecraft viewer. The initial process-name/command-line search missed it because Windows returns no executable path/command line for its protected Node processes. A missing command line must not be treated as absence of a service.

## Confirmed live instances

| Endpoint | Owner and evidence |
| --- | --- |
| 7788 | Node PID 18088, parent 8176. Started 2026-10-13 16:12:14 Beijing (parent 16:12:08). Browser identifies Cortico/可缇mini. Run diagnostics show paused, zero cumulative batches at inspection; only terminal World is active. Minecraft and mcvisual are inactive, zero tools. |
| 28985 | Node PID 40556, parent MCP 50552, framework Python 34884 / venv launcher 13276, PowerShell launcher 50892. Started 2026-10-14 18:15:55–58 for the independent Neko test. Actual command names `agent-mc-world/dist/runtime/core/engine-child.js`. |
| 25571 | Vanilla server Java PID 40552, unchanged since 15:19:02. Only Java process in the inspected local process list. |
| 18030 | Existing local model PID 43604, unchanged since 15:19:04. |
| 48911 / 48916 | Neko main 39124 / plugin service 48016, unchanged since 15:20. |

The two Node trees are separate. The configured Neko observer URL is 28985; its controller is `agent-mc-autonomy` 0.1.26, and its body is pinned `agent-mc-world` 0.4.0 at source `41fbc284cb0e7157c520f28c21110782870472a5`. Its installed `node_modules/cortico` is absent; `npm ls cortico --all --json` returns an empty dependency result (exit 1). The package directly depends on Mineflayer and MCP libraries, with neutral local host contracts. SDK-free packed consumer tests prohibit Cortico/Neko imports and pass.

No running Docker containers were reported; Ubuntu-24.04 is stopped. Neither result disproves the separate Windows Cortico instance at 7788.

## Remaining old names

Runtime decoupling does not mean every historical name has been removed. Canonical body source still contains `launcher_name: 'cortico'`, `Cortico-Resources` suggested paths, legacy realm/procedure identities, compatibility symbols/environment variables and an optional native chat filter name. The viewer has `corti-*` DOM IDs and legacy build-plugin names. Some are persistent compatibility identifiers; renaming them requires explicit migration and coordinated body/viewer verification, not removing arbitrary strings or saved data.

The separate 7788 instance's exact source/data directory could not be established from protected process metadata; it is not in this test's parent tree. The user was given a concrete choice to shut down only 7788 through its normal application shutdown action or retain it. No activation/resume, model probe, configuration rewrite or cross-project process kill was performed during the audit. The current Minecraft session and livestream remained running.

Filtered endpoint evidence is saved privately in `local/live-runtime/planner-recovery-20261014/cortico-service-audit.json`. This report contains no credentials or private conversation content.
