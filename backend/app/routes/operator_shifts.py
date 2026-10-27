"""Operator Shifts routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta

operator_shifts_bp = Blueprint("operator_shifts", __name__)


@operator_shifts_bp.route("/operator-shifts")
def list_shifts():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("operator_shift").select("*", count="exact")
    if request.args.get("plant_id"):
        query = query.eq("plant_id", request.args["plant_id"])
    if request.args.get("shift_type"):
        query = query.eq("shift_type", request.args["shift_type"].upper())
    res = query.order("shift_start", desc=True).range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@operator_shifts_bp.route("/operator-shifts/<shift_id>")
def get_shift(shift_id):
    sb = get_supabase()
    res = sb.table("operator_shift").select("*").eq("id", shift_id).execute()
    if not res.data:
        res = sb.table("operator_shift").select("*").eq("shift_code", shift_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"OperatorShift '{shift_id}' not found", 404)
    shift = res.data[0]
    acks = sb.table("acknowledgement").select("*").eq("operator_shift_id", shift["id"]).limit(50).execute()
    shift["acknowledgements"] = acks.data or []
    return success_response(shift)
