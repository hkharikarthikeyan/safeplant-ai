"""Alarm Definitions routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta

alarm_definitions_bp = Blueprint("alarm_definitions", __name__)


@alarm_definitions_bp.route("/alarm-definitions")
def list_alarm_definitions():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    query = sb.table("alarm_definition").select("*", count="exact")
    if request.args.get("machine_id"):
        query = query.eq("machine_id", request.args["machine_id"])
    if request.args.get("severity"):
        query = query.eq("severity", request.args["severity"].upper())
    if request.args.get("category"):
        query = query.eq("category", request.args["category"].upper())
    res = query.order("alarm_code").range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@alarm_definitions_bp.route("/alarm-definitions/<def_id>")
def get_alarm_definition(def_id):
    sb = get_supabase()
    res = sb.table("alarm_definition").select("*").eq("id", def_id).execute()
    if not res.data:
        res = sb.table("alarm_definition").select("*").eq("alarm_code", def_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"AlarmDefinition '{def_id}' not found", 404)
    return success_response(res.data[0])
