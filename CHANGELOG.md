# Changelog

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
