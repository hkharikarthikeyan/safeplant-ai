"""Audit log routes"""
import uuid
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta

audit_bp = Blueprint("audit", __name__)


def _fetch_all(sb, table, select="*", filters=None):
    """Paginate through all rows bypassing the 1000-row default limit."""
    rows, offset, limit = [], 0, 1000
    while True:
        q = sb.table(table).select(select)
        if filters:
            for col, val in filters.items():
                q = q.eq(col, val)
        res = q.range(offset, offset + limit - 1).execute()
        rows.extend(res.data or [])
        if len(res.data or []) < limit:
            break
        offset += limit
    return rows


def _bulk_insert(sb, rows, chunk=500):
    for i in range(0, len(rows), chunk):
        sb.table("audit_log").insert(rows[i:i + chunk]).execute()


@audit_bp.route("/audit-logs")
def list_audit_logs():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("audit_log").select("*", count="exact")
    if request.args.get("entity_type"):
        query = query.eq("entity_type", request.args["entity_type"])
    if request.args.get("entity_id"):
        query = query.eq("entity_id", request.args["entity_id"])
    if request.args.get("action"):
        query = query.eq("action", request.args["action"])
    res = query.order("occurred_at", desc=True).range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@audit_bp.route("/audit-logs/backfill", methods=["POST"])
def backfill_audit_logs():
    """
    One-shot backfill: reads incident_state_event, corrective_action_event,
    machine_state_event, acknowledgement and mirrors them into audit_log.
    Safe to re-run — clears existing rows first.
    """
    sb = get_supabase()

    # Clear existing audit log to avoid duplicates on re-run
    sb.table("audit_log").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    rows = []

    # 1. Incident state events
    for ev in _fetch_all(sb, "incident_state_event"):
        rows.append({
            "id": str(uuid.uuid4()),
            "entity_type": "Incident",
            "entity_id": ev["incident_id"],
            "action": f"STATE → {ev['to_state']}" + (f" (from {ev['from_state']})" if ev.get("from_state") else " (created)"),
            "actor": ev.get("transitioned_by") or "SYSTEM",
            "before_state": {"status": ev["from_state"]} if ev.get("from_state") else None,
            "after_state": {"status": ev["to_state"], "notes": ev.get("notes")},
            "occurred_at": ev["transitioned_at"],
        })

    # 2. Corrective action events
    for ev in _fetch_all(sb, "corrective_action_event"):
        rows.append({
            "id": str(uuid.uuid4()),
            "entity_type": "CorrectiveAction",
            "entity_id": ev["corrective_action_id"],
            "action": f"STATUS → {ev['to_status']}" + (f" (from {ev['from_status']})" if ev.get("from_status") else " (created)"),
            "actor": ev.get("transitioned_by") or "SYSTEM",
            "before_state": {"status": ev["from_status"]} if ev.get("from_status") else None,
            "after_state": {"status": ev["to_status"], "notes": ev.get("notes")},
            "occurred_at": ev["transitioned_at"],
        })

    # 3. Machine state events
    for ev in _fetch_all(sb, "machine_state_event"):
        rows.append({
            "id": str(uuid.uuid4()),
            "entity_type": "Machine",
            "entity_id": ev["machine_id"],
            "action": f"STATE → {ev['to_state']}" + (f" (from {ev['from_state']})" if ev.get("from_state") else ""),
            "actor": "SYSTEM",
            "before_state": {"state": ev["from_state"], "valid": ev.get("is_valid_transition")} if ev.get("from_state") else None,
            "after_state": {"state": ev["to_state"], "trigger": ev.get("trigger_reason")},
            "occurred_at": ev["occurred_at"],
        })

    # 4. Acknowledgements
    for ev in _fetch_all(sb, "acknowledgement"):
        rows.append({
            "id": str(uuid.uuid4()),
            "entity_type": "Acknowledgement",
            "entity_id": ev["alarm_event_id"],
            "action": f"ACK {ev['status']} — response {ev.get('response_time_seconds', '?')}s",
            "actor": ev.get("operator_name") or ev.get("operator_id") or "OPERATOR",
            "before_state": {"ack_status": "PENDING"},
            "after_state": {"ack_status": ev["status"], "ack_code": ev.get("ack_code")},
            "occurred_at": ev["ack_timestamp"],
        })

    _bulk_insert(sb, rows)

    return success_response({
        "backfilled": len(rows),
        "breakdown": {
            "incident_transitions": sum(1 for r in rows if r["entity_type"] == "Incident"),
            "corrective_action_transitions": sum(1 for r in rows if r["entity_type"] == "CorrectiveAction"),
            "machine_state_changes": sum(1 for r in rows if r["entity_type"] == "Machine"),
            "acknowledgements": sum(1 for r in rows if r["entity_type"] == "Acknowledgement"),
        }
    })
