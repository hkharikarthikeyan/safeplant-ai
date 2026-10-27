"""Plants routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta

plants_bp = Blueprint("plants", __name__)


@plants_bp.route("/plants")
def list_plants():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()

    query = sb.table("plant").select("*", count="exact")
    if request.args.get("status"):
        query = query.eq("status", request.args["status"].upper())
    if request.args.get("search"):
        query = query.ilike("name", f"%{request.args['search']}%")

    res = query.order("plant_code").range(offset, offset + per_page - 1).execute()
    total = res.count or 0
    return success_response(res.data, meta=pagination_meta(page, per_page, total))


@plants_bp.route("/plants/<plant_id>")
def get_plant(plant_id):
    sb = get_supabase()
    res = sb.table("plant").select("*").eq("id", plant_id).execute()
    if not res.data:
        res = sb.table("plant").select("*").eq("plant_code", plant_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"Plant '{plant_id}' not found", 404)
    plant = res.data[0]
    count_res = sb.table("machine").select("id", count="exact").eq("plant_id", plant["id"]).execute()
    plant["machine_count"] = count_res.count or 0
    return success_response(plant)
