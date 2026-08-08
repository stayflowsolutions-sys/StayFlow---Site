from flask import Blueprint, jsonify, request

from database import (
    create_event_space,
    get_event_spaces,
    get_event_space,
    update_event_space,
    create_event,
    get_events,
    get_event,
    update_event,
    update_event_status,
    create_event_addon,
    get_event_addons,
    update_event_addon,
    add_event_addon_selection,
    remove_event_addon_selection,
    get_events_summary,
    check_event_space_conflict,
)
from utils.tenant import require_permission, require_plan_feature

events_bp = Blueprint("events", __name__)


# ===== Espaços =====

@events_bp.route("/events/spaces", methods=["GET"])
@require_permission("events")
@require_plan_feature("events")
def list_event_spaces(hostel_id):
    include_inactive = request.args.get("include_inactive") == "1"
    return jsonify(get_event_spaces(hostel_id, include_inactive=include_inactive))


@events_bp.route("/events/spaces", methods=["POST"])
@require_permission("events")
@require_plan_feature("events")
def create_event_space_route(hostel_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"success": False, "message": "Nome do espaço é obrigatório."}), 400

    space_id = create_event_space(
        hostel_id, name,
        capacity_seated=data.get("capacity_seated"),
        capacity_standing=data.get("capacity_standing"),
        price_per_event=data.get("price_per_event") or 0,
        description=data.get("description"),
    )
    return jsonify({"success": True, "space_id": space_id})


@events_bp.route("/events/spaces/<int:space_id>", methods=["PATCH"])
@require_permission("events")
@require_plan_feature("events")
def update_event_space_route(hostel_id, space_id):
    data = request.get_json() or {}
    updated = update_event_space(hostel_id, space_id, **data)

    if not updated:
        return jsonify({"success": False, "message": "Espaço não encontrado."}), 404

    return jsonify({"success": True})


# ===== Adicionais =====

@events_bp.route("/events/addons", methods=["GET"])
@require_permission("events")
@require_plan_feature("events")
def list_event_addons(hostel_id):
    include_inactive = request.args.get("include_inactive") == "1"
    return jsonify(get_event_addons(hostel_id, include_inactive=include_inactive))


@events_bp.route("/events/addons", methods=["POST"])
@require_permission("events")
@require_plan_feature("events")
def create_event_addon_route(hostel_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"success": False, "message": "Nome do adicional é obrigatório."}), 400

    addon_id = create_event_addon(hostel_id, name, price=data.get("price") or 0, unit=data.get("unit"))
    return jsonify({"success": True, "addon_id": addon_id})


@events_bp.route("/events/addons/<int:addon_id>", methods=["PATCH"])
@require_permission("events")
@require_plan_feature("events")
def update_event_addon_route(hostel_id, addon_id):
    data = request.get_json() or {}
    updated = update_event_addon(hostel_id, addon_id, **data)

    if not updated:
        return jsonify({"success": False, "message": "Adicional não encontrado."}), 404

    return jsonify({"success": True})


# ===== Eventos =====

@events_bp.route("/events", methods=["GET"])
@require_permission("events")
@require_plan_feature("events")
def list_events(hostel_id):
    status = request.args.get("status")
    upcoming_only = request.args.get("upcoming_only") == "1"
    return jsonify(get_events(hostel_id, status=status, upcoming_only=upcoming_only))


@events_bp.route("/events/availability", methods=["GET"])
@require_permission("events")
@require_plan_feature("events")
def check_event_availability(hostel_id):
    space_id = request.args.get("space_id", type=int)
    start = request.args.get("start")
    end = request.args.get("end")
    exclude_event_id = request.args.get("exclude_event_id", type=int)

    if not space_id or not start or not end:
        return jsonify({"success": False, "message": "space_id, start e end são obrigatórios."}), 400

    conflict = check_event_space_conflict(hostel_id, space_id, start, end, exclude_event_id=exclude_event_id)
    return jsonify({"success": True, "available": not conflict})


@events_bp.route("/events", methods=["POST"])
@require_permission("events")
@require_plan_feature("events")
def create_event_route(hostel_id):
    data = request.get_json() or {}
    client_name = (data.get("client_name") or "").strip()
    space_id = data.get("space_id")
    start_datetime = data.get("start_datetime")
    end_datetime = data.get("end_datetime")

    if not client_name or not space_id or not start_datetime or not end_datetime:
        return jsonify({"success": False, "message": "Espaço, cliente e período são obrigatórios."}), 400

    try:
        event_id = create_event(
            hostel_id, space_id, client_name, start_datetime, end_datetime,
            client_phone=data.get("client_phone"),
            client_email=data.get("client_email"),
            guest_id=data.get("guest_id"),
            event_type=data.get("event_type"),
            title=data.get("title"),
            expected_guests=data.get("expected_guests"),
            base_price=data.get("base_price"),
            notes=data.get("notes"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 409

    return jsonify({"success": True, "event_id": event_id})


@events_bp.route("/events/<int:event_id>", methods=["GET"])
@require_permission("events")
@require_plan_feature("events")
def get_event_route(hostel_id, event_id):
    event = get_event(hostel_id, event_id)
    if not event:
        return jsonify({"success": False, "message": "Evento não encontrado."}), 404
    return jsonify({"success": True, "event": event})


@events_bp.route("/events/<int:event_id>", methods=["PATCH"])
@require_permission("events")
@require_plan_feature("events")
def update_event_route(hostel_id, event_id):
    data = request.get_json() or {}

    try:
        updated = update_event(hostel_id, event_id, **data)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 409

    if not updated:
        return jsonify({"success": False, "message": "Evento não encontrado."}), 404

    return jsonify({"success": True})


@events_bp.route("/events/<int:event_id>/status", methods=["POST"])
@require_permission("events")
@require_plan_feature("events")
def update_event_status_route(hostel_id, event_id):
    data = request.get_json() or {}
    status = data.get("status")

    try:
        updated = update_event_status(hostel_id, event_id, status)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    if not updated:
        return jsonify({"success": False, "message": "Evento não encontrado."}), 404

    return jsonify({"success": True})


@events_bp.route("/events/<int:event_id>/addons", methods=["POST"])
@require_permission("events")
@require_plan_feature("events")
def add_event_addon_route(hostel_id, event_id):
    data = request.get_json() or {}
    addon_id = data.get("addon_id")

    if not addon_id:
        return jsonify({"success": False, "message": "addon_id é obrigatório."}), 400

    try:
        selection_id = add_event_addon_selection(hostel_id, event_id, addon_id, quantity=data.get("quantity") or 1)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404

    return jsonify({"success": True, "selection_id": selection_id})


@events_bp.route("/events/<int:event_id>/addons/<int:selection_id>", methods=["DELETE"])
@require_permission("events")
@require_plan_feature("events")
def remove_event_addon_route(hostel_id, event_id, selection_id):
    removed = remove_event_addon_selection(hostel_id, event_id, selection_id)

    if not removed:
        return jsonify({"success": False, "message": "Adicional não encontrado neste evento."}), 404

    return jsonify({"success": True})


@events_bp.route("/events/summary", methods=["GET"])
@require_permission("events")
@require_plan_feature("events")
def events_summary_route(hostel_id):
    return jsonify(get_events_summary(hostel_id))
