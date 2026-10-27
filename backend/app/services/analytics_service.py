"""
Analytics Service — risk scoring, repeated conditions, shift performance, etc.
"""
import logging
from datetime import datetime, timezone, timedelta
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

RISK_WEIGHTS = {
    "critical_alarms": 10,
    "high_incidents": 8,
    "repeated_unsafe": 6,
    "delayed_acks": 4,
    "overdue_actions": 5,
    "interlock_violations": 7,
}
NORMALIZATION_FACTOR = sum(RISK_WEIGHTS.values()) * 5


def compute_machine_risk_score(machine_id, window_days=30):
    sb = get_supabase()
    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    now = datetime.now(timezone.utc).isoformat()

    critical_alarms = sb.table("alarm_event").select("id", count="exact").eq("machine_id", machine_id).eq("severity", "CRITICAL").gte("alarm_timestamp", since).execute().count or 0
    high_incidents = sb.table("incident").select("id", count="exact").eq("machine_id", machine_id).in_("severity", ["CRITICAL", "HIGH"]).gte("detected_at", since).execute().count or 0

    all_incidents = sb.table("incident").select("id", count="exact").eq("machine_id", machine_id).execute().count or 0
    repeated_unsafe = max(0, all_incidents - 1)

    delayed_acks = sb.table("alarm_event").select("id", count="exact").eq("machine_id", machine_id).in_("acknowledgement_status", ["DELAYED", "MISSING"]).gte("alarm_timestamp", since).execute().count or 0

    # Overdue actions: join via incidents
    inc_ids_res = sb.table("incident").select("id").eq("machine_id", machine_id).execute().data or []
    inc_ids = [r["id"] for r in inc_ids_res]
    overdue_actions = 0
    if inc_ids:
        overdue_actions = sb.table("corrective_action").select("id", count="exact").in_("incident_id", inc_ids).not_.in_("status", ["VERIFIED", "CLOSED"]).lt("due_at", now).execute().count or 0

    raw_score = (
        critical_alarms * RISK_WEIGHTS["critical_alarms"] +
        high_incidents * RISK_WEIGHTS["high_incidents"] +
        repeated_unsafe * RISK_WEIGHTS["repeated_unsafe"] +
        delayed_acks * RISK_WEIGHTS["delayed_acks"] +
        overdue_actions * RISK_WEIGHTS["overdue_actions"]
    )
    score = min(100.0, (raw_score / NORMALIZATION_FACTOR) * 100)

    return {
        "machine_id": machine_id,
        "risk_score": round(score, 2),
        "contributing_factors": {
            "critical_alarms": critical_alarms,
            "high_incidents": high_incidents,
            "repeated_unsafe_conditions": repeated_unsafe,
            "delayed_acknowledgements": delayed_acks,
            "overdue_corrective_actions": overdue_actions,
        },
    }


def get_machine_risk_scores(limit=10):
    sb = get_supabase()
    machine_ids = [r["id"] for r in (sb.table("machine").select("id").execute().data or [])]
    scores = [compute_machine_risk_score(mid) for mid in machine_ids]
    scores.sort(key=lambda x: x["risk_score"], reverse=True)
    for s in scores:
        sb.table("machine").update({"risk_score": s["risk_score"]}).eq("id", s["machine_id"]).execute()
    return scores[:limit]


def get_repeated_unsafe_conditions():
    sb = get_supabase()
    rows = sb.table("incident").select("machine_id, safety_zone_id").execute().data or []
    from collections import Counter
    counts = Counter((r["machine_id"], r["safety_zone_id"]) for r in rows)
    results = []
    for (machine_id, safety_zone_id), count in counts.items():
        if count < 2:
            continue
        machine = sb.table("machine").select("machine_code").eq("id", machine_id).execute()
        results.append({
            "machine_id": machine_id,
            "machine_code": machine.data[0]["machine_code"] if machine.data else None,
            "safety_zone_id": safety_zone_id,
            "incident_count": count,
            "rule_id": "RULE-008",
            "severity": "MEDIUM",
        })
    return results


