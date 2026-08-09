"""
Webhook de entrada do Mercado Pago - notifica pagamento aprovado/
rejeitado/pendente de uma preferencia criada em routes/guest_charges.py.

A notificacao do Mercado Pago (IPN/webhook) e so um ponteiro fino
(type='payment', data.id=<payment_id>) - nao traz valor nem status,
isso precisa de um GET separado em /v1/payments/{id}, autenticado com
o token do HOSTEL dono do pagamento (payment ids sao escopados a conta
que recebeu). Como a notificacao nao identifica de qual hostel e, a
notification_url de cada preferencia ja e gerada com o hostel_id no
proprio path (/webhook/mercadopago/<hostel_id>) - a rota sabe de qual
hostel e antes de tocar em qualquer dado, mesmo principio de isolamento
por tenant ja usado no webhook do Beds24.

Sempre responde 200, nunca deixa excecao estourar - mesmo estilo
defensivo de routes/beds24_webhook.py.
"""

import json

from flask import Blueprint, request, jsonify

import services.mercadopago_service as mercadopago_service
from database import (
    try_claim_mp_webhook_event,
    finalize_mp_webhook_event,
    get_hostel_mercadopago_config,
    update_hostel_mercadopago_tokens,
    mark_guest_charge_paid,
)

mercadopago_webhook_bp = Blueprint("mercadopago_webhook", __name__)


@mercadopago_webhook_bp.route("/webhook/mercadopago/<int:hostel_id>", methods=["POST"])
def receive_mercadopago_webhook(hostel_id):
    payload = request.get_json(silent=True) or {}
    # O Mercado Pago manda o id do pagamento tanto no corpo (formato
    # novo, `data.id`) quanto na query string (formato antigo, `id`/
    # `data.id`) dependendo de como a preferencia foi configurada -
    # trata os dois pra nao perder notificacao por causa do formato.
    payment_id = (
        (payload.get("data") or {}).get("id")
        or request.args.get("data.id")
        or request.args.get("id")
    )
    event_type = payload.get("type") or request.args.get("type") or request.args.get("topic")

    print(f"Webhook Mercado Pago recebido (hostel_id={hostel_id}, type={event_type}, payment_id={payment_id}):", payload)

    if event_type not in (None, "payment") or not payment_id:
        # Mercado Pago manda outros tipos de notificacao (merchant_order
        # etc.) que nao interessam aqui - responde 200 e ignora.
        return jsonify({"status": "ignored"}), 200

    try:
        _process_payment(hostel_id, str(payment_id), json.dumps(payload, ensure_ascii=False))
    except Exception as error:
        print(f"Erro ao processar webhook Mercado Pago (hostel_id={hostel_id}, payment_id={payment_id}):", error)

    return jsonify({"status": "ok"}), 200


def _process_payment(hostel_id, payment_id, payload_json):
    if not try_claim_mp_webhook_event(payment_id, hostel_id, payload_json):
        print(f"Webhook Mercado Pago: pagamento {payment_id} já processado antes, ignorando.")
        return

    _mp_user_id, access_token, refresh_token, _public_key = get_hostel_mercadopago_config(hostel_id)
    if not access_token:
        finalize_mp_webhook_event(payment_id, "failed", error_message="Hospedagem sem Mercado Pago conectado.")
        return

    status, transaction_amount, external_reference, error = mercadopago_service.get_payment(access_token, payment_id)

    if error == "unauthorized" and refresh_token:
        new_access_token, new_refresh_token, refresh_error = mercadopago_service.refresh_access_token(refresh_token)
        if refresh_error:
            finalize_mp_webhook_event(payment_id, "failed", error_message=f"Falha ao renovar token: {refresh_error}")
            return
        update_hostel_mercadopago_tokens(hostel_id, new_access_token, new_refresh_token)
        status, transaction_amount, external_reference, error = mercadopago_service.get_payment(new_access_token, payment_id)

    if error:
        finalize_mp_webhook_event(payment_id, "failed", error_message=error)
        return

    if not external_reference:
        finalize_mp_webhook_event(payment_id, "failed", error_message="Pagamento sem external_reference (guest_charge_id).")
        return

    guest_charge_id = int(external_reference)

    if status != "approved":
        finalize_mp_webhook_event(payment_id, "ignored", error_message=f"status={status}", guest_charge_id=guest_charge_id)
        return

    mark_guest_charge_paid(hostel_id, guest_charge_id, payment_id, transaction_amount)
    finalize_mp_webhook_event(payment_id, "processed", guest_charge_id=guest_charge_id)
    print(f"Webhook Mercado Pago: cobrança {guest_charge_id} marcada como paga (payment_id={payment_id}).")
