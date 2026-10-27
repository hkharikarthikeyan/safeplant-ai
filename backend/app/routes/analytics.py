"""Analytics routes"""
from flask import Blueprint, request
from datetime import datetime, timedelta, timezone
from app.extensions import get_supabase
from app.utils import success_response
from app.services.analytics_service import (
    get_machine_risk_scores,
    get_repeated_unsafe_conditions,
    get_acknowledgement_metrics,
    get_incident_metrics,
    get_action_metrics,
    get_shift_performance,
)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics/severity")
def severity_distribution():
    sb = get_supabase()
    rows = sb.table("alarm_event").select("severity").execute().data or []
    from collections import Counter
    counts = Counter(r["severity"] for r in rows)
    return success_response([{"severity": k, "count": v} for k, v in counts.items()])


@analytics_bp.route("/analytics/alarm-trends")
def alarm_trends():
    sb = get_supabase()
    days = int(request.args.get("days", 30))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = sb.table("alarm_event").select("alarm_timestamp, severity").gte("alarm_timestamp", since).execute().data or []
    trend_map = {}
    for row in rows:
        ts = row["alarm_timestamp"]
        date_str = ts[:10] if ts else None
        if not date_str:
            continue
        if date_str not in trend_map:
            trend_map[date_str] = {"date": date_str, "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0}
        sev = row.get("severity", "")
        if sev in trend_map[date_str]:
            trend_map[date_str][sev] += 1
            trend_map[date_str]["total"] += 1
    return success_response(sorted(trend_map.values(), key=lambda x: x["date"]))


@analytics_bp.route("/analytics/machine-risk")
def machine_risk():
    scores = get_machine_risk_scores(limit=int(request.args.get("limit", 10)))
    return success_response(scores)


@analytics_bp.route("/analytics/repeated-conditions")
def repeated_conditions():
    return success_response(get_repeated_unsafe_conditions())


@analytics_bp.route("/analytics/acknowledgements")
def ack_analytics():
    return success_response(get_acknowledgement_metrics())


@analytics_bp.route("/analytics/incidents")
def incident_analytics():
    return success_response(get_incident_metrics())


@analytics_bp.route("/analytics/actions")
def action_analytics():
    return success_response(get_action_metrics())


@analytics_bp.route("/analytics/shift-performance")
def shift_performance():
    return success_response(get_shift_performance())
