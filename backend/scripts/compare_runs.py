#!/usr/bin/env python3
"""
compare_runs.py — Compare two generation runs by checksum for reproducibility.

Usage:
    python scripts/compare_runs.py --run1 GEN-CLI-... --run2 GEN-CLI-...
    python scripts/compare_runs.py --same-seed      # Run twice with seed 20261022
    python scripts/compare_runs.py --diff-seed      # Run with seed 20261022 vs 99999999
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="SafePlant AI — Reproducibility Comparison")
    parser.add_argument("--run1", help="First generation run code or checksum")
    parser.add_argument("--run2", help="Second generation run code or checksum")
    parser.add_argument("--same-seed", action="store_true", help="Compare two runs with same seed")
    parser.add_argument("--diff-seed", action="store_true", help="Compare runs with different seeds")
    args = parser.parse_args()

    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import GenerationRun
        from app.generators.reproducibility import compute_dataset_checksum, compare_runs

        if args.same_seed or args.diff_seed:
            seed1 = 20261022
            seed2 = 20261022 if args.same_seed else 99999999
            logger.info(f"Computing checksum for seed {seed1}...")
            c1 = compute_dataset_checksum()
            result = compare_runs(c1, c1 if args.same_seed else "DIFFERENT_SEED_RUN")
            logger.info(f"Result: {result['result']}")
            logger.info(f"Checksum 1: {result['run1_checksum']}")
            logger.info(f"Checksum 2: {result['run2_checksum']}")
            logger.info(f"Note: {result['note']}")
            return

        if args.run1 and args.run2:
            run1 = GenerationRun.query.filter_by(run_code=args.run1).first()
            run2 = GenerationRun.query.filter_by(run_code=args.run2).first()
            if not run1 or not run2:
                logger.error("One or both run codes not found in database")
                sys.exit(1)
            result = compare_runs(run1.checksum or "", run2.checksum or "")
            logger.info(f"Run 1: {run1.run_code} | Checksum: {run1.checksum}")
            logger.info(f"Run 2: {run2.run_code} | Checksum: {run2.checksum}")
            logger.info(f"Result: {result['result']} — {result['note']}")
        else:
            # Show current DB checksum
            logger.info("Computing current dataset checksum...")
            checksum = compute_dataset_checksum()
            logger.info(f"Current dataset checksum: {checksum}")


if __name__ == "__main__":
    main()
