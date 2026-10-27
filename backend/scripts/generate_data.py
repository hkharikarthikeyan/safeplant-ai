#!/usr/bin/env python3
"""
generate_data.py — CLI for deterministic data generation.

Usage:
    python scripts/generate_data.py --mode starter --seed 20261022
    python scripts/generate_data.py --mode full --seed 20261022
    python scripts/generate_data.py --mode full --seed 20261022 --output-dir ../data/full
"""
import argparse
import logging
import os
import sys

# Ensure backend root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="SafePlant AI — Deterministic Data Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode", choices=["starter", "full"], default="starter",
        help="Generation mode: 'starter' (1 plant, 5 machines, 1000 alarms) or 'full' (4 plants, 60 machines, 50000 alarms)"
    )
    parser.add_argument(
        "--seed", type=int, default=20261022,
        help="Fixed random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir", default="../data",
        help="Output directory for exported files"
    )
    parser.add_argument(
        "--clear-existing", action="store_true",
        help="Clear existing data before generating (USE WITH CAUTION)"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export CSV/JSON/SQL files after generation"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Run validation checks after generation"
    )
    args = parser.parse_args()

    logger.info(f"SafePlant AI Data Generator")
    logger.info(f"Mode: {args.mode} | Seed: {args.seed}")
    logger.info(f"Generation period: 2026-10-01 to 2026-10-30 (30 days)")

    from app import create_app
    from app.extensions import db
    app = create_app()

    with app.app_context():
        if args.clear_existing:
            logger.warning("Clearing existing data...")
            _clear_all_data(db)

        from app.models import GenerationRun
        from datetime import datetime, timezone

        run = GenerationRun(
            run_code=f"GEN-CLI-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            mode=args.mode,
            seed=args.seed,
            status="RUNNING",
            configuration={"cli": True, "output_dir": args.output_dir},
        )
        db.session.add(run)
        db.session.commit()

        try:
            from app.generators.master_generator import generate_all
            counts = generate_all(mode=args.mode, seed=args.seed, run_id=run.id)

            import hashlib, json
            checksum = hashlib.sha256(json.dumps(counts, sort_keys=True).encode()).hexdigest()
            run.entity_counts = counts
            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run.checksum = checksum
            db.session.commit()

            logger.info("=" * 60)
            logger.info("GENERATION COMPLETE")
            logger.info("=" * 60)
            for entity, count in counts.items():
                logger.info(f"  {entity:35s}: {count:>8,}")
            logger.info(f"  Checksum: {checksum[:16]}...")

            if args.validate:
                logger.info("Running validation checks...")
                from app.services.validation_service import run_validation
                report = run_validation(generation_run_id=run.id)
                logger.info(f"  Validation: {report.overall_status} "
                            f"({report.passed_checks}/{report.total_checks} checks passed)")
                logger.info(f"  Expected anomalies: {report.expected_anomalies}")
                logger.info(f"  Unexpected failures: {report.unexpected_failures}")

            if args.export:
                logger.info("Exporting data files...")
                _export_all(args.output_dir, args.mode)

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            run.status = "FAILED"
            run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.session.commit()
            sys.exit(1)


def _clear_all_data(db):
    """Clear all generated data (preserves schema)."""
    from app.models import (
        CorrectiveActionEvent, CorrectiveAction, IncidentStateEvent,
        IncidentAlarm, Incident, Acknowledgement, AlarmEvent,
        MachineStateEvent, InterlockStateEvent, AlarmDefinition,
        MachineInterlock, MachineSafetyZone, OperatorShift,
        Interlock, SafetyZone, Machine, Plant, GenerationRun, ValidationRun,
    )
    tables = [
        CorrectiveActionEvent, CorrectiveAction, IncidentStateEvent,
        IncidentAlarm, Incident, Acknowledgement, AlarmEvent,
        MachineStateEvent, InterlockStateEvent, AlarmDefinition,
        MachineInterlock, MachineSafetyZone, OperatorShift,
        Interlock, SafetyZone, Machine, Plant, ValidationRun, GenerationRun,
    ]
    for model in tables:
        db.session.query(model).delete()
    db.session.commit()


def _export_all(output_dir, mode):
    """Export all data files."""
    import os
    mode_dir = os.path.join(output_dir, mode)
    os.makedirs(mode_dir, exist_ok=True)
    from app.services.export_service import (
        export_alarms_csv, export_incidents_csv,
        export_anomalies_csv, export_validation_json,
    )
    for fn, name in [
        (export_alarms_csv, "alarms"),
        (export_incidents_csv, "incidents"),
        (export_anomalies_csv, "anomalies"),
    ]:
        content, filename = fn()
        path = os.path.join(mode_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        logger.info(f"  Exported: {path}")

    content, filename = export_validation_json()
    path = os.path.join(mode_dir, filename)
    with open(path, "w") as f:
        f.write(content)
    logger.info(f"  Exported: {path}")


if __name__ == "__main__":
    main()
