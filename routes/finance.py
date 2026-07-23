from flask import Blueprint, jsonify
from database import get_finance_summary
from utils.tenant import require_permission

finance_bp = Blueprint("finance", __name__)


@finance_bp.route("/finance", methods=["GET"])
@require_permission("finance")
def finance(hostel_id):
    return jsonify(get_finance_summary(hostel_id))
