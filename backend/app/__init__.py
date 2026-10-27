"""
SafePlant AI — Flask Application Factory
"""
import logging
import os
from flask import Flask, jsonify
from app.config import config
from app.extensions import cors


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config["default"]))

    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=False)

    from app.routes.system import system_bp
    from app.routes.plants import plants_bp
    from app.routes.machines import machines_bp
    from app.routes.safety_zones import safety_zones_bp
    from app.routes.interlocks import interlocks_bp
    from app.routes.alarm_definitions import alarm_definitions_bp
    from app.routes.alarms import alarms_bp
    from app.routes.operator_shifts import operator_shifts_bp
    from app.routes.incidents import incidents_bp
    from app.routes.corrective_actions import corrective_actions_bp
    from app.routes.analytics import analytics_bp
    from app.routes.anomalies import anomalies_bp
    from app.routes.generator import generator_bp
    from app.routes.validation import validation_bp
    from app.routes.exports import exports_bp
    from app.routes.audit import audit_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(system_bp)
    app.register_blueprint(plants_bp, url_prefix="/api/v1")
    app.register_blueprint(machines_bp, url_prefix="/api/v1")
    app.register_blueprint(safety_zones_bp, url_prefix="/api/v1")
    app.register_blueprint(interlocks_bp, url_prefix="/api/v1")
    app.register_blueprint(alarm_definitions_bp, url_prefix="/api/v1")
    app.register_blueprint(alarms_bp, url_prefix="/api/v1")
    app.register_blueprint(operator_shifts_bp, url_prefix="/api/v1")
    app.register_blueprint(incidents_bp, url_prefix="/api/v1")
    app.register_blueprint(corrective_actions_bp, url_prefix="/api/v1")
    app.register_blueprint(analytics_bp, url_prefix="/api/v1")
    app.register_blueprint(anomalies_bp, url_prefix="/api/v1")
    app.register_blueprint(generator_bp, url_prefix="/api/v1")
    app.register_blueprint(validation_bp, url_prefix="/api/v1")
    app.register_blueprint(exports_bp, url_prefix="/api/v1")
    app.register_blueprint(audit_bp, url_prefix="/api/v1")
    app.register_blueprint(dashboard_bp, url_prefix="/api/v1")

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "BAD_REQUEST", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "NOT_FOUND", "message": str(e)}), 404

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({"error": "CONFLICT", "message": str(e)}), 409

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": "UNPROCESSABLE", "message": str(e)}), 422

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal error: {e}")
        return jsonify({"error": "INTERNAL_ERROR", "message": "An internal error occurred"}), 500

    return app
