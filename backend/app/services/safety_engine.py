"""
Safety Rule Engine — SafePlant AI
Evaluates machine state + interlock combinations against documented safety rules.
Separated from HTTP routes and UI code.
"""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Machine state machine
# ---------------------------------------------------------------------------
VALID_MACHINE_STATES = {
    "OFFLINE", "IDLE", "STARTING", "RUNNING",
    "STOPPING", "MAINTENANCE", "FAULT", "EMERGENCY_STOP",
}

VALID_MACHINE_TRANSITIONS = {
    "OFFLINE": {"IDLE"},
    "IDLE": {"STARTING", "MAINTENANCE", "OFFLINE"},
    "STARTING": {"RUNNING", "FAULT", "EMERGENCY_STOP"},
    "RUNNING": {"STOPPING", "FAULT", "EMERGENCY_STOP", "MAINTENANCE"},
    "STOPPING": {"IDLE", "FAULT"},
    "MAINTENANCE": {"IDLE", "OFFLINE"},
    "FAULT": {"MAINTENANCE", "IDLE", "EMERGENCY_STOP"},
    "EMERGENCY_STOP": {"MAINTENANCE", "OFFLINE"},
}

# ---------------------------------------------------------------------------
# Interlock states
# ---------------------------------------------------------------------------
VALID_INTERLOCK_STATES = {"ENGAGED", "DISENGAGED", "FAULT", "BYPASSED"}

# ---------------------------------------------------------------------------
# Safety rules
# ---------------------------------------------------------------------------
SAFETY_RULES = [
    {
        "rule_id": "RULE-001",
        "description": "Machine RUNNING with guard-door interlock DISENGAGED",
        "severity": "CRITICAL",
        "machine_states": {"RUNNING"},
        "interlock_states": {"DISENGAGED"},
        "interlock_type": "GUARD_DOOR",
        "is_required": True,
    },
    {
        "rule_id": "RULE-002",
        "description": "Machine RUNNING with emergency-stop interlock ENGAGED",
        "severity": "CRITICAL",
        "machine_states": {"RUNNING"},
        "interlock_states": {"ENGAGED"},
        "interlock_type": "EMERGENCY_STOP",
        "is_required": True,
    },
    {
        "rule_id": "RULE-003",
        "description": "Machine RUNNING with required safety interlock BYPASSED",
        "severity": "HIGH",
        "machine_states": {"RUNNING"},
        "interlock_states": {"BYPASSED"},
        "interlock_type": None,  # Any type
        "is_required": True,
    },
    {
        "rule_id": "RULE-010",
        "description": "Machine RUNNING with required interlock in FAULT state",
        "severity": "CRITICAL",
        "machine_states": {"RUNNING"},
        "interlock_states": {"FAULT"},
        "interlock_type": None,
        "is_required": True,
    },
]


def is_valid_machine_transition(from_state: str, to_state: str) -> bool:
    """Return True if the machine state transition is valid per the documented state machine."""
    allowed = VALID_MACHINE_TRANSITIONS.get(from_state, set())
    return to_state in allowed


def evaluate_machine_interlock_safety(machine, machine_interlocks):
    """
    Evaluate all safety rules for a machine + its interlock states.
    Returns list of triggered rule evaluations.
    """
    triggered = []

    for rule in SAFETY_RULES:
        if machine.current_state not in rule["machine_states"]:
            continue

        for mi in machine_interlocks:
            interlock = mi.interlock
            if not interlock:
                continue
            if rule["is_required"] and not mi.is_required:
                continue
            if rule["interlock_type"] and interlock.interlock_type != rule["interlock_type"]:
                continue
            if interlock.current_state not in rule["interlock_states"]:
                continue

            triggered.append({
                "rule_id": rule["rule_id"],
                "description": rule["description"],
                "machine_id": machine.id,
                "machine_code": machine.machine_code,
                "machine_state": machine.current_state,
                "interlock_id": interlock.id,
                "interlock_code": interlock.interlock_code,
                "interlock_state": interlock.current_state,
                "severity": rule["severity"],
                "detection_timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "explanation": (
                    f"Machine '{machine.machine_code}' is in state '{machine.current_state}' "
                    f"while interlock '{interlock.interlock_code}' (type: {interlock.interlock_type}) "
                    f"is in state '{interlock.current_state}'. "
                    f"Rule: {rule['description']}"
                ),
            })

    return triggered


def evaluate_repeated_unsafe_conditions(machine_id, incidents, window_days=30, threshold=2):
    """
    Detect repeated unsafe conditions for a machine.
    Returns flagged machine+zone combinations.
    """
    from collections import Counter
    key_counts = Counter()
    for inc in incidents:
        if inc.machine_id != machine_id:
            continue
        key = (inc.machine_id, inc.safety_zone_id)
        key_counts[key] += 1

    flagged = []
    for (mid, szid), count in key_counts.items():
        if count >= threshold:
            flagged.append({
                "machine_id": mid,
                "safety_zone_id": szid,
                "incident_count": count,
                "rule_id": "RULE-008",
                "severity": "MEDIUM",
                "description": f"Machine has {count} incidents in same safety zone within {window_days} days",
            })
    return flagged
