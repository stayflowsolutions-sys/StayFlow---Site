from datetime import date

from flask import Blueprint, jsonify
from database import get_connection, get_cleaning_list
from utils.tenant import require_permission

operations_bp = Blueprint("operations", __name__)


@operations_bp.route("/operations", methods=["GET"])
@require_permission("operations")
def operations(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()
    alerts = []

    # Check-ins e check-outs de hoje ainda não confirmados
    cursor.execute("""
        SELECT guest_name, checkin_date, checkout_date, status
        FROM reservations
        WHERE hostel_id = ?
          AND (checkin_date = ? OR checkout_date = ?)
          AND status != 'confirmed'
    """, (hostel_id, today, today))

    for row in cursor.fetchall():
        kind = "Check-in" if row["checkin_date"] == today else "Check-out"
        alerts.append(
            f"{kind} de hoje ainda pendente: {row['guest_name']} (status: {row['status']})"
        )

    # Oportunidades urgentes ainda em aberto
    cursor.execute("""
        SELECT o.description, g.phone
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open' AND o.urgency = 'high'
    """, (hostel_id,))

    for row in cursor.fetchall():
        alerts.append(f"Hóspede aguardando resposta urgente ({row['phone']}): {row['description']}")

    # Itens de estoque no mínimo ou abaixo
    cursor.execute("""
        SELECT name, quantity, min_threshold, unit
        FROM inventory_items
        WHERE hostel_id = ? AND quantity <= min_threshold
    """, (hostel_id,))

    for row in cursor.fetchall():
        alerts.append(
            f"Estoque baixo: {row['name']} ({row['quantity']} {row['unit']}, "
            f"mínimo {row['min_threshold']} {row['unit']})"
        )

    # Reservas criadas automaticamente (WhatsApp, Beds24/qualquer OTA -
    # tudo que nao veio de cadastro manual da equipe) nas ultimas 24h.
    # Janela de tempo em vez de "todas pra sempre" pra nao acumular
    # alerta de reserva antiga que a equipe ja viu ha dias.
    cursor.execute("""
        SELECT guest_name, source, checkin_date, checkout_date
        FROM reservations
        WHERE hostel_id = ? AND source != 'manual'
          AND created_at >= datetime('now', '-1 day')
        ORDER BY created_at DESC
    """, (hostel_id,))

    for row in cursor.fetchall():
        alerts.append(
            f"Nova reserva via {row['source']}: {row['guest_name']} "
            f"({row['checkin_date']} → {row['checkout_date']})"
        )

    conn.close()

    # Tarefas de limpeza vem direto do Mapa de Quartos - mesma fonte de
    # verdade (camas com status 'needs_cleaning'), sem tabela duplicada.
    cleaning_list = get_cleaning_list(hostel_id)
    tasks = [
        {
            "task": f"Limpar {item['label']} ({item['room_name']})",
            "assignee": "Equipe de limpeza",
            "status": "pending"
        }
        for item in cleaning_list
    ]

    # Cada cama aguardando limpeza tambem conta como alerta (nao so
    # tarefa) - sem isso, um check-out nunca incrementava o sininho de
    # notificacoes nem aparecia pra quem loga so olhando o resumo geral.
    for item in cleaning_list:
        alerts.append(f"Limpeza pendente: {item['label']} ({item['room_name']})")

    return jsonify({
        "alerts": alerts,
        "tasks": tasks
    })