"""Exports routes"""
from flask import Blueprint, Response
from app.services.export_service import (
    export_alarms_csv,
    export_incidents_csv,
    export_anomalies_csv,
    export_validation_json,
)

exports_bp = Blueprint("exports", __name__)


@exports_bp.route("/exports/alarms")
def export_alarms():
    content, filename = export_alarms_csv()
    return Response(content, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


@exports_bp.route("/exports/incidents")
def export_incidents():
    content, filename = export_incidents_csv()
    return Response(content, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


@exports_bp.route("/exports/anomalies")
def export_anomalies():
    content, filename = export_anomalies_csv()
    return Response(content, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


@exports_bp.route("/exports/validation")
def export_validation():
    content, filename = export_validation_json()
    return Response(content, mimetype="application/json", headers={"Content-Disposition": f"attachment; filename={filename}"})
