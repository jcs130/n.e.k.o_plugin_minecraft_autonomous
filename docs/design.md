# Minecraft Autonomous — repository scope

## Product goal

Create a N.E.K.O plugin through which an AI player can autonomously play Minecraft:
observe the world, choose goals, plan, execute actions, learn from results, and continue
surviving without a human issuing every individual action. Human intervention can
change goals, take over, or stop play. Commentary is optional output from gameplay.

## Current repository

The official identity, inert SDK entry points, offline tests and Market workflows
are established. Agent MC World 0.3.0-next.2 is now pinned as the independent game
execution backend. An explicit installer, validated configuration and Python MCP
transport have been prepared and exercised with networking denied. They are not yet
connected to the plugin's start entry; the plugin continues to refuse gameplay.
Source, disconnected transport verification and live gameplay are separate milestones.

## Constraints

- Plugin ID: `minecraft_autonomous`; entry class: `MinecraftAutonomousPlugin`.
- Public GitHub repository: `jcs130/n.e.k.o_plugin_minecraft_autonomous`.
- Python 3.11; use the public `plugin.sdk.plugin` facade.
- Keep the official Verify/Release workflow templates intact.
- Default `plugin_runtime.auto_start = false` and `autonomy.enabled = false`.
- No game/model/voice processes, server connections, model requests, or automatic
  recovery in this increment. Existing N.E.K.O services stay stopped.
- Reuse Agent MC World and mc-visual-console without a Cortico runtime dependency.
  Do not bind the repository to the retired installation, account, GPU, credentials,
  voice, or private server.
- Record a structural scaffold as such. Passing package checks is not gameplay proof.

## Next functional increment

First preserve the event trigger, tool barrier, cancellation and turn-end semantics
used by Cortico's World host. The generic MCP interface does not currently carry all
of them. Then implement one game controller with goal, current-fact and task ledgers;
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
