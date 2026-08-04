"""
Seguranca PATRIMONIAL/fisica do predio (cameras, incidentes, controle
de acesso) - modulo novo, NAO confundir com routes/security.py (que e
seguranca da CONTA: trocar senha, sessoes, tentativas de login).
Nomes de arquivo/blueprint/URL deliberadamente diferentes pra nunca
colidir.
"""

from flask import Blueprint, request, jsonify

from database import (
    create_security_incident,
    get_open_tickets,
    get_ticket,
    assign_ticket,
    resolve_ticket,
    get_hostel_system_integration,
    set_hostel_system_integration,
    notify_on_duty_staff_for_ticket,
)
from utils.tenant import require_permission

patrimonial_security_bp = Blueprint("patrimonial_security", __name__)


@patrimonial_security_bp.route("/patrimonial-security/incidents", methods=["GET"])
@require_permission("patrimonial_security")
def list_security_incidents(hostel_id):
    return jsonify(get_open_tickets(hostel_id, ticket_type="security_incident"))


@patrimonial_security_bp.route("/patrimonial-security/incidents", methods=["POST"])
@require_permission("patrimonial_security")
def create_security_incident_route(hostel_id):
    """
    Criacao manual (equipe registrando ronda/ocorrencia) - quando o
    relato vem de um hospede pelo chat ("vi algo suspeito"), a IA chama
    create_security_incident direto (routes/chat.py).
    """
    data = request.get_json() or {}
    location = (data.get("location") or "").strip()
    description = (data.get("description") or "").strip()

    if not location or not description:
        return jsonify({"success": False, "message": "location and description are required."}), 400

    ticket_id = create_security_incident(
        hostel_id, location, description,
        incident_type=data.get("incident_type"),
        reported_via=data.get("reported_via", "staff_patrol"),
        base_urgency=data.get("base_urgency", "high"),
        channel=data.get("channel", "dashboard"),
    )

    section_id = data.get("section_id")
    notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "patrimonial_security", section_id)

    return jsonify({"success": True, "id": ticket_id}), 201


@patrimonial_security_bp.route("/patrimonial-security/incidents/<int:ticket_id>/assign", methods=["POST"])
@require_permission("patrimonial_security")
def assign_security_incident_route(hostel_id, ticket_id):
    data = request.get_json() or {}
    membership_id = data.get("membership_id")
    if not membership_id:
        return jsonify({"success": False, "message": "membership_id is required."}), 400

    updated = assign_ticket(hostel_id, ticket_id, membership_id)
    if not updated:
        return jsonify({"success": False, "message": "Incidente não encontrado."}), 404
    return jsonify({"success": True})


@patrimonial_security_bp.route("/patrimonial-security/incidents/<int:ticket_id>/resolve", methods=["POST"])
@require_permission("patrimonial_security")
def resolve_security_incident_route(hostel_id, ticket_id):
    data = request.get_json() or {}
    updated = resolve_ticket(hostel_id, ticket_id, resolution_notes=data.get("resolution_notes"))
    if not updated:
        return jsonify({"success": False, "message": "Incidente não encontrado."}), 404
    return jsonify({"success": True})


@patrimonial_security_bp.route("/patrimonial-security/integrations/<capability>", methods=["GET"])
@require_permission("patrimonial_security")
def get_integration_route(hostel_id, capability):
    return jsonify(get_hostel_system_integration(hostel_id, capability))


@patrimonial_security_bp.route("/patrimonial-security/integrations/<capability>", methods=["POST"])
@require_permission("patrimonial_security")
def set_integration_route(hostel_id, capability):
    """
    provider default 'manual_fallback' de proposito - so vira 'api'
    quando o hotel confirmar de verdade o sistema (camera/acesso/PBX)
    que usa. Nunca fica sem caminho nenhum (ver get_hostel_system_
    integration, que devolve fallback implicito mesmo sem nenhuma
    linha configurada ainda).
    """
    data = request.get_json() or {}
    set_hostel_system_integration(
        hostel_id, capability,
        provider=data.get("provider", "manual_fallback"),
        config=data.get("config"),
        fallback_phone_number=data.get("fallback_phone_number"),
    )
    return jsonify({"success": True})
