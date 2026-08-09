"""
Cobranca paga pelo hospede via Mercado Pago (Split de Pagos) - serve
tres cenarios: venda de passeio/excursao ('tour'), aluguel ('rental')
e link de pagamento pra uma reserva de quarto existente ('reservation').
O front-end pre-preenche guest_id/titulo/valor a partir da origem
(opportunity_id ou reservation_id) usando dados que ja tem carregados
na tela - esta rota nao re-consulta a oportunidade/reserva, so grava a
referencia.

Criar a cobranca ja gera a preferencia no Mercado Pago (usando o token
MP do proprio hostel) e devolve o link de pagamento pronto.
"""

from flask import Blueprint, jsonify, request

import services.mercadopago_service as mercadopago_service
from database import (
    create_guest_charge,
    get_guest_charge,
    list_guest_charges,
    mark_guest_charge_checkout_created,
    get_hostel_mercadopago_config,
)
from utils.tenant import require_permission

guest_charges_bp = Blueprint("guest_charges", __name__)


@guest_charges_bp.route("/guest-charges", methods=["POST"])
@require_permission("opportunities")
def create_guest_charge_route(hostel_id):
    data = request.get_json() or {}

    charge_type = data.get("charge_type")
    title = data.get("title")
    total_amount = data.get("total_amount")

    if not charge_type or not title or total_amount is None:
        return jsonify({"success": False, "message": "charge_type, title e total_amount são obrigatórios."}), 400

    mp_user_id, mp_access_token, _refresh, _public_key = get_hostel_mercadopago_config(hostel_id)
    if not mp_access_token:
        return jsonify({
            "success": False,
            "message": "Conecte o Mercado Pago em Configurações antes de gerar cobranças.",
        }), 409

    try:
        charge = create_guest_charge(
            hostel_id=hostel_id,
            charge_type=charge_type,
            title=title,
            total_amount=total_amount,
            payment_mode=data.get("payment_mode", "full"),
            deposit_amount=data.get("deposit_amount"),
            description=data.get("description"),
            guest_id=data.get("guest_id"),
            opportunity_id=data.get("opportunity_id"),
            reservation_id=data.get("reservation_id"),
            created_by_user_id=None,
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    charge_amount = charge["deposit_amount"] if charge["payment_mode"] == "deposit" else charge["total_amount"]
    commission_amount = round(charge["total_amount"] * charge["commission_pct"] / 100, 2)

    notification_url = f"{request.url_root.rstrip('/')}/webhook/mercadopago/{hostel_id}"
    back_url = f"{request.url_root.rstrip('/')}/app?guest_charge={charge['id']}"

    preference_id, init_point, error = mercadopago_service.create_checkout_preference(
        seller_access_token=mp_access_token,
        title=charge["title"],
        amount=charge_amount,
        currency=charge["currency"],
        marketplace_fee=commission_amount,
        external_reference=charge["id"],
        notification_url=notification_url,
        back_url=back_url,
    )
    if error:
        return jsonify({"success": False, "message": error}), 502

    mark_guest_charge_checkout_created(hostel_id, charge["id"], preference_id, init_point)

    return jsonify({"success": True, "charge": get_guest_charge(hostel_id, charge["id"])})


@guest_charges_bp.route("/guest-charges/<int:charge_id>", methods=["GET"])
@require_permission("opportunities")
def get_guest_charge_route(hostel_id, charge_id):
    charge = get_guest_charge(hostel_id, charge_id)
    if not charge:
        return jsonify({"success": False, "message": "Cobrança não encontrada."}), 404
    return jsonify({"success": True, "charge": charge})


@guest_charges_bp.route("/guest-charges", methods=["GET"])
@require_permission("opportunities")
def list_guest_charges_route(hostel_id):
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    charges = list_guest_charges(hostel_id, limit=limit, offset=offset)
    return jsonify({"success": True, "charges": charges})
