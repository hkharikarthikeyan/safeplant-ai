"""Safety Zones routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta

safety_zones_bp = Blueprint("safety_zones", __name__)


@safety_zones_bp.route("/safety-zones")
def list_safety_zones():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("safety_zone").select("*", count="exact")
    if request.args.get("plant_id"):
        query = query.eq("plant_id", request.args["plant_id"])
    if request.args.get("hazard_level"):
        query = query.eq("hazard_level", request.args["hazard_level"].upper())
    res = query.order("zone_code").range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@safety_zones_bp.route("/safety-zones/<zone_id>")
def get_safety_zone(zone_id):
    sb = get_supabase()
    res = sb.table("safety_zone").select("*").eq("id", zone_id).execute()
    if not res.data:
        res = sb.table("safety_zone").select("*").eq("zone_code", zone_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"SafetyZone '{zone_id}' not found", 404)
    zone = res.data[0]
    msz_res = sb.table("machine_safety_zone").select("machine_id").eq("safety_zone_id", zone["id"]).execute()
    machines = []
    for msz in (msz_res.data or []):
        m = sb.table("machine").select("*").eq("id", msz["machine_id"]).execute()
        if m.data:
            machines.append(m.data[0])
    zone["machines"] = machines
    return success_response(zone)
