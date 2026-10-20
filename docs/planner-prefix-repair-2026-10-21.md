# Planner prefix continuity

Development adapter 0.6.78 pins host-neutral autonomy 0.2.74 at
`7ac713e5b517e082b71213023ca9eada4ab4299a`. The game core and viewer pins are
unchanged. This is a dependency update; planning behavior remains in MC friend.

Full-mode temporary read deferral and ahead planning previously rewrote the
provider's leading function declarations. A replay through the real controller
and selected local Chat template/tokenizer reproduced almost total prefix
invalidation on the same retained history. The framework now keeps declarations
stable and sends current tool/append-only permissions in the final scene. The
same restricted validators still reject deferred reads, insertion/replacement
and forbidden mutations before native dispatch. Compact mode is unchanged.

The framework adds bounded request-context counts and hashes to successful,
cancelled and rejected decision journals. This helps distinguish cache loss,
history retirement and shared service pressure; it logs no prompt or private
memory contents in those diagnostics. Original receipts remain available.

The deadline stays bounded at the existing setting. CPU prefix replay and
offline tests establish this defect and repair; they do not establish a live
speedup, explain every timeout or prove long-term survival. This development
update does not publish a new GitHub or Market release, modify the host SDK or
change the selected model route.

The intermediate 0.6.77/0.2.73 live trial confirmed stable declarations across
ordinary/ahead planning and real cache reuse. It also exposed a separate
106,549-token deadline immediately after old history rotated, with unchanged
head/tool hashes. The existing 8K cache margin was smaller than large game
exchanges. The 0.2.74 follow-up measures the latest whole exchange only on actual
overflow, amortizes rotation within a quarter-window cap, and preserves the
latest fitting exchange plus fresh facts and raw journals. Its default remains
opt-in; no fitting history is removed early and the 128K capacity is unchanged.
Full framework regression passed 1,389 tests and 184 isolated-wheel checks;
the counter/template CPU replay proves prefix preservation, not live latency.
