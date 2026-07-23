from flask import Blueprint, jsonify, request

from database import (
    create_room_category,
    list_room_categories,
    delete_room_category,
    create_room,
    create_rooms_bulk,
    list_rooms,
    delete_room,
    create_bed,
    delete_bed,
    update_bed_label,
    get_bed_map,
    get_cleaning_list,
    set_linen_kit,
    get_linen_kit,
    checkin_reservation_to_bed,
    checkout_reservation_bed,
    mark_bed_cleaned,
    return_items_from_laundry,
    set_bed_maintenance,
)
from utils.tenant import require_permission

rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.route("/bed-map", methods=["GET"])
@require_permission("operations")
def bed_map(hostel_id):
    return jsonify(get_bed_map(hostel_id))


@rooms_bp.route("/cleaning-list", methods=["GET"])
@require_permission("operations")
def cleaning_list(hostel_id):
    return jsonify(get_cleaning_list(hostel_id))


@rooms_bp.route("/room-categories", methods=["GET"])
@require_permission("operations")
def room_categories_route(hostel_id):
    return jsonify(list_room_categories(hostel_id))


@rooms_bp.route("/room-categories", methods=["POST"])
@require_permission("operations")
def create_room_category_route(hostel_id):
    data = request.get_json() or {}
    try:
        category_id = create_room_category(
            hostel_id, data.get("name"), data.get("capacity"),
            data.get("price_per_night"), data.get("description"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, "id": category_id}), 201


@rooms_bp.route("/room-categories/<int:category_id>", methods=["DELETE"])
@require_permission("operations")
def delete_room_category_route(hostel_id, category_id):
    try:
        delete_room_category(hostel_id, category_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404
    return jsonify({"success": True})


@rooms_bp.route("/rooms", methods=["GET"])
@require_permission("operations")
def rooms(hostel_id):
    return jsonify(list_rooms(hostel_id))


@rooms_bp.route("/rooms", methods=["POST"])
@require_permission("operations")
def create_room_route(hostel_id):
    data = request.get_json() or {}
    try:
        room_id = create_room(hostel_id, data.get("name"), data.get("category_name"), data.get("floor"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, "id": room_id}), 201


@rooms_bp.route("/rooms/bulk", methods=["POST"])
@require_permission("operations")
def create_rooms_bulk_route(hostel_id):
    data = request.get_json() or {}
    try:
        room_ids = create_rooms_bulk(hostel_id, data.get("names", []), data.get("category_name"), data.get("floor"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, "ids": room_ids, "count": len(room_ids)}), 201


@rooms_bp.route("/rooms/<int:room_id>", methods=["DELETE"])
@require_permission("operations")
def delete_room_route(hostel_id, room_id):
    try:
        delete_room(hostel_id, room_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404
    return jsonify({"success": True})


@rooms_bp.route("/rooms/<int:room_id>/beds", methods=["POST"])
@require_permission("operations")
def create_bed_route(hostel_id, room_id):
    data = request.get_json() or {}
    try:
        bed_id = create_bed(
            hostel_id, room_id,
            label=data.get("label"),
            bed_kind=data.get("bed_kind", "single"),
            bunk_group=data.get("bunk_group"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, "id": bed_id}), 201


@rooms_bp.route("/beds/<int:bed_id>", methods=["DELETE"])
@require_permission("operations")
def delete_bed_route(hostel_id, bed_id):
    try:
        delete_bed(hostel_id, bed_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True})


@rooms_bp.route("/beds/<int:bed_id>", methods=["PATCH"])
@require_permission("operations")
def update_bed_route(hostel_id, bed_id):
    data = request.get_json() or {}
    try:
        update_bed_label(hostel_id, bed_id, data.get("label"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True})


@rooms_bp.route("/beds/<int:bed_id>/mark-cleaned", methods=["POST"])
@require_permission("operations")
def mark_bed_cleaned_route(hostel_id, bed_id):
    try:
        result = mark_bed_cleaned(hostel_id, bed_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, **result})


@rooms_bp.route("/beds/<int:bed_id>/maintenance", methods=["POST"])
@require_permission("operations")
def set_bed_maintenance_route(hostel_id, bed_id):
    data = request.get_json() or {}
    try:
        result = set_bed_maintenance(hostel_id, bed_id, bool(data.get("under_maintenance", True)))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, **result})


@rooms_bp.route("/reservations/<int:reservation_id>/checkin", methods=["POST"])
@require_permission("operations")
def checkin_route(hostel_id, reservation_id):
    data = request.get_json() or {}
    bed_id = data.get("bed_id")
    if not bed_id:
        return jsonify({"success": False, "message": "bed_id is required."}), 400
    try:
        result = checkin_reservation_to_bed(hostel_id, reservation_id, bed_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, **result})


@rooms_bp.route("/reservations/<int:reservation_id>/checkout", methods=["POST"])
@require_permission("operations")
def checkout_route(hostel_id, reservation_id):
    try:
        result = checkout_reservation_bed(hostel_id, reservation_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, **result})


@rooms_bp.route("/linen-kits/<bed_kind>", methods=["GET"])
@require_permission("operations")
def linen_kit_route(hostel_id, bed_kind):
    return jsonify(get_linen_kit(hostel_id, bed_kind))


@rooms_bp.route("/linen-kits/<bed_kind>", methods=["POST"])
@require_permission("operations")
def set_linen_kit_route(hostel_id, bed_kind):
    data = request.get_json() or {}
    try:
        result = set_linen_kit(hostel_id, bed_kind, data.get("items", []))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, **result})


@rooms_bp.route("/inventory/return-from-laundry", methods=["POST"])
@require_permission("operations")
def return_from_laundry_route(hostel_id):
    data = request.get_json() or {}
    try:
        result = return_items_from_laundry(hostel_id, data.get("item_name"), data.get("quantity", 0))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, **result})
