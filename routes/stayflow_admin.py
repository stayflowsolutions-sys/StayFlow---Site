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
import os
import secrets

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
    get_hostel_id_by_ai_persona,
    get_guests_inbox,
    get_guest_profile,
    set_guest_ai_paused,
    send_message_to_guest_now,
    mark_guest_seen_by_admin,
    count_new_hostels_last_days,
    create_support_message,
    get_support_messages,
    mark_support_seen_by_admin,
    list_support_threads,
    set_hostel_is_own_test_account,
    list_recent_guest_charges,
    create_stayflow_expense,
    list_stayflow_expenses,
    update_stayflow_expense,
    delete_stayflow_expense,
    mark_stayflow_expense_paid,
    list_stayflow_team,
    add_stayflow_team_member,
    remove_stayflow_team_member,
    get_account_growth_by_month,
    snapshot_todays_metrics,
    get_metrics_history,
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
            "is_own_test_account": bool(row["is_own_test_account"]),
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

    total_estimated_mrr = sum(h["estimated_mrr"] for h in hostels)
    total_commission_collected = sum(h["commission_collected"] for h in hostels)

    # So tira o snapshot do dia quando e o overview COMPLETO (sem filtro
    # de kind) - senao um load de admin-list.html?kind=agency salvaria
    # um total parcial errado pro dia.
    if not kind:
        snapshot_todays_metrics(len(hostels), total_estimated_mrr, total_commission_collected)

    return jsonify({
        "success": True,
        "hostels": hostels,
        "summary": {
            "total_hostels": len(hostels),
            "by_status": {
                status: sum(1 for h in hostels if h["status"] == status)
                for status in {h["status"] for h in hostels if h["status"]}
            },
            "total_estimated_mrr": total_estimated_mrr,
            "total_commission_collected": total_commission_collected,
            "new_hostels_last_7_days": count_new_hostels_last_days(7),
        },
    })


@stayflow_admin_bp.route("/stayflow-admin/growth", methods=["GET"])
@require_stayflow_admin
def growth():
    return jsonify({
        "success": True,
        "accounts_by_month": get_account_growth_by_month(),
        "metrics_history": get_metrics_history(days=90),
    })


@stayflow_admin_bp.route("/stayflow-admin/ask", methods=["POST"])
@require_stayflow_admin
def ask_admin():
    """
    "Ask StayFlow" do Meu painel - versao propria, diferente da IA
    interna de cada hospedagem (services/ask_agent_service.py, que gira
    em torno de reservas/quartos/hospedes de UM hostel). Aqui nao ha
    tool-calling: monta um snapshot real e atual dos numeros do
    negocio (contas, MRR, comissao, trials, nao-lidos) e pede pro
    modelo responder com base nisso, sem inventar numero nenhum.
    """
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []
    if not message:
        return jsonify({"success": False, "message": "Mensagem vazia."}), 400

    from services.ai_service import client as openai_client

    overview_rows = get_stayflow_admin_overview()
    total_hostels = len(overview_rows)
    total_mrr = sum(PLAN_PRICES.get(r["plan_name"], 0) if r["plan_name"] else 0 for r in overview_rows)
    total_commission = sum(r["commission_collected"] for r in overview_rows)
    by_status = {}
    for r in overview_rows:
        if r["status"]:
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    trialing_names = [r["hostel_name"] for r in overview_rows if r["status"] == "trialing"]
    past_due_names = [r["hostel_name"] for r in overview_rows if r["status"] == "past_due"]

    support_threads = list_support_threads()
    support_unread = sum(1 for t in support_threads if t["unread_count"] > 0)

    software_hostel_id = get_hostel_id_by_ai_persona("software")
    chat_unread = 0
    if software_hostel_id:
        chat_unread = sum(1 for g in get_guests_inbox(software_hostel_id) if g["unread"])

    pending_expenses = [e for e in list_stayflow_expenses(status="pending")]
    pending_expenses_total = sum(e["amount"] for e in pending_expenses)

    snapshot = (
        f"Total accounts: {total_hostels}\n"
        f"Accounts by status: {by_status}\n"
        f"Trialing accounts: {', '.join(trialing_names) or 'none'}\n"
        f"Past-due accounts: {', '.join(past_due_names) or 'none'}\n"
        f"New accounts in the last 7 days: {count_new_hostels_last_days(7)}\n"
        f"Estimated MRR (list price, not yet auto-charged): US$ {total_mrr:.2f}\n"
        f"Real commission collected (via Mercado Pago Split de Pagos): US$ {total_commission:.2f}\n"
        f"Unread sales-lead conversations (Meu chat): {chat_unread}\n"
        f"Unread support tickets: {support_unread}\n"
        f"Pending expenses: {len(pending_expenses)} totaling roughly US$ {pending_expenses_total:.2f} (mixed currencies, approximate)\n"
    )

    system_prompt = (
        "You are the internal assistant of StayFlow's OWN operator dashboard ('Meu painel') — "
        "you're helping the founder of the StayFlow company itself understand and manage the "
        "business, not a hostel's guest-facing assistant. Below is a live, real snapshot of the "
        "current business data. Use it to answer precisely — never invent a number that isn't in "
        "the snapshot. If asked about something outside this snapshot, say honestly that you "
        "don't have that data here. Reply in the same language the founder writes in. Keep "
        "answers concise and to the point, like a sharp analyst, not a wall of text.\n\n"
        f"CURRENT SNAPSHOT:\n{snapshot}"
    )

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai_client.chat.completions.create(model="gpt-4.1-mini", temperature=0.4, messages=messages)
    answer = response.choices[0].message.content

    return jsonify({"success": True, "answer": answer})


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
        "is_own_test_account": bool(hostel["is_own_test_account"]),
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


