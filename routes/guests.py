from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_auth

guests_bp = Blueprint("guests", __name__)


@guests_bp.route("/guests", methods=["GET"])
@require_auth
def list_guests(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            g.id,
            g.name,
            g.phone,
            g.email,
            g.language,
            g.created_at,
            (
                SELECT COUNT(*)
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.guest_id = g.id
            ) AS message_count,
            (
                SELECT COALESCE(SUM(o.estimated_value), 0)
                FROM opportunities o
                WHERE o.guest_id = g.id
            ) AS total_value
        FROM guests g
        WHERE g.hostel_id = ?
        ORDER BY g.created_at DESC
    """, (hostel_id,))

    guests = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(guests)


@guests_bp.route("/guests/<int:guest_id>", methods=["GET"])
@require_auth
def guest_profile(hostel_id, guest_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, email, language, created_at
        FROM guests
        WHERE id = ? AND hostel_id = ?
    """, (guest_id, hostel_id))

    guest = cursor.fetchone()

    if not guest:
        conn.close()
        return jsonify({"error": "Guest not found"}), 404

    cursor.execute("""
        SELECT m.sender, m.message, m.created_at
        FROM messages m
        JOIN conversations c
            ON m.conversation_id = c.id
        WHERE c.guest_id = ?
        ORDER BY m.created_at ASC, m.id ASC
    """, (guest_id,))

    messages = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT type, description, score, urgency, estimated_value,
               next_action, status, created_at
        FROM opportunities
        WHERE guest_id = ?
        ORDER BY created_at DESC, id DESC
    """, (guest_id,))

    opportunities = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "guest": dict(guest),
        "messages": messages,
        "opportunities": opportunities
    })