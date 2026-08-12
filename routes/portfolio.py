from flask import Blueprint, jsonify, request

from database import (
    get_hostel,
    create_portfolio_item,
    get_portfolio_item,
    list_portfolio_items,
    update_portfolio_item,
    AGENCY_CATEGORIES,
)
from utils.tenant import require_permission

portfolio_bp = Blueprint("portfolio", __name__)


def _require_agency(hostel_id):
    """Checagem no backend, nao so no frontend (mesmo espirito de require_stayflow_admin) - so agencia mexe no proprio portfolio."""
    hostel = get_hostel(hostel_id)
    if not hostel or hostel.get("account_kind") != "agency":
        return jsonify({"success": False, "message": "Só contas de agência têm portfólio."}), 403
    return None


@portfolio_bp.route("/portfolio/items", methods=["GET"])
@require_permission("portfolio")
def list_portfolio_items_route(hostel_id):
    error = _require_agency(hostel_id)
    if error:
        return error
    include_inactive = request.args.get("include_inactive") == "1"
    return jsonify({"success": True, "items": list_portfolio_items(hostel_id, include_inactive=include_inactive)})


@portfolio_bp.route("/portfolio/items", methods=["POST"])
@require_permission("portfolio")
def create_portfolio_item_route(hostel_id):
    error = _require_agency(hostel_id)
    if error:
        return error

    data = request.get_json() or {}
    category = data.get("category")
    if category and category not in AGENCY_CATEGORIES:
        return jsonify({"success": False, "message": "Categoria inválida."}), 400

    try:
        item = create_portfolio_item(
            hostel_id,
            name=data.get("name"),
            description=data.get("description"),
            photo_url=data.get("photo_url"),
            category=category,
            price_type=data.get("price_type", "fixed"),
            price=data.get("price"),
        )
    except ValueError as error_msg:
        return jsonify({"success": False, "message": str(error_msg)}), 400

    return jsonify({"success": True, "item": item})


@portfolio_bp.route("/portfolio/items/import", methods=["POST"])
@require_permission("portfolio")
def import_portfolio_items_route(hostel_id):
    """
    Importa itens de portfolio em lote a partir de uma planilha ja
    parseada no frontend (lista de {name, description, category,
    price_type, price}) - equivalente da importacao de quartos, so que
    pro lado agencia (que nao tem quarto, tem item de portfolio).
    """
    error = _require_agency(hostel_id)
    if error:
        return error

    data = request.get_json() or {}
    rows = data.get("rows", [])
    if not rows:
        return jsonify({"success": False, "message": "Nenhuma linha pra importar."}), 400

    created = 0
    errors = []
    for i, row in enumerate(rows):
        category = row.get("category") or None
        if category and category not in AGENCY_CATEGORIES:
            errors.append({"row": i + 1, "message": f"Categoria '{category}' inválida."})
            continue
        try:
            create_portfolio_item(
                hostel_id,
                name=row.get("name"),
                description=row.get("description"),
                category=category,
                price_type=row.get("price_type") or "fixed",
                price=row.get("price"),
            )
            created += 1
        except (ValueError, TypeError) as error_msg:
            errors.append({"row": i + 1, "message": str(error_msg)})

    return jsonify({"success": True, "created": created, "errors": errors}), 201


@portfolio_bp.route("/portfolio/items/<int:item_id>", methods=["PATCH"])
@require_permission("portfolio")
def update_portfolio_item_route(hostel_id, item_id):
    error = _require_agency(hostel_id)
    if error:
        return error

    if not get_portfolio_item(hostel_id, item_id):
        return jsonify({"success": False, "message": "Item não encontrado."}), 404

    data = request.get_json() or {}
    item = update_portfolio_item(hostel_id, item_id, **data)
    return jsonify({"success": True, "item": item})