# "Meu chat" - conversas do numero comercial oficial da StayFlow (o
# hostel com ai_persona='software', ver services/ai_service.py e a
# coluna hostels.ai_persona em database.py). O admin da StayFlow NAO e
# membro real dessa conta (nao ha hostel_memberships pra ele ali), por
# isso essas rotas resolvem o hostel_id sozinhas via ai_persona em vez
# de vir da sessao, e reaproveitam as MESMAS funcoes de database.py que
# /guests (routes/guests.py) usa pra qualquer hospedagem normal -
# mesma logica de negocio, so a origem do hostel_id e diferente.
def _get_software_hostel_id():
    return get_hostel_id_by_ai_persona("software")


@stayflow_admin_bp.route("/stayflow-admin/my-chat/guests", methods=["GET"])
@require_stayflow_admin
def my_chat_guests():
    hostel_id = _get_software_hostel_id()
    if not hostel_id:
        return jsonify({"success": True, "configured": False, "guests": []})
    return jsonify({
        "success": True,
        "configured": True,
        "hostel_id": hostel_id,
        "guests": get_guests_inbox(hostel_id),
    })


@stayflow_admin_bp.route("/stayflow-admin/my-chat/guests/<int:guest_id>", methods=["GET"])
@require_stayflow_admin
def my_chat_guest_profile(guest_id):
    hostel_id = _get_software_hostel_id()
    if not hostel_id:
        return jsonify({"success": False, "message": "Nenhum número marcado como assistente comercial da StayFlow ainda."}), 404

    profile = get_guest_profile(hostel_id, guest_id)
    if not profile:
        return jsonify({"success": False, "message": "Conversa não encontrada."}), 404

    mark_guest_seen_by_admin(guest_id)
    return jsonify({"success": True, **profile})


@stayflow_admin_bp.route("/stayflow-admin/my-chat/guests/<int:guest_id>/toggle-ai", methods=["POST"])
@require_stayflow_admin
def my_chat_toggle_ai(guest_id):
    hostel_id = _get_software_hostel_id()
    if not hostel_id:
        return jsonify({"success": False, "message": "Nenhum número marcado como assistente comercial da StayFlow ainda."}), 404

    data = request.get_json() or {}
    try:
        result = set_guest_ai_paused(hostel_id, guest_id, bool(data.get("paused")))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404

    return jsonify({"success": True, **result})


