# Changelog

## 0.6.7 — Development candidate

- Use original compass frames from observed own-player state and original inactive crossbow GUI textures.

- Prevent late server status replies from doubling the refresh interval and
  expiring health/mana. Bundle the original backpack profile texture and render
  its exact 1.21.1 head/hat model rather than a generic item label.
- Pin the shared core repair that applies explicit server action denials to the
  exact native block and preserves the original error for replanning.
- Consume the shared SNBT text fix and original untrimmed armor icons, plus an
  independently checked optional server item catalog.
- Bundle Qiandengji's original custom item icons/models/textures. Keep its own
  connection attestation through death and opt into bounded read-only status
  refresh. Ordinary servers gain no custom protocol, queries or resource rules.
- Validate every bundled extension resource before selecting the pack. Neko
  main/SDK and model processes remain outside the plugin's lifecycle.

## 0.6.2 — Release preparation

### Fixed
- Keep a planning-voice timer's own bounded HTTP/audio task alive until completion. The official host creates a separate event loop per timer callback, so returning immediately previously cancelled an enqueued line before submission. Waiting happens in that voice timer, independently of the MC controller and main brain; stop/expiry/unknown-output protections remain intact.
- Add a regression reproducing return-before-delivery, retaining the tool-only narration support and the existing official TTS/persona/model-slot boundaries.

## 0.6.1 — Release preparation

### Fixed
- Pin framework 0.2.1: models that return only tool calls can include the same-decision line in an optional host-only `mc_do._spoken_text` field. It is removed before the original native argument validation and dispatch; assistant-content narration remains supported. No extra generation or Minecraft chat message is introduced.
- Retain 0.6.0's public model-slot, character-persona and existing-voice integration. Candidate artifacts remain separate from public Release and Market approval.

## 0.6.0 — Release preparation

### Added
- Forward optional natural commentary from the existing MC planning response through Neko's public character and game-speech APIs. Ordinary speech no longer requires a completed main-brain review or an extra narration model call; voice synthesis runs independently of body work.
- Follow the selected user's current cat when the role is blank. Share only public persona fields; retain the cat's existing TTS configuration without reading voice IDs or supplier credentials.
- Add panel controls for same-decision speech, explicit local host address and pacing, plus installation guidance distinguishing Core, Assist and the official Plugin API model bindings.

### Safety and verification
- Pin the host-neutral framework's bounded, once-claimed speech outbox. Stop, actor/world/runtime changes, new intent, death and expiry invalidate old lines; unknown delivery is never replayed.
- This is a release candidate preparation. Public Release publication, Market approval, clean-machine installation and long-term gameplay remain separate acceptance steps.

## 0.5.65 — Internal candidate

- Pin autonomy 0.1.89: a review proven never offered or inspected receives fresh evidence and a new ID after expiration. Offline time no longer creates a false host-acknowledgement failure and five-minute silence. Actual, rejected and unknown deliveries retain their existing bounds; no action or old acknowledgement is replayed.
- Retain 0.5.64's original YSM UV, terrain preparation, optional-context-read and native reconnect continuity repairs. Source checks, actual playback/action receipts and long-term survival remain separate.

## 0.5.64 — Internal candidate

### Fixed
- Pin autonomy 0.1.88 / shared viewer 3553c60d: yield terrain preparation through browser tasks so throttled painting does not hold up a complete terrain commit. Keep the prior recovery-budget, exact YSM UV and bounded column-cache fixes.
- An intermittent denied optional status read no longer aborts the strategic review timer; unavailable recent conversation material stays unavailable, without altering ownership or replaying work.

- Keep the owned runtime alive through native connecting/retrying phases, suspend model/action work on unavailable facts and require fresh queue/body state after recovery. Explicit stop and stopped/unknown states retain their fences.

## 0.5.63 — Internal candidate

### Fixed
- Keep the review ID and required death reflection visible in short host notification previews; avoid repeating the full standing goal there.
- Pin framework 0.1.86: preserve individually bounded live facts and put short recovery completion requirements first. Missing reflections return the same bound contract without acknowledging or dispatching anything.
- Retain viewer 43e23250, including the original YSM crown/chin UV conversion fix and bounded terrain caches. Source validation is separate from actual deployment and gameplay acceptance.

