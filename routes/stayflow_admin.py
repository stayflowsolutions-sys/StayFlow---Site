"""
Painel interno da StayFlow (nao de uma hospedagem especifica) - visao
cross-tenant de todas as hospedagens, combinando duas fontes de
receita que NAO devem ser somadas como se fossem a mesma coisa:

1. Assinatura (billing.plan_name) - so uma ESTIMATIVA de MRR
   (PLAN_PRICES), ja que o processador de pagamento dessa cobranca
   (Stripe/MercadoPago Fase 2/3) ainda nao foi ligado.
2. Comissao de guest_charges pagos - dinheiro REAL, ja processado pelo
   Mercado Pago Split de Pagos.

So leitura nesta fase - editar plano/status/comissao de uma hospedagem
continua sendo feito pelos endpoints ja existentes em routes/billing.py
(/billing/admin/set-plan, set-addon, set-commission).
"""

import datetime

from flask import Blueprint, jsonify, request

from database import (
    get_stayflow_admin_overview,
    get_hostel_currency,
    get_hostel,
    get_billing_info,
    get_dashboard_stats,
    count_rooms,
    count_active_seats,
    get_partner_referral_ledger_summary,
    mark_partner_referral_paid_out,
    list_portfolio_items,
    AGENCY_CATEGORY_LABELS,
    set_session_impersonation,
    log_impersonation_start,
    log_impersonation_end,
    PLAN_PRICES,
    PLAN_ROOM_LIMITS,
    PLAN_SEAT_LIMITS,
)
from utils.tenant import (
    require_stayflow_admin,
    require_auth,
    get_current_session_id,
    get_current_user_id,
    get_current_hostel_id,
    is_impersonating,
    get_impersonation_origin_hostel_id,
)

stayflow_admin_bp = Blueprint("stayflow_admin", __name__)


def _trial_days_left(status, trial_ends_at):
    if status != "trialing" or not trial_ends_at:
        return None
    ends_at = datetime.datetime.fromisoformat(trial_ends_at)
    remaining = (ends_at - datetime.datetime.utcnow()).days
    return max(remaining, 0)


@stayflow_admin_bp.route("/stayflow-admin/overview", methods=["GET"])
@require_stayflow_admin
def overview():
    # ?kind=agency|lodging filtra pra uma das duas listagens dedicadas
    # (admin-list.html) - sem filtro, traz tudo (usado pelos cards de
    # resumo financeiro em admin.html).
    kind = request.args.get("kind")
    if kind not in (None, "agency", "lodging"):
        return jsonify({"success": False, "message": "kind inválido."}), 400

    rows = get_stayflow_admin_overview(account_kind=kind)

    hostels = []
    for row in rows:
        plan_name = row["plan_name"]
        hostels.append({
            "hostel_id": row["hostel_id"],
            "hostel_name": row["hostel_name"],
            "account_kind": row["account_kind"],
            "plan_name": plan_name,
            "status": row["status"],
            "trial_days_left": _trial_days_left(row["status"], row["trial_ends_at"]),
            "estimated_mrr": PLAN_PRICES.get(plan_name, 0) if plan_name else 0,
            "guest_payment_volume": row["guest_payment_volume"],
            "commission_collected": row["commission_collected"],
            # Moeda operacional da hospedagem (Configuracoes > Empresa) -
            # so pra exibir ao lado do valor na tabela; a soma total no
            # card de resumo NAO converte entre moedas (nota explicita
            # no frontend), ja que cada hospedagem pode operar numa
            # moeda diferente.
            "currency": get_hostel_currency(row["hostel_id"]),
        })

    return jsonify({
        "success": True,
        "hostels": hostels,
        "summary": {
            "total_hostels": len(hostels),
            "by_status": {
                status: sum(1 for h in hostels if h["status"] == status)
                for status in {h["status"] for h in hostels if h["status"]}
            },
            "total_estimated_mrr": sum(h["estimated_mrr"] for h in hostels),
            "total_commission_collected": sum(h["commission_collected"] for h in hostels),
        },
    })


