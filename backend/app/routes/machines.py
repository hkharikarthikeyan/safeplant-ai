"""Machines routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta

machines_bp = Blueprint("machines", __name__)


@machines_bp.route("/machines")
def list_machines():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()

    query = sb.table("machine").select("*", count="exact")
    if request.args.get("plant_id"):
        query = query.eq("plant_id", request.args["plant_id"])
    if request.args.get("state"):
        query = query.eq("current_state", request.args["state"].upper())
    if request.args.get("search"):
        query = query.ilike("name", f"%{request.args['search']}%")

    sort = request.args.get("sort", "machine_code")
    if sort == "risk_score":
        query = query.order("risk_score", desc=True)
    else:
        query = query.order("machine_code")

    res = query.range(offset, offset + per_page - 1).execute()
    total = res.count or 0
    return success_response(res.data, meta=pagination_meta(page, per_page, total))


@machines_bp.route("/machines/<machine_id>")
def get_machine(machine_id):
    sb = get_supabase()
    res = sb.table("machine").select("*").eq("id", machine_id).execute()
    if not res.data:
        res = sb.table("machine").select("*").eq("machine_code", machine_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"Machine '{machine_id}' not found", 404)
    machine = res.data[0]

    machine["alarm_count"] = (
        sb.table("alarm_event").select("id", count="exact").eq("machine_id", machine["id"]).execute().count or 0
    )
    machine["incident_count"] = (
        sb.table("incident").select("id", count="exact").eq("machine_id", machine["id"]).execute().count or 0
    )
    plant_res = sb.table("plant").select("*").eq("id", machine["plant_id"]).execute()
    machine["plant"] = plant_res.data[0] if plant_res.data else None

    msz_res = sb.table("machine_safety_zone").select("safety_zone_id").eq("machine_id", machine["id"]).execute()
    zones = []
    for msz in (msz_res.data or []):
        z = sb.table("safety_zone").select("*").eq("id", msz["safety_zone_id"]).execute()
        if z.data:
            zones.append(z.data[0])
    machine["safety_zones"] = zones

    mi_res = sb.table("machine_interlock").select("interlock_id, is_required").eq("machine_id", machine["id"]).execute()
    interlocks = []
    for mi in (mi_res.data or []):
        il = sb.table("interlock").select("*").eq("id", mi["interlock_id"]).execute()
        if il.data:
            interlocks.append({**il.data[0], "is_required": mi["is_required"]})
    machine["interlocks"] = interlocks

    return success_response(machine)


@machines_bp.route("/machines/<machine_id>/timeline")
def machine_timeline(machine_id):
    sb = get_supabase()
    res = sb.table("machine").select("id").eq("id", machine_id).execute()
    if not res.data:
        res = sb.table("machine").select("id").eq("machine_code", machine_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"Machine '{machine_id}' not found", 404)
    mid = res.data[0]["id"]

    state_events = sb.table("machine_state_event").select("*").eq("machine_id", mid).order("occurred_at", desc=True).limit(100).execute().data or []
    alarm_events = sb.table("alarm_event").select("*").eq("machine_id", mid).order("alarm_timestamp", desc=True).limit(50).execute().data or []
    incidents = sb.table("incident").select("*").eq("machine_id", mid).order("detected_at", desc=True).limit(20).execute().data or []

    timeline = (
        [{"type": "STATE_CHANGE", "timestamp": e["occurred_at"], "data": e} for e in state_events] +
        [{"type": "ALARM", "timestamp": a["alarm_timestamp"], "data": a} for a in alarm_events] +
        [{"type": "INCIDENT", "timestamp": i["detected_at"], "data": i} for i in incidents]
    )
    timeline.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    return success_response(timeline[:100])
