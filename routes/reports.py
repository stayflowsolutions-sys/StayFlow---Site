from flask import Blueprint, jsonify
from database import get_reports_summary
from utils.tenant import require_permission

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports", methods=["GET"])
@require_permission("reports")
def reports(hostel_id):
    return jsonify(get_reports_summary(hostel_id))
