"""
Validation Service — 20 automated integrity checks.
"""
import logging
import uuid
from datetime import datetime, timezone
from app.extensions import get_supabase

logger = logging.getLogger(__name__)


def _sb():
    return get_supabase()


def _check(name, query_fn, expected_anomaly=False):
    """Run a single validation check and return a result dict."""
    try:
        passed, failed, evidence = query_fn()
        return {
            "check": name,
            "passed": passed,
            "failed": failed,
            "is_expected_anomaly": expected_anomaly,
            "status": "PASS" if failed == 0 else ("EXPECTED_ANOMALY" if expected_anomaly else "FAIL"),
            "evidence_sample": evidence[:5] if evidence else [],
        }
    except Exception as e:
        logger.error(f"Validation check '{name}' raised: {e}")
        return {
            "check": name,
            "passed": 0,
            "failed": 1,
            "is_expected_anomaly": False,
            "status": "ERROR",
            "evidence_sample": [str(e)],
        }


def run_validation(generation_run_id=None):
    """Run all validation checks and persist a ValidationRun record."""
    sb = _sb()
    run_id = str(uuid.uuid4())
    run_code = f"VAL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    started_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    sb.table("validation_run").insert({
        "id": run_id,
        "run_code": run_code,
        "generation_run_id": generation_run_id,
        "started_at": started_at,
    }).execute()

    checks = [
        # 1. PK uniqueness
        _check("PK_UNIQUENESS_ALARMS", lambda: _pk_uniqueness("alarm_event", "id")),
        _check("PK_UNIQUENESS_INCIDENTS", lambda: _pk_uniqueness("incident", "id")),
        _check("PK_UNIQUENESS_MACHINES", lambda: _pk_uniqueness("machine", "id")),

        # 2. FK integrity
        _check("FK_MACHINE_TO_PLANT", lambda: _fk_integrity("machine", "plant_id", "plant")),
        _check("FK_ALARM_TO_MACHINE", lambda: _fk_integrity("alarm_event", "machine_id", "machine")),
        _check("FK_INCIDENT_TO_MACHINE", lambda: _fk_integrity("incident", "machine_id", "machine")),
        _check("FK_ACK_TO_ALARM", lambda: _fk_integrity("acknowledgement", "alarm_event_id", "alarm_event")),
        _check("FK_CA_TO_INCIDENT", lambda: _fk_integrity("corrective_action", "incident_id", "incident")),
        _check("FK_INCIDENT_ALARM_BRIDGE", lambda: _incident_alarm_bridge_integrity()),

        # 3. Required field completeness
        _check("REQUIRED_ALARM_TIMESTAMP", lambda: _required_field("alarm_event", "alarm_timestamp")),
        _check("REQUIRED_INCIDENT_DESCRIPTION", lambda: _required_field("incident", "description")),

        # 4. Enum values
        _check("ENUM_ALARM_SEVERITY", lambda: _enum_check("alarm_event", "severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])),
        _check("ENUM_MACHINE_STATE", lambda: _enum_check("machine", "current_state", [
            "OFFLINE", "IDLE", "STARTING", "RUNNING", "STOPPING", "MAINTENANCE", "FAULT", "EMERGENCY_STOP"
        ])),
        _check("ENUM_INCIDENT_STATUS", lambda: _enum_check("incident", "status", [
            "OPEN", "INVESTIGATING", "ACTION_REQUIRED", "VERIFICATION_PENDING", "CLOSED", "REOPENED"
        ])),

        # 5. Timestamp ordering (ack before alarm is EXPECTED anomaly)
        _check("TIMESTAMP_ACK_AFTER_ALARM", lambda: _ack_timestamp_ordering(), expected_anomaly=True),

        # 6. Lifecycle checks
        _check("MACHINE_LIFECYCLE_TRANSITIONS", lambda: _flag_count("machine_state_event", "is_valid_transition", False), expected_anomaly=True),
        _check("INCIDENT_LIFECYCLE_TRANSITIONS", lambda: _flag_count("incident_state_event", "is_valid", False)),
        _check("CA_LIFECYCLE_TRANSITIONS", lambda: _flag_count("corrective_action_event", "is_valid", False), expected_anomaly=True),

        # 7. Duplicate alarm fingerprints (replayed = EXPECTED)
        _check("ALARM_REPLAY_FINGERPRINTS", lambda: _flag_count("alarm_event", "is_replayed", True), expected_anomaly=True),

        # 8. Missing incident context (EXPECTED anomaly)
        _check("INCIDENT_MISSING_CONTEXT", lambda: _flag_count("incident", "has_missing_context", True), expected_anomaly=True),

        # 9. Interlock impossible combinations (EXPECTED anomaly)
        _check("INTERLOCK_IMPOSSIBLE_COMBINATIONS", lambda: _flag_count("interlock_state_event", "is_valid_combination", False), expected_anomaly=True),

        # 10. Corrective action closed without verification (EXPECTED anomaly)
        _check("CA_CLOSED_WITHOUT_VERIFY", lambda: _flag_count("corrective_action", "is_closed_without_verification", True), expected_anomaly=True),
    ]

    passed = sum(1 for c in checks if c["status"] in ("PASS", "EXPECTED_ANOMALY"))
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    expected_anomalies = sum(1 for c in checks if c["is_expected_anomaly"] and c["failed"] > 0)
    unexpected = sum(1 for c in checks if c["status"] == "FAIL")
    overall = "PASS" if unexpected == 0 else "PARTIAL_FAIL"

    completed_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    sb.table("validation_run").update({
        "completed_at": completed_at,
        "overall_status": overall,
        "check_results": checks,
        "total_checks": len(checks),
        "passed_checks": passed,
        "failed_checks": failed,
        "expected_anomalies": expected_anomalies,
        "unexpected_failures": unexpected,
    }).eq("id", run_id).execute()

    return {
        "id": run_id,
        "run_code": run_code,
        "generation_run_id": generation_run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "overall_status": overall,
        "check_results": checks,
        "total_checks": len(checks),
        "passed_checks": passed,
        "failed_checks": failed,
        "expected_anomalies": expected_anomalies,
        "unexpected_failures": unexpected,
    }


# ---------------------------------------------------------------------------
# Individual check implementations
# ---------------------------------------------------------------------------

def _fetch_all(table, fields="id"):
    """Fetch all rows bypassing Supabase's 1000-row default limit."""
    sb = _sb()
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        batch = sb.table(table).select(fields).range(offset, offset + limit - 1).execute().data or []
        all_rows.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return all_rows


def _fk_integrity(child_table, fk_field, parent_table):
    children = _fetch_all(child_table, f"id,{fk_field}")
    parent_ids = {r["id"] for r in _fetch_all(parent_table)}
    orphans = [r["id"] for r in children if r.get(fk_field) and r[fk_field] not in parent_ids]
    return len(children) - len(orphans), len(orphans), orphans


def _incident_alarm_bridge_integrity():
    rows = _fetch_all("incident_alarm", "id,incident_id,alarm_event_id")
    incident_ids = {r["id"] for r in _fetch_all("incident")}
    alarm_ids = {r["id"] for r in _fetch_all("alarm_event")}
    failed = {r["id"] for r in rows if r["incident_id"] not in incident_ids or r["alarm_event_id"] not in alarm_ids}
    return len(rows) - len(failed), len(failed), list(failed)


def _pk_uniqueness(table, field):
    rows = _fetch_all(table, field)
    total = len(rows)
    distinct = len({r[field] for r in rows})
    return distinct, total - distinct, []


def _required_field(table, field):
    rows = _fetch_all(table, field)
    missing = sum(1 for r in rows if r.get(field) is None)
    return len(rows) - missing, missing, []


def _enum_check(table, field, allowed):
    rows = _fetch_all(table, field)
    invalid = sum(1 for r in rows if r.get(field) not in allowed)
    return len(rows) - invalid, invalid, []


def _ack_timestamp_ordering():
    acks = _fetch_all("acknowledgement", "id,alarm_event_id,ack_timestamp")
    alarms = {r["id"]: r["alarm_timestamp"] for r in _fetch_all("alarm_event", "id,alarm_timestamp")}
    invalid = [a["id"] for a in acks if alarms.get(a["alarm_event_id"]) and a["ack_timestamp"] < alarms[a["alarm_event_id"]]]
    return len(acks) - len(invalid), len(invalid), invalid


def _flag_count(table, field, flag_value):
    rows = _fetch_all(table, field)
    flagged = sum(1 for r in rows if r.get(field) == flag_value)
    return len(rows) - flagged, flagged, []
