"""Anomaly detection routes"""
from flask import Blueprint, request
from app.utils import success_response, error_response
from app.services.anomaly_engine import (
    run_all_detectors,
    get_all_anomalies,
    get_anomaly_by_id,
    compute_evaluation_metrics,
    get_confusion_matrix,
)

anomalies_bp = Blueprint("anomalies", __name__)


@anomalies_bp.route("/anomalies")
def list_anomalies():
    issue_type = request.args.get("issue_type")
    severity = request.args.get("severity")
    anomalies = get_all_anomalies(issue_type=issue_type, severity=severity)
    return success_response(anomalies)


@anomalies_bp.route("/anomalies/<anomaly_id>")
def get_anomaly(anomaly_id):
    anomaly = get_anomaly_by_id(anomaly_id)
    if not anomaly:
        return error_response("NOT_FOUND", f"Anomaly '{anomaly_id}' not found", 404)
    return success_response(anomaly)


@anomalies_bp.route("/anomalies/detect", methods=["POST"])
def detect_anomalies():
    results = run_all_detectors()
    return success_response(results, 200)


@anomalies_bp.route("/evaluation/metrics")
def evaluation_metrics():
    metrics = compute_evaluation_metrics()
    return success_response(metrics)


@anomalies_bp.route("/evaluation/confusion-matrix")
def confusion_matrix():
    matrix = get_confusion_matrix()
    return success_response(matrix)
