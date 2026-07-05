from datetime import date

from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_auth

operations_bp = Blueprint("operations", __name__)


@operations_bp.route("/operations", methods=["GET"])
@require_auth
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

    conn.close()

    return jsonify({
        "alerts": alerts,
        # Tarefas operacionais de verdade (limpeza, manutenção) dependem do
        # mapa de camas e do fluxo da equipe — ainda não construído.
        "tasks": []
    })