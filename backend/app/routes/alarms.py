"""Alarms routes"""
from flask import Blueprint, request
from datetime import datetime, timezone
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta
from app.services.alarm_engine import calculate_ack_status, detect_alarm_floods, detect_nuisance_clusters
import uuid

alarms_bp = Blueprint("alarms", __name__)


@alarms_bp.route("/alarms")
def list_alarms():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("alarm_event").select("*", count="exact")

    if request.args.get("machine_id"):
        query = query.eq("machine_id", request.args["machine_id"])
    if request.args.get("severity"):
        query = query.eq("severity", request.args["severity"].upper())
    if request.args.get("ack_status"):
        query = query.eq("acknowledgement_status", request.args["ack_status"].upper())
    if request.args.get("safety_zone_id"):
        query = query.eq("safety_zone_id", request.args["safety_zone_id"])
    if request.args.get("from_date"):
        query = query.gte("alarm_timestamp", request.args["from_date"])
    if request.args.get("to_date"):
        query = query.lte("alarm_timestamp", request.args["to_date"])
    if request.args.get("is_replayed") is not None:
        query = query.eq("is_replayed", request.args["is_replayed"].lower() == "true")

    direction = request.args.get("direction", "desc")
    sort = request.args.get("sort", "alarm_timestamp")
    query = query.order(sort, desc=(direction == "desc"))

    res = query.range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@alarms_bp.route("/alarms/<alarm_id>")
def get_alarm(alarm_id):
    sb = get_supabase()
    res = sb.table("alarm_event").select("*").eq("id", alarm_id).execute()
    if not res.data:
        res = sb.table("alarm_event").select("*").eq("alarm_event_code", alarm_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"AlarmEvent '{alarm_id}' not found", 404)
    alarm = res.data[0]
    machine = sb.table("machine").select("*").eq("id", alarm["machine_id"]).execute()
    alarm["machine"] = machine.data[0] if machine.data else None
    adef = sb.table("alarm_definition").select("*").eq("id", alarm["alarm_definition_id"]).execute()
    alarm["alarm_definition"] = adef.data[0] if adef.data else None
    acks = sb.table("acknowledgement").select("*").eq("alarm_event_id", alarm["id"]).execute()
    alarm["acknowledgements"] = acks.data or []
    return success_response(alarm)


@alarms_bp.route("/alarms/<alarm_id>/timeline")
def alarm_timeline(alarm_id):
    sb = get_supabase()
    res = sb.table("alarm_event").select("*").eq("id", alarm_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"AlarmEvent '{alarm_id}' not found", 404)
    alarm = res.data[0]
    acks = sb.table("acknowledgement").select("*").eq("alarm_event_id", alarm_id).order("ack_timestamp").execute().data or []
    ia_res = sb.table("incident_alarm").select("incident_id").eq("alarm_event_id", alarm_id).execute().data or []
    incidents = []
    for ia in ia_res:
        inc = sb.table("incident").select("*").eq("id", ia["incident_id"]).execute()
        if inc.data:
            incidents.append(inc.data[0])
    return success_response({"alarm": alarm, "acknowledgements": acks, "incidents": incidents})


@alarms_bp.route("/alarms/<alarm_id>/acknowledge", methods=["POST"])
def acknowledge_alarm(alarm_id):
    sb = get_supabase()
    res = sb.table("alarm_event").select("*").eq("id", alarm_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"AlarmEvent '{alarm_id}' not found", 404)
    alarm = res.data[0]

    body = request.get_json(force=True, silent=True) or {}
    operator_id = body.get("operator_id", "MANUAL")
    operator_name = body.get("operator_name", "Manual Operator")
    notes = body.get("notes", "")
    ack_time = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    existing = sb.table("acknowledgement").select("id", count="exact").eq("alarm_event_id", alarm_id).execute()
    count = existing.count or 0
    ack_code = f"ACK-{alarm['alarm_event_code']}-{count + 1:02d}"

    adef_res = sb.table("alarm_definition").select("ack_deadline_seconds").eq("id", alarm["alarm_definition_id"]).execute()
    deadline_seconds = adef_res.data[0]["ack_deadline_seconds"] if adef_res.data else 120

    alarm_ts = alarm["alarm_timestamp"]
    from datetime import datetime as dt
    ack_dt = dt.fromisoformat(ack_time)
    alarm_dt = dt.fromisoformat(alarm_ts) if isinstance(alarm_ts, str) else alarm_ts
    response_time = int((ack_dt - alarm_dt).total_seconds())

    if ack_dt < alarm_dt:
        status, validation_result, is_anomalous = "INVALID", "INVALID", True
    elif response_time <= deadline_seconds:
        status, validation_result, is_anomalous = "ON_TIME", "VALID", False
    else:
        status, validation_result, is_anomalous = "DELAYED", "VALID", False

    ack = {
        "id": str(uuid.uuid4()),
        "ack_code": ack_code,
        "alarm_event_id": alarm_id,
        "operator_id": operator_id,
        "operator_name": operator_name,
        "ack_timestamp": ack_time,
        "response_time_seconds": response_time,
        "status": status,
        "validation_result": validation_result,
        "notes": notes,
        "is_anomalous": is_anomalous,
    }
    sb.table("acknowledgement").insert(ack).execute()

    if not (ack_dt < alarm_dt) and alarm["acknowledgement_status"] == "PENDING":
        sb.table("alarm_event").update({"acknowledgement_status": status}).eq("id", alarm_id).execute()

    return success_response(ack, 201)


@alarms_bp.route("/alarms/floods")
def alarm_floods():
    return success_response(detect_alarm_floods())


@alarms_bp.route("/alarms/nuisance-clusters")
def nuisance_clusters():
    return success_response(detect_nuisance_clusters())
