"""Dashboard summary routes"""
from flask import Blueprint
from app.extensions import get_supabase
from app.utils import success_response
from datetime import datetime, timedelta, timezone

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard/summary")
def summary():
    sb = get_supabase()

    total_plants = sb.table("plant").select("id", count="exact").execute().count or 0
    total_machines = sb.table("machine").select("id", count="exact").execute().count or 0
    total_alarms = sb.table("alarm_event").select("id", count="exact").execute().count or 0
    critical_alarms = sb.table("alarm_event").select("id", count="exact").eq("severity", "CRITICAL").execute().count or 0
    open_incidents = sb.table("incident").select("id", count="exact").in_("status", ["OPEN", "INVESTIGATING", "ACTION_REQUIRED"]).execute().count or 0
    delayed_acks = sb.table("acknowledgement").select("id", count="exact").eq("status", "DELAYED").execute().count or 0
    missing_acks = sb.table("alarm_event").select("id", count="exact").eq("acknowledgement_status", "MISSING").execute().count or 0
    pending_actions = sb.table("corrective_action").select("id", count="exact").in_("status", ["OPEN", "IN_PROGRESS"]).execute().count or 0

    # Repeated unsafe: machines with ≥2 incidents
    all_incidents = sb.table("incident").select("machine_id").execute().data or []
    from collections import Counter
    machine_counts = Counter(i["machine_id"] for i in all_incidents)
    repeated_unsafe = sum(1 for c in machine_counts.values() if c >= 2)

    recent_critical = sb.table("alarm_event").select("*").eq("severity", "CRITICAL").order("alarm_timestamp", desc=True).limit(10).execute().data or []

    return success_response({
        "kpis": {
            "total_plants": total_plants,
            "total_machines": total_machines,
            "total_alarms": total_alarms,
            "critical_alarms": critical_alarms,
            "open_incidents": open_incidents,
            "delayed_acknowledgements": delayed_acks + missing_acks,
            "repeated_unsafe_conditions": repeated_unsafe,
            "pending_corrective_actions": pending_actions,
        },
        "recent_critical_events": recent_critical,
    })


@dashboard_bp.route("/dashboard/trends")
def trends():
    sb = get_supabase()
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    rows = sb.table("alarm_event").select("alarm_timestamp, severity").gte("alarm_timestamp", thirty_days_ago).execute().data or []

    trend_map = {}
    for row in rows:
        ts = row["alarm_timestamp"]
        date_str = ts[:10] if ts else None
        if not date_str:
            continue
        if date_str not in trend_map:
            trend_map[date_str] = {"date": date_str, "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        sev = row.get("severity", "")
        if sev in trend_map[date_str]:
            trend_map[date_str][sev] += 1

    return success_response(sorted(trend_map.values(), key=lambda x: x["date"]))
