"""Data generation routes"""
from flask import Blueprint, request
from app.extensions import get_supabase
from app.utils import success_response, error_response, get_pagination_params, pagination_meta
from app.services.generation_service import trigger_generation

generator_bp = Blueprint("generator", __name__)


@generator_bp.route("/generator/run", methods=["POST"])
def run_generator():
    sb = get_supabase()
    body = request.get_json(force=True, silent=True) or {}
    mode = body.get("mode", "starter").lower()
    seed = int(body.get("seed", 20261022))

    if mode not in ("starter", "full"):
        return error_response("BAD_REQUEST", "mode must be 'starter' or 'full'", 400)

    running = sb.table("generation_run").select("id").eq("status", "RUNNING").execute()
    if running.data:
        return error_response("CONFLICT", "A generation run is already in progress", 409)

    run = trigger_generation(mode=mode, seed=seed, config_overrides=body)
    return success_response(run, 201)


@generator_bp.route("/generator/runs")
def list_runs():
    sb = get_supabase()
    page, per_page, offset = get_pagination_params()
    res = sb.table("generation_run").select("*", count="exact").order("started_at", desc=True).range(offset, offset + per_page - 1).execute()
    return success_response(res.data, meta=pagination_meta(page, per_page, res.count or 0))


@generator_bp.route("/generator/runs/<run_id>")
def get_run(run_id):
    sb = get_supabase()
    res = sb.table("generation_run").select("*").eq("id", run_id).execute()
    if not res.data:
        res = sb.table("generation_run").select("*").eq("run_code", run_id).execute()
    if not res.data:
        return error_response("NOT_FOUND", f"GenerationRun '{run_id}' not found", 404)
    return success_response(res.data[0])
