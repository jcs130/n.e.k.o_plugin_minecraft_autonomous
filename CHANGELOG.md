# Changelog

## 0.5.19 — Unreleased

- Consume autonomy 0.1.35: expose bounded public native queue and actual action/terminal history to the configured shared viewer. Full arguments, private planner context and raw errors remain local.
- Keep inventory, crafting, trading, survival, terrain and operation rendering in mc-visual-console; the plugin remains a thin host adapter. The independently pinned native 0.4.0 body is unchanged.

## 0.5.18 — Unreleased

- Consume autonomy 0.1.34: inject bounded public goal, tool/skill and real receipt state into the explicitly configured native viewer. Private planner context and configuration stay out of the viewer projection.
- Use the shared viewer's same-body path/trail/input and observed hand-motion integration. Rendering remains in `mc-visual-console`; no duplicate renderer or body queue is added to the plugin.
- Pass the shared Mineflayer window projection for original inventory/crafting layouts, actual cursor stacks, slot-click playback and received furnace progress.
- Preserve the separately verified native backend pin and service ownership; unrelated concurrent native-core source updates are not silently deployed.

## 0.5.17 — Unreleased

- Consume autonomy 0.1.32: a newly queued observation ends the planning turn even while feedback awaits its first body plan. Wait for the actual native result before deciding again, without consuming feedback queue policy or interrupting unrelated native work.

## 0.5.16 — Unreleased

- Consume autonomy 0.1.31: keep a rejected body plan across intervening failed observations, cached retries and corrected reads. A read error cannot overwrite the action error that still needs correction.
- Allow explicit `tool_choice=required` for compatible Chat/Responses planners, so supported providers can prevent text-only plans without forcing a particular Minecraft action. Defaults remain unchanged.
- Preserve concurrent upstream source while keeping the separately verified Mineflayer core pin. The optional new Java client body is not enabled by this deployment.

## 0.5.15 — Unreleased

- Consume autonomy 0.1.29: queued observations retain rejected body-plan evidence, including after history eviction, and rejected batches explain that earlier steps did not run.
- Clarify the Neko transport: autonomous heartbeat strategy uses the existing review/inspect/revise port; the separate intent tool relays new user goals and must not replay stale stages or entity IDs. This wording does not guarantee model compliance.
- Pin the checked independent core with distinct live-chicken search receipts, preserving food item labels and native retry guards.

## 0.5.14 — Unreleased

- Put the current speaking policy and 30-character highlight limit directly at the front of the small notification preview. Tool-result-only instructions were insufficient when the main brain spoke without inspecting; same-review retries explicitly request tool confirmation without repeating narration.

## 0.5.13 — Unreleased

- Consume autonomy 0.1.28 for fresh commentary signals, preserving full facts for strategic decisions while ignoring inventory counts, durability and read-only task churn.
- Share ordinary commentary timing with strategic heartbeats; allow a new critical-health/death warning without repeating the same warning. Ask for one natural highlight in 1–2 short sentences instead of inventory/inspection readouts.
- Keep official host voice and normal user conversation. Speaking opportunities, strategic acknowledgement, native completion and actual playback remain separate; the public SDK does not enforce silent tool-only output.

## 0.5.8 — Unreleased

- Consume autonomy 0.1.22, preserving complete native action/scout parameter structure while omitting repeated manuals and retaining coordinate/angle units.
- Preserve existing model, game, queue and explicit stop policies. Schema/context verification remains separate from real survival acceptance.

## 0.5.7 — Unreleased

- Consume autonomy 0.1.21 for explicit goal provenance, paged original parent goals and complete rejected-call history.
- Mark manual panel goals as user-sourced while preserving legacy UUID retries and unknown model-intent provenance. Show a bounded current-user-goal cue and expose framework lineage inspection through the existing review tool.
- Document the installed Neko SDK's separate review-history limitation and a forwardable upstream capability request; do not impersonate the legacy plugin or modify host SDK internals.

## 0.5.6 — Unreleased

- Consume shared autonomy 0.1.20, preserving native scalar parameter constraints in compact model tools while keeping full manuals progressive.
- Add an explicit control-panel action to resume Neko participation after an external runtime restart. Require its account lease and fresh connected evidence; preserve stop on stale state, configuration changes or concurrent stop.
- Show the separate host stop flag. Resume does not start a game, dispatch a task, reset review history or invoke a model; the existing framework review transport continues normally afterward.
- Offline checks and deployment do not establish sustained survival, food acquisition or voice playback. No Release or Market publication.

## 0.5.2 — Unreleased

- Consume shared agent-mc-autonomy 0.1.16 for native Chat/Responses, Claude and Gemini model APIs; add explicit domestic provider presets, streaming and protocol-specific parameters.
- Add optional official OpenAI/Google OAuth, OS credential storage and refresh in the shared framework. Default Neko model binding is unchanged; no host account files are reused.
- Add direct model settings, explicit catalog/tool checks and pre-start validation to the hosted panel. Provider implementation stays out of the Neko adapter and Minecraft body.
- Offline protocol, authentication and hosted-form checks do not prove cloud account access or live gameplay. No release/Market publication or running agent reload.

