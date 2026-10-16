"""Categorical plugin call diagnostics; no review payload or host internals."""

import asyncio
import json
import re
import uuid
from functools import wraps

ERRORS = frozenset({
    "disabled_or_stopped", "configuration_changed_or_stopped", "review_superseded",
    "review_expired_or_changed", "review_expired_or_game_unavailable", "invalid_review",
    "invalid_lineage_offset", "reason_and_stage_goal_required", "review_choice_conflict",
    "fresh_inspection_required", "fresh_recovery_inspection_required", "critical_baseline_changed",
    "death_episode_superseded", "death_episode_mismatch", "death_reflection_required",
    "death_reflection_already_completed", "death_evidence_reference_mismatch",
    "intent_or_scope_changed", "intent_revision_changed", "game_not_running",
    "no_active_review_stage", "previous_intent_pending", "goal_already_active",
    "detail_is_read_only", "inspect_is_read_only", "evidence_reference_required",
    "meaningful_review_requires_decision",
})


def identifier(value, pattern):
    return value if isinstance(value, str) and re.fullmatch(pattern, value) else None


def emit(plugin, row):
    try:
        plugin.logger.info("minecraft_review_rpc %s", json.dumps(row, separators=(",", ":")))
    except Exception:
        pass  # Optional diagnostics must not alter return, exception or dispatch.


def review_completion(method):
    @wraps(method)
    async def wrapped(plugin, heartbeat_id, decision, *args, **kwargs):
        reflection = kwargs.get("death_reflection", args[5] if len(args) > 5 else None)
        reference = kwargs.get("evidence_ref", args[6] if len(args) > 6 else None)
        reference = reference or (reflection.get("evidence_ref") if isinstance(reflection, dict) else None)
        row = {"call_id": str(uuid.uuid4()), "review_id": identifier(heartbeat_id, r"[a-f0-9]{12}"),
               "phase": "inspect" if decision == "inspect" else "final" if decision in ("continue", "insert", "revise") else "invalid",
               "evidence_ref_present": identifier(reference, r"[a-f0-9]{24}") is not None}
        emit(plugin, {**row, "event": "entered"})
        try:
            result = await method(plugin, heartbeat_id, decision, *args, **kwargs)
        except BaseException as error:
            emit(plugin, {**row, "event": "raised", "error_category": "cancelled" if isinstance(error, asyncio.CancelledError) else "exception"})
            raise
        data = result if isinstance(result, dict) else {}
        error = data.get("error")
        emit(plugin, {**row, "event": "completed", "acknowledged": data.get("acknowledged") if type(data.get("acknowledged")) is bool else None,
                     "error_category": error if isinstance(error, str) and error in ERRORS else "other_error" if error or data.get("is_error") else None,
                     "request_id": identifier(data.get("request_id"), r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}"),
                     "evidence_ref_present": row["evidence_ref_present"] or identifier(data.get("evidence_ref"), r"[a-f0-9]{24}") is not None})
        return result
    return wrapped
