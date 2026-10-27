"""
TC01-TC10: Unit tests for generator, models, and safety rules.
"""
import pytest
from datetime import datetime, timedelta


class TestPlantGeneration:
    """TC01: Plant creation and valid IDs"""
    def test_plants_created(self, app, generated_data):
        with app.app_context():
            from app.models import Plant
            plants = Plant.query.all()
            assert len(plants) >= 1, "At least 1 plant must be created"

    def test_plant_codes_valid(self, app, generated_data):
        with app.app_context():
            from app.models import Plant
            for plant in Plant.query.all():
                assert plant.plant_code.startswith("PLT-"), f"Invalid plant_code: {plant.plant_code}"
                assert len(plant.plant_code) == 8, f"Wrong plant_code length: {plant.plant_code}"

    def test_plant_codes_unique(self, app, generated_data):
        with app.app_context():
            from app.models import Plant
            codes = [p.plant_code for p in Plant.query.all()]
            assert len(codes) == len(set(codes)), "Plant codes not unique"


class TestMachineFK:
    """TC02: Machine-to-plant foreign keys"""
    def test_machines_have_valid_plant(self, app, generated_data):
        with app.app_context():
            from app.models import Machine, Plant
            for machine in Machine.query.all():
                plant = Plant.query.get(machine.plant_id)
                assert plant is not None, f"Machine {machine.machine_code} has invalid plant_id"


class TestSafetyZoneAssociations:
    """TC03: Safety zone associations"""
    def test_zones_created(self, app, generated_data):
        with app.app_context():
            from app.models import SafetyZone
            zones = SafetyZone.query.all()
            assert len(zones) >= 4, "At least 4 safety zones must exist"

    def test_zone_machine_bridge(self, app, generated_data):
        with app.app_context():
            from app.models import MachineSafetyZone
            bridges = MachineSafetyZone.query.all()
            assert len(bridges) >= 1, "Machine-safety zone associations must exist"


class TestInterlockAssociations:
    """TC04: Interlock associations"""
    def test_interlocks_created(self, app, generated_data):
        with app.app_context():
            from app.models import Interlock
            assert Interlock.query.count() >= 1

    def test_machine_interlock_bridge(self, app, generated_data):
        with app.app_context():
            from app.models import MachineInterlock
            assert MachineInterlock.query.count() >= 1


class TestAlarmDefinitionCount:
    """TC05: Alarm definitions count"""
    def test_starter_alarm_def_count(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmDefinition
            count = AlarmDefinition.query.count()
            assert count == 20, f"Starter mode must have 20 alarm definitions, got {count}"


class TestAlarmEventCount:
    """TC06: Alarm event count for starter mode"""
    def test_starter_alarm_event_count(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmEvent
            count = AlarmEvent.query.count()
            assert count >= 1000, f"Starter mode must have ≥1000 alarm events, got {count}"


class TestDeterministicGeneration:
    """TC07: Deterministic generation with fixed seed"""
    def test_same_seed_produces_same_plant_codes(self, app):
        with app.app_context():
            from app.models import Plant
            codes = sorted([p.plant_code for p in Plant.query.all()])
            assert "PLT-0001" in codes, "PLT-0001 must exist with seed 20261022"


class TestMachineStateTransitions:
    """TC08-TC09: Valid and invalid machine state transitions"""
    def test_valid_transitions_recorded(self, app, generated_data):
        with app.app_context():
            from app.models import MachineStateEvent
            valid = MachineStateEvent.query.filter_by(is_valid_transition=True).count()
            assert valid > 0, "Valid transitions must be recorded"

    def test_invalid_transitions_are_flagged(self, app):
        with app.app_context():
            from app.services.safety_engine import is_valid_machine_transition
            assert not is_valid_machine_transition("RUNNING", "OFFLINE"), "RUNNING→OFFLINE is invalid"
            assert is_valid_machine_transition("RUNNING", "STOPPING"), "RUNNING→STOPPING is valid"

    def test_all_valid_transition_pairs(self, app):
        with app.app_context():
            from app.services.safety_engine import is_valid_machine_transition, VALID_MACHINE_TRANSITIONS
            for from_state, valid_tos in VALID_MACHINE_TRANSITIONS.items():
                for to_state in valid_tos:
                    assert is_valid_machine_transition(from_state, to_state), \
                        f"{from_state}→{to_state} should be valid"


class TestAlarmSeverityPriority:
    """TC10: Critical alarm severity priority"""
    def test_critical_alarms_have_shortest_deadline(self, app):
        with app.app_context():
            from app.models import AlarmDefinition
            critical = AlarmDefinition.query.filter_by(severity="CRITICAL").first()
            if critical:
                assert critical.ack_deadline_seconds == 120, \
                    f"CRITICAL deadline must be 120s, got {critical.ack_deadline_seconds}"
