from flask import Blueprint, jsonify, request

import services.nuvemshop_service as nuvemshop_service
from database import (
    get_hostel_id_by_nuvemshop_store_id,
    get_hostel_nuvemshop_config,
    delete_portfolio_item_by_external_id,
)
from services.push_service import send_push_to_hostel
from utils.webhook_security import verify_nuvemshop_signature

nuvemshop_webhook_bp = Blueprint("nuvemshop_webhook", __name__)


@nuvemshop_webhook_bp.route("/webhook/nuvemshop", methods=["POST"])
def nuvemshop_webhook():
    """
    Recebe eventos de produto/pedido da Nuvemshop - payload so traz
    {store_id, event, id}, precisa buscar o recurso completo via API
    antes de fazer qualquer coisa. Sempre responde 200 rapido (exigencia
    da propria Nuvemshop: 2XX em ate 3s), mesmo em erro interno - so
    assinatura invalida derruba com 403, ANTES de qualquer processamento.
    """
    if not verify_nuvemshop_signature(request):
        return "Invalid signature", 403

    payload = request.get_json(silent=True) or {}
    store_id = payload.get("store_id")
    event = payload.get("event")
    resource_id = payload.get("id")

    try:
        hostel_id = get_hostel_id_by_nuvemshop_store_id(store_id)
        if not hostel_id:
            print(f"Webhook Nuvemshop recebido de loja desconhecida: {store_id}")
            return jsonify({"status": "unknown_store"}), 200

        _, access_token = get_hostel_nuvemshop_config(hostel_id)
        if not access_token:
            return jsonify({"status": "not_configured"}), 200

        if event == "product/deleted":
            delete_portfolio_item_by_external_id(hostel_id, "nuvemshop", resource_id)
        elif event in ("product/created", "product/updated"):
            product = nuvemshop_service.get_product(store_id, access_token, resource_id)
            if product:
                nuvemshop_service.map_and_upsert_product(hostel_id, product)
        elif event == "order/paid":
            order = nuvemshop_service.get_order(store_id, access_token, resource_id)
            if order:
                total = order.get("total")
                currency = order.get("currency", "")
                send_push_to_hostel(
                    hostel_id,
                    "Novo pedido na loja",
                    f"Pedido #{order.get('number', resource_id)} pago — {total} {currency}".strip(),
                    url="/app?page=portfolio",
                    notification_type="nuvemshop_order",
                )
    except Exception as error:
        print("Erro ao processar webhook da Nuvemshop:", error)

    return jsonify({"status": "ok"}), 200
