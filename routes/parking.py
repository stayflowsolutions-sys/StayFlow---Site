from flask import Blueprint, request, jsonify

from database import (
    check_in_vehicle,
    check_out_vehicle,
    request_valet,
    get_hostel_parking_settings,
    set_hostel_parking_settings,
    get_open_tickets,
    notify_on_duty_staff_for_ticket,
)
from utils.tenant import require_permission

parking_bp = Blueprint("parking", __name__)


@parking_bp.route("/parking/vehicles", methods=["POST"])
@require_permission("parking")
def check_in_vehicle_route(hostel_id):
    data = request.get_json() or {}
    guest_id = data.get("guest_id")

    if not guest_id:
        return jsonify({"success": False, "message": "guest_id is required."}), 400

    vehicle_id = check_in_vehicle(
        hostel_id, guest_id,
        plate=data.get("plate"),
        model=data.get("model"),
        color=data.get("color"),
        spot_number=data.get("spot_number"),
        service_type=data.get("service_type", "autoatendimento"),
        reservation_id=data.get("reservation_id"),
    )
    return jsonify({"success": True, "id": vehicle_id}), 201


@parking_bp.route("/parking/vehicles/<int:vehicle_id>/checkout", methods=["POST"])
@require_permission("parking")
def check_out_vehicle_route(hostel_id, vehicle_id):
    updated = check_out_vehicle(hostel_id, vehicle_id)
    if not updated:
        return jsonify({"success": False, "message": "Veículo não encontrado ou já com saída registrada."}), 404
    return jsonify({"success": True})


@parking_bp.route("/parking/vehicles/<int:vehicle_id>/valet-request", methods=["POST"])
@require_permission("parking")
def request_valet_route(hostel_id, vehicle_id):
    """
    "Traz meu carro" - quando o pedido vem do hospede pelo chat, a IA
    chama request_valet direto (routes/chat.py); esta rota e pro caso
    de a propria equipe registrar o pedido manualmente.
    """
    data = request.get_json() or {}
    ticket_id = request_valet(hostel_id, vehicle_id, channel=data.get("channel", "dashboard"))

    section_id = data.get("section_id")
    notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "parking", section_id)

    return jsonify({"success": True, "id": ticket_id}), 201


@parking_bp.route("/parking/valet-requests", methods=["GET"])
@require_permission("parking")
def list_valet_requests(hostel_id):
    return jsonify(get_open_tickets(hostel_id, ticket_type="valet_request"))


@parking_bp.route("/parking/settings", methods=["GET"])
@require_permission("parking")
def get_parking_settings_route(hostel_id):
    return jsonify(get_hostel_parking_settings(hostel_id))


@parking_bp.route("/parking/settings", methods=["POST"])
@require_permission("parking")
def set_parking_settings_route(hostel_id):
    data = request.get_json() or {}
    pricing_model = data.get("pricing_model", "incluso")

    if pricing_model not in ("incluso", "cobrado", "por_categoria"):
        return jsonify({"success": False, "message": "pricing_model inválido."}), 400

    set_hostel_parking_settings(
        hostel_id, pricing_model,
        daily_rate=data.get("daily_rate", 0),
        included_for_categories=data.get("included_for_categories"),
    )
    return jsonify({"success": True})
