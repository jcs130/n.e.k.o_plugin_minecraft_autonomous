# Repository instructions

- This repository provides independent Minecraft autonomy and an optional N.E.K.O frontend, with a generic 1.21.1 controller.
  Offline tests do not prove live gameplay, native-server support or viewer/body binding.
- Use Python 3.11+ and the public `plugin.sdk.plugin` API. Do not modify the host SDK.
- Keep plugin ID `minecraft_autonomous` and manifest/project versions consistent.
- Keep the official managed Verify, Release and Ruff templates intact.
- Do not connect to games, start services, call models or send messages during tests.
  Use temporary storage and the real SDK from `NEKO_ROOT` or the CI host checkout.
- Keep automatic startup and autonomy disabled by default. Preserve explicit stop.
- Keep `autonomy/` importable without a host SDK. N.E.K.O supplies high-level intent and
  narration/voice; the optional planner refines actions, and the native executor owns
  the real work queue. External frontend shutdown must not stop the standalone runtime.
- Natural-language goals and feedback use the durable command mailbox. Preserve request
  IDs, distinguish insert/resume from explicit replacement, and never turn planner reports
  into verified goal success. Unknown native dispatch blocks replay.
- Add only the dependencies needed for the selected backend; do not copy a legacy
  deployment, private config, credentials, weights, voice caches or user world saves.
- Before enabling gameplay, require a core whose source, build, default entry and
  public types are independent of Cortico. Optional host adapters depend on neutral
  contracts and the core; do not import Core/Persona/provider/Memory implementations.
  Preserve useful behavior from the user's fork through explicit contracts and tests.
- Use the pinned independent 0.4.0 headless core and its checked build receipt.
  Do not replace it with the historical 0.3 distribution. Legacy speech discovery, server
  policies and additional model endpoints must be explicit optional integrations.
- Before committing, run pytest, Ruff and the official release/Market-structure check
  using the commands in `CONTRIBUTING.md`. Inspect package contents and staged changes.
- Do not create release tags, publish releases or submit to Market unless that work
  is explicitly requested and functionality has been verified.