## 0.5.1 — Unreleased

- Consume the canonical shared core through agent-mc-autonomy 0.1.15: inventory recovery, generic tactics and scoped game memory, with no plugin-specific core patch/compiler.
- Expose local keyword, optional embedding and external Mem0/Bailian/PowerContext/HTTP memory configuration in the existing settings panel. Provider logic, evidence and revisions remain in agent-mc-world.
- Default to local retrieval; forward only the configured memory key environment variable. External failures preserve local notes and report degraded retrieval. No game, model or service starts during checks.
- Pin the archive and build/type receipts, preserve old world identities and permission channels, and validate the disconnected Python-to-MCP channel. Source checks do not establish live gameplay or cloud connectivity.

## 0.5.0 — Unreleased

- Move the complete autonomous runtime and strategic review lifecycle into minecraft-ai-friend/packages/agent-mc-autonomy. Consume one pinned dependency; remove gameplay/viewer assembly copies from the Neko adapter.

- Add opt-in main-character strategic heartbeats with useful fresh facts, material/terminal changes, periodic review and a public inspect/continue/safe-insert decision tool. Preserve independent execution and official host speech.
- Persist review IDs and acknowledgements, bound retries, suppress duplicate in-flight goals and fence stale reviews against new user intent in the same mailbox transaction. Expose heartbeat settings/results in the existing Neko panel.
- Declare separate Neko configuration/control and observation panels through public UI APIs, with a legacy static UI entry.
- Add real bounded runtime statistics, health/food/position observations, native queue, latency chart and decision/receipt details. Stale reads and failed runs remain visible.
- Embed a configured modern viewer only after an explicit click, with separate-window and unload controls. No viewer deployment, second account or player-binding claim is implied.
- Allow validated viewer-only settings to change without stopping an embedded worker; keep runtime changes blocked while it is active.
- Pause observation reads when the page or its Neko panel is hidden. Render observations as text and reject unsafe viewer URLs.
- Add optional exact-version viewer assembly over the current player's native connection; request one browser open after joining. Keep full browser rendering separate from identity/data validation.
- Forward fresh, deduplicated game changes through the public Neko notification API, with an explicit narration action and configurable role/rate limit. Verified official online voice delivery and desktop playback receipts.
- Bound failure diagnostics and spatial previews while preserving original evidence, completed scout results and the latest synchronous inventory receipt.
- Restrict action/scout queue policies consistently. Reject invalid replacement locally with a correctable receipt instead of disconnecting the body.
- Verify the actual Neko manager tabs, public assets/context, viewer-only save, responsive layout and isolated viewer loading. Sustained vanilla survival and complete scene parity remain unverified.

## 0.4.0 — Unreleased

- Add public Neko `decision`, optional `vision` and `fast` model routing without reading provider credentials.
- Fall back to text on unavailable/invalid vision responses; keep native observation/queues alive when decision is unbound.
- Consume one fresh core PNG at the request tail with a separate image budget; standalone vision capability is explicit.
- Add optional bounded System One (remote Jev/local compatible Decider) or Neko-slot focus selection, with rules as the default and failure fallback. Native physical control stays in the core.
- Add a Hosted TSX panel for validated settings, natural-language goals and bounded real observations, decision/receipt samples, usage and latency.
- Add explicit text/tool and synthetic-image model diagnostics through the same SDK adapter; no game commands are dispatched.
- Keep short numeric/coordinate descriptions, prioritize survival facts under pressure and load script/artifact schemas on demand; one image still fits the default context budget.
- Reject empty provider successes before dispatch and record them for bounded recovery.
- Verify real public-gateway text/tool calls, missing-vision text fallback, bound-vision recognition and hosted settings/context APIs. Browser visual acceptance and paid Jev inference remain unverified.

## 0.3.0 — Development snapshot

### Added

- Independent runtime and explicit HTTP planner configuration, without a N.E.K.O installation.
- Natural-language goals and feedback: insert at native checkpoints and resume, or explicitly replace current work.
- Shared observations and deduplicated command receipts for Neko to guide and narrate an external runtime.
- Continuous event-driven planning with `max_decisions=0`, and planner-free execution of already planned native tasks.
- Public Neko LLM tools for compact state/fact pages, natural-language intents and explicit stop.
- Private rejected-inference diagnostics and bounded recovery before any game action is dispatched.

### Changed

- Neko is optional in external mode; closing it does not stop the independently launched runtime.
- Newly planned actions preserve native queued work by default. Unknown delivery still blocks automatic replay.
- Embedded mode still supports the public `decision` slot. This slot supplies planning inference, not Neko's full main conversation.
- Keep the latest tool receipt when a large fixed prefix previously evicted all error feedback.
- Advertise native scouting directly and reject standing-goal completion reports without disconnecting the body.

### Acceptance

- Development build only. Vanilla 1.21.1 login, collection, crafting and Neko intent delivery were observed; see the dated live-acceptance report.
- Long-running survival, automatic game narration and viewer binding remain unverified. Planner-reported goal success stays explicitly unverified.
