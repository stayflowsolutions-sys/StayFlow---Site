from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_auth

finance_bp = Blueprint("finance", __name__)


@finance_bp.route("/finance", methods=["GET"])
@require_auth
def finance(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Receita confirmada: reservas já confirmadas
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM reservations
        WHERE hostel_id = ? AND status = 'confirmed'
    """, (hostel_id,))
    confirmed_revenue = cursor.fetchone()["total"]

    # Receita em risco: oportunidades abertas e urgentes (cliente pode desistir)
    cursor.execute("""
        SELECT COALESCE(SUM(o.estimated_value), 0) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open' AND o.urgency = 'high'
    """, (hostel_id,))
    at_risk = cursor.fetchone()["total"]

    # Recuperável: todas as oportunidades abertas (potencial de receita)
    cursor.execute("""
        SELECT COALESCE(SUM(o.estimated_value), 0) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open'
    """, (hostel_id,))
    recoverable = cursor.fetchone()["total"]

    # Recuperada pela IA: oportunidades já fechadas com sucesso
    # (hoje nenhuma rota fecha oportunidades ainda, então normalmente será 0 —
    # não é bug, é reflexo honesto do que ainda não foi construído)
    cursor.execute("""
        SELECT COALESCE(SUM(o.estimated_value), 0) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'closed'
    """, (hostel_id,))
    recovered = cursor.fetchone()["total"]

    # Movimentações: reservas + oportunidades juntas, mais recentes primeiro
    cursor.execute("""
        SELECT
            'Reserva' AS type,
            guest_name || COALESCE(' - ' || NULLIF(room_type, ''), '') AS description,
            amount AS value,
            status,
            created_at
        FROM reservations
        WHERE hostel_id = ?

        UNION ALL

        SELECT
            'Oportunidade' AS type,
            o.description AS description,
            o.estimated_value AS value,
            o.status,
            o.created_at
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ?

        ORDER BY created_at DESC
        LIMIT 30
    """, (hostel_id, hostel_id))

    movements = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "confirmed_revenue": confirmed_revenue,
        "recovered": recovered,
        "at_risk": at_risk,
        "recoverable": recoverable,
        "movements": movements
    })