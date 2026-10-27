"""Interlocks routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta

interlocks_bp = Blueprint("interlocks", __name__)


@interlocks_bp.route("/interlocks")
def list_interlocks():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("interlock").select("*", count="exact")
    if request.args.get("plant_id"):
        query = query.eq("plant_id", request.args["plant_id"])
    if request.args.get("state"):
        query = query.eq("current_state", request.args["state"].upper())
    res = query.order("interlock_code").range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@interlocks_bp.route("/interlocks/<interlock_id>")
def get_interlock(interlock_id):
    sb = get_supabase()
    res = sb.table("interlock").select("*").eq("id", interlock_id).execute()
    if not res.data:
        res = sb.table("interlock").select("*").eq("interlock_code", interlock_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"Interlock '{interlock_id}' not found", 404)
    interlock = res.data[0]
    mi_res = sb.table("machine_interlock").select("machine_id, is_required").eq("interlock_id", interlock["id"]).execute()
    machines = []
    for mi in (mi_res.data or []):
        m = sb.table("machine").select("*").eq("id", mi["machine_id"]).execute()
        if m.data:
            machines.append({**m.data[0], "is_required": mi["is_required"]})
    interlock["machines"] = machines
    return success_response(interlock)
