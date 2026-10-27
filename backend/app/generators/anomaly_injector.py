"""
Anomaly Injector — Injects exactly 5 mandatory negative scenarios.
"""
import hashlib
import logging
from datetime import datetime, timedelta
from app.extensions import get_supabase

logger = logging.getLogger(__name__)
GEN_START = datetime(2026, 10, 1, 0, 0, 0)


def _det_uuid(seed_str):
    h = hashlib.md5(seed_str.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-a{h[17:20]}-{h[20:32]}"


def _ts(dt):
    return dt.isoformat() if dt else None


def inject_all_anomalies(rng, alarm_events, interlocks, machines, incidents, cas, run_id=None):
    count = 0
    count += inject_case1_ack_before_alarm(rng, alarm_events, run_id)
    count += inject_case2_impossible_interlock(rng, machines, interlocks, run_id)
    count += inject_case3_incident_missing_context(rng, machines, run_id)
    count += inject_case4_alarm_flood_replay(rng, alarm_events, run_id)
    count += inject_case5_action_closed_without_verify(rng, incidents, run_id)
    return count


def inject_case1_ack_before_alarm(rng, alarm_events, run_id=None):
    sb = get_supabase()
    target = next((ae for ae in alarm_events if ae["severity"] == "CRITICAL"), alarm_events[0] if alarm_events else None)
    if not target:
        return 0
    alarm_dt = datetime.fromisoformat(target["alarm_timestamp"])
    ack_ts = alarm_dt - timedelta(minutes=rng.randint(5, 30))
    sb.table("acknowledgement").insert({
        "id": _det_uuid(f"case1-ack-{target['id']}"),
        "ack_code": f"ACK-{target['alarm_event_code']}-ANOMALY-01",
        "alarm_event_id": target["id"],
        "operator_id": "OP-ANOMALY-01",
        "operator_name": "Anomaly Operator (Case 1)",
        "ack_timestamp": _ts(ack_ts),
        "response_time_seconds": int((ack_ts - alarm_dt).total_seconds()),
        "status": "INVALID",
        "validation_result": "INVALID",
        "notes": "[ANOMALY-CASE1] Timestamp before alarm. Temporal inconsistency detected.",
        "is_anomalous": True,
        "created_at": _ts(ack_ts),
    }).execute()
    logger.info(f"  [CASE1] Injected ack-before-alarm anomaly")
    return 1


def inject_case2_impossible_interlock(rng, machines, interlocks, run_id=None):
    sb = get_supabase()
    if not interlocks or not machines:
        return 0
    target_il = next((il for il in interlocks if il["interlock_type"] == "GUARD_DOOR"), interlocks[0])
    target_machine = next((m for m in machines if m["plant_id"] == target_il["plant_id"]), machines[0])
    sb.table("interlock_state_event").insert({
        "id": _det_uuid(f"case2-ile-{target_il['id']}"),
        "interlock_id": target_il["id"],
        "machine_id": target_machine["id"],
        "from_state": "ENGAGED",
        "to_state": "DISENGAGED",
        "is_valid_combination": False,
        "unsafe_condition_code": "RULE-001",
        "occurred_at": _ts(GEN_START + timedelta(days=5, hours=10)),
        "generation_run_id": run_id,
    }).execute()
    logger.info(f"  [CASE2] Injected impossible interlock state")
    return 1


def inject_case3_incident_missing_context(rng, machines, run_id=None):
    sb = get_supabase()
    if not machines:
        return 0
    machine = machines[rng.randint(0, len(machines) - 1)]
    detected_at = GEN_START + timedelta(days=10)
    inc_id = _det_uuid("case3-incident")
    sb.table("incident").insert({
        "id": inc_id,
        "incident_code": "INC-2026-CASE3-ANOM",
        "plant_id": machine["plant_id"],
        "machine_id": machine["id"],
        "safety_zone_id": None,
        "severity": "HIGH",
        "status": "OPEN",
        "root_cause_category": "OPERATOR_ERROR",
        "description": "[ANOMALY-CASE3] Incident created without required triggering alarm evidence.",
        "assigned_engineer": "Eng. Marcus Obi",
        "detected_at": _ts(detected_at),
        "has_missing_context": True,
        "generation_run_id": run_id,
        "created_at": _ts(detected_at),
        "updated_at": _ts(detected_at),
    }).execute()
    sb.table("incident_state_event").insert({
        "id": _det_uuid("case3-ise-open"),
        "incident_id": inc_id,
        "from_state": None,
        "to_state": "OPEN",
        "transitioned_by": "SYSTEM",
        "notes": "[ANOMALY-CASE3] Incident opened without triggering alarm. Traceability failure.",
        "is_valid": True,
        "transitioned_at": _ts(detected_at),
    }).execute()
    logger.info(f"  [CASE3] Injected incident-missing-context")
    return 1


def inject_case4_alarm_flood_replay(rng, alarm_events, run_id=None):
    sb = get_supabase()
    if len(alarm_events) < 15:
        return 0
    from collections import Counter
    machine_counts = Counter(ae["machine_id"] for ae in alarm_events)
    target_machine_id = machine_counts.most_common(1)[0][0]
    targets = [ae for ae in alarm_events if ae["machine_id"] == target_machine_id][:3]
    rows = []
    for i, orig in enumerate(targets):
        orig_ingested = datetime.fromisoformat(orig["ingested_at"])
        rows.append({
            "id": _det_uuid(f"case4-replay-{orig['id']}-{i}"),
            "alarm_event_code": f"{orig['alarm_event_code']}-REPLAY-{i+1:02d}",
            "alarm_definition_id": orig["alarm_definition_id"],
            "machine_id": orig["machine_id"],
            "safety_zone_id": orig.get("safety_zone_id"),
            "trigger_value": orig["trigger_value"],
            "severity": orig["severity"],
            "status": orig["status"],
            "acknowledgement_status": "PENDING",
            "alarm_timestamp": orig["alarm_timestamp"],
            "cleared_timestamp": orig.get("cleared_timestamp"),
            "ingested_at": (orig_ingested + timedelta(seconds=rng.randint(1, 60))).isoformat(),
            "source_fingerprint": orig["source_fingerprint"],
            "is_replayed": True,
            "generation_run_id": run_id,
        })
    sb.table("alarm_event").insert(rows).execute()
    logger.info(f"  [CASE4] Injected {len(rows)} alarm replay records")
    return len(rows)


def inject_case5_action_closed_without_verify(rng, incidents, run_id=None):
    sb = get_supabase()
    if not incidents:
        return 0
    inc = incidents[0]
    ca_id = _det_uuid("case5-ca")
    sb.table("corrective_action").insert({
        "id": ca_id,
        "action_code": f"ACT-{inc['incident_code']}-CASE5",
        "incident_id": inc["id"],
        "description": "[ANOMALY-CASE5] Action with invalid closure attempt (no verification).",
        "assigned_engineer": "Eng. Priya Sharma",
        "priority": "HIGH",
        "status": "COMPLETED",
        "due_at": (GEN_START + timedelta(days=7)).isoformat(),
        "completed_at": (GEN_START + timedelta(days=5)).isoformat(),
        "is_closed_without_verification": True,
        "created_at": (GEN_START + timedelta(days=1)).isoformat(),
        "updated_at": (GEN_START + timedelta(days=5)).isoformat(),
    }).execute()
    sb.table("corrective_action_event").insert([
        {"id": _det_uuid("case5-cae-open"), "corrective_action_id": ca_id, "from_status": None, "to_status": "OPEN", "transitioned_by": "SYSTEM", "notes": "Created", "is_valid": True, "transitioned_at": (GEN_START + timedelta(days=1)).isoformat()},
        {"id": _det_uuid("case5-cae-prog"), "corrective_action_id": ca_id, "from_status": "OPEN", "to_status": "IN_PROGRESS", "transitioned_by": "Eng. Priya Sharma", "notes": "Work started", "is_valid": True, "transitioned_at": (GEN_START + timedelta(days=2)).isoformat()},
        {"id": _det_uuid("case5-cae-comp"), "corrective_action_id": ca_id, "from_status": "IN_PROGRESS", "to_status": "COMPLETED", "transitioned_by": "Eng. Priya Sharma", "notes": "Completed", "is_valid": True, "transitioned_at": (GEN_START + timedelta(days=5)).isoformat()},
        {"id": _det_uuid("case5-cae-invalid-close"), "corrective_action_id": ca_id, "from_status": "COMPLETED", "to_status": "CLOSED", "transitioned_by": "Eng. Priya Sharma", "notes": "[ANOMALY-CASE5] Invalid closure attempt without verification. Rejected.", "is_valid": False, "transitioned_at": (GEN_START + timedelta(days=6)).isoformat()},
    ]).execute()
    logger.info(f"  [CASE5] Injected action-closed-without-verify")
    return 1
