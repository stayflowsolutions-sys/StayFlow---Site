from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_auth

opportunities_bp = Blueprint("opportunities", __name__)


@opportunities_bp.route("/opportunities", methods=["GET"])
@require_auth
def opportunities(hostel_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            o.id,
            g.phone,
            o.type,
            o.description,
            o.status,
            o.score,
            o.urgency,
            o.estimated_value,
            o.next_action,
            o.created_at
        FROM opportunities o
        JOIN guests g
            ON o.guest_id = g.id
        WHERE g.hostel_id = ?
        ORDER BY o.created_at DESC
    """, (hostel_id,))

    data = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(data)