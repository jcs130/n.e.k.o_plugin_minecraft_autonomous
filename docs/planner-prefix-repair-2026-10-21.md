# Planner prefix continuity

Development adapter 0.6.77 pins host-neutral autonomy 0.2.73 at
`1369c56f3c735618c22b3e9241ec03af823363b4`. The game core and viewer pins are
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
