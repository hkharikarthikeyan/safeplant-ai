"""
Incident Engine — lifecycle transitions, traceability chain.
"""
import logging
import uuid
from datetime import datetime, timezone
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    "OPEN": {"INVESTIGATING"},
    "INVESTIGATING": {"ACTION_REQUIRED", "REOPENED"},
    "ACTION_REQUIRED": {"VERIFICATION_PENDING"},
    "VERIFICATION_PENDING": {"CLOSED", "REOPENED"},
    "CLOSED": {"REOPENED"},
    "REOPENED": {"INVESTIGATING"},
}

VALID_CA_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS"},
    "IN_PROGRESS": {"COMPLETED", "OPEN"},
    "COMPLETED": {"VERIFICATION_PENDING"},
    "VERIFICATION_PENDING": {"VERIFIED", "IN_PROGRESS"},
    "VERIFIED": {"CLOSED"},
    "CLOSED": {"REOPENED"},
    "REOPENED": {"IN_PROGRESS"},
}


def transition_incident(incident, to_state, transitioned_by="SYSTEM", notes=""):
    sb = get_supabase()
    from_state = incident["status"]
    allowed = VALID_TRANSITIONS.get(from_state, set())
    is_valid = to_state in allowed

    sb.table("incident_state_event").insert({
        "id": str(uuid.uuid4()),
        "incident_id": incident["id"],
        "from_state": from_state,
        "to_state": to_state,
        "transitioned_by": transitioned_by,
        "notes": notes,
        "is_valid": is_valid,
    }).execute()

    if not is_valid:
        return None, f"Invalid transition from '{from_state}' to '{to_state}'. Allowed: {allowed}"

    updates = {"status": to_state}
    if to_state == "CLOSED":
        updates["closed_at"] = datetime.now(timezone.utc).isoformat()

    sb.table("incident").update(updates).eq("id", incident["id"]).execute()
    incident.update(updates)
    return incident, None


def transition_corrective_action(ca, to_status, transitioned_by="SYSTEM", notes=""):
    sb = get_supabase()
    from_status = ca["status"]
    allowed = VALID_CA_TRANSITIONS.get(from_status, set())
    is_valid = to_status in allowed

    if to_status == "CLOSED" and ca.get("verification_result") != "PASS":
        sb.table("corrective_action").update({"is_closed_without_verification": True}).eq("id", ca["id"]).execute()
        ca["is_closed_without_verification"] = True
        is_valid = False
        notes = f"[ANOMALY-CASE5] Closure attempted without verification. {notes}"

    sb.table("corrective_action_event").insert({
        "id": str(uuid.uuid4()),
        "corrective_action_id": ca["id"],
        "from_status": from_status,
        "to_status": to_status,
        "transitioned_by": transitioned_by,
        "notes": notes,
        "is_valid": is_valid,
    }).execute()

    if not is_valid:
        return None, f"Invalid transition from '{from_status}' to '{to_status}'. Allowed: {allowed}"

    sb.table("corrective_action").update({"status": to_status}).eq("id", ca["id"]).execute()
    ca["status"] = to_status
    return ca, None


def get_traceability_chain(incident):
    sb = get_supabase()

    ia_res = sb.table("incident_alarm").select("alarm_event_id").eq("incident_id", incident["id"]).execute().data or []
    alarm_events = []
    for ia in ia_res:
        ae = sb.table("alarm_event").select("*").eq("id", ia["alarm_event_id"]).execute()
        if ae.data:
            alarm_events.append(ae.data[0])

    state_history = sb.table("incident_state_event").select("*").eq("incident_id", incident["id"]).order("transitioned_at").execute().data or []

    cas_res = sb.table("corrective_action").select("*").eq("incident_id", incident["id"]).execute().data or []
    corrective_actions = []
    for ca in cas_res:
        ca["status_history"] = sb.table("corrective_action_event").select("*").eq("corrective_action_id", ca["id"]).order("transitioned_at").execute().data or []
        corrective_actions.append(ca)

    plant = sb.table("plant").select("*").eq("id", incident["plant_id"]).execute()
    machine = sb.table("machine").select("*").eq("id", incident["machine_id"]).execute()
    safety_zone = None
    if incident.get("safety_zone_id"):
        sz = sb.table("safety_zone").select("*").eq("id", incident["safety_zone_id"]).execute()
        safety_zone = sz.data[0] if sz.data else None

    has_triggering_context = len(alarm_events) > 0
    return {
        "incident": incident,
        "plant": plant.data[0] if plant.data else None,
        "machine": machine.data[0] if machine.data else None,
        "safety_zone": safety_zone,
        "triggering_alarms": alarm_events,
        "has_triggering_context": has_triggering_context,
        "missing_context_flag": incident.get("has_missing_context", False),
        "state_history": state_history,
        "corrective_actions": corrective_actions,
        "traceability_complete": has_triggering_context and not incident.get("has_missing_context", False),
    }
