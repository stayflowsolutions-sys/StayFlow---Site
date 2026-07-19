from flask import Blueprint, jsonify
from database import get_connection
from utils.tenant import require_permission

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
@require_permission("dashboard")
def dashboard(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM guests WHERE hostel_id = ?",
        (hostel_id,)
    )
    guests = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    messages = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM leads WHERE hostel_id = ?",
        (hostel_id,)
    )
    leads = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    opportunities = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT phone, interest, status, created_at
        FROM leads
        WHERE hostel_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (hostel_id,))
    recent_leads = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT m.sender, m.message, m.created_at
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
        ORDER BY m.id DESC
        LIMIT 5
    """, (hostel_id,))
    recent_messages = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "stats": {
            "guests": guests,
            "messages": messages,
            "leads": leads,
            "opportunities": opportunities
        },
        "recent_leads": recent_leads,
        "recent_messages": recent_messages
    })