"""Validation routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta
from app.services.validation_service import run_validation

validation_bp = Blueprint("validation", __name__)


@validation_bp.route("/validation/run", methods=["POST"])
def run_validation_route():
    body = request.get_json(force=True, silent=True) or {}
    report = run_validation(generation_run_id=body.get("generation_run_id"))
    return success_response(report, 201)


@validation_bp.route("/validation/reports")
def list_reports():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    res = sb.table("validation_run").select("*", count="exact").order("started_at", desc=True).range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@validation_bp.route("/validation/reports/<report_id>")
def get_report(report_id):
    sb = get_supabase()
    res = sb.table("validation_run").select("*").eq("id", report_id).execute()
    if not res.data:
        res = sb.table("validation_run").select("*").eq("run_code", report_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"ValidationRun '{report_id}' not found", 404)
    return success_response(res.data[0])
