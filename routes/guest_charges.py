"""
Cobranca paga pelo hospede via Mercado Pago (Split de Pagos) - serve
quatro cenarios: venda de passeio/excursao ('tour'), aluguel ('rental'),
link de pagamento pra uma reserva de quarto existente ('reservation') e
venda do portfolio de uma agencia parceira feita por uma hospedagem
('partner_item'). O front-end pre-preenche guest_id/titulo/valor a
partir da origem (opportunity_id ou reservation_id) usando dados que ja
tem carregados na tela - esta rota nao re-consulta a oportunidade/
reserva, so grava a referencia.

Criar a cobranca ja gera a preferencia no Mercado Pago e devolve o link
de pagamento pronto. Pra 'partner_item' o VENDEDOR (dono do token MP
usado no checkout) e a agencia, nao a hospedagem que chamou a rota -
ver _resolve_seller_hostel_id abaixo, o unico lugar onde essa excecao
existe.
"""

from flask import Blueprint, jsonify, request

import services.mercadopago_service as mercadopago_service
from database import (
    create_guest_charge,
    get_guest_charge,
    list_guest_charges,
    mark_guest_charge_checkout_created,
    get_hostel_mercadopago_config,
    get_portfolio_item,
    get_connection,
)
from utils.tenant import require_permission

guest_charges_bp = Blueprint("guest_charges", __name__)


def _resolve_partner_item(portfolio_item_id):
    """Busca o item de portfolio direto na tabela (sem escopo de hostel - o vendedor pode ser qualquer agencia), pra nunca confiar em agency_hostel_id/preco vindo cru do cliente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio_items WHERE id = ? AND active = 1", (portfolio_item_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


@guest_charges_bp.route("/guest-charges", methods=["POST"])
@require_permission("opportunities")
def create_guest_charge_route(hostel_id):
    data = request.get_json() or {}

    charge_type = data.get("charge_type")
    title = data.get("title")
    total_amount = data.get("total_amount")
    referring_hostel_id = None
    seller_hostel_id = hostel_id

    if charge_type == "partner_item":
        portfolio_item_id = data.get("portfolio_item_id")
        if not portfolio_item_id:
            return jsonify({"success": False, "message": "portfolio_item_id é obrigatório."}), 400
        item = _resolve_partner_item(portfolio_item_id)
        if not item:
            return jsonify({"success": False, "message": "Item de portfólio não encontrado."}), 404

        # O vendedor real e a agencia dona do item - o token MP usado no
        # checkout e o dela, nunca o da hospedagem que esta oferecendo.
        seller_hostel_id = item["hostel_id"]
        referring_hostel_id = hostel_id
        title = item["name"]
        total_amount = item["price"] if item["price_type"] == "fixed" else data.get("total_amount")
        if total_amount is None:
            return jsonify({"success": False, "message": "Esse item não tem preço fixo - informe total_amount."}), 400

    if not charge_type or not title or total_amount is None:
        return jsonify({"success": False, "message": "charge_type, title e total_amount são obrigatórios."}), 400

    mp_user_id, mp_access_token, _refresh, _public_key = get_hostel_mercadopago_config(seller_hostel_id)
    if not mp_access_token:
        return jsonify({
            "success": False,
            "message": "Conecte o Mercado Pago em Configurações antes de gerar cobranças." if seller_hostel_id == hostel_id
                        else "A agência ainda não conectou o Mercado Pago dela.",
        }), 409

    try:
        charge = create_guest_charge(
            hostel_id=seller_hostel_id,
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
            referring_hostel_id=referring_hostel_id,
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    charge_amount = charge["deposit_amount"] if charge["payment_mode"] == "deposit" else charge["total_amount"]
    commission_amount = round(charge["total_amount"] * charge["commission_pct"] / 100, 2)

    notification_url = f"{request.url_root.rstrip('/')}/webhook/mercadopago/{seller_hostel_id}"
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

    mark_guest_charge_checkout_created(seller_hostel_id, charge["id"], preference_id, init_point)

    return jsonify({"success": True, "charge": get_guest_charge(seller_hostel_id, charge["id"])})


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
