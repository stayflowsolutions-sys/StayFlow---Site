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

from flask import Blueprint, jsonify

from database import get_stayflow_admin_overview, get_hostel_currency, PLAN_PRICES
from utils.tenant import require_stayflow_admin

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
    rows = get_stayflow_admin_overview()

    hostels = []
    for row in rows:
        plan_name = row["plan_name"]
        hostels.append({
            "hostel_id": row["hostel_id"],
            "hostel_name": row["hostel_name"],
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
