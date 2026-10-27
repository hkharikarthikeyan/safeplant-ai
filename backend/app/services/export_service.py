"""
Export Service — CSV, JSON exports.
"""
import csv
import io
import json
from datetime import datetime, timezone
from app.extensions import get_supabase


def _sb():
    return get_supabase()


def export_alarms_csv():
    """Export all alarm events as CSV."""
    alarms = _sb().table("alarm_event").select("*").order("alarm_timestamp").execute().data or []
    output = io.StringIO()
    fieldnames = [
        "alarm_event_code", "machine_id", "severity", "status",
        "acknowledgement_status", "alarm_timestamp", "cleared_timestamp",
        "source_fingerprint", "is_replayed",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for alarm in alarms:
        writer.writerow({k: alarm.get(k, "") for k in fieldnames})
    filename = f"alarms_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
    return output.getvalue(), filename


def export_incidents_csv():
    """Export all incidents as CSV."""
    incidents = _sb().table("incident").select("*").order("detected_at").execute().data or []
    output = io.StringIO()
    fieldnames = [
        "incident_code", "plant_id", "machine_id", "safety_zone_id",
        "severity", "status", "root_cause_category", "assigned_engineer",
        "detected_at", "closed_at", "has_missing_context",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for inc in incidents:
        writer.writerow({k: inc.get(k, "") for k in fieldnames})
    filename = f"incidents_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
    return output.getvalue(), filename


def export_anomalies_csv():
    """Export detected anomalies as CSV."""
    from app.services.anomaly_engine import get_all_anomalies
    anomalies = get_all_anomalies()
    output = io.StringIO()
    fieldnames = [
        "anomaly_id", "issue_type", "entity_type", "entity_id",
        "rule_id", "severity", "expected_decision", "description", "detected_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for a in anomalies:
        writer.writerow({k: a.get(k, "") for k in fieldnames})
    filename = f"anomalies_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
    return output.getvalue(), filename


def export_validation_json():
    """Export latest validation report as JSON."""
    res = _sb().table("validation_run").select("*").order("started_at", desc=True).limit(1).execute().data
    if res:
        content = json.dumps(res[0], indent=2, default=str)
    else:
        content = json.dumps({"message": "No validation run found"})
    filename = f"validation_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
    return content, filename
