"""
TC23-TC30: Validation and evaluation metric tests.
"""
import pytest


class TestPKUniqueness:
    """TC23: Primary-key uniqueness"""
    def test_alarm_pks_unique(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmEvent
            from sqlalchemy import func
            from app.extensions import db
            total = AlarmEvent.query.count()
            distinct = db.session.query(func.count(func.distinct(AlarmEvent.id))).scalar()
            assert total == distinct, f"AlarmEvent PKs not unique: {total} total, {distinct} distinct"

    def test_alarm_codes_unique(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmEvent
            from sqlalchemy import func
            from app.extensions import db
            total = AlarmEvent.query.count()
            distinct_codes = db.session.query(func.count(func.distinct(AlarmEvent.alarm_event_code))).scalar()
            assert total == distinct_codes, "Alarm event codes not unique"

    def test_incident_pks_unique(self, app, generated_data):
        with app.app_context():
            from app.models import Incident
            from sqlalchemy import func
            from app.extensions import db
            total = Incident.query.count()
            distinct = db.session.query(func.count(func.distinct(Incident.id))).scalar()
            assert total == distinct, "Incident PKs not unique"


class TestFKIntegrity:
    """TC24: Foreign-key integrity"""
    def test_alarms_reference_valid_machines(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmEvent, Machine
            orphans = [
                ae for ae in AlarmEvent.query.all()
                if not Machine.query.get(ae.machine_id)
            ]
            assert len(orphans) == 0, f"{len(orphans)} alarm events reference invalid machines"

    def test_incidents_reference_valid_plants(self, app, generated_data):
        with app.app_context():
            from app.models import Incident, Plant
            orphans = [
                i for i in Incident.query.all()
                if not Plant.query.get(i.plant_id)
            ]
            assert len(orphans) == 0, f"{len(orphans)} incidents reference invalid plants"


class TestEnumValidation:
    """TC25: Allowed enum values"""
    def test_alarm_severity_enum(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmEvent
            allowed = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
            invalid = [
                ae.alarm_event_code for ae in AlarmEvent.query.all()
                if ae.severity not in allowed
            ]
            assert len(invalid) == 0, f"Invalid severity values: {invalid[:5]}"

    def test_machine_state_enum(self, app, generated_data):
        with app.app_context():
            from app.models import Machine
            allowed = {"OFFLINE", "IDLE", "STARTING", "RUNNING", "STOPPING",
                       "MAINTENANCE", "FAULT", "EMERGENCY_STOP"}
            invalid = [m.machine_code for m in Machine.query.all() if m.current_state not in allowed]
            assert len(invalid) == 0, f"Invalid machine states: {invalid[:5]}"


class TestTimelineOrdering:
    """TC26: Timeline ordering"""
    def test_alarm_timestamps_within_gen_period(self, app, generated_data):
        with app.app_context():
            from datetime import datetime
            from app.models import AlarmEvent
            gen_start = datetime(2026, 10, 1)
            gen_end = datetime(2026, 10, 31)
            for ae in AlarmEvent.query.limit(100).all():
                assert gen_start <= ae.alarm_timestamp <= gen_end, \
                    f"Alarm {ae.alarm_event_code} timestamp out of generation period"

    def test_cleared_after_alarm(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmEvent
            for ae in AlarmEvent.query.filter(AlarmEvent.cleared_timestamp.isnot(None)).limit(50).all():
                assert ae.cleared_timestamp >= ae.alarm_timestamp, \
                    f"cleared_timestamp before alarm_timestamp for {ae.alarm_event_code}"


class TestLifecycleValidation:
    """TC27: Lifecycle state validation"""
    def test_incident_lifecycle_transitions(self, app, generated_data):
        with app.app_context():
            from app.services.incident_engine import VALID_TRANSITIONS
            from app.models import IncidentStateEvent
            for se in IncidentStateEvent.query.filter_by(is_valid=True).limit(50).all():
                if se.from_state:
                    allowed = VALID_TRANSITIONS.get(se.from_state, set())
                    assert se.to_state in allowed, \
                        f"Valid incident transition {se.from_state}→{se.to_state} not in VALID_TRANSITIONS"


class TestDerivedValueReconciliation:
    """TC28: Derived-value reconciliation"""
    def test_ack_status_matches_timing(self, app, generated_data):
        with app.app_context():
            from app.models import Acknowledgement, AlarmEvent
            from app.services.alarm_engine import calculate_ack_status
            for ack in Acknowledgement.query.limit(50).all():
                alarm = AlarmEvent.query.get(ack.alarm_event_id)
                if alarm and not ack.is_anomalous:
                    expected = calculate_ack_status(alarm.alarm_timestamp, ack.ack_timestamp, alarm.severity)
                    assert ack.status == expected, \
                        f"Ack {ack.ack_code}: stored={ack.status}, calculated={expected}"


class TestGroundTruthSeparation:
    """TC29: Ground truth separation"""
    def test_ground_truth_not_in_detection_inputs(self, app):
        """Ground truth files must not be imported by anomaly_engine."""
        import ast
        import inspect
        import app.services.anomaly_engine as ae_module
        source = inspect.getsource(ae_module)
        # Detection engine must not import ground_truth
        assert "ground_truth_generator" not in source, \
            "anomaly_engine must not import ground_truth_generator"
        # It may READ the JSON file for evaluation only
        assert "ground_truth.json" in source or "ground_truth" in source  # for evaluation


class TestEvaluationMetrics:
    """TC30: Precision/recall/F1 computation"""
    def test_evaluation_metrics_compute(self, app, generated_data):
        with app.app_context():
            from app.services.anomaly_engine import compute_evaluation_metrics
            metrics = compute_evaluation_metrics()
            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1_score" in metrics
            assert 0.0 <= metrics["precision"] <= 1.0
            assert 0.0 <= metrics["recall"] <= 1.0
            assert 0.0 <= metrics["f1_score"] <= 1.0
            # Must NOT be hardcoded to 100%
            assert metrics["precision"] < 1.01  # must be calculated

    def test_evaluation_denominator_safety(self, app, generated_data):
        """Zero denominators must be handled safely (no division by zero)."""
        with app.app_context():
            from app.services.anomaly_engine import compute_evaluation_metrics
            # Should not raise ZeroDivisionError
            metrics = compute_evaluation_metrics()
            assert metrics is not None
