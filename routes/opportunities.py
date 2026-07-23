from flask import Blueprint, jsonify
from database import get_opportunities_list
from utils.tenant import require_permission

opportunities_bp = Blueprint("opportunities", __name__)


@opportunities_bp.route("/opportunities", methods=["GET"])
@require_permission("opportunities")
def opportunities(hostel_id):
    return jsonify(get_opportunities_list(hostel_id))
