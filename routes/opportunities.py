from flask import Blueprint, jsonify, request
from database import get_opportunities_list
from services.translation_service import translate_opportunity_fields
from utils.tenant import require_permission

opportunities_bp = Blueprint("opportunities", __name__)


@opportunities_bp.route("/opportunities", methods=["GET"])
@require_permission("opportunities")
def opportunities(hostel_id):
    lang = request.args.get("lang", "pt")
    data = get_opportunities_list(hostel_id)
    data = translate_opportunity_fields(data, lang)
    return jsonify(data)
