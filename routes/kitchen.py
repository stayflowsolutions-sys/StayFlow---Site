from flask import Blueprint, request, jsonify

from database import (
    create_menu_item,
    get_menu_items,
    set_menu_item_active,
    set_menu_item_ingredient,
    create_kitchen_order,
    get_kitchen_order_items,
    get_kitchen_order_aggregate_status,
    update_kitchen_order_item_status,
    get_open_tickets,
    notify_on_duty_staff_for_ticket,
    resolve_ticket,
)
from utils.tenant import require_permission

kitchen_bp = Blueprint("kitchen", __name__)


@kitchen_bp.route("/kitchen/menu", methods=["GET"])
@require_permission("kitchen")
def list_menu_items(hostel_id):
    active_only = request.args.get("active_only", "true").lower() != "false"
    return jsonify(get_menu_items(hostel_id, active_only=active_only))


@kitchen_bp.route("/kitchen/menu", methods=["POST"])
@require_permission("kitchen")
def create_menu_item_route(hostel_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "").strip()

    if not name or not category:
        return jsonify({"success": False, "message": "name and category are required."}), 400

    menu_item_id = create_menu_item(
        hostel_id, name, category,
        price=data.get("price", 0),
        station=data.get("station", "cozinha"),
    )
    return jsonify({"success": True, "id": menu_item_id}), 201


@kitchen_bp.route("/kitchen/menu/<int:menu_item_id>/active", methods=["POST"])
@require_permission("kitchen")
def set_menu_item_active_route(hostel_id, menu_item_id):
    data = request.get_json() or {}
    updated = set_menu_item_active(hostel_id, menu_item_id, bool(data.get("active", True)))
    if not updated:
        return jsonify({"success": False, "message": "Item de cardápio não encontrado."}), 404
    return jsonify({"success": True})


@kitchen_bp.route("/kitchen/menu/<int:menu_item_id>/ingredients", methods=["POST"])
@require_permission("kitchen")
def set_menu_item_ingredient_route(hostel_id, menu_item_id):
    """
    Sem checar hostel_id contra menu_item_id/inventory_item_id aqui de
    proposito - segue o mesmo padrao ja usado no resto do arquivo
    (confia no escopo de quem chama estar dentro do proprio hostel,
    igual /inventory e /revenue ja fazem).
    """
    data = request.get_json() or {}
    inventory_item_id = data.get("inventory_item_id")
    quantity = data.get("quantity")

    if not inventory_item_id or quantity is None:
        return jsonify({"success": False, "message": "inventory_item_id and quantity are required."}), 400

    set_menu_item_ingredient(menu_item_id, inventory_item_id, quantity)
    return jsonify({"success": True})


@kitchen_bp.route("/kitchen/orders", methods=["GET"])
@require_permission("kitchen")
def list_kitchen_orders(hostel_id):
    orders = get_open_tickets(hostel_id, ticket_type="kitchen_order")
    for order in orders:
        order["items"] = get_kitchen_order_items(order["id"])
        order["aggregate_status"] = get_kitchen_order_aggregate_status(order["id"])
    return jsonify(orders)


@kitchen_bp.route("/kitchen/orders", methods=["POST"])
@require_permission("kitchen")
def create_kitchen_order_route(hostel_id):
    """
    Criacao manual (pela equipe, via dashboard) - o mesmo caminho que a
    IA usa (routes/chat.py, quando um pedido chega por WhatsApp/
    Messenger/Instagram) chama create_kitchen_order direto, sem passar
    por essa rota HTTP.
    """
    data = request.get_json() or {}
    items = data.get("items") or []
    location = (data.get("location") or "").strip()

    if not location or not items:
        return jsonify({"success": False, "message": "location and items are required."}), 400

    try:
        ticket_id = create_kitchen_order(
            hostel_id, location, items,
            channel=data.get("channel", "dashboard"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    section_id = data.get("section_id")
    notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "kitchen", section_id)

    return jsonify({"success": True, "id": ticket_id}), 201


@kitchen_bp.route("/kitchen/orders/<int:ticket_id>/items/<int:item_id>/status", methods=["POST"])
@require_permission("kitchen")
def update_kitchen_order_item_status_route(hostel_id, ticket_id, item_id):
    data = request.get_json() or {}
    status = data.get("status")

    if status not in ("pending", "preparing", "ready", "delivered"):
        return jsonify({"success": False, "message": "status inválido."}), 400

    updated = update_kitchen_order_item_status(ticket_id, item_id, status)
    if not updated:
        return jsonify({"success": False, "message": "Item não encontrado."}), 404

    if get_kitchen_order_aggregate_status(ticket_id) == "delivered":
        resolve_ticket(hostel_id, ticket_id, resolution_notes="Todos os itens entregues.")

    return jsonify({"success": True, "aggregate_status": get_kitchen_order_aggregate_status(ticket_id)})
