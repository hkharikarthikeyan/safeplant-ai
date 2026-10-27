"""
Ground Truth Generator — Produces separate ground truth files.
Detection logic must NEVER read these files.
"""
import csv
import json
import logging
import os
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

GROUND_TRUTH_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ground_truth")

GROUND_TRUTH = [
    {"anomaly_id": "ANOM-CASE1-ACK-BEFORE-ALARM", "issue_type": "ACK_BEFORE_ALARM", "entity_type": "Acknowledgement", "entity_id": "PLACEHOLDER_CASE1", "related_entity_ids": ["PLACEHOLDER_ALARM1"], "rule_id": "RULE-ACK-TIMELINE", "expected_label": "ANOMALY", "expected_decision": "INVALID", "evidence_ids": ["PLACEHOLDER_CASE1"], "injection_reason": "Temporal inconsistency: ack timestamp before alarm timestamp", "severity": "HIGH"},
    {"anomaly_id": "ANOM-CASE2-IMPOSSIBLE-INTERLOCK", "issue_type": "IMPOSSIBLE_INTERLOCK_STATE", "entity_type": "InterlockStateEvent", "entity_id": "PLACEHOLDER_CASE2", "related_entity_ids": [], "rule_id": "RULE-001", "expected_label": "ANOMALY", "expected_decision": "UNSAFE_COMBINATION", "evidence_ids": ["PLACEHOLDER_CASE2"], "injection_reason": "Machine RUNNING with guard-door interlock DISENGAGED", "severity": "CRITICAL"},
    {"anomaly_id": "ANOM-CASE3-MISSING-INCIDENT-CONTEXT", "issue_type": "MISSING_INCIDENT_CONTEXT", "entity_type": "Incident", "entity_id": "PLACEHOLDER_CASE3", "related_entity_ids": [], "rule_id": "RULE-INC-TRACE", "expected_label": "ANOMALY", "expected_decision": "TRACEABILITY_FAILURE", "evidence_ids": ["PLACEHOLDER_CASE3"], "injection_reason": "Incident created without any triggering alarm events", "severity": "HIGH"},
    {"anomaly_id": "ANOM-CASE4-ALARM-FLOOD-REPLAY", "issue_type": "ALARM_REPLAY_DUPLICATE", "entity_type": "AlarmEvent", "entity_id": "PLACEHOLDER_CASE4", "related_entity_ids": [], "rule_id": "RULE-REPLAY-DETECT", "expected_label": "ANOMALY", "expected_decision": "REPLAY_DETECTED", "evidence_ids": ["PLACEHOLDER_CASE4"], "injection_reason": "Alarm event replayed with same source fingerprint but new ingestion ID", "severity": "MEDIUM"},
    {"anomaly_id": "ANOM-CASE5-ACTION-CLOSED-NO-VERIFY", "issue_type": "ACTION_CLOSED_WITHOUT_VERIFICATION", "entity_type": "CorrectiveAction", "entity_id": "PLACEHOLDER_CASE5", "related_entity_ids": [], "rule_id": "RULE-CA-VERIFY", "expected_label": "ANOMALY", "expected_decision": "LIFECYCLE_VIOLATION", "evidence_ids": ["PLACEHOLDER_CASE5"], "injection_reason": "Corrective action closure attempted without successful verification", "severity": "HIGH"},
]


def _resolve_entity_ids():
    try:
        sb = get_supabase()
        gt = [dict(r) for r in GROUND_TRUTH]

        case1 = sb.table("acknowledgement").select("id,alarm_event_id").eq("is_anomalous", True).limit(1).execute().data
        if case1:
            gt[0]["entity_id"] = case1[0]["id"]
            gt[0]["related_entity_ids"] = [case1[0]["alarm_event_id"]]
            gt[0]["evidence_ids"] = [case1[0]["id"]]

        case2 = sb.table("interlock_state_event").select("id,machine_id,interlock_id").eq("is_valid_combination", False).limit(1).execute().data
        if case2:
            gt[1]["entity_id"] = case2[0]["id"]
            gt[1]["related_entity_ids"] = [case2[0]["machine_id"], case2[0]["interlock_id"]]
            gt[1]["evidence_ids"] = [case2[0]["id"]]

        case3 = sb.table("incident").select("id").eq("has_missing_context", True).limit(1).execute().data
        if case3:
            gt[2]["entity_id"] = case3[0]["id"]
            gt[2]["evidence_ids"] = [case3[0]["id"]]

        case4 = sb.table("alarm_event").select("id,source_fingerprint").eq("is_replayed", True).limit(1).execute().data
        if case4:
            gt[3]["entity_id"] = case4[0]["id"]
            originals = sb.table("alarm_event").select("id").eq("source_fingerprint", case4[0]["source_fingerprint"]).eq("is_replayed", False).execute().data or []
            gt[3]["related_entity_ids"] = [o["id"] for o in originals]
            gt[3]["evidence_ids"] = [case4[0]["id"]] + [o["id"] for o in originals]

        case5 = sb.table("corrective_action").select("id,incident_id").eq("is_closed_without_verification", True).limit(1).execute().data
        if case5:
            gt[4]["entity_id"] = case5[0]["id"]
            gt[4]["related_entity_ids"] = [case5[0]["incident_id"]]
            gt[4]["evidence_ids"] = [case5[0]["id"]]

        return gt
    except Exception as e:
        logger.warning(f"Could not resolve ground truth IDs from DB: {e}")
        return GROUND_TRUTH


def generate_ground_truth():
    os.makedirs(GROUND_TRUTH_DIR, exist_ok=True)
    gt_data = _resolve_entity_ids()

    json_path = os.path.join(GROUND_TRUTH_DIR, "ground_truth.json")
    with open(json_path, "w") as f:
        json.dump(gt_data, f, indent=2)

    csv_path = os.path.join(GROUND_TRUTH_DIR, "ground_truth.csv")
    fieldnames = ["anomaly_id", "issue_type", "entity_type", "entity_id", "related_entity_ids", "rule_id", "expected_label", "expected_decision", "evidence_ids", "injection_reason", "severity"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in gt_data:
            r = dict(row)
            r["related_entity_ids"] = "|".join(r.get("related_entity_ids", []))
            r["evidence_ids"] = "|".join(r.get("evidence_ids", []))
            writer.writerow(r)

    logger.info(f"  Ground truth written: {json_path}, {csv_path}")
    return gt_data
