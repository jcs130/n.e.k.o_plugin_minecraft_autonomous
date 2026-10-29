# Measured container opening recovery

Plugin 0.6.125 consumes canonical `agent-mc-autonomy` 0.2.122 at
`f4592874d46edbc5141ec54f7a9264642cc6735a`. The body remains the independently
verified core rc.124; server extensions and model configuration are unchanged.

Previously a failed `use` followed by a skipped `take` lacked a measured take
effect, and an explicit `face` was outside the container recovery candidate.
Repeated batches could therefore run despite two unchanged failed openings.

The shared runtime now recognizes exactly measured failed openings, including
their face and skipped dependent withdrawal. At the same approach and inventory,
a third identical batch receives dated evidence instead of being dispatched.
Different targets, faces, prerequisite acquisition, movement, scope, connection,
death epoch and expiry remain eligible. Unknown effects never certify failure
or success. Refusals expire within 120 seconds and do not infer current block
state or permissions. No host-local gameplay policy is added.

Offline replay and package checks are separate from deployment and subsequent
native gameplay evidence. The existing account, persona, memory and goals must
be preserved across any explicitly authorized short host reload.