## 0.5.62 — Internal candidate

### Fixed
- A missing public SDK model gateway no longer crashes explicit direct planning or the model-check entry; unavailable host planning stays explicit.
- Pin framework 0.1.85: unique tool names, provider-compatible tuple projection with original native validation, bounded safe HTTP rejection diagnostics and queue-preserving backoff.
- Pin viewer 43e23250: bounded received/decoded terrain caches recover normally beyond 512 columns and preserve updates, block entities and unload semantics.
- Refresh visible control panels periodically without polling hidden panels or overwriting an advanced edit. Exclude author backup files from packages.
- Clarify exact offline pairing, Windows TOML paths, inherited API-key environments and official metadata rebuild/import. Keep source validation distinct from recipient and gameplay acceptance.

## 0.5.53 — Internal candidate

- Pin reviewed canonical autonomy 0.1.77 at `ed94de1277ff0bf61182733374ec8ac8db7e8413` (final recovery fix2), retaining exact checked core .39 / `3ee62ca2` and packaged viewer c799.
- Consume bounded private first-error diagnostics and the pending operator-acknowledgement startup fence. Recovery remains an explicit offline operator CLI action; the adapter adds no recovery tool, automatic acknowledgement or replay. Accepted-only old native work remains unknown.
- Preserve recent-context filtering, profile leases, speech admission, native queue ownership and disabled automatic startup. Source/package checks do not cure the original PermissionError or establish live recovery. See `docs/integration-0.5.53-20261017.md` for provenance and deployment order.

## 0.5.52 — Internal candidate

- Refresh bounded public same-character conversation context and independently fresh configured persona through the existing observer, including when no review is pending. Canonical autonomy reads the private file at every body model round; historical language is never a new command or verified world fact.
- Suppress exact explicit-output repeats within 300 seconds for positively bound ordinary automatic opportunities. Keep same-opportunity receipts, urgent/manual/unknown paths and independent action dispatch. Accepted or unknown output never proves playback.
- Pin reviewed autonomy 0.1.76 at `bb538c7bc1e1b4bc33e8b38aceaf27079a6ab0df`, including exact checked core .39 / `3ee62ca2`. Default external viewer c799 remains separate. Source/package checks do not establish live acceptance.

## 0.5.51 — Internal candidate

- Pin reachable canonical `6178073c38e671771a90cf507e492fe3b23841a0` / autonomy0.1.73 with exact corec9ac/.32 and shared viewerc799 source/build receipts. Preserve the bundled speaking skill, original YUI assets and reviewed GUI producer/abort/stow contracts.
- Default public context settings to65536, document optional131072 on supporting services and preserve explicit other valid values. Current service capacity remains an independent configuration constraint.
- Source-only incoming core.33 method capabilities are separate from the frozen.32 distribution. Offline candidate checks do not establish deployment, full scene/voice coverage or survival.

## 0.5.50 — Internal candidate

- Pin reviewed autonomy 0.1.71 at `6cbff24070a2ff4ee224e6d5bf94e82cebe4a914`, with frozen engine-only core .24 from exact `2723d39f8129a6d2f87a773832289888dda1d51c` and unchanged viewer `567d95e6`.
- Consume optional viewer-state persistence isolation: failed writes preserve the complete prior snapshot; normal publication recovers using current state, and obsolete/disposed attachments cannot publish. Preserve reviewed short-final, death, ownership and no-replay behavior.
- Retain disabled startup/gameplay defaults, original bundled YUI assets, saved appearance choices and external configuration. Later incoming core source .25 is preserved in canonical history but excluded from this frozen core artifact; its delivery remains required follow-up. Exact hashes distinguish concurrent .24 source labels.
- Offline checks do not establish natural ACK, playback, busy-file live continuity, all animations or sustained survival. No release tag or Market publication.

## 0.5.49 — Internal candidate

