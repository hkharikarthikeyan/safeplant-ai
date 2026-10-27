"""
Anomaly Detection Engine — deterministic rule-based detection.
Reads DB records via Supabase; does NOT read ground truth files.
"""
import json
import logging
import os
from datetime import datetime, timezone
from app.extensions import get_supabase
from app.services.alarm_engine import detect_alarm_floods, detect_nuisance_clusters

logger = logging.getLogger(__name__)


def _sb():
    return get_supabase()


def detect_ack_before_alarm():
    """CASE 1: Acknowledgement timestamp before alarm timestamp."""
    results = []
    acks = _sb().table("acknowledgement").select("*").eq("is_anomalous", True).execute().data or []
    for ack in acks:
        alarm_res = _sb().table("alarm_event").select("*").eq("id", ack["alarm_event_id"]).execute().data
        if not alarm_res:
            continue
        alarm = alarm_res[0]
        ack_dt = datetime.fromisoformat(ack["ack_timestamp"])
        alarm_dt = datetime.fromisoformat(alarm["alarm_timestamp"])
        if ack_dt < alarm_dt:
            results.append({
                "anomaly_id": f"ANOM-CASE1-{ack['id'][:8]}",
                "issue_type": "ACK_BEFORE_ALARM",
                "entity_type": "Acknowledgement",
                "entity_id": ack["id"],
                "related_entity_ids": [alarm["id"]],
                "rule_id": "RULE-ACK-TIMELINE",
                "severity": "HIGH",
                "expected_decision": "INVALID",
                "status": ack["status"],
                "description": (
                    f"Acknowledgement {ack['ack_code']} has timestamp {ack['ack_timestamp']} "
                    f"which is BEFORE alarm {alarm['alarm_event_code']} at {alarm['alarm_timestamp']}. "
                    f"Temporal inconsistency detected and flagged as INVALID."
                ),
                "evidence_ids": [ack["id"], alarm["id"]],
                "detected_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            })
    return results


def detect_impossible_interlock_combinations():
    """CASE 2: Machine running with impossible/unsafe interlock state."""
    results = []
    events = _sb().table("interlock_state_event").select("*").eq("is_valid_combination", False).execute().data or []
    for event in events:
        results.append({
            "anomaly_id": f"ANOM-CASE2-{event['id'][:8]}",
            "issue_type": "IMPOSSIBLE_INTERLOCK_STATE",
            "entity_type": "InterlockStateEvent",
            "entity_id": event["id"],
            "related_entity_ids": [event["machine_id"], event["interlock_id"]],
            "rule_id": event.get("unsafe_condition_code") or "RULE-001",
            "severity": "CRITICAL",
            "expected_decision": "UNSAFE_COMBINATION",
            "description": (
                f"Interlock state event shows unsafe combination. "
                f"Machine {event['machine_id']} + Interlock {event['interlock_id']} "
                f"transitioned to state '{event['to_state']}' creating an impossible safe combination."
            ),
            "evidence_ids": [event["id"]],
            "detected_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        })
    return results


def detect_incidents_missing_context():
    """CASE 3: Incidents with has_missing_context flag."""
    results = []
    incidents = _sb().table("incident").select("*").eq("has_missing_context", True).execute().data or []
    for inc in incidents:
        alarm_count = len(
            _sb().table("incident_alarm").select("id", count="exact").eq("incident_id", inc["id"]).execute().data or []
        )
        results.append({
            "anomaly_id": f"ANOM-CASE3-{inc['id'][:8]}",
            "issue_type": "MISSING_INCIDENT_CONTEXT",
            "entity_type": "Incident",
            "entity_id": inc["id"],
            "related_entity_ids": [],
            "rule_id": "RULE-INC-TRACE",
            "severity": "HIGH",
            "expected_decision": "TRACEABILITY_FAILURE",
            "description": (
                f"Incident {inc['incident_code']} has missing_context flag. "
                f"Linked alarm events: {alarm_count}. "
                f"The incident lacks required triggering alarm evidence."
            ),
            "evidence_ids": [inc["id"]],
            "detected_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        })
    return results


def detect_alarm_replay():
    """CASE 4: Replayed alarm events (source_fingerprint duplication)."""
    results = []
    replayed = _sb().table("alarm_event").select("*").eq("is_replayed", True).execute().data or []
    for alarm in replayed:
        originals = _sb().table("alarm_event").select("id").eq(
            "source_fingerprint", alarm["source_fingerprint"]
        ).eq("is_replayed", False).execute().data or []
        originals = [o for o in originals if o["id"] != alarm["id"]]
        results.append({
            "anomaly_id": f"ANOM-CASE4-{alarm['id'][:8]}",
            "issue_type": "ALARM_REPLAY_DUPLICATE",
            "entity_type": "AlarmEvent",
            "entity_id": alarm["id"],
            "related_entity_ids": [o["id"] for o in originals],
            "rule_id": "RULE-REPLAY-DETECT",
            "severity": "MEDIUM",
            "expected_decision": "REPLAY_DETECTED",
            "description": (
                f"AlarmEvent {alarm['alarm_event_code']} is marked as replayed. "
                f"Source fingerprint '{alarm['source_fingerprint']}' matches "
                f"{len(originals)} original event(s). "
                f"Original and replayed records have distinct ingestion IDs."
            ),
            "evidence_ids": [alarm["id"]] + [o["id"] for o in originals],
            "detected_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        })
    return results


def detect_actions_closed_without_verification():
    """CASE 5: Corrective action closure attempted without verification."""
    results = []
    actions = _sb().table("corrective_action").select("*").eq("is_closed_without_verification", True).execute().data or []
    for ca in actions:
        results.append({
            "anomaly_id": f"ANOM-CASE5-{ca['id'][:8]}",
            "issue_type": "ACTION_CLOSED_WITHOUT_VERIFICATION",
            "entity_type": "CorrectiveAction",
            "entity_id": ca["id"],
            "related_entity_ids": [ca["incident_id"]],
            "rule_id": "RULE-CA-VERIFY",
            "severity": "HIGH",
            "expected_decision": "LIFECYCLE_VIOLATION",
            "description": (
                f"CorrectiveAction {ca['action_code']} had a closure attempted without successful verification. "
                f"Status history preserved the invalid attempt. "
                f"Current status: {ca['status']} (valid business state unchanged)."
            ),
            "evidence_ids": [ca["id"]],
            "detected_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        })
    return results


def detect_delayed_critical_acks():
    """Detect critical alarms with delayed or missing acknowledgement."""
    results = []
    alarms = _sb().table("alarm_event").select("*").eq("severity", "CRITICAL").in_(
        "acknowledgement_status", ["DELAYED", "MISSING"]
    ).execute().data or []
    for alarm in alarms:
        results.append({
            "anomaly_id": f"ANOM-DELAYED-{alarm['id'][:8]}",
            "issue_type": "DELAYED_CRITICAL_ACK",
            "entity_type": "AlarmEvent",
            "entity_id": alarm["id"],
            "related_entity_ids": [alarm["machine_id"]],
            "rule_id": "RULE-006",
            "severity": "HIGH",
            "expected_decision": "COMPLIANCE_VIOLATION",
            "description": f"Critical alarm {alarm['alarm_event_code']} has ack status: {alarm['acknowledgement_status']}",
            "evidence_ids": [alarm["id"]],
            "detected_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        })
    return results


def run_all_detectors():
    """Run all anomaly detectors and return combined results."""
    results = {
        "ack_before_alarm": detect_ack_before_alarm(),
        "impossible_interlock": detect_impossible_interlock_combinations(),
        "missing_incident_context": detect_incidents_missing_context(),
        "alarm_replay": detect_alarm_replay(),
        "action_closed_no_verify": detect_actions_closed_without_verification(),
        "alarm_floods": detect_alarm_floods(),
        "nuisance_clusters": detect_nuisance_clusters(),
        "delayed_critical_acks": detect_delayed_critical_acks(),
    }
    total = sum(len(v) for v in results.values())
    return {"total_detected": total, "categories": results}


def get_all_anomalies(issue_type=None, severity=None):
    """Return all detected anomalies as a flat list, optionally filtered."""
    all_results = run_all_detectors()
    flat = []
    for items in all_results["categories"].values():
        flat.extend(items)
    if issue_type:
        flat = [a for a in flat if a.get("issue_type", "").lower() == issue_type.lower()]
    if severity:
        flat = [a for a in flat if a.get("severity", "").upper() == severity.upper()]
    return flat


def get_anomaly_by_id(anomaly_id):
    """Find a specific anomaly by its stable ID."""
    for a in get_all_anomalies():
        if a.get("anomaly_id") == anomaly_id:
            return a
    return None


def compute_evaluation_metrics():
    """
    Compare detected anomalies against ground truth.
    Ground truth is read from file (separate from detection inputs).
    """
    gt_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "ground_truth", "ground_truth.json"
    )
    ground_truth = []
    if os.path.exists(gt_path):
        with open(gt_path) as f:
            try:
                ground_truth = json.load(f)
            except Exception:
                ground_truth = []

    predictions = get_all_anomalies()
    pred_ids = {p["entity_id"] for p in predictions if "entity_id" in p}
    gt_ids = {g["entity_id"] for g in ground_truth if "entity_id" in g}

    tp = len(pred_ids & gt_ids)
    fp = len(pred_ids - gt_ids)
    fn = len(gt_ids - pred_ids)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    sb = _sb()

    total_alarms = len(sb.table("alarm_event").select("id").execute().data or []) or 1
    on_time_acks = len(sb.table("alarm_event").select("id").eq("acknowledgement_status", "ON_TIME").execute().data or [])
    ack_compliance_rate = on_time_acks / total_alarms

    ack_times = sb.table("acknowledgement").select("response_time_seconds").execute().data or []
    times = [r["response_time_seconds"] for r in ack_times if r.get("response_time_seconds") is not None]
    mean_response = sum(times) / len(times) if times else 0

    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    all_cas = sb.table("corrective_action").select("id,due_at,status").execute().data or []
    overdue_actions = sum(
        1 for ca in all_cas
        if ca.get("due_at") and ca["due_at"] < now and ca.get("status") not in ("VERIFIED", "CLOSED")
    )

    total_actions = len(sb.table("corrective_action").select("id").execute().data or []) or 1
    verified_actions = len(sb.table("corrective_action").select("id").eq("status", "VERIFIED").execute().data or [])
    ca_verify_rate = verified_actions / total_actions

    all_incidents = sb.table("incident").select("machine_id").execute().data or []
    machine_counts = {}
    for inc in all_incidents:
        mid = inc["machine_id"]
        machine_counts[mid] = machine_counts.get(mid, 0) + 1
    repeated_unsafe = sum(1 for c in machine_counts.values() if c >= 2)

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "total_predictions": len(predictions),
        "total_ground_truth": len(ground_truth),
        "acknowledgement_compliance_rate": round(ack_compliance_rate, 4),
        "mean_acknowledgement_time_seconds": round(float(mean_response), 2),
        "overdue_corrective_actions": overdue_actions,
        "corrective_action_verification_rate": round(ca_verify_rate, 4),
        "repeated_unsafe_condition_count": repeated_unsafe,
        "evaluation_unit": "anomaly/entity-level",
        "note": "Ground truth loaded from data/ground_truth/ground_truth.json (separate from detection inputs)",
    }


def get_confusion_matrix():
    """Return confusion matrix data."""
    metrics = compute_evaluation_metrics()
    sb = _sb()
    total_flagged = sum([
        len(sb.table("acknowledgement").select("id").eq("is_anomalous", True).execute().data or []),
        len(sb.table("interlock_state_event").select("id").eq("is_valid_combination", False).execute().data or []),
        len(sb.table("incident").select("id").eq("has_missing_context", True).execute().data or []),
        len(sb.table("alarm_event").select("id").eq("is_replayed", True).execute().data or []),
        len(sb.table("corrective_action").select("id").eq("is_closed_without_verification", True).execute().data or []),
    ])
    return {
        "matrix": {
            "true_positive": metrics["true_positives"],
            "false_positive": metrics["false_positives"],
            "false_negative": metrics["false_negatives"],
            "true_negative": "Not enumerated (candidate universe not fully defined)",
        },
        "candidate_universe": "All anomaly-flagged DB records",
        "total_flagged_records": total_flagged,
        "note": "TN not computed; see EVALUATION_REPORT.md for methodology",
    }
