"""
Generation Service — triggers data generation via Supabase.
"""
import hashlib
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from app.extensions import get_supabase

logger = logging.getLogger(__name__)


def trigger_generation(mode="starter", seed=20261022, config_overrides=None):
    sb = get_supabase()
    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "run_code": f"GEN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "mode": mode,
        "seed": seed,
        "status": "RUNNING",
        "configuration": config_overrides or {},
    }
    sb.table("generation_run").insert(run).execute()

    from flask import current_app
    app = current_app._get_current_object()
    thread = threading.Thread(target=_run_generation, args=(app, run_id, mode, seed), daemon=False)
    thread.start()

    return run


def _run_generation(app, run_id, mode, seed):
    with app.app_context():
        sb = get_supabase()
        try:
            from app.generators.master_generator import generate_all
            counts = generate_all(mode=mode, seed=seed, run_id=run_id)
            checksum = hashlib.sha256(json.dumps(counts, sort_keys=True).encode()).hexdigest()
            sb.table("generation_run").update({
                "entity_counts": counts,
                "status": "COMPLETED",
                "completed_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "checksum": checksum,
            }).eq("id", run_id).execute()
            logger.info(f"Generation run {run_id} completed: {counts}")
        except Exception as e:
            logger.error(f"Generation run {run_id} failed: {e}", exc_info=True)
            try:
                sb.table("generation_run").update({
                    "status": "FAILED",
                    "completed_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                }).eq("id", run_id).execute()
            except Exception:
                pass