- Pin reviewed autonomy 0.1.70 at `ec20aef983cdd25fe6e124adf7a95ad2040bca15`, retaining immutable engine-only core .13 and shared viewer `567d95e6`.
- Inspect exposes the evidence-bound minimal final completion contract. Finish the same-brain tool transaction before optional narration; preserve authored reasons, goals, death lesson/deferral, public character context and optional speech-before-dispatch without audio waits or replay.
- Keep startup/gameplay disabled by default. Offline package/SDK checks do not establish natural provider final ACK, playback, complete scene fidelity or sustained survival. No release tag or Market publication.

## 0.5.48 — Internal candidate

- Pin reviewed autonomy 0.1.69 at `2b0db6308c93a5b155e17abe0ed5d4708424fe20` and immutable engine-only core 0.5.7-dev.20261016.13. Consume reviewed fresh-connection/current-death recovery and strategic applicability repairs without copying gameplay policy into the adapter.
- Default Neko embedded Web appearance to original bundled YUI YSM; preserve explicit defaults and saved browser choices, including server-follow. Expose Web-only choice/status and canonical `/3dview/` links. Shared viewer `567d95e6` carries validated defaults and opaque server/account scopes; ambiguous old preferences require one-time reselection, not guessed migration.
- Require evidence for legacy episode-only lessons while retaining compact evidence references and honest deferral. Log only categorical review entry/completion/exception diagnostics with plugin `call_id`, validated review/command IDs and evidence-reference presence. Preserve original results, exceptions, acknowledgement and speech/action dispatch semantics.
- Retain public speech-ID/audio flags with playback unverified. Full entity rendering, natural host speech/final-ACK compliance, swimming and sustained survival remain acceptance work. New upstream core .21 is separately scheduled for final integration; this candidate deliberately keeps the reviewed .13 artifact. No release tag or Market publication.

## 0.5.47 — Internal candidate

- Use autonomy 0.1.67 compact inspection and bounded original evidence pages. Final decisions use a short same-brain contract with optional natural speech and validated compact death references; ordinary Neko finals require a fresh inspection.
- Bind the configured public character during inspection independently of strategic acknowledgement. Preserve fresh explicit persona, current intent and selected memory; static identity never represents memory recall or revives expired intent.
- Retain validated public speech ID/audio queue/completion metadata alongside the text hash. Queued output is not playback. Core .9 remains pinned and live model/speech acceptance is still separate.

## 0.5.46 — Internal candidate

- Pin autonomy 0.1.66 at `fd205ba5f3cb8957a70a3709fa42c0beef6c2fd4` with unchanged checked core 0.5.7-dev.20261016.9 inputs. Pending death decisions require an inspected evidence-based lesson or explicit justified deferral before acknowledgement, speech or goal delivery; missing reflection can be corrected on the same heartbeat.
- Expose lesson/deferral requirements through the public SDK schema and tool help. Freshly inspect and complete legacy acknowledged pending reflections without replaying their original goal or speech. Historical lessons remain hypotheses with improvement unverified.
- Normal-drain the independent body to 0.1.66 as well: its transactional history writer preserves concurrent host reflection/completion fields. Reloading only the adapter leaves the old 0.1.65 producer's stale-write race. Startup/autonomy remain disabled by default; package checks do not prove live recovery or playback.

## 0.5.45 — Internal candidate

- Pin reviewed autonomy 0.1.64 at `784047e72a67d616e8847c3032b3b79c4d0d672e` so installation provides the heartbeat idle-presence and final-review speech/death-reflection APIs already used by this adapter.
- Keep its checked core 0.5.7-dev.20261016.6 pin and refresh matching installation metadata. This candidate is not deployed or released; startup/autonomy remain disabled by default.

## 0.5.44 — Internal candidate

- Pin autonomy 0.1.61 and core 0.5.7-dev.20261016.2. New operation evidence sums duplicate inventory stacks, preserves unknown inventory and leaves historical records unchanged.
- Preserve the canonical memory read preference through full dashboard draft saves, so typed field feedback reaches the panel.
- Explain local installation metadata in Chinese and distinguish external executor resources from local configuration; actual scene and role binding remain to be verified in the viewer.
- Refresh exact committed source and archive pins. Default startup/autonomy remain disabled; no public release or Market submission.

