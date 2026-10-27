"""
Master Generator — Deterministic synthetic data for SafePlant AI.
Fixed seed: 20261022
Generation period: 2026-10-01 to 2026-10-30 (30 days)
"""

import random
import hashlib
import logging
from datetime import datetime, timedelta
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

GEN_START = datetime(2026, 10, 1, 0, 0, 0)
GEN_END = datetime(2026, 10, 30, 23, 59, 59)

MODE_CONFIG = {
    "starter": {"plants": 1, "machines_per_plant": 5, "alarm_definitions": 20, "alarm_events": 1000},
    "full": {"plants": 4, "machines_per_plant": 15, "alarm_definitions": 200, "alarm_events": 50000},
}

MACHINE_TYPES = ["COMPRESSOR", "PUMP", "REACTOR", "CONVEYOR", "FURNACE", "MIXER", "SEPARATOR", "HEAT_EXCHANGER", "BOILER", "TURBINE"]
MANUFACTURERS = ["Siemens", "ABB", "Honeywell", "Emerson", "GE Industrial"]
ALARM_CATEGORIES = ["TEMPERATURE", "PRESSURE", "FLOW", "VIBRATION", "LEVEL", "GAS_DETECTION", "ELECTRICAL"]
ALARM_SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
SEVERITY_WEIGHTS = [0.05, 0.15, 0.40, 0.40]
ZONE_TYPES = ["HAZARDOUS", "CONTROLLED", "RESTRICTED", "MAINTENANCE"]
HAZARD_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
INTERLOCK_TYPES = ["GUARD_DOOR", "EMERGENCY_STOP", "PRESSURE_RELIEF", "TEMPERATURE_LIMIT", "FLOW_SWITCH"]
SHIFT_TYPES = ["DAY", "EVENING", "NIGHT"]
ROOT_CAUSES = ["EQUIPMENT_FAILURE", "OPERATOR_ERROR", "PROCESS_DEVIATION", "MAINTENANCE_LAPSE", "DESIGN_DEFICIENCY", "EXTERNAL_FACTOR"]
MACHINE_STATES = ["OFFLINE", "IDLE", "STARTING", "RUNNING", "STOPPING", "MAINTENANCE", "FAULT", "EMERGENCY_STOP"]
VALID_TRANSITIONS = {
    "OFFLINE": ["IDLE"],
    "IDLE": ["STARTING", "MAINTENANCE", "OFFLINE"],
    "STARTING": ["RUNNING", "FAULT", "EMERGENCY_STOP"],
    "RUNNING": ["STOPPING", "FAULT", "EMERGENCY_STOP", "MAINTENANCE"],
    "STOPPING": ["IDLE", "FAULT"],
    "MAINTENANCE": ["IDLE", "OFFLINE"],
    "FAULT": ["MAINTENANCE", "IDLE", "EMERGENCY_STOP"],
    "EMERGENCY_STOP": ["MAINTENANCE", "OFFLINE"],
}
ACK_DEADLINES = {"CRITICAL": 120, "HIGH": 300, "MEDIUM": 900, "LOW": 1800}
ENGINEERS = ["Dr. Sarah Chen", "Eng. Marcus Obi", "Eng. Priya Sharma", "Dr. James Kowalski", "Eng. Fatima Al-Hassan", "Dr. Liu Wei", "Eng. Carlos Mendez", "Eng. Anika Patel"]
OPERATORS = [("OP-001", "John Miller"), ("OP-002", "Sandra Lee"), ("OP-003", "David Park"), ("OP-004", "Maria Santos"), ("OP-005", "Tom Hughes"), ("OP-006", "Yuki Tanaka"), ("OP-007", "Ahmed Hassan"), ("OP-008", "Elena Popov")]

PLANT_DATA = [
    ("Alpha Chemical Complex", "Houston, TX", "North America"),
    ("Beta Refinery East", "Rotterdam, Netherlands", "Europe"),
    ("Gamma Processing Hub", "Singapore", "Asia-Pacific"),
    ("Delta Energy Plant", "Abu Dhabi, UAE", "Middle East"),
]


