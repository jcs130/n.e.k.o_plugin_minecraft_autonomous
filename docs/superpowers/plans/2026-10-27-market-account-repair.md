# Market Windows and account startup repair

**Goal:** Deliver the same official Market artifact on Windows and Linux, repair account startup diagnostics and the Plugin API link, and consume the reviewed current MC core.

**Architecture:** Keep Neko and its official workflows unchanged. The plugin selects its own verified platform resources before importing native dependencies. The framework continues to own all gameplay and model contracts. Account readiness remains a required check for imported identities; ordinary original accounts keep their normal login flow.

**Constraints:** Python 3.11, explicit start, one native queue, no unknown replay, no host/Java/model restart, no paid trial, no account creation or password changes in verification. Preserve protected local files and private data. Official build evidence must describe actual released bytes.

## Work and verification

- [x] Reproduce API link and imported-identity/password material failure with isolated fixtures. Fix `/ui/model-api`, report safe specific account failures, and accept the plugin's own scoped login material without bypassing fresh ready validation.
- [x] Review and merge current core rc.107 at 5f8f5166, build the fixed LF package, run core regression/type/packed consumer checks and consume framework 0.2.109. Core 2349 tests passed (6 optional skips); source and installed wheel each passed 1586 framework tests.
- [x] Keep required MCP/jsonschema/OpenAI SDK dependencies. Add verified Windows dependency resources and a stdlib bootstrap inside the plugin, leaving official Ubuntu workflow and SDK unchanged.
- [ ] Build the same final `.neko-plugin` with the official CLI; formally import and exercise real native imports on Windows and Linux. Check dependency versions, deep paths, private login, read-only panels, and update/config preservation.
- [x] Replay the real free-model reasoning-history rejection against Neko's validator offline, then verify normal tool follow-ups live. Preserve advertised-tool, schema, ordering and unknown guards.
- [ ] Finish status-page native health, direct 3D-viewer opening and visible stop confirmation acceptance. Keep unknown health maxima and server framing protections intact.
- [ ] Run relevant full checks, inspect staged sources/package/privacy and fresh upstream heads, then commit and ordinarily push. Publish only the verified artifact through standard Release/Market and update the website under the user's explicit release instruction.
- [ ] Record live development deployment separately from offline/package acceptance. Do not represent queries as gameplay or package verification as a real account activation.
