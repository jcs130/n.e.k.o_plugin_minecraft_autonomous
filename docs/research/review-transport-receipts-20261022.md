# Preserve structured review transport evidence

The latest `structured-review.json` is a UI snapshot. Previously a later timeout
overwrote an earlier output-budget failure, so provider-success accounting could
not establish whether a final review transaction had existed or been adopted.

Version 0.6.85 adds append-only `structured-review-attempts.jsonl` receipts. Each
actual gateway await has an opaque attempt ID, review ID, timestamps, wait/output
budgets, elapsed time, categorical outcome, whitelisted finish/tool labels and
available numeric usage. Content and private reasoning contribute only character
counts. The final delivery receipt links those attempts and records canonical
acknowledgement separately. Cancellation is retained before it propagates.

No model text, tool arguments, selected memories, persona, credentials or exception
messages enter the journal. Missing usage stays unknown; transport success remains
distinct from a valid final tool, review acknowledgement and native achievement.
Optional journal I/O failure cannot alter adoption or dispatch and is exposed in
the latest receipt. Original records are not replaced or replayed.

Regression coverage exercises the real heartbeat: a length-limited response
followed by a timeout, evidence reads plus one correction, caller cancellation,
untrusted provider labels and journal I/O failure. Existing output limits, original
opportunity deadline, automatic tool selection, bounded correction/evidence reads,
stop/ownership checks and the sole native body queue are unchanged.

Read-only inspection of the current local serving template found that omitted
reasoning effort injects `xhigh`; its CPU-counter copy matched the actual container
template hash. The public host gateway currently accepts no reasoning-effort or
template-kwargs extension, including through model-slot defaults. This is a
configuration difference from the standalone body, not proof that every prior
3072-token review was truncated. This change records actual finish reasons; it
does not change the host SDK, healthy model, reasoning configuration or inference
budgets, and makes no claim of repaired latency or autonomous project progress.

The dependency remains autonomy 0.2.80. This is an adapter-only development change;
the independent body, core and renderer need no replacement. Public release and
Market publication are outside this maintenance operation.
