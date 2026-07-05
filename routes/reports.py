from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_auth

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports", methods=["GET"])
@require_auth
def reports(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Receita por canal de origem da reserva
    cursor.execute("""
        SELECT
            COALESCE(NULLIF(source, ''), 'manual') AS channel,
            COALESCE(SUM(amount), 0) AS revenue
        FROM reservations
        WHERE hostel_id = ?
        GROUP BY channel
        ORDER BY revenue DESC
    """, (hostel_id,))
    by_channel = [dict(row) for row in cursor.fetchall()]

    # Funil: hóspedes -> mensagens -> oportunidades -> reservas confirmadas
    cursor.execute("SELECT COUNT(*) AS c FROM guests WHERE hostel_id = ?", (hostel_id,))
    total_guests = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    total_messages = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    total_opportunities = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c
        FROM reservations
        WHERE hostel_id = ? AND status = 'confirmed'
    """, (hostel_id,))
    total_confirmed = cursor.fetchone()["c"]

    funnel = [
        {"stage": "Hóspedes", "count": total_guests},
        {"stage": "Mensagens", "count": total_messages},
        {"stage": "Oportunidades", "count": total_opportunities},
        {"stage": "Reservas confirmadas", "count": total_confirmed},
    ]

    conn.close()

    return jsonify({
        "by_channel": by_channel,
        "funnel": funnel
    })