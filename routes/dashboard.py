from flask import Blueprint, jsonify
from database import get_dashboard_stats
from utils.tenant import require_permission

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
@require_permission("dashboard")
def dashboard(hostel_id):
    return jsonify(get_dashboard_stats(hostel_id))
