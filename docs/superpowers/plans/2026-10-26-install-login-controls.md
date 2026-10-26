# Installation, private login and model controls implementation plan

**Goal:** Make existing-player login and ordinary configuration usable from the plugin, verify Windows delivery, and document the actual App installation/update contract.

**Architecture:** Keep Minecraft authentication and native behavior in the canonical core. The host-neutral framework validates native configuration and writes scoped private login references; the thin adapter presents a write-only password form and optional presets. The running external body remains untouched during offline work.

**Constraints:** Preserve account identity, unknown-result and inventory barriers, one native queue, explicit start/stop, 180-second deadlines, managed official workflows, original user data and private credentials. Do not publish a Linux binary as Windows. Do not replace published evidence or assets. DeepSeek live switching waits for the pending human choice.

## Acceptance and implementation

- [ ] Reproduce missing ordinary password UI with `tests/test_server_login_panel.py`; prove no password enters settings responses, status or error messages.
- [ ] Add canonical `server_login.py` material handling and temporary-directory tests: matching account/address, blank preserves an existing credential, explicit disable, wrong identity, invalid multiline input, write failures, POSIX modes and Windows encryption.
- [ ] Add adapter `configure_server_login` using the public SDK action, existing worker guard and normal settings persistence. Add a local write-only password field, saved-state indicator and explicit disable control; retain the advanced external-file path.
- [ ] Add canonical typed native settings for scaffold blocks, combat/reflex, idle and journey. Omitted values preserve core defaults. Reject unknown keys, invalid booleans/numbers and permission or process options. Cover exact forwarding and unchanged defaults in `tests/test_native_settings.py`.
- [ ] Add a collapsed advanced native section and simple DeepSeek presets using the existing `decision_policy` port. Test routine/complex request isolation, `none`/`low` payloads and host-route limitation; keep unsupported settings visible as unsupported.
- [ ] Read the official Market release workflow, installed-source lock and App install/upgrade transaction. Verify published package ABI independently. Record whether Windows defaults and unattended updates are supported; do not bypass SHA/provenance validation.
- [ ] Build and inspect a Windows candidate with the official SDK, independently import it and exercise a deep Chinese/space installation path with the new password/configuration surface using temporary storage. Keep tests offline.
- [ ] Run framework and adapter checks required by their AGENTS/CONTRIBUTING instructions, inspect staged diffs, ordinary-push atomic source changes. Separate source/candidate results from any future publication or live model observations.

## Review focus

1. Refresh and editing never reveal or erase a saved password.
2. Changing the server or account never silently reuses another account's credential.
3. Active embedded workers and external bodies cannot be reconfigured by the password form.
4. Empty native options leave every core default intact; no process, permission, collision or deadline override is admitted.
5. App import and Market upgrade have different source ownership; a manual Windows import must not be represented as Market automatic updates.