@stayflow_admin_bp.route("/stayflow-admin/my-chat/guests/<int:guest_id>/send-message", methods=["POST"])
@require_stayflow_admin
def my_chat_send_message(guest_id):
    hostel_id = _get_software_hostel_id()
    if not hostel_id:
        return jsonify({"success": False, "message": "Nenhum número marcado como assistente comercial da StayFlow ainda."}), 404

    data = request.get_json() or {}
    try:
        result = send_message_to_guest_now(hostel_id, guest_id, data.get("message"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    if not result["sent"]:
        return jsonify({"success": False, "message": "WhatsApp não configurado — mensagem não enviada."}), 502

    return jsonify({"success": True, **result})


# "Suporte" - 1 thread continuo por hostel_id entre a equipe daquela
# conta e a StayFlow (ver database.py, tabela support_messages). Do
# lado da hospedagem/agencia, ver routes/support.py (/support/thread).
@stayflow_admin_bp.route("/stayflow-admin/support/threads", methods=["GET"])
@require_stayflow_admin
def support_threads():
    return jsonify({"success": True, "threads": list_support_threads()})


@stayflow_admin_bp.route("/stayflow-admin/support/threads/<int:hostel_id>", methods=["GET"])
@require_stayflow_admin
def support_thread_detail(hostel_id):
    if not get_hostel(hostel_id):
        return jsonify({"success": False, "message": "Conta não encontrada."}), 404

    messages = get_support_messages(hostel_id)
    mark_support_seen_by_admin(hostel_id)
    return jsonify({"success": True, "messages": messages})


@stayflow_admin_bp.route("/stayflow-admin/support/threads/<int:hostel_id>/send", methods=["POST"])
@require_stayflow_admin
def support_thread_send(hostel_id):
    if not get_hostel(hostel_id):
        return jsonify({"success": False, "message": "Conta não encontrada."}), 404

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"success": False, "message": "Mensagem vazia."}), 400

    create_support_message(hostel_id, "stayflow", message)
    return jsonify({"success": True})


@stayflow_admin_bp.route("/stayflow-admin/hostel/<int:hostel_id>/test-account", methods=["POST"])
@require_stayflow_admin
def set_test_account(hostel_id):
    """
    Marca/desmarca uma conta como conta de TESTE do proprio dono da
    StayFlow (ver comentario da coluna hostels.is_own_test_account em
    database.py) - so essas aparecem no seletor rapido de "Propriedades"
    no topo do Meu painel.
    """
    if not get_hostel(hostel_id):
        return jsonify({"success": False, "message": "Conta não encontrada."}), 404

    data = request.get_json() or {}
    set_hostel_is_own_test_account(hostel_id, bool(data.get("is_test")))
    return jsonify({"success": True})


@stayflow_admin_bp.route("/stayflow-admin/transactions", methods=["GET"])
@require_stayflow_admin
def transactions():
    """Registro de transacoes (aba Financeiro do Meu painel) - paginado via ?limit=&offset=, filtro opcional ?status=."""
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return jsonify({"success": False, "message": "limit/offset inválidos."}), 400

    status = request.args.get("status") or None
    rows, total = list_recent_guest_charges(limit=limit, offset=offset, status=status)
    return jsonify({"success": True, "transactions": rows, "total": total, "limit": limit, "offset": offset})


@stayflow_admin_bp.route("/stayflow-admin/integrations-status", methods=["GET"])
@require_stayflow_admin
def integrations_status():
    """
    Status (so leitura) das integracoes de NIVEL StayFlow - credenciais
    unicas da plataforma (app registrado na Meta/Mercado Pago, conta
    master do Beds24), diferente de credencial POR hostel (essas ficam
    em Configuracoes de cada conta). Edicao continua sendo via variavel
    de ambiente no Render, nao por aqui - essa tela e so pra saber o
    que ja esta ligado sem precisar abrir o painel do Render.
    """
    import services.beds24_service as beds24_service
    import services.mercadopago_service as mercadopago_service

    return jsonify({
        "success": True,
        "integrations": {
            "beds24_master": beds24_service.is_master_account_configured(),
            "mercadopago_marketplace": mercadopago_service.is_configured(),
            "meta_app": bool(os.getenv("META_APP_ID") and os.getenv("META_APP_SECRET")),
            "instagram_app": bool(os.getenv("INSTAGRAM_APP_ID") and os.getenv("INSTAGRAM_APP_SECRET")),
        },
        "admin_emails": [e.strip() for e in os.getenv("STAYFLOW_ADMIN_EMAILS", "").split(",") if e.strip()],
        "software_persona_hostel_id": get_hostel_id_by_ai_persona("software"),
    })


