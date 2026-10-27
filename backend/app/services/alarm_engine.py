"""
Alarm Engine — acknowledgement deadline calculation, flood detection, nuisance cluster detection.
"""
import logging
from datetime import timedelta
from collections import defaultdict
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

ACK_DEADLINES = {"CRITICAL": 120, "HIGH": 300, "MEDIUM": 900, "LOW": 1800}
ALARM_FLOOD_COUNT = 10
ALARM_FLOOD_WINDOW_MINUTES = 5
NUISANCE_ALARM_COUNT = 3
NUISANCE_ALARM_WINDOW_HOURS = 1


def calculate_ack_status(alarm_timestamp, ack_timestamp, severity):
    if ack_timestamp is None:
        return "MISSING"
    deadline = ACK_DEADLINES.get(severity, 120)
    if ack_timestamp < alarm_timestamp:
        return "INVALID"
    response_secs = (ack_timestamp - alarm_timestamp).total_seconds()
    return "ON_TIME" if response_secs <= deadline else "DELAYED"


def detect_alarm_floods():
    sb = get_supabase()
    rows = sb.table("alarm_event").select("id, machine_id, alarm_timestamp, severity").order("machine_id").order("alarm_timestamp").execute().data or []

    machine_events = defaultdict(list)
    for row in rows:
        machine_events[row["machine_id"]].append(row)

    floods = []
    window_minutes = ALARM_FLOOD_WINDOW_MINUTES

    for machine_id, events in machine_events.items():
        if len(events) < ALARM_FLOOD_COUNT:
            continue
        i = 0
        while i < len(events):
            t0 = events[i]["alarm_timestamp"]
            if not t0:
                i += 1
                continue
            from datetime import datetime
            t0_dt = datetime.fromisoformat(t0)
            window_end_dt = t0_dt + timedelta(minutes=window_minutes)
            window_events = [e for e in events[i:] if e["alarm_timestamp"] and datetime.fromisoformat(e["alarm_timestamp"]) <= window_end_dt]
            if len(window_events) >= ALARM_FLOOD_COUNT:
                floods.append({
                    "machine_id": machine_id,
                    "window_start": t0,
                    "window_end": window_end_dt.isoformat(),
                    "alarm_count": len(window_events),
                    "alarm_ids": [e["id"] for e in window_events],
                    "rule_id": "RULE-009",
                    "severity": "MEDIUM",
                    "description": f"Alarm flood: {len(window_events)} alarms in {window_minutes} minutes",
                })
                i += len(window_events)
            else:
                i += 1
    return floods


def detect_nuisance_clusters():
    sb = get_supabase()
    rows = sb.table("alarm_event").select("id, alarm_definition_id, machine_id, alarm_timestamp").order("alarm_definition_id").order("alarm_timestamp").execute().data or []

    def_events = defaultdict(list)
    for row in rows:
        def_events[row["alarm_definition_id"]].append(row)

    clusters = []
    window_hours = NUISANCE_ALARM_WINDOW_HOURS

    for def_id, events in def_events.items():
        if len(events) < NUISANCE_ALARM_COUNT:
            continue
        i = 0
        while i < len(events):
            t0 = events[i]["alarm_timestamp"]
            if not t0:
                i += 1
                continue
            from datetime import datetime
            t0_dt = datetime.fromisoformat(t0)
            window_end_dt = t0_dt + timedelta(hours=window_hours)
            window_events = [e for e in events[i:] if e["alarm_timestamp"] and datetime.fromisoformat(e["alarm_timestamp"]) <= window_end_dt]
            if len(window_events) >= NUISANCE_ALARM_COUNT:
                clusters.append({
                    "alarm_definition_id": def_id,
                    "machine_id": events[i]["machine_id"],
                    "window_start": t0,
                    "window_end": window_end_dt.isoformat(),
                    "alarm_count": len(window_events),
                    "alarm_ids": [e["id"] for e in window_events],
                    "rule_id": "RULE-005",
                    "severity": "MEDIUM",
                    "description": f"Nuisance cluster: {len(window_events)} repeat alarms within 1 hour",
                })
                i += len(window_events)
            else:
                i += 1
    return clusters
