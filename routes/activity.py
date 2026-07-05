from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_auth

activity_bp = Blueprint("activity", __name__)


@activity_bp.route("/activity", methods=["GET"])
@require_auth
def activity(hostel_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            m.created_at,
            m.sender,
            m.message,
            g.phone
        FROM messages m
        JOIN conversations c
            ON m.conversation_id = c.id
        JOIN guests g
            ON c.guest_id = g.id
        WHERE g.hostel_id = ?
        ORDER BY m.created_at DESC
        LIMIT 20
    """, (hostel_id,))

    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(rows)