def get_acknowledgement_metrics():
    sb = get_supabase()
    rows = sb.table("alarm_event").select("acknowledgement_status, severity").execute().data or []
    total = len(rows) or 1
    from collections import Counter
    ack_counts = Counter(r["acknowledgement_status"] for r in rows)

    mean_res = sb.table("acknowledgement").select("response_time_seconds").execute().data or []
    times = [r["response_time_seconds"] for r in mean_res if r["response_time_seconds"] is not None]
    mean_response = sum(times) / len(times) if times else 0

    by_severity = []
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        sev_rows = [r for r in rows if r["severity"] == sev]
        sev_total = len(sev_rows) or 1
        sev_on_time = sum(1 for r in sev_rows if r["acknowledgement_status"] == "ON_TIME")
        by_severity.append({"severity": sev, "total": sev_total, "on_time": sev_on_time, "compliance_rate": round(sev_on_time / sev_total, 4)})

    on_time = ack_counts.get("ON_TIME", 0)
    return {
        "total_alarms": total,
        "on_time": on_time,
        "delayed": ack_counts.get("DELAYED", 0),
        "missing": ack_counts.get("MISSING", 0),
        "invalid": ack_counts.get("INVALID", 0),
        "pending": ack_counts.get("PENDING", 0),
        "compliance_rate": round(on_time / total, 4),
        "mean_response_time_seconds": round(float(mean_response), 2),
        "by_severity": by_severity,
    }


def get_incident_metrics():
    sb = get_supabase()
    rows = sb.table("incident").select("status, severity, detected_at, closed_at").execute().data or []
    total = len(rows)
    from collections import Counter
    status_counts = Counter(r["status"] for r in rows)
    severity_counts = Counter(r["severity"] for r in rows)
    closed = status_counts.get("CLOSED", 0)

    durations = []
    for r in rows:
        if r["status"] == "CLOSED" and r.get("closed_at") and r.get("detected_at"):
            try:
                d = (datetime.fromisoformat(r["closed_at"]) - datetime.fromisoformat(r["detected_at"])).total_seconds()
                durations.append(d)
            except Exception:
                pass
    mean_closure = round(sum(durations) / len(durations), 2) if durations else None

    return {
        "total": total,
        "closed": closed,
        "open_rate": round((total - closed) / max(total, 1), 4),
        "mean_closure_time_seconds": mean_closure,
        "by_status": [{"status": k, "count": v} for k, v in status_counts.items()],
        "by_severity": [{"severity": k, "count": v} for k, v in severity_counts.items()],
    }


def get_action_metrics():
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    rows = sb.table("corrective_action").select("status, due_at").execute().data or []
    total = len(rows)
    from collections import Counter
    status_counts = Counter(r["status"] for r in rows)
    overdue = sum(1 for r in rows if r.get("due_at") and r["due_at"] < now and r["status"] not in ("VERIFIED", "CLOSED"))
    verified = status_counts.get("VERIFIED", 0)
    closed = status_counts.get("CLOSED", 0)
    return {
        "total": total,
        "verified": verified,
        "closed": closed,
        "overdue": overdue,
        "verification_rate": round(verified / max(total, 1), 4),
        "by_status": [{"status": k, "count": v} for k, v in status_counts.items()],
    }


def get_shift_performance():
    sb = get_supabase()
    results = []
    for shift_type in ["DAY", "EVENING", "NIGHT"]:
        shift_ids_res = sb.table("operator_shift").select("id").eq("shift_type", shift_type).execute().data or []
        shift_ids = [r["id"] for r in shift_ids_res]
        if not shift_ids:
            continue
        acks = sb.table("acknowledgement").select("status").in_("operator_shift_id", shift_ids).execute().data or []
        total_acks = len(acks)
        on_time = sum(1 for a in acks if a["status"] == "ON_TIME")
        results.append({
            "shift_type": shift_type,
            "total_acknowledgements": total_acks,
            "on_time": on_time,
            "compliance_rate": round(on_time / max(total_acks, 1), 4),
        })
    return results