@stayflow_admin_bp.route("/stayflow-admin/hostel/<int:hostel_id>", methods=["GET"])
@require_stayflow_admin
def hostel_profile(hostel_id):
    """
    Perfil de UMA hospedagem, visto pelo admin da StayFlow - reaproveita
    tudo que ja existe (get_dashboard_stats e a mesma funcao que
    alimenta o Dashboard da propria hospedagem, count_rooms/
    count_active_seats ja usados pro limite de plano) em vez de
    duplicar consulta.
    """
    hostel = get_hostel(hostel_id)
    if not hostel:
        return jsonify({"success": False, "message": "Hospedagem não encontrada."}), 404

    billing = get_billing_info(hostel_id)
    stats = get_dashboard_stats(hostel_id)["stats"]
    plan_name = billing["plan_name"]

    # Reaproveita a agregacao cross-tenant e filtra so essa hospedagem,
    # em vez de duplicar a query de comissao de guest_charges.
    overview_row = next(
        (r for r in get_stayflow_admin_overview() if r["hostel_id"] == hostel_id),
        None
    )
    commission_collected = overview_row["commission_collected"] if overview_row else 0
    guest_payment_volume = overview_row["guest_payment_volume"] if overview_row else 0

    room_limit = PLAN_ROOM_LIMITS.get(plan_name)
    seat_base_limit = PLAN_SEAT_LIMITS.get(plan_name)
    seat_limit = None if seat_base_limit is None else seat_base_limit + (billing["extra_seats"] or 0)

    is_agency = hostel["account_kind"] == "agency"
    if is_agency:
        # Rooms/beds/occupancy nao fazem sentido pra agencia - troca o
        # bloco "operacao" por estatisticas de portfolio.
        items = list_portfolio_items(hostel_id, include_inactive=True)
        by_category = {}
        for item in items:
            by_category[item["category"]] = by_category.get(item["category"], 0) + 1
        operacao = {
            "items_total": len(items),
            "items_active": sum(1 for i in items if i["active"]),
            "by_category": [
                {"category": cat, "label": AGENCY_CATEGORY_LABELS.get(cat, cat), "count": count}
                for cat, count in by_category.items()
            ],
            "seats_used": count_active_seats(hostel_id),
            "seat_limit": seat_limit,
            "messages": stats["messages"],
            "opportunities": stats["opportunities"],
        }
    else:
        operacao = {
            "rooms_used": count_rooms(hostel_id),
            "room_limit": room_limit,
            "beds_total": stats["beds_total"],
            "beds_occupied": stats["beds_occupied"],
            "occupancy_pct": stats["occupancy_pct"],
            "seats_used": count_active_seats(hostel_id),
            "seat_limit": seat_limit,
            "guests": stats["guests"],
            "reservations": stats["reservations"],
            "messages": stats["messages"],
            "opportunities": stats["opportunities"],
        }

    return jsonify({
        "success": True,
        "hostel_id": hostel_id,
        "hostel_name": hostel["name"],
        "hostel_email": hostel["email"],
        "hostel_phone": hostel["phone"],
        "account_kind": hostel["account_kind"],
        "agency_category": hostel.get("agency_category"),
        "agency_category_label": AGENCY_CATEGORY_LABELS.get(hostel.get("agency_category")),
        "plan_name": plan_name,
        "status": billing["status"],
        "trial_days_left": _trial_days_left(billing["status"], billing["trial_ends_at"]),
        "estimated_mrr": PLAN_PRICES.get(plan_name, 0) if plan_name else 0,
        "currency": get_hostel_currency(hostel_id),
        "operacao": operacao,
        "financeiro": {
            "revenue": stats["revenue"],
            "guest_payment_volume": guest_payment_volume,
            "commission_collected": commission_collected,
        },
    })