## 0.5.43 — Internal candidate

- Pin autonomy 0.1.60 and reviewed core 0.5.7-dev.20261016.1; expose bounded installation metadata without repeated full runtime hashes. Explicit starts still verify the pinned runtime.
- Return safe field-specific configuration guidance, retain rejected drafts, and explain local addresses and Microsoft human authorization. Public-server shortcuts preserve the user account and authentication choice.
- Document exact locally staged core/viewer/optional sound assets and reproducible setup. No public artifact URLs, clean-machine guarantee, release or Market submission are claimed.
- Exclude development/private artifacts while retaining only Certifi's public CA PEM bundle, so packaged direct-model clients can construct their TLS context.

## 0.5.29 — Unreleased

- Consume checked autonomy 0.1.46/core 0.5.2, preserving current main's Java 1.21.1 build/registry/login defaults and the existing knowledge, food and queue fixes.
- Synchronize shared viewer main `4b59ce79`: the native entry now uses the common toolbar, display settings, chat history and photo entry. Actual capture provider and night vision gaps stay explicit.
- Default to ordinary Mineflayer data. Optional server visuals follow validated received capabilities/state and exact resources; hostname/chat/profile guesses cannot enable Qiandengji abilities or mana. Loss/reset removes stale panels.
- Add public-SDK-only host boundary regressions. No Neko main program/SDK source patch, second game account, extra model loop or host restart is introduced.

## 0.5.28 — Unreleased

- Make vanilla Java 1.21.1 the primary optimization/acceptance target; consume autonomy 0.1.45 and checked core 0.5.1 from pinned main commits.
- Expose the core's bounded `mc_knowledge` search/get for versioned food, cooking, regeneration and full registered item/block/crafting references. Retrieval defaults to local reference data; historical memory and explicitly configured vector providers remain separate. No extra model request or duplicated gameplay policy in this adapter.
- Prefer an available cooked counterpart during routine eating, keep emergency food usable, and include baseline hunger/saturation, cooking gains and harmful-food warnings in current ration facts. Ominous bottles are not rations. Explicit eat requests are not silently rewritten.

- Live follow-up: infer read-only search/get when action is omitted and expose verified cooking/charcoal recipes through recipe-filtered search.

## 0.5.27 — Unreleased

- Consume autonomy 0.1.43 and checked core 0.4.7. Every named craft step is checked for a known recipe before accepting a batch, so a later nonexistent recipe cannot consume materials in earlier steps or interrupt existing work.
- Preserve deferred material checks, explicit custom grids, tagged recipes, smithing and unknown recipe-reader states. This is a specific admission fix, not a claim that autonomous planning or sustained survival is fully reliable.

## 0.5.26 — Unreleased

- Consume autonomy 0.1.42: reuse an attached internal viewer after runtime handover, with a bounded reconnect grace before opening a new page. This prevents repeated automatic opens from exhausting the four read-only stream connections.
- Keep the checked 0.4.6 body, synchronized food-reserve facts and private source/build evidence. This change does not claim complete visualization or sustained survival.

## 0.5.23 — Unreleased

- Consume autonomy 0.1.39 and checked core 0.4.4: keep concise native action parameter meanings, return a legal bounded voxel retry, and expose repeated read-only activity to the optional planner. Game decisions and body execution remain in the independent framework.
- Preserve the deployed fall safeguards, explicit stops and unknown-dispatch protection. Offline validation does not establish sustained survival.

## 0.5.22 — Unreleased

- Consume autonomy 0.1.38 and the hash-checked independent 0.4.3 body: reject damaging dry navigation drops, brake predicted cliff falls with real physics, and remove the lower-goal deep-fall exemption. The thin adapter owns no movement policy.
- Preserve source/build/deployment evidence separately; this does not claim sustained survival or publish a Market release.

## 0.5.20 — Unreleased

- Consume autonomy 0.1.36 so manually inserted native tasks appear in the same public timeline as planner tasks. Queue entries reuse their public skill summary, and each rejection keeps one sanitized diagnostic row.

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
