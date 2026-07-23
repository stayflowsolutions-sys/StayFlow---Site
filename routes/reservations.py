from flask import Blueprint, jsonify, request

from database import (
    get_reservations_with_stats,
    create_reservation_record,
    update_reservation_status_record,
)
from utils.tenant import require_permission

reservations_bp = Blueprint("reservations", __name__)


@reservations_bp.route("/reservations", methods=["GET"])
@require_permission("reservations")
def list_reservations(hostel_id):
    return jsonify(get_reservations_with_stats(hostel_id))


@reservations_bp.route("/reservations", methods=["POST"])
@require_permission("reservations")
def create_reservation(hostel_id):
    data = request.get_json() or {}

    try:
        reservation_id = create_reservation_record(
            hostel_id,
            guest_name=data.get("guest_name"),
            room_type=data.get("room_type"),
            bed=data.get("bed"),
            checkin_date=data.get("checkin_date"),
            checkout_date=data.get("checkout_date"),
            source=data.get("source"),
            payment_method=data.get("payment_method"),
            amount=data.get("amount"),
            status=data.get("status"),
            phone=data.get("phone"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, "id": reservation_id}), 201


@reservations_bp.route("/reservations/<int:reservation_id>", methods=["PATCH"])
@require_permission("reservations")
def update_reservation(hostel_id, reservation_id):
    data = request.get_json() or {}

    if "status" in data:
        try:
            update_reservation_status_record(hostel_id, reservation_id, data["status"])
        except ValueError as error:
            return jsonify({"success": False, "message": str(error)}), 404

    return jsonify({"success": True})