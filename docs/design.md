# Minecraft Autonomous — architecture

## Current implementation

Version 0.2.0 uses the package-owned core from `minecraft-ai-friend@7889ce261a2309d94400b739c6198468d8271d83`,
with a reviewed standalone cleanup patch. `backend/source.json` pins source, patch hashes, archive and the derived
headless build profile. Runtime files and public declarations build without a framework checkout.

The N.E.K.O public SDK exposes explicit start/status/stop entries and the `decision` model usage. A single
worker thread owns one asyncio loop, model client, MCP session and Minecraft child, across host entry loops.
The model gateway supplies inference, not Main's persona/history, an autonomous scheduler or memory handoff.

`Controller` opens real decision turns, sends unique request/turn IDs, archives full tool receipts, acknowledges
barriers and closes turns explicitly. Pending executions wake on terminal evidence or urgent events. Routine
snapshots and polling do not replace useful long actions. Inference is cancellable; late results cannot dispatch
after stop. Events arriving during inference remain queued for a later context. No tool results enter game chat
except an intentional social action chosen within the user's goal.

Request construction keeps stable rules and curated schemas first, complete assistant/tool pairs next and
replacement facts/events last. Long schema descriptions and advanced tools are discovered on demand.
The backend still validates original schemas. Full originals remain in the archive, with bounded page reads.
UTF-8 byte counting is conservative; real tokenizer/cache statistics have not been measured.

## Ownership and recovery

- Startup is passive even when autonomy is enabled. An explicit start is required; an explicit stop is persisted.
- One worker per plugin instance; core connection ownership also uses a per-account data-directory lease.
- Server/account identity determines the ledger directory, not the backend version.
- Journal the request before dispatch. Unknown delivery or pending state from an unclean exit blocks a fresh run.
- Confirm generic-core disconnect before clearing pending executions; keep uncertain mutations blocked.
- Numen disconnect has different semantics and must not reuse this cleanup assumption.
- Model and game errors end the session; no automatic restart or replay loop.
- Neither accepted actions nor terminal execution receipts imply that a user goal is complete.

## Compatibility and remaining acceptance

Minecraft Java protocol is fixed at 1.21.1; authentication uses Mineflayer's offline/Microsoft modes.
No local server launcher, observer/player launcher, legacy speech discovery, provider key or GPU choice is added.
Built-in viewer/console is disabled because upstream assets target 1.20.6. An external viewer URL is informational;
real frame freshness and binding to this body's identity still require live verification.

The optional My Agent World adapter in the same commit requires its native SDK/world-adapter closure and
original body ledger. It is not wired into this generic plugin. See
[the source evaluation and server-author handoff](research/agent-mc-world-04-integration.md).
A vanilla protocol version string cannot satisfy a custom NeoForge handshake or native registry.

Before release, separately verify a configured server login, movement/collection/crafting, failures, explicit stop,
connection loss, long-running survival and the chosen viewer's actual data/frames. Desktop speech, Main persona
context and experience handoff require explicit public contracts, not imports of Cortico or private N.E.K.O APIs.
Historical studies in `docs/research` describe the prior 0.3 baseline; the 0.4 evaluation supersedes those build gaps.
