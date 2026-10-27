"""
TC31-TC43: API integration tests.
"""
import pytest
import json


class TestAPIPaginationFiltering:
    """TC31: API pagination and filtering"""
    def test_alarms_pagination(self, client, generated_data):
        resp = client.get("/api/v1/alarms?page=1&per_page=10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) <= 10

    def test_alarms_severity_filter(self, client, generated_data):
        resp = client.get("/api/v1/alarms?severity=CRITICAL&per_page=5")
        assert resp.status_code == 200
        data = resp.get_json()
        for alarm in data["data"]:
            assert alarm["severity"] == "CRITICAL"

    def test_incidents_status_filter(self, client, generated_data):
        resp = client.get("/api/v1/incidents?status=OPEN")
        assert resp.status_code == 200

    def test_plants_listing(self, client, generated_data):
        resp = client.get("/api/v1/plants")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) >= 1


class TestAPIInvalidInput:
    """TC32: API invalid input handling"""
    def test_acknowledge_nonexistent_alarm(self, client, generated_data):
        resp = client.post(
            "/api/v1/alarms/nonexistent-id/acknowledge",
            json={"operator_id": "OP-001"},
        )
        assert resp.status_code == 404

    def test_generator_invalid_mode(self, client, generated_data):
        resp = client.post("/api/v1/generator/run", json={"mode": "invalid"})
        assert resp.status_code == 400

    def test_incident_transition_missing_body(self, client, generated_data):
        resp = client.post("/api/v1/incidents/nonexistent/transitions", json={})
        assert resp.status_code in (400, 404)


class TestAPINotFound:
    """TC33: API not-found handling"""
    def test_machine_not_found(self, client, generated_data):
        resp = client.get("/api/v1/machines/definitely-not-a-real-id")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    def test_incident_not_found(self, client, generated_data):
        resp = client.get("/api/v1/incidents/FAKE-INC-000000")
        assert resp.status_code == 404

    def test_alarm_not_found(self, client, generated_data):
        resp = client.get("/api/v1/alarms/FAKE-ALARM")
        assert resp.status_code == 404


class TestAPIStateConflict:
    """TC34: API state-conflict handling"""
    def test_generator_conflict_when_running(self, app, client):
        """Prevent overlapping generation runs."""
        with app.app_context():
            from app.models import GenerationRun
            from app.extensions import db
            # Simulate a running run
            running = GenerationRun(
                run_code="GEN-TEST-RUNNING",
                mode="full",
                seed=20261022,
                status="RUNNING",
            )
            db.session.add(running)
            db.session.commit()

            resp = client.post("/api/v1/generator/run", json={"mode": "starter"})
            assert resp.status_code == 409

            # Clean up
            db.session.delete(running)
            db.session.commit()


class TestAPIExports:
    """TC35-TC37: Export endpoints"""
    def test_csv_alarm_export(self, client, generated_data):
        resp = client.get("/api/v1/exports/alarms")
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type
        content = resp.data.decode()
        assert "alarm_event_code" in content  # header present

    def test_csv_incident_export(self, client, generated_data):
        resp = client.get("/api/v1/exports/incidents")
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type

    def test_json_validation_export(self, client, generated_data):
        resp = client.get("/api/v1/exports/validation")
        assert resp.status_code == 200
        assert "application/json" in resp.content_type


class TestAPIHealth:
    """Health endpoint"""
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in ("ok", "degraded")

    def test_dashboard_summary(self, client, generated_data):
        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "kpis" in data["data"]
        assert "total_plants" in data["data"]["kpis"]


class TestReplayIdempotency:
    """TC43: Replay idempotency and ingestion identity"""
    def test_replayed_alarms_have_distinct_ids(self, app, generated_data):
        with app.app_context():
            from app.models import AlarmEvent
            replayed = AlarmEvent.query.filter_by(is_replayed=True).all()
            originals = AlarmEvent.query.filter_by(is_replayed=False).all()
            replayed_ids = {ae.id for ae in replayed}
            original_ids = {ae.id for ae in originals}
            assert len(replayed_ids & original_ids) == 0, \
                "Replayed and original alarms must have distinct ingestion IDs"


class TestIncidentAlarmBridgeIntegrity:
    """TC45: Incident-to-alarm bridge integrity"""
    def test_bridge_records_valid(self, app, generated_data):
        with app.app_context():
            from app.models import IncidentAlarm, Incident, AlarmEvent
            for ia in IncidentAlarm.query.all():
                assert Incident.query.get(ia.incident_id), f"IncidentAlarm has invalid incident_id"
                assert AlarmEvent.query.get(ia.alarm_event_id), f"IncidentAlarm has invalid alarm_event_id"


class TestCAVerificationHistory:
    """TC46: Corrective action verification history preserved"""
    def test_invalid_closure_preserved_in_history(self, app, generated_data):
        with app.app_context():
            from app.models import CorrectiveAction, CorrectiveActionEvent
            bad_ca = CorrectiveAction.query.filter_by(is_closed_without_verification=True).first()
            if bad_ca:
                invalid_events = CorrectiveActionEvent.query.filter(
                    CorrectiveActionEvent.corrective_action_id == bad_ca.id,
                    CorrectiveActionEvent.is_valid == False,
                ).all()
                assert len(invalid_events) >= 1, "Invalid closure attempt must be preserved in history"
                assert bad_ca.status != "CLOSED", "Business state must not be corrupted by invalid closure"


class TestAllFiveAnomalsInGroundTruth:
    """TC50: All 5 injected anomaly types appear in ground truth and are detectable"""
    def test_all_5_cases_detectable(self, app, generated_data):
        with app.app_context():
            from app.services.anomaly_engine import (
                detect_ack_before_alarm,
                detect_impossible_interlock_combinations,
                detect_incidents_missing_context,
                detect_alarm_replay,
                detect_actions_closed_without_verification,
            )
            assert len(detect_ack_before_alarm()) >= 1, "CASE1 not detected"
            assert len(detect_impossible_interlock_combinations()) >= 1, "CASE2 not detected"
            assert len(detect_incidents_missing_context()) >= 1, "CASE3 not detected"
            assert len(detect_alarm_replay()) >= 1, "CASE4 not detected"
            assert len(detect_actions_closed_without_verification()) >= 1, "CASE5 not detected"
