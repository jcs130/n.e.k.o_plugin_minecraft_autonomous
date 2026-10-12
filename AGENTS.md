# Repository instructions

- This repository is a N.E.K.O plugin for autonomous Minecraft play, currently at
  the repository-scaffold stage. Do not claim the game backend works before it exists.
- Use Python 3.11+ and the public `plugin.sdk.plugin` API. Do not modify the host SDK.
- Keep plugin ID `minecraft_autonomous` and manifest/project versions consistent.
- Keep the official managed Verify, Release and Ruff templates intact.
- Do not connect to games, start services, call models or send messages during tests.
  Use temporary storage and the real SDK from `NEKO_ROOT` or the CI host checkout.
- Keep automatic startup and autonomy disabled by default. Preserve explicit stop.
- Add only the dependencies needed for the selected backend; do not copy a legacy
  deployment, private config, credentials, weights, voice caches or user world saves.
- Before enabling gameplay, require a core whose source, build, default entry and
  public types are independent of Cortico. Optional host adapters depend on neutral
  contracts and the core; do not import Core/Persona/provider/Memory implementations.
  Preserve useful behavior from the user's fork through explicit contracts and tests.
- Treat the pinned Agent MC World release as a transport/capability baseline until
  the documented decoupling gaps are resolved. Legacy speech discovery, server
  policies and additional model endpoints must be explicit optional integrations.
- Before committing, run pytest, Ruff and the official release/Market-structure check
  using the commands in `CONTRIBUTING.md`. Inspect package contents and staged changes.
- Do not create release tags, publish releases or submit to Market unless that work
  is explicitly requested and functionality has been verified.
