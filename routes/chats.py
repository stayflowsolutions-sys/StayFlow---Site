from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_auth

chats_bp = Blueprint("chats", __name__)


@chats_bp.route("/chats", methods=["GET"])
@require_auth
def chats(hostel_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            g.id AS guest_id,
            g.phone,
            g.name,
            m.message AS last_message,
            m.sender AS last_sender,
            m.created_at AS last_activity,
            o.type AS intent,
            o.score,
            o.urgency,
            o.estimated_value,
            o.next_action
        FROM guests g

        LEFT JOIN conversations c
            ON c.guest_id = g.id

        LEFT JOIN messages m
            ON m.id = (
                SELECT m2.id
                FROM messages m2
                JOIN conversations c2
                    ON m2.conversation_id = c2.id
                WHERE c2.guest_id = g.id
                ORDER BY m2.created_at DESC, m2.id DESC
                LIMIT 1
            )

        LEFT JOIN opportunities o
            ON o.id = (
                SELECT o2.id
                FROM opportunities o2
                WHERE o2.guest_id = g.id
                ORDER BY o2.created_at DESC, o2.id DESC
                LIMIT 1
            )

        WHERE m.message IS NOT NULL
          AND g.hostel_id = ?

        GROUP BY g.id

        ORDER BY m.created_at DESC
    """, (hostel_id,))

    data = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(data)