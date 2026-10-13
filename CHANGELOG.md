# Changelog

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
