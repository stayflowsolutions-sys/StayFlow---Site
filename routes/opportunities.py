from flask import Blueprint, jsonify, request
from database import get_opportunities_list
from services.translation_service import translate_opportunity_fields
from utils.tenant import require_permission

opportunities_bp = Blueprint("opportunities", __name__)


@opportunities_bp.route("/opportunities", methods=["GET"])
@require_permission("opportunities")
def opportunities(hostel_id):
    lang = request.args.get("lang", "pt")
    sort = request.args.get("sort", "recent")

    try:
        limit = min(max(int(request.args.get("limit", 20)), 1), 100)
    except (TypeError, ValueError):
        limit = 20
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except (TypeError, ValueError):
        offset = 0

    result = get_opportunities_list(hostel_id, limit=limit, offset=offset, sort=sort)
    result["items"] = translate_opportunity_fields(result["items"], lang)
    return jsonify(result)
