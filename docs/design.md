# Minecraft Autonomous — repository scope

## Product goal

Create a N.E.K.O plugin through which an AI player can autonomously play Minecraft:
observe the world, choose goals, plan, execute actions, learn from results, and continue
surviving without a human issuing every individual action. Human intervention can
change goals, take over, or stop play. Commentary is optional output from gameplay.

## This initial repository

The first increment establishes the official plugin identity, SDK entry points,
configuration example, offline tests, package rules, and standard Market workflows.
It exposes its actual readiness and refuses to start gameplay until a game backend
has been selected and integrated. It contains no game backend or claim of completed
autonomous survival. Market submission requires that functional increment and testing.

## Constraints

- Plugin ID: `minecraft_autonomous`; entry class: `MinecraftAutonomousPlugin`.
- Public GitHub repository: `jcs130/n.e.k.o_plugin_minecraft_autonomous`.
- Python 3.11; use the public `plugin.sdk.plugin` facade.
- Keep the official Verify/Release workflow templates intact.
- Default `plugin_runtime.auto_start = false` and `autonomy.enabled = false`.
- No game/model/voice processes, server connections, model requests, or automatic
  recovery in this increment. Existing N.E.K.O services stay stopped.
- The game framework remains an open product choice. Do not bind this repository
  to the retired installation, account, GPU, credentials, voice, or private server.
- Record a structural scaffold as such. Passing package checks is not gameplay proof.

## Next functional increment

After framework selection, implement a backend boundary for observations, bounded
actions, cancellation, and observed completion. Build an event-driven goal loop,
retain complete raw evidence with query access, and keep frequently changing facts
at the request tail. Respect manual stop and preserve natural long-running actions.
Acceptance requires offline backend tests plus separately authorized game verification.
