"""Incidents routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta, write_audit
from app.services.incident_engine import transition_incident, get_traceability_chain

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.route("/incidents")
def list_incidents():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("incident").select("*", count="exact")
    if request.args.get("plant_id"):
        query = query.eq("plant_id", request.args["plant_id"])
    if request.args.get("machine_id"):
        query = query.eq("machine_id", request.args["machine_id"])
    if request.args.get("severity"):
        query = query.eq("severity", request.args["severity"].upper())
    if request.args.get("status"):
        query = query.eq("status", request.args["status"].upper())
    if request.args.get("safety_zone_id"):
        query = query.eq("safety_zone_id", request.args["safety_zone_id"])
    if request.args.get("from_date"):
        query = query.gte("detected_at", request.args["from_date"])
    res = query.order("detected_at", desc=True).range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@incidents_bp.route("/incidents/<incident_id>")
def get_incident(incident_id):
    sb = get_supabase()
    res = sb.table("incident").select("*").eq("id", incident_id).execute()
    if not res.data:
        res = sb.table("incident").select("*").eq("incident_code", incident_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"Incident '{incident_id}' not found", 404)
    incident = res.data[0]

    machine = sb.table("machine").select("*").eq("id", incident["machine_id"]).execute()
    incident["machine"] = machine.data[0] if machine.data else None
    plant = sb.table("plant").select("*").eq("id", incident["plant_id"]).execute()
    incident["plant"] = plant.data[0] if plant.data else None
    if incident.get("safety_zone_id"):
        sz = sb.table("safety_zone").select("*").eq("id", incident["safety_zone_id"]).execute()
        incident["safety_zone"] = sz.data[0] if sz.data else None
    else:
        incident["safety_zone"] = None

    cas = sb.table("corrective_action").select("*").eq("incident_id", incident["id"]).execute()
    incident["corrective_actions"] = cas.data or []

    ia_res = sb.table("incident_alarm").select("alarm_event_id").eq("incident_id", incident["id"]).execute().data or []
    alarm_events = []
    for ia in ia_res:
        ae = sb.table("alarm_event").select("*").eq("id", ia["alarm_event_id"]).execute()
        if ae.data:
            alarm_events.append(ae.data[0])
    incident["alarm_events"] = alarm_events

    history = sb.table("incident_state_event").select("*").eq("incident_id", incident["id"]).order("transitioned_at").execute()
    incident["state_history"] = history.data or []

    return success_response(incident)


@incidents_bp.route("/incidents/<incident_id>/traceability")
def incident_traceability(incident_id):
    sb = get_supabase()
    res = sb.table("incident").select("*").eq("id", incident_id).execute()
    if not res.data:
        res = sb.table("incident").select("*").eq("incident_code", incident_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"Incident '{incident_id}' not found", 404)
    chain = get_traceability_chain(res.data[0])
    return success_response(chain)


@incidents_bp.route("/incidents/<incident_id>/transitions", methods=["POST"])
def transition_incident_route(incident_id):
    sb = get_supabase()
    res = sb.table("incident").select("*").eq("id", incident_id).execute()
    if not res.data:
        res = sb.table("incident").select("*").eq("incident_code", incident_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"Incident '{incident_id}' not found", 404)

    body = request.get_json(force=True, silent=True) or {}
    to_state = body.get("to_state", "").upper()
    if not to_state:
        return error_response("BAD_REQUEST", "to_state is required", 400)

    incident = res.data[0]
    result, err = transition_incident(incident, to_state, body.get("transitioned_by", "SYSTEM"), body.get("notes", ""))
    if err:
        return error_response("CONFLICT", err, 409)
    write_audit(sb, "Incident", incident["id"],
                f"STATE → {to_state} (from {incident['status']})",
                actor=body.get("transitioned_by", "SYSTEM"),
                before={"status": incident["status"]},
                after={"status": to_state, "notes": body.get("notes", "")})
    return success_response(result)