@stayflow_admin_bp.route("/stayflow-admin/partner-ledger", methods=["GET"])
@require_stayflow_admin
def partner_ledger():
    """
    Saldo acumulado (status='accrued') de repasse devido a cada
    hospedagem por ter indicado venda de item de agencia parceira -
    dinheiro que a StayFlow ja recebeu (embutido na marketplace_fee)
    mas ainda nao repassou. So registro contabil, sem processador de
    payout automatico (ver partner-ledger/payout abaixo).
    """
    rows = get_partner_referral_ledger_summary()
    balances = [{
        "hostel_id": row["referring_hostel_id"],
        "hostel_name": (get_hostel(row["referring_hostel_id"]) or {}).get("name"),
        "currency": row["currency"],
        "total_owed": row["total_owed"],
        "charge_count": row["charge_count"],
    } for row in rows]

    return jsonify({"success": True, "balances": balances})


@stayflow_admin_bp.route("/stayflow-admin/impersonate", methods=["POST"])
@require_stayflow_admin
def impersonate():
    """
    "Entra" no dashboard de verdade de uma hospedagem/agencia sem ser
    membro real dela - reaponta o hostel_id da PROPRIA sessao do admin
    pra conta alvo (update_session_hostel, ja existe) e guarda o
    hostel_id original em impersonating_from_hostel_id (o "endereco de
    volta"). require_permission/require_plan_feature/get_current_user
    (utils/tenant.py) liberam acesso completo quando is_impersonating()
    - nenhuma hostel_memberships e criada em lugar nenhum.
    """
    data = request.get_json() or {}
    target_hostel_id = data.get("hostel_id")

    if not target_hostel_id:
        return jsonify({"success": False, "message": "hostel_id é obrigatório."}), 400

    target = get_hostel(target_hostel_id)
    if not target:
        return jsonify({"success": False, "message": "Conta não encontrada."}), 404

    session_id = get_current_session_id()
    user_id = get_current_user_id()

    # Visita encadeada: se ja esta visitando outra conta, mantem o
    # endereco de volta ORIGINAL (nunca sobrescreve com o hostel que
    # estava sendo visitado ate agora) - senao "sair" levaria pra uma
    # conta visitada anterior, nao pro hostel de verdade do admin.
    origin_hostel_id = get_impersonation_origin_hostel_id() or get_current_hostel_id()

    from database import update_session_hostel
    set_session_impersonation(session_id, origin_hostel_id)
    update_session_hostel(session_id, target_hostel_id)
    log_impersonation_start(user_id, target_hostel_id)

    return jsonify({"success": True})


@stayflow_admin_bp.route("/stayflow-admin/stop-impersonating", methods=["POST"])
@require_auth
def stop_impersonating(hostel_id):
    """
    Sai da visita - so faz sentido se a sessao realmente esta visitando
    (protecao real e a propria coluna impersonating_from_hostel_id
    estar preenchida, nao um allowlist de e-mail aqui: so uma sessao
    que passou por /impersonate teria esse campo setado).
    """
    origin_hostel_id = get_impersonation_origin_hostel_id()
    if not origin_hostel_id:
        return jsonify({"success": False, "message": "Esta sessão não está em visita."}), 400

    session_id = get_current_session_id()
    user_id = get_current_user_id()

    from database import update_session_hostel
    log_impersonation_end(user_id, hostel_id)
    update_session_hostel(session_id, origin_hostel_id)
    set_session_impersonation(session_id, None)

    return jsonify({"success": True})


@stayflow_admin_bp.route("/stayflow-admin/partner-ledger/payout", methods=["POST"])
@require_stayflow_admin
def partner_ledger_payout():
    data = request.get_json() or {}
    hostel_id = data.get("hostel_id")
    note = data.get("note")

    if not hostel_id:
        return jsonify({"success": False, "message": "hostel_id é obrigatório."}), 400

    affected = mark_partner_referral_paid_out(hostel_id, note=note)
    return jsonify({"success": True, "rows_paid_out": affected})