# ===== Despesas (custos da PROPRIA StayFlow - hosting, ferramentas,
# impostos etc, nada a ver com guest_charges) =====
_EXPENSE_CATEGORIES = {"hosting", "tools", "marketing", "taxes", "other"}
_EXPENSE_RECURRENCES = {"none", "monthly", "yearly"}


@stayflow_admin_bp.route("/stayflow-admin/expenses", methods=["GET"])
@require_stayflow_admin
def expenses_list():
    status = request.args.get("status") or None
    return jsonify({"success": True, "expenses": list_stayflow_expenses(status=status)})


@stayflow_admin_bp.route("/stayflow-admin/expenses", methods=["POST"])
@require_stayflow_admin
def expenses_create():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"success": False, "message": "Título é obrigatório."}), 400

    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Valor inválido."}), 400
    if amount <= 0:
        return jsonify({"success": False, "message": "Valor precisa ser maior que zero."}), 400

    category = data.get("category") or "other"
    if category not in _EXPENSE_CATEGORIES:
        return jsonify({"success": False, "message": "Categoria inválida."}), 400

    recurrence = data.get("recurrence") or "none"
    if recurrence not in _EXPENSE_RECURRENCES:
        return jsonify({"success": False, "message": "Recorrência inválida."}), 400

    expense_id = create_stayflow_expense(
        title, category, amount, (data.get("currency") or "USD").upper(),
        data.get("due_date") or None, recurrence, data.get("notes") or None
    )
    return jsonify({"success": True, "expense_id": expense_id}), 201


@stayflow_admin_bp.route("/stayflow-admin/expenses/<int:expense_id>", methods=["PATCH"])
@require_stayflow_admin
def expenses_update(expense_id):
    data = request.get_json() or {}
    if "category" in data and data["category"] not in _EXPENSE_CATEGORIES:
        return jsonify({"success": False, "message": "Categoria inválida."}), 400
    if "recurrence" in data and data["recurrence"] not in _EXPENSE_RECURRENCES:
        return jsonify({"success": False, "message": "Recorrência inválida."}), 400
    update_stayflow_expense(expense_id, **data)
    return jsonify({"success": True})


@stayflow_admin_bp.route("/stayflow-admin/expenses/<int:expense_id>", methods=["DELETE"])
@require_stayflow_admin
def expenses_delete(expense_id):
    delete_stayflow_expense(expense_id)
    return jsonify({"success": True})


@stayflow_admin_bp.route("/stayflow-admin/expenses/<int:expense_id>/mark-paid", methods=["POST"])
@require_stayflow_admin
def expenses_mark_paid(expense_id):
    try:
        result = mark_stayflow_expense_paid(expense_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404
    return jsonify({"success": True, **result})


# ===== Equipe da propria StayFlow =====
@stayflow_admin_bp.route("/stayflow-admin/team", methods=["GET"])
@require_stayflow_admin
def team_list():
    return jsonify({"success": True, "team": list_stayflow_team()})


@stayflow_admin_bp.route("/stayflow-admin/team", methods=["POST"])
@require_stayflow_admin
def team_add():
    from routes.auth import hash_password

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    if not name or not email:
        return jsonify({"success": False, "message": "Nome e e-mail são obrigatórios."}), 400

    temp_password = secrets.token_urlsafe(9)
    try:
        result = add_stayflow_team_member(name, email, hash_password(temp_password))
    except Exception as error:
        return jsonify({"success": False, "message": "E-mail já cadastrado no sistema."}), 400

    return jsonify({"success": True, "temp_password": temp_password, **result}), 201


@stayflow_admin_bp.route("/stayflow-admin/team/<int:team_id>", methods=["DELETE"])
@require_stayflow_admin
def team_remove(team_id):
    removed_email = remove_stayflow_team_member(team_id)
    if not removed_email:
        return jsonify({"success": False, "message": "Membro não encontrado."}), 404
    return jsonify({"success": True})