def _det_uuid(seed_str):
    h = hashlib.md5(seed_str.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-a{h[17:20]}-{h[20:32]}"


def _unit_for_category(category):
    return {"TEMPERATURE": "°C", "PRESSURE": "bar", "FLOW": "m³/h", "VIBRATION": "mm/s", "LEVEL": "m", "GAS_DETECTION": "ppm", "ELECTRICAL": "V"}.get(category, "unit")


def _ts(dt):
    return dt.isoformat() if dt else None


def _bulk_insert(sb, table, rows, chunk=500):
    for i in range(0, len(rows), chunk):
        sb.table(table).insert(rows[i:i + chunk]).execute()


def generate_all(mode="starter", seed=20261022, run_id=None):
    sb = get_supabase()
    cfg = MODE_CONFIG.get(mode, MODE_CONFIG["starter"])
    rng = random.Random(seed)
    counts = {}

    logger.info(f"Starting {mode} generation with seed={seed}")

    # STEP 1: Plants
    plants = []
    for i, (name, location, region) in enumerate(PLANT_DATA[:cfg["plants"]]):
        plants.append({
            "id": _det_uuid(f"plant-{i}"),
            "plant_code": f"PLT-{i+1:04d}",
            "name": name,
            "location": location,
            "region": region,
            "timezone": "UTC",
            "status": "ACTIVE",
            "is_active": True,
            "created_at": _ts(GEN_START),
            "updated_at": _ts(GEN_START),
        })
    _bulk_insert(sb, "plant", plants)
    counts["plants"] = len(plants)
    logger.info(f"  Generated {len(plants)} plants")

    # STEP 2: Machines
    machines = []
    machine_counter = 0
    for pi, plant in enumerate(plants):
        for mi in range(cfg["machines_per_plant"]):
            machine_counter += 1
            mtype = rng.choice(MACHINE_TYPES)
            machines.append({
                "id": _det_uuid(f"machine-{machine_counter}"),
                "machine_code": f"MCH-{pi+1:04d}-{mi+1:04d}",
                "plant_id": plant["id"],
                "name": f"{mtype.replace('_', ' ').title()} Unit {mi+1:02d}",
                "machine_type": mtype,
                "model_number": f"MDL-{rng.randint(100, 999)}",
                "manufacturer": rng.choice(MANUFACTURERS),
                "current_state": "IDLE",
                "risk_score": 0.0,
                "status": "ACTIVE",
                "commissioned_at": _ts(GEN_START - timedelta(days=rng.randint(100, 1000))),
                "is_active": True,
                "created_at": _ts(GEN_START),
                "updated_at": _ts(GEN_START),
            })
    _bulk_insert(sb, "machine", machines)
    counts["machines"] = len(machines)
    logger.info(f"  Generated {len(machines)} machines")

    # STEP 3: Safety Zones
    safety_zones = []
    for pi, plant in enumerate(plants):
        for zi in range(4):
            safety_zones.append({
                "id": _det_uuid(f"zone-{pi}-{zi}"),
                "zone_code": f"SAFE-{plant['plant_code']}-{zi+1:03d}",
                "plant_id": plant["id"],
                "name": f"{ZONE_TYPES[zi % len(ZONE_TYPES)].replace('_', ' ').title()} Zone {zi+1}",
                "zone_type": ZONE_TYPES[zi % len(ZONE_TYPES)],
                "hazard_level": HAZARD_LEVELS[zi % len(HAZARD_LEVELS)],
                "description": f"Safety zone {zi+1} at {plant['name']}",
                "is_active": True,
                "created_at": _ts(GEN_START),
            })
    _bulk_insert(sb, "safety_zone", safety_zones)
    counts["safety_zones"] = len(safety_zones)
    logger.info(f"  Generated {len(safety_zones)} safety zones")

    # STEP 4: Interlocks
    interlocks = []
    for pi, plant in enumerate(plants):
        for ii in range(5):
            itype = INTERLOCK_TYPES[ii % len(INTERLOCK_TYPES)]
            interlocks.append({
                "id": _det_uuid(f"interlock-{pi}-{ii}"),
                "interlock_code": f"INTLK-{plant['plant_code']}-{ii+1:03d}",
                "plant_id": plant["id"],
                "name": f"{itype.replace('_', ' ').title()} {ii+1}",
                "interlock_type": itype,
                "current_state": "ENGAGED",
                "description": f"Safety interlock {ii+1} at {plant['name']}",
                "is_safety_critical": True,
                "is_active": True,
                "created_at": _ts(GEN_START),
            })
    _bulk_insert(sb, "interlock", interlocks)
    counts["interlocks"] = len(interlocks)
    logger.info(f"  Generated {len(interlocks)} interlocks")

    # STEP 5: Machine-Zone Associations
    plant_zones = {}
    for zone in safety_zones:
        plant_zones.setdefault(zone["plant_id"], []).append(zone)

    machine_to_zone = {}
    msz_rows = []
    for machine in machines:
        zones = plant_zones.get(machine["plant_id"], [])
        if zones:
            zone = rng.choice(zones)
            machine_to_zone[machine["id"]] = zone["id"]
            msz_rows.append({
                "id": _det_uuid(f"msz-{machine['id']}-{zone['id']}"),
                "machine_id": machine["id"],
                "safety_zone_id": zone["id"],
                "effective_from": _ts(GEN_START),
            })
    _bulk_insert(sb, "machine_safety_zone", msz_rows)
    logger.info(f"  Generated machine-zone associations")

    # STEP 6: Machine-Interlock Associations
    plant_interlocks = {}
    for il in interlocks:
        plant_interlocks.setdefault(il["plant_id"], []).append(il)

    mi_rows = []
    for machine in machines:
        ils = plant_interlocks.get(machine["plant_id"], [])
        for idx, il in enumerate(rng.sample(ils, min(2, len(ils)))):
            mi_rows.append({
                "id": _det_uuid(f"mi-{machine['id']}-{il['id']}"),
                "machine_id": machine["id"],
                "interlock_id": il["id"],
                "is_required": (idx == 0),
                "effective_from": _ts(GEN_START),
            })
    _bulk_insert(sb, "machine_interlock", mi_rows)
    logger.info(f"  Generated machine-interlock associations")

    # STEP 7: Alarm Definitions
    alarm_defs = []
    machines_cycle = machines * (cfg["alarm_definitions"] // len(machines) + 1)
    for i in range(cfg["alarm_definitions"]):
        machine = machines_cycle[i]
        category = rng.choice(ALARM_CATEGORIES)
        severity = rng.choices(ALARM_SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
        alarm_defs.append({
            "id": _det_uuid(f"almdef-{i+1}"),
            "alarm_code": f"ALMDEF-{machine['machine_code']}-{i+1:03d}",
            "machine_id": machine["id"],
            "name": f"{category.replace('_', ' ').title()} {severity.title()} Alarm",
            "description": f"Monitors {category.lower()} levels on {machine['name']}",
            "severity": severity,
            "category": category,
            "threshold_value": round(rng.uniform(10.0, 500.0), 2),
            "threshold_unit": _unit_for_category(category),
            "ack_deadline_seconds": ACK_DEADLINES[severity],
            "is_active": True,
            "created_at": _ts(GEN_START),
        })
    _bulk_insert(sb, "alarm_definition", alarm_defs)
    counts["alarm_definitions"] = len(alarm_defs)
    logger.info(f"  Generated {len(alarm_defs)} alarm definitions")

    # STEP 8: Operator Shifts
    shifts = []
    shift_counter = 0
    for plant in plants:
        current_dt = GEN_START
        while current_dt < GEN_END:
            for shift_type in SHIFT_TYPES:
                op_id, op_name = rng.choice(OPERATORS)
                shift_end = current_dt + timedelta(hours=8)
                shift_counter += 1
                shifts.append({
                    "id": _det_uuid(f"shift-{shift_counter}"),
                    "shift_code": f"SHIFT-{plant['plant_code']}-{shift_counter:05d}",
                    "plant_id": plant["id"],
                    "operator_id": op_id,
                    "operator_name": op_name,
                    "shift_type": shift_type,
                    "shift_start": _ts(current_dt),
                    "shift_end": _ts(shift_end),
                    "status": "COMPLETED",
                    "created_at": _ts(GEN_START),
                })
                current_dt = shift_end
            if current_dt >= GEN_END:
                break
    _bulk_insert(sb, "operator_shift", shifts)
    counts["operator_shifts"] = len(shifts)
    logger.info(f"  Generated {len(shifts)} operator shifts")

    # STEP 9: Machine State Events
    state_events = []
    state_counter = 0
    machine_final_states = {}
    for machine in machines:
        current_state = "OFFLINE"
        current_dt = GEN_START
        while current_dt < GEN_END:
            cycle = [
                ("IDLE", timedelta(minutes=rng.randint(5, 30))),
                ("STARTING", timedelta(minutes=rng.randint(2, 10))),
                ("RUNNING", timedelta(hours=rng.randint(4, 16))),
                ("STOPPING", timedelta(minutes=rng.randint(2, 10))),
                ("IDLE", timedelta(minutes=rng.randint(10, 60))),
            ]
            if rng.random() < 0.15:
                cycle += [("MAINTENANCE", timedelta(hours=rng.randint(1, 4))), ("IDLE", timedelta(minutes=30))]
            if rng.random() < 0.05:
                cycle += [("FAULT", timedelta(minutes=rng.randint(10, 60))), ("MAINTENANCE", timedelta(hours=1)), ("IDLE", timedelta(minutes=30))]
            for to_state, duration in cycle:
                if current_dt >= GEN_END:
                    break
                state_counter += 1
                state_events.append({
                    "id": _det_uuid(f"mse-{state_counter}"),
                    "machine_id": machine["id"],
                    "from_state": current_state,
                    "to_state": to_state,
                    "is_valid_transition": to_state in VALID_TRANSITIONS.get(current_state, []),
                    "trigger_reason": "NORMAL_OPERATION",
                    "occurred_at": _ts(current_dt),
                    "generation_run_id": run_id,
                })
                current_state = to_state
                current_dt += duration
        machine_final_states[machine["id"]] = current_state

    _bulk_insert(sb, "machine_state_event", state_events)
    counts["machine_state_events"] = len(state_events)
    logger.info(f"  Generated {len(state_events)} machine state events")

    # Update machine final states — group by state to minimize requests
    from collections import defaultdict
    state_groups = defaultdict(list)
    for machine in machines:
        state_groups[machine_final_states.get(machine["id"], "IDLE")].append(machine["id"])
    for state, ids in state_groups.items():
        sb.table("machine").update({"current_state": state}).in_("id", ids).execute()

    # STEP 10: Interlock State Events
    ile_rows = []
    ile_counter = 0
    interlock_final_states = {}
    for il in interlocks:
        current_state = "ENGAGED"
        current_dt = GEN_START + timedelta(hours=rng.randint(1, 12))
        plant_machines = [m["id"] for m in machines if m["plant_id"] == il["plant_id"]]
        while current_dt < GEN_END:
            new_state = rng.choices(["ENGAGED", "DISENGAGED"], weights=[0.95, 0.05])[0] if current_state == "ENGAGED" else "ENGAGED"
            ile_counter += 1
            ile_rows.append({
                "id": _det_uuid(f"ile-{ile_counter}"),
                "interlock_id": il["id"],
                "machine_id": rng.choice(plant_machines) if plant_machines else machines[0]["id"],
                "from_state": current_state,
                "to_state": new_state,
                "is_valid_combination": True,
                "occurred_at": _ts(current_dt),
                "generation_run_id": run_id,
            })
            current_state = new_state
            current_dt += timedelta(hours=rng.randint(4, 24))
        interlock_final_states[il["id"]] = current_state

    _bulk_insert(sb, "interlock_state_event", ile_rows)
    counts["interlock_state_events"] = len(ile_rows)
    logger.info(f"  Generated {len(ile_rows)} interlock state events")

    il_state_groups = defaultdict(list)
    for il in interlocks:
        il_state_groups[interlock_final_states.get(il["id"], "ENGAGED")].append(il["id"])
    for state, ids in il_state_groups.items():
        sb.table("interlock").update({"current_state": state}).in_("id", ids).execute()

    # STEP 11: Alarm Events
    machine_to_defs = {}
    for adef in alarm_defs:
        machine_to_defs.setdefault(adef["machine_id"], []).append(adef)

    alarm_events = []
    machine_alarm_counters = {m["id"]: 0 for m in machines}
    target_count = cfg["alarm_events"]
    ae_counter = 0
    while ae_counter < target_count:
        machine = rng.choice(machines)
        defs = machine_to_defs.get(machine["id"], [])
        if not defs:
            continue
        adef = rng.choice(defs)
        alarm_ts = GEN_START + timedelta(seconds=rng.randint(0, int((GEN_END - GEN_START).total_seconds())))
        machine_alarm_counters[machine["id"]] += 1
        fingerprint = hashlib.sha256(f"{machine['machine_code']}-{adef['alarm_code']}-{alarm_ts.isoformat()}".encode()).hexdigest()[:20]
        ae_counter += 1
        cleared = rng.random() < 0.7
        alarm_events.append({
            "id": _det_uuid(f"ae-{ae_counter}"),
            "alarm_event_code": f"ALM-{machine['machine_code']}-{machine_alarm_counters[machine['id']]:06d}",
            "alarm_definition_id": adef["id"],
            "machine_id": machine["id"],
            "safety_zone_id": machine_to_zone.get(machine["id"]),
            "trigger_value": round(rng.uniform(adef["threshold_value"], adef["threshold_value"] * 1.5), 2),
            "severity": adef["severity"],
            "status": "CLEARED" if cleared else "ACTIVE",
            "acknowledgement_status": "PENDING",
            "alarm_timestamp": _ts(alarm_ts),
            "cleared_timestamp": _ts(alarm_ts + timedelta(minutes=rng.randint(5, 120))) if cleared else None,
            "ingested_at": _ts(alarm_ts),
            "source_fingerprint": fingerprint,
            "is_replayed": False,
            "generation_run_id": run_id,
        })
        if ae_counter % 5000 == 0:
            _bulk_insert(sb, "alarm_event", alarm_events[-5000:])
            logger.info(f"  Alarm events: {ae_counter}/{target_count}")

    remaining = alarm_events[-(ae_counter % 5000 or len(alarm_events)):]
    if remaining:
        _bulk_insert(sb, "alarm_event", remaining)
    counts["alarm_events"] = len(alarm_events)
    logger.info(f"  Generated {len(alarm_events)} alarm events")

    # STEP 12: Acknowledgements
    acks = []
    ack_counter = 0
    alarms_to_ack = rng.sample(alarm_events, int(len(alarm_events) * 0.70))
    acked_ids = {ae["id"] for ae in alarms_to_ack}

    for ae in alarms_to_ack:
        deadline = ACK_DEADLINES.get(ae["severity"], 120)
        if rng.random() < 0.60:
            delay = rng.randint(10, deadline)
            status = "ON_TIME"
        else:
            delay = rng.randint(deadline + 1, deadline * 5)
            status = "DELAYED"
        alarm_dt = datetime.fromisoformat(ae["alarm_timestamp"])
        ack_ts = alarm_dt + timedelta(seconds=delay)
        ack_counter += 1
        op_id, op_name = rng.choice(OPERATORS)
        acks.append({
            "id": _det_uuid(f"ack-{ack_counter}"),
            "ack_code": f"ACK-{ae['alarm_event_code']}-01",
            "alarm_event_id": ae["id"],
            "operator_id": op_id,
            "operator_name": op_name,
            "ack_timestamp": _ts(ack_ts),
            "response_time_seconds": delay,
            "status": status,
            "validation_result": "VALID",
            "is_anomalous": False,
            "created_at": _ts(ack_ts),
        })
        ae["acknowledgement_status"] = status

    for ae in alarm_events:
        if ae["id"] not in acked_ids:
            ae["acknowledgement_status"] = "MISSING"

    _bulk_insert(sb, "acknowledgement", acks)
    counts["acknowledgements"] = len(acks)
    logger.info(f"  Generated {len(acks)} acknowledgements")

    # Update alarm ack statuses in bulk by status group
    for status in ["ON_TIME", "DELAYED", "MISSING"]:
        ids = [ae["id"] for ae in alarm_events if ae.get("acknowledgement_status") == status]
        for i in range(0, len(ids), 500):
            sb.table("alarm_event").update({"acknowledgement_status": status}).in_("id", ids[i:i+500]).execute()

    # STEP 13-15: Incidents + Corrective Actions
    incidents = []
    cas = []
    ia_rows = []
    ise_rows = []
    cae_rows = []
    incident_counter = 0

    critical_alarms = [ae for ae in alarm_events if ae["severity"] in ("CRITICAL", "HIGH")]
    incident_triggers = rng.sample(critical_alarms, min(len(critical_alarms), target_count // 25))
    machine_map = {m["id"]: m for m in machines}

    for ae in incident_triggers:
        machine = machine_map.get(ae["machine_id"])
        if not machine:
            continue
        incident_counter += 1
        alarm_dt = datetime.fromisoformat(ae["alarm_timestamp"])
        detected_at = alarm_dt + timedelta(minutes=rng.randint(5, 30))
        status = rng.choice(["OPEN", "INVESTIGATING", "ACTION_REQUIRED", "CLOSED"])
        inc_id = _det_uuid(f"inc-{incident_counter}")
        inc = {
            "id": inc_id,
            "incident_code": f"INC-2026-{incident_counter:06d}",
            "plant_id": machine["plant_id"],
            "machine_id": machine["id"],
            "safety_zone_id": ae.get("safety_zone_id"),
            "severity": ae["severity"],
            "status": status,
            "root_cause_category": rng.choice(ROOT_CAUSES),
            "description": f"Safety incident triggered by {ae['alarm_event_code']} on {machine['name']}",
            "assigned_engineer": rng.choice(ENGINEERS),
            "detected_at": _ts(detected_at),
            "closed_at": _ts(detected_at + timedelta(days=rng.randint(1, 14))) if status == "CLOSED" else None,
            "has_missing_context": False,
            "generation_run_id": run_id,
            "created_at": _ts(alarm_dt),
            "updated_at": _ts(alarm_dt),
        }
        incidents.append(inc)

        ia_rows.append({
            "id": _det_uuid(f"ia-{inc_id}-{ae['id']}"),
            "incident_id": inc_id,
            "alarm_event_id": ae["id"],
            "relationship_type": "TRIGGER",
            "linked_at": _ts(detected_at),
        })

        ise_rows.append({
            "id": _det_uuid(f"ise-{inc_id}-open"),
            "incident_id": inc_id,
            "from_state": None,
            "to_state": "OPEN",
            "transitioned_by": "SYSTEM",
            "notes": "Auto-created from safety rule detection",
            "is_valid": True,
            "transitioned_at": _ts(detected_at),
        })

        for ca_idx in range(rng.randint(1, 3)):
            ca_status = rng.choice(["OPEN", "IN_PROGRESS", "COMPLETED", "VERIFIED"])
            ca_id = _det_uuid(f"ca-{inc_id}-{ca_idx}")
            cas.append({
                "id": ca_id,
                "action_code": f"ACT-INC-2026-{incident_counter:06d}-{ca_idx+1:02d}",
                "incident_id": inc_id,
                "description": f"Corrective action {ca_idx+1} for INC-2026-{incident_counter:06d}",
                "assigned_engineer": rng.choice(ENGINEERS),
                "priority": rng.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "status": ca_status,
                "due_at": _ts(detected_at + timedelta(days=rng.randint(1, 30))),
                "completed_at": _ts(detected_at + timedelta(days=rng.randint(1, 7))) if ca_status in ("COMPLETED", "VERIFIED") else None,
                "verified_at": _ts(detected_at + timedelta(days=rng.randint(7, 14))) if ca_status == "VERIFIED" else None,
                "verification_result": "PASS" if ca_status == "VERIFIED" else None,
                "is_closed_without_verification": False,
                "created_at": _ts(detected_at),
                "updated_at": _ts(detected_at),
            })
            cae_rows.append({
                "id": _det_uuid(f"cae-{ca_id}-open"),
                "corrective_action_id": ca_id,
                "from_status": None,
                "to_status": "OPEN",
                "transitioned_by": "SYSTEM",
                "notes": "Created",
                "is_valid": True,
                "transitioned_at": _ts(detected_at),
            })

    _bulk_insert(sb, "incident", incidents)
    _bulk_insert(sb, "incident_alarm", ia_rows)
    _bulk_insert(sb, "incident_state_event", ise_rows)
    _bulk_insert(sb, "corrective_action", cas)
    _bulk_insert(sb, "corrective_action_event", cae_rows)
    counts["incidents"] = len(incidents)
    counts["corrective_actions"] = len(cas)
    logger.info(f"  Generated {len(incidents)} incidents, {len(cas)} corrective actions")

    # STEP 17: Anomaly Injection
    from app.generators.anomaly_injector import inject_all_anomalies
    anomaly_count = inject_all_anomalies(
        rng=rng, alarm_events=alarm_events, interlocks=interlocks,
        machines=machines, incidents=incidents, cas=cas, run_id=run_id,
    )
    counts["injected_anomalies"] = anomaly_count

    # STEP 18: Ground Truth
    from app.generators.ground_truth_generator import generate_ground_truth
    generate_ground_truth()

    logger.info(f"Generation complete. Counts: {counts}")
    return counts
