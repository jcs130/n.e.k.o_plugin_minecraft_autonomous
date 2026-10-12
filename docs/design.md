# Minecraft Autonomous — repository scope

## Product goal

Create a N.E.K.O plugin through which an AI player can autonomously play Minecraft:
observe the world, choose goals, plan, execute actions, learn from results, and continue
surviving without a human issuing every individual action. Human intervention can
change goals, take over, or stop play. Commentary is optional output from gameplay.

## Current repository

The official identity, inert SDK entry points, offline tests and Market workflows
are established. Agent MC World 0.3.0-next.2 is pinned as the candidate game
execution backend and migration baseline. An explicit installer, validated
configuration and Python MCP transport have been prepared and exercised with
networking denied. They are not yet
connected to the plugin's start entry; the plugin continues to refuse gameplay.
Source, disconnected transport verification and live gameplay are separate milestones.
Its standalone entry needs no Cortico npm runtime, but the upstream build still
extracts Cortico sources. Root exports/types, viewer speech discovery and host
contract gaps must pass the decoupling checks before enabling the backend.

## Constraints

- Plugin ID: `minecraft_autonomous`; entry class: `MinecraftAutonomousPlugin`.
- Public GitHub repository: `jcs130/n.e.k.o_plugin_minecraft_autonomous`.
- Python 3.11; use the public `plugin.sdk.plugin` facade.
- Keep the official Verify/Release workflow templates intact.
- Default `plugin_runtime.auto_start = false` and `autonomy.enabled = false`.
- No game/model/voice processes, server connections, model requests, or automatic
  recovery in this increment. Existing N.E.K.O services stay stopped.
- Reuse Agent MC World and mc-visual-console without a Cortico runtime dependency.
  The production core must also build and expose its public types without a
  Cortico checkout. Host adapters depend on neutral contracts and the core;
  the core must not depend on a host adapter or scan legacy speech services.
  Do not bind the repository to the retired installation, account, GPU, credentials,
  voice, or private server.
- Record a structural scaffold as such. Passing package checks is not gameplay proof.

## Next functional increment

First complete the independent source/build boundary and define versioned neutral
contracts for event scheduling, tool barriers, cancellation and turn boundaries.
Preserve useful behavior verified in the user's fork through these contracts;
do not copy Cortico Core, Persona, provider, Memory or deployment assumptions.
The generic MCP interface currently drops some of the required metadata.
Then implement one game controller with goal, current-fact and task ledgers;
retain raw evidence with bounded query access and replace frequently changing facts
at the request tail. Preserve useful long-running actions and explicit stop.

N.E.K.O Main provides user goals and character communication. Its public plugin
model gateway is an inference API, not Main's persona/history or an autonomous loop.
The game controller requires an explicit character-task context and experience
handoff. Speech playback must not be the clock for game actions.

The [source comparison and proposed architecture](research/neko-integration-architecture.md)
records these boundaries, the [Cortico host study](research/cortico-host-architecture.md)
traces the scheduling contract, and the [Minecraft study](research/mineflayer-protocol-and-harness.md)
covers protocol, remote-server and viewer behavior. Acceptance requires offline
contract tests plus separately authorized gameplay compared with the existing
Cortico setup; no equivalence is claimed yet.

The [fork delta and migration boundary](research/fork-improvements-and-decoupling-boundary.md)
records which user changes belong in the execution core or host controller, and
the [package audit](research/agent-mc-world-decoupling-audit.md) identifies remaining
build, public-entry and optional-service coupling. Provenance and license notices
remain intact; a source attribution is not an active runtime dependency.
