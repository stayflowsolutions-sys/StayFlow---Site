from flask import Blueprint, jsonify, request

from database import (
    get_connection,
    list_agencies,
    list_portfolio_items,
    list_partner_offers,
    set_partner_offer,
)
from utils.tenant import require_permission

partners_bp = Blueprint("partners", __name__)


@partners_bp.route("/partners", methods=["GET"])
@require_permission("partners")
def list_partners_route(hostel_id):
    return jsonify({"success": True, "agencies": list_agencies()})


@partners_bp.route("/partners/<int:agency_hostel_id>/items", methods=["GET"])
@require_permission("partners")
def list_partner_items_route(hostel_id, agency_hostel_id):
    items = list_portfolio_items(agency_hostel_id, include_inactive=False)
    enabled_ids = set(list_partner_offers(hostel_id))
    for item in items:
        item["enabled"] = item["id"] in enabled_ids
    return jsonify({"success": True, "items": items})


@partners_bp.route("/partners/opt-in", methods=["POST"])
@require_permission("partners")
def set_partner_opt_in_route(hostel_id):
    data = request.get_json() or {}
    portfolio_item_id = data.get("portfolio_item_id")
    enabled = bool(data.get("enabled", True))

    if not portfolio_item_id:
        return jsonify({"success": False, "message": "portfolio_item_id é obrigatório."}), 400

    # portfolio_item_id sempre validado contra a tabela real - nunca
    # confiamos que o item existe so porque o cliente mandou um id.
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM portfolio_items WHERE id = ? AND active = 1", (portfolio_item_id,))
    exists = cursor.fetchone()
    conn.close()
    if not exists:
        return jsonify({"success": False, "message": "Item de portfólio não encontrado."}), 404

    set_partner_offer(hostel_id, portfolio_item_id, enabled)
    return jsonify({"success": True})
