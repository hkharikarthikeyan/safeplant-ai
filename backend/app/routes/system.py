"""System health routes"""
from flask import Blueprint, jsonify
from app.extensions import get_supabase

system_bp = Blueprint("system", __name__)


@system_bp.route("/health")
def health():
    try:
        get_supabase().table("plant").select("id").limit(1).execute()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "SafePlant AI",
        "version": "1.0.0",
        "database": db_status,
    })
