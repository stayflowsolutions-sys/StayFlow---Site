from flask import Blueprint, request, jsonify

from database import (
    create_maintenance_ticket,
    get_open_tickets,
    get_ticket,
    assign_ticket,
    resolve_ticket,
    update_ticket_status,
    get_recurring_maintenance_alerts,
    notify_on_duty_staff_for_ticket,
)
from utils.tenant import require_permission

maintenance_bp = Blueprint("maintenance", __name__)


@maintenance_bp.route("/maintenance/tickets", methods=["GET"])
@require_permission("maintenance")
def list_maintenance_tickets(hostel_id):
    return jsonify(get_open_tickets(hostel_id, ticket_type="maintenance"))


@maintenance_bp.route("/maintenance/tickets", methods=["POST"])
@require_permission("maintenance")
def create_maintenance_ticket_route(hostel_id):
    """
    Criacao manual (equipe relatando algo, ex: ronda de manutencao
    preventiva) - quando o relato vem de um hospede pelo chat, a IA
    chama create_maintenance_ticket direto (routes/chat.py), sem passar
    por essa rota.
    """
    data = request.get_json() or {}
    location = (data.get("location") or "").strip()
    description = (data.get("description") or "").strip()

    if not location or not description:
        return jsonify({"success": False, "message": "location and description are required."}), 400

    ticket_id = create_maintenance_ticket(
        hostel_id, location, description,
        category=data.get("category"),
        guest_reported_urgency=data.get("guest_reported_urgency"),
        base_urgency=data.get("base_urgency", "normal"),
        channel=data.get("channel", "dashboard"),
    )

    section_id = data.get("section_id")
    notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "maintenance", section_id)

    return jsonify({"success": True, "id": ticket_id}), 201


@maintenance_bp.route("/maintenance/tickets/<int:ticket_id>", methods=["GET"])
@require_permission("maintenance")
def get_maintenance_ticket_route(hostel_id, ticket_id):
    ticket = get_ticket(hostel_id, ticket_id)
    if not ticket:
        return jsonify({"success": False, "message": "Chamado não encontrado."}), 404
    return jsonify(ticket)


@maintenance_bp.route("/maintenance/tickets/<int:ticket_id>/assign", methods=["POST"])
@require_permission("maintenance")
def assign_maintenance_ticket_route(hostel_id, ticket_id):
    data = request.get_json() or {}
    membership_id = data.get("membership_id")
    if not membership_id:
        return jsonify({"success": False, "message": "membership_id is required."}), 400

    updated = assign_ticket(hostel_id, ticket_id, membership_id)
    if not updated:
        return jsonify({"success": False, "message": "Chamado não encontrado."}), 404
    return jsonify({"success": True})


@maintenance_bp.route("/maintenance/tickets/<int:ticket_id>/in-progress", methods=["POST"])
@require_permission("maintenance")
def start_maintenance_ticket_route(hostel_id, ticket_id):
    updated = update_ticket_status(hostel_id, ticket_id, "in_progress")
    if not updated:
        return jsonify({"success": False, "message": "Chamado não encontrado."}), 404
    return jsonify({"success": True})


@maintenance_bp.route("/maintenance/tickets/<int:ticket_id>/resolve", methods=["POST"])
@require_permission("maintenance")
def resolve_maintenance_ticket_route(hostel_id, ticket_id):
    data = request.get_json() or {}
    updated = resolve_ticket(hostel_id, ticket_id, resolution_notes=data.get("resolution_notes"))
    if not updated:
        return jsonify({"success": False, "message": "Chamado não encontrado."}), 404
    return jsonify({"success": True})


@maintenance_bp.route("/maintenance/recurring-alerts", methods=["GET"])
@require_permission("maintenance")
def recurring_maintenance_alerts_route(hostel_id):
    window_days = request.args.get("window_days", 30, type=int)
    threshold = request.args.get("threshold", 3, type=int)
    return jsonify(get_recurring_maintenance_alerts(hostel_id, window_days=window_days, threshold=threshold))
