from flask import Blueprint, jsonify
from database import get_guests_list, get_guest_profile
from utils.tenant import require_permission

guests_bp = Blueprint("guests", __name__)


@guests_bp.route("/guests", methods=["GET"])
@require_permission("guests")
def list_guests(hostel_id):
    return jsonify(get_guests_list(hostel_id))


@guests_bp.route("/guests/<int:guest_id>", methods=["GET"])
@require_permission("guests")
def guest_profile(hostel_id, guest_id):
    profile = get_guest_profile(hostel_id, guest_id)

    if not profile:
        return jsonify({"error": "Guest not found"}), 404

    return jsonify(profile)
