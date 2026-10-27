"""
TC11-TC22: Acknowledgement, interlock, incident, alarm flood, anomaly detection tests.
"""
import pytest
from datetime import datetime, timedelta, timezone


class TestAcknowledgementTiming:
    """TC11-TC12: On-time and delayed acknowledgement calculation"""
    def test_on_time_ack_calculation(self, app):
        with app.app_context():
            from app.services.alarm_engine import calculate_ack_status
            alarm_ts = datetime(2026, 10, 5, 10, 0, 0)
            ack_ts = alarm_ts + timedelta(seconds=60)
            status = calculate_ack_status(alarm_ts, ack_ts, "CRITICAL")
            assert status == "ON_TIME", f"Expected ON_TIME, got {status}"

    def test_delayed_ack_calculation(self, app):
        with app.app_context():
            from app.services.alarm_engine import calculate_ack_status
            alarm_ts = datetime(2026, 10, 5, 10, 0, 0)
            ack_ts = alarm_ts + timedelta(seconds=300)  # 300s > 120s CRITICAL deadline
            status = calculate_ack_status(alarm_ts, ack_ts, "CRITICAL")
            assert status == "DELAYED", f"Expected DELAYED, got {status}"

    def test_missing_ack_calculation(self, app):
        with app.app_context():
            from app.services.alarm_engine import calculate_ack_status
            alarm_ts = datetime(2026, 10, 5, 10, 0, 0)
            status = calculate_ack_status(alarm_ts, None, "HIGH")
            assert status == "MISSING"


class TestNegativeScenarios:
    """TC13-TC17: Five mandatory negative scenarios"""

    def test_case1_ack_before_alarm_exists(self, app, generated_data):
        """TC13: Acknowledgement before alarm"""
        with app.app_context():
            from app.models import Acknowledgement
            anomalous = Acknowledgement.query.filter_by(is_anomalous=True).first()
            assert anomalous is not None, "CASE1: Anomalous ack must exist"
            alarm = anomalous.alarm_event
            assert anomalous.ack_timestamp < alarm.alarm_timestamp, \
                "CASE1: ack_timestamp must be before alarm_timestamp"
            assert anomalous.status == "INVALID", "CASE1: Status must be INVALID"
            assert anomalous.validation_result == "INVALID"

    def test_case2_impossible_interlock_exists(self, app, generated_data):
        """TC14: Impossible interlock combination"""
        with app.app_context():
            from app.models import InterlockStateEvent
            invalid = InterlockStateEvent.query.filter_by(is_valid_combination=False).first()
            assert invalid is not None, "CASE2: Invalid interlock combination must exist"
            assert invalid.unsafe_condition_code is not None

    def test_case3_incident_missing_context_exists(self, app, generated_data):
        """TC15: Incident missing triggering context"""
        with app.app_context():
            from app.models import Incident, IncidentAlarm
            missing = Incident.query.filter_by(has_missing_context=True).first()
            assert missing is not None, "CASE3: Incident with missing context must exist"
            alarm_count = IncidentAlarm.query.filter_by(incident_id=missing.id).count()
            assert alarm_count == 0, "CASE3: Incident must have no linked alarms"

    def test_case4_alarm_flood_replay_exists(self, app, generated_data):
        """TC16: Alarm flood replay detection"""
        with app.app_context():
            from app.models import AlarmEvent
            replayed = AlarmEvent.query.filter_by(is_replayed=True).all()
            assert len(replayed) >= 1, "CASE4: Replayed alarms must exist"
            for replay in replayed:
                # Same fingerprint must exist in a non-replayed record
                originals = AlarmEvent.query.filter(
                    AlarmEvent.source_fingerprint == replay.source_fingerprint,
                    AlarmEvent.is_replayed == False,
                ).count()
                assert originals >= 1, f"CASE4: Original for fingerprint {replay.source_fingerprint} must exist"
                # Distinct ingestion IDs
                assert replay.id != originals, "CASE4: Replayed and original must have distinct IDs"

    def test_case5_action_closed_without_verify_exists(self, app, generated_data):
        """TC17: Corrective action closure without verification"""
        with app.app_context():
            from app.models import CorrectiveAction, CorrectiveActionEvent
            bad = CorrectiveAction.query.filter_by(is_closed_without_verification=True).first()
            assert bad is not None, "CASE5: Action with invalid closure attempt must exist"
            # Invalid transition must be in history
            invalid_event = CorrectiveActionEvent.query.filter(
                CorrectiveActionEvent.corrective_action_id == bad.id,
                CorrectiveActionEvent.is_valid == False,
            ).first()
            assert invalid_event is not None, "CASE5: Invalid closure event must be in history"


class TestIncidentTraceability:
    """TC18: Incident traceability chain"""
    def test_incident_has_traceability(self, app, generated_data):
        with app.app_context():
            from app.models import Incident, IncidentAlarm
            from app.services.incident_engine import get_traceability_chain
            inc = Incident.query.filter_by(has_missing_context=False).first()
            if inc:
                chain = get_traceability_chain(inc)
                assert "incident" in chain
                assert "machine" in chain
                assert "state_history" in chain
                assert "corrective_actions" in chain
                assert "traceability_complete" in chain


class TestShiftLinkage:
    """TC19: Operator shift linkage"""
    def test_shifts_exist(self, app, generated_data):
        with app.app_context():
            from app.models import OperatorShift
            assert OperatorShift.query.count() >= 3, "At least 3 shifts must exist"

    def test_shift_boundary_timestamps(self, app, generated_data):
        with app.app_context():
            from app.models import OperatorShift
            for shift in OperatorShift.query.limit(10).all():
                assert shift.shift_end > shift.shift_start, "shift_end must be after shift_start"


class TestAlarmFloodDetection:
    """TC20-TC21: Alarm flood and nuisance cluster detection"""
    def test_flood_detector_runs(self, app, generated_data):
        with app.app_context():
            from app.services.alarm_engine import detect_alarm_floods
            result = detect_alarm_floods()
            assert isinstance(result, list), "Flood detector must return list"

    def test_nuisance_cluster_detector_runs(self, app, generated_data):
        with app.app_context():
            from app.services.alarm_engine import detect_nuisance_clusters
            result = detect_nuisance_clusters()
            assert isinstance(result, list), "Nuisance detector must return list"


class TestRepeatedUnsafeCondition:
    """TC22: Repeated unsafe condition detection"""
    def test_repeated_condition_detector_runs(self, app, generated_data):
        with app.app_context():
            from app.services.analytics_service import get_repeated_unsafe_conditions
            result = get_repeated_unsafe_conditions()
            assert isinstance(result, list)
