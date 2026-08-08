from flask import Blueprint, request, jsonify

from database import (
    check_in_vehicle,
    check_out_vehicle,
    list_active_vehicles,
    request_valet,
    get_hostel_parking_settings,
    set_hostel_parking_settings,
    get_open_tickets,
    notify_on_duty_staff_for_ticket,
    resolve_ticket,
)
from utils.tenant import require_permission, require_plan_feature

parking_bp = Blueprint("parking", __name__)


@parking_bp.route("/parking/vehicles", methods=["GET"])
@require_permission("parking")
@require_plan_feature("parking")
def list_active_vehicles_route(hostel_id):
    return jsonify(list_active_vehicles(hostel_id))


@parking_bp.route("/parking/vehicles", methods=["POST"])
@require_permission("parking")
@require_plan_feature("parking")
def check_in_vehicle_route(hostel_id):
    """
    guest_id OU guest_name - o manobrista pode registrar o carro de
    alguem que chegou na hora, sem hospede formal cadastrado ainda
    (digita so o nome; guest_id continua o caminho normal quando o
    hospede ja existe no sistema).
    """
    data = request.get_json() or {}
    guest_id = data.get("guest_id")
    guest_name = (data.get("guest_name") or "").strip() or None

    if not guest_id and not guest_name:
        return jsonify({"success": False, "message": "guest_id or guest_name is required."}), 400

    vehicle_id = check_in_vehicle(
        hostel_id, guest_id=guest_id, guest_name=guest_name,
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
@require_plan_feature("parking")
def check_out_vehicle_route(hostel_id, vehicle_id):
    updated = check_out_vehicle(hostel_id, vehicle_id)
    if not updated:
        return jsonify({"success": False, "message": "Veículo não encontrado ou já com saída registrada."}), 404
    return jsonify({"success": True})


@parking_bp.route("/parking/vehicles/<int:vehicle_id>/valet-request", methods=["POST"])
@require_permission("parking")
@require_plan_feature("parking")
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
@require_plan_feature("parking")
def list_valet_requests(hostel_id):
    return jsonify(get_open_tickets(hostel_id, ticket_type="valet_request"))


@parking_bp.route("/parking/valet-requests/<int:ticket_id>/resolve", methods=["POST"])
@require_permission("parking")
@require_plan_feature("parking")
def resolve_valet_request_route(hostel_id, ticket_id):
    data = request.get_json() or {}
    updated = resolve_ticket(hostel_id, ticket_id, resolution_notes=data.get("resolution_notes"))
    if not updated:
        return jsonify({"success": False, "message": "Solicitação não encontrada."}), 404
    return jsonify({"success": True})


@parking_bp.route("/parking/settings", methods=["GET"])
@require_permission("parking")
@require_plan_feature("parking")
def get_parking_settings_route(hostel_id):
    return jsonify(get_hostel_parking_settings(hostel_id))


@parking_bp.route("/parking/settings", methods=["POST"])
@require_permission("parking")
@require_plan_feature("parking")
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
