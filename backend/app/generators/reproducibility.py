"""
Reproducibility module — SHA-256 checksum comparison between two generation runs.
"""
import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)


def compute_dataset_checksum(run_id=None):
    """
    Compute a SHA-256 checksum of all deterministic data for a given run.
    Excludes runtime metadata (timestamps of generation runs themselves).
    """
    from app.extensions import db
    from app.models import (
        Plant, Machine, SafetyZone, AlarmDefinition, AlarmEvent, Incident,
    )

    data_parts = []

    # Collect sorted deterministic records
    for plant in Plant.query.order_by(Plant.plant_code).all():
        data_parts.append(f"plant:{plant.plant_code}:{plant.name}:{plant.location}")

    for machine in Machine.query.order_by(Machine.machine_code).all():
        data_parts.append(f"machine:{machine.machine_code}:{machine.name}:{machine.machine_type}")

    for zone in SafetyZone.query.order_by(SafetyZone.zone_code).all():
        data_parts.append(f"zone:{zone.zone_code}:{zone.zone_type}")

    for adef in AlarmDefinition.query.order_by(AlarmDefinition.alarm_code).all():
        data_parts.append(f"almdef:{adef.alarm_code}:{adef.severity}:{adef.category}")

    for ae in AlarmEvent.query.order_by(AlarmEvent.alarm_event_code).all():
        data_parts.append(
            f"alarm:{ae.alarm_event_code}:{ae.severity}:{ae.alarm_timestamp.isoformat() if ae.alarm_timestamp else ''}"
        )

    for inc in Incident.query.order_by(Incident.incident_code).all():
        data_parts.append(f"incident:{inc.incident_code}:{inc.severity}:{inc.status}")

    content = "\n".join(data_parts)
    checksum = hashlib.sha256(content.encode()).hexdigest()
    return checksum


def compare_runs(run1_checksum, run2_checksum):
    """
    Compare two run checksums.
    Returns dict with result and details.
    """
    match = run1_checksum == run2_checksum
    return {
        "run1_checksum": run1_checksum,
        "run2_checksum": run2_checksum,
        "match": match,
        "result": "REPRODUCIBLE" if match else "DIVERGED",
        "note": (
            "Identical deterministic outputs — reproducibility confirmed."
            if match else
            "Outputs diverged — check seed or generation configuration."
        ),
    }
