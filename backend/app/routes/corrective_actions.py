"""Corrective Actions routes"""
from flask import Blueprint, request
from datetime import datetime, timezone
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta, write_audit
from app.services.incident_engine import transition_corrective_action
import uuid

corrective_actions_bp = Blueprint("corrective_actions", __name__)


@corrective_actions_bp.route("/corrective-actions")
def list_corrective_actions():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("corrective_action").select("*", count="exact")
    if request.args.get("incident_id"):
        query = query.eq("incident_id", request.args["incident_id"])
    if request.args.get("status"):
        query = query.eq("status", request.args["status"].upper())
    if request.args.get("priority"):
        query = query.eq("priority", request.args["priority"].upper())
    if request.args.get("overdue", "").lower() == "true":
        now = datetime.now(timezone.utc).isoformat()
        query = query.lt("due_at", now).not_.in_("status", ["VERIFIED", "CLOSED"])
    res = query.order("due_at").range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@corrective_actions_bp.route("/corrective-actions/<action_id>")
def get_corrective_action(action_id):
    sb = get_supabase()
    res = sb.table("corrective_action").select("*").eq("id", action_id).execute()
    if not res.data:
        res = sb.table("corrective_action").select("*").eq("action_code", action_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"CorrectiveAction '{action_id}' not found", 404)
    ca = res.data[0]
    inc = sb.table("incident").select("*").eq("id", ca["incident_id"]).execute()
    ca["incident"] = inc.data[0] if inc.data else None
    history = sb.table("corrective_action_event").select("*").eq("corrective_action_id", ca["id"]).order("transitioned_at").execute()
    ca["status_history"] = history.data or []
    now = datetime.now(timezone.utc).isoformat()
    ca["is_overdue"] = bool(ca.get("due_at") and ca["due_at"] < now and ca["status"] not in ("VERIFIED", "CLOSED"))
    return success_response(ca)


@corrective_actions_bp.route("/corrective-actions", methods=["POST"])
def create_corrective_action():
    sb = get_supabase()
    body = request.get_json(force=True, silent=True) or {}
    incident_id = body.get("incident_id")
    if not incident_id:
        return error_response("BAD_REQUEST", "incident_id is required", 400)
    inc_res = sb.table("incident").select("incident_code").eq("id", incident_id).execute()
    if not inc_res.data:
        return error_response("NOT_FOUND", f"Incident '{incident_id}' not found", 404)
    incident_code = inc_res.data[0]["incident_code"]

    count_res = sb.table("corrective_action").select("id", count="exact").eq("incident_id", incident_id).execute()
    count = (count_res.count or 0) + 1
    action_code = f"ACT-{incident_code}-{count:02d}"
    ca_id = str(uuid.uuid4())

    ca = {
        "id": ca_id,
        "action_code": action_code,
        "incident_id": incident_id,
        "description": body.get("description", ""),
        "assigned_engineer": body.get("assigned_engineer"),
        "priority": body.get("priority", "MEDIUM").upper(),
        "status": "OPEN",
        "due_at": body.get("due_at"),
        "is_closed_without_verification": False,
    }
    sb.table("corrective_action").insert(ca).execute()
    sb.table("corrective_action_event").insert({
        "id": str(uuid.uuid4()),
        "corrective_action_id": ca_id,
        "from_status": None,
        "to_status": "OPEN",
        "transitioned_by": "SYSTEM",
        "notes": "Created",
        "is_valid": True,
    }).execute()
    write_audit(sb, "CorrectiveAction", ca_id, "STATUS → OPEN (created)",
                actor="SYSTEM", before=None, after={"status": "OPEN", "action_code": action_code})
    return success_response(ca, 201)


@corrective_actions_bp.route("/corrective-actions/<action_id>/transitions", methods=["POST"])
def transition_action(action_id):
    sb = get_supabase()
    res = sb.table("corrective_action").select("*").eq("id", action_id).execute()
    if not res.data:
        res = sb.table("corrective_action").select("*").eq("action_code", action_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"CorrectiveAction '{action_id}' not found", 404)
    body = request.get_json(force=True, silent=True) or {}
    to_status = body.get("to_status", "").upper()
    if not to_status:
        return error_response("BAD_REQUEST", "to_status is required", 400)
    ca = res.data[0]
    result, err = transition_corrective_action(ca, to_status, body.get("transitioned_by", "SYSTEM"), body.get("notes", ""))
    if err:
        return error_response("CONFLICT", err, 409)
    write_audit(sb, "CorrectiveAction", ca["id"],
                f"STATUS → {to_status} (from {ca['status']})",
                actor=body.get("transitioned_by", "SYSTEM"),
                before={"status": ca["status"]},
                after={"status": to_status, "notes": body.get("notes", "")})
    return success_response(result)


@corrective_actions_bp.route("/corrective-actions/<action_id>/verify", methods=["POST"])
def verify_action(action_id):
    sb = get_supabase()
    res = sb.table("corrective_action").select("*").eq("id", action_id).execute()
    if not res.data:
        res = sb.table("corrective_action").select("*").eq("action_code", action_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"CorrectiveAction '{action_id}' not found", 404)
    ca = res.data[0]
    if ca["status"] != "VERIFICATION_PENDING":
        return error_response("CONFLICT", f"Cannot verify action in status '{ca['status']}'. Must be VERIFICATION_PENDING.", 409)

    body = request.get_json(force=True, silent=True) or {}
    result_val = body.get("result", "PASS").upper()
    transitioned_by = body.get("verified_by", "SYSTEM")
    notes = body.get("notes", "")
    now = datetime.now(timezone.utc).isoformat()
    new_status = "VERIFIED" if result_val == "PASS" else "IN_PROGRESS"

    sb.table("corrective_action").update({
        "verified_at": now,
        "verification_result": result_val,
        "status": new_status,
    }).eq("id", ca["id"]).execute()

    sb.table("corrective_action_event").insert({
        "id": str(uuid.uuid4()),
        "corrective_action_id": ca["id"],
        "from_status": "VERIFICATION_PENDING",
        "to_status": new_status,
        "transitioned_by": transitioned_by,
        "notes": notes,
        "is_valid": True,
    }).execute()

    write_audit(sb, "CorrectiveAction", ca["id"],
                f"VERIFIED → {new_status} (result: {result_val})",
                actor=transitioned_by,
                before={"status": "VERIFICATION_PENDING"},
                after={"status": new_status, "verification_result": result_val})

    ca.update({"verified_at": now, "verification_result": result_val, "status": new_status})
    return success_response(ca)
