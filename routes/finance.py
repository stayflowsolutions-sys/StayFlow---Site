from flask import Blueprint, jsonify, request
from database import get_finance_summary, create_currency_exchange, get_currency_exchanges
from services.exchange_rate_service import get_usd_ars_blue_rate
from utils.tenant import require_permission, get_current_user

finance_bp = Blueprint("finance", __name__)


@finance_bp.route("/finance", methods=["GET"])
@require_permission("finance")
def finance(hostel_id):
    return jsonify(get_finance_summary(hostel_id))


@finance_bp.route("/finance/exchange-rate", methods=["GET"])
@require_permission("finance")
def get_reference_exchange_rate(hostel_id):
    """
    Cotacao de referencia pra ajudar a preencher o cambio manual - so
    existe pra USD->ARS hoje (unica fonte que temos, finanzasargy.com,
    e um site voltado pro mercado argentino). Qualquer outro par devolve
    rate=None e o frontend so esconde a referencia, sem quebrar nada.
    """
    currency = (request.args.get("currency") or "").upper()
    if currency != "USD":
        return jsonify({"rate": None})
    return jsonify(get_usd_ars_blue_rate())


@finance_bp.route("/finance/exchanges", methods=["GET"])
@require_permission("finance")
def list_exchanges(hostel_id):
    return jsonify(get_currency_exchanges(hostel_id))


@finance_bp.route("/finance/exchanges", methods=["POST"])
@require_permission("finance")
def create_exchange(hostel_id):
    data = request.get_json() or {}
    foreign_currency = (data.get("foreign_currency") or "").strip()
    description = (data.get("description") or "").strip()
    guest_id = data.get("guest_id") or None

    try:
        foreign_amount = float(data.get("foreign_amount"))
        exchange_rate = float(data.get("exchange_rate"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "foreign_amount and exchange_rate must be numbers."}), 400

    if not foreign_currency or foreign_amount <= 0 or exchange_rate <= 0:
        return jsonify({"success": False, "message": "foreign_currency, foreign_amount and exchange_rate are required."}), 400

    market_rate = None
    if data.get("market_rate") not in (None, ""):
        try:
            market_rate = float(data.get("market_rate"))
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "market_rate must be a number."}), 400

    current_user = get_current_user()
    operator_user_id = current_user["id"] if current_user else None
    operator_name = current_user["name"] if current_user else None

    exchange_id = create_currency_exchange(
        hostel_id, description, foreign_currency, foreign_amount, exchange_rate,
        market_rate=market_rate, operator_user_id=operator_user_id, operator_name=operator_name,
        guest_id=guest_id,
    )
    return jsonify({"success": True, "id": exchange_id}), 201
