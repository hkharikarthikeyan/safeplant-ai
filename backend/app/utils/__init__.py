from flask import request, jsonify
from functools import wraps
from datetime import datetime, timezone
import uuid


def success_response(data, status_code=200, meta=None):
    response = {"status": "success", "data": data}
    if meta:
        response["meta"] = meta
    return jsonify(response), status_code


def error_response(error_code, message, status_code=400):
    return jsonify({"status": "error", "error": error_code, "message": message}), status_code


def get_pagination_params(default_per_page=50, max_per_page=500):
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(max_per_page, max(1, int(request.args.get("per_page", default_per_page))))
    offset = (page - 1) * per_page
    return page, per_page, offset


def pagination_meta(page, per_page, total):
    pages = (total + per_page - 1) // per_page if per_page else 1
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }


def write_audit(sb, entity_type, entity_id, action, actor="SYSTEM", before=None, after=None):
    sb.table("audit_log").insert({
        "id": str(uuid.uuid4()),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "actor": actor,
        "before_state": before,
        "after_state": after,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def require_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return error_response("BAD_REQUEST", "Content-Type must be application/json", 400)
        return f(*args, **kwargs)
    return decorated
