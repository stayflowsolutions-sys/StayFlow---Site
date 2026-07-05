from datetime import date

from flask import Blueprint, jsonify, request

from database import get_connection
from utils.tenant import require_auth

reservations_bp = Blueprint("reservations", __name__)


@reservations_bp.route("/reservations", methods=["GET"])
@require_auth
def list_reservations(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, guest_id, guest_name, room_type, bed, checkin_date,
               checkout_date, source, payment_method, amount, status,
               created_at
        FROM reservations
        WHERE hostel_id = ?
        ORDER BY checkin_date ASC, id DESC
        """,
        (hostel_id,)
    )

    reservations = [dict(row) for row in cursor.fetchall()]

    today = date.today().isoformat()

    stats = {
        "today": sum(1 for r in reservations if r["checkin_date"] == today),
        "checkins_today": sum(1 for r in reservations if r["checkin_date"] == today),
        "checkouts_today": sum(1 for r in reservations if r["checkout_date"] == today),
        "no_show": sum(1 for r in reservations if r["status"] == "no_show"),
        "total": len(reservations),
        "confirmed_revenue": sum(
            r["amount"] or 0 for r in reservations if r["status"] == "confirmed"
        ),
    }

    conn.close()

    return jsonify({
        "reservations": reservations,
        "stats": stats
    })


@reservations_bp.route("/reservations", methods=["POST"])
@require_auth
def create_reservation(hostel_id):
    data = request.get_json() or {}

    guest_name = (data.get("guest_name") or "").strip()
    room_type = (data.get("room_type") or "").strip()
    checkin_date = (data.get("checkin_date") or "").strip()
    checkout_date = (data.get("checkout_date") or "").strip()

    if not guest_name:
        return jsonify({"success": False, "message": "guest_name is required."}), 400
    if not checkin_date or not checkout_date:
        return jsonify({"success": False, "message": "checkin_date and checkout_date are required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # tenta linkar com um guest já existente do MESMO hostel, pelo telefone
    guest_id = None
    phone = (data.get("phone") or "").strip()
    if phone:
        cursor.execute(
            "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
            (hostel_id, phone)
        )
        row = cursor.fetchone()
        if row:
            guest_id = row["id"]

    cursor.execute(
        """
        INSERT INTO reservations
        (hostel_id, guest_id, guest_name, room_type, bed, checkin_date,
         checkout_date, source, payment_method, amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            hostel_id,
            guest_id,
            guest_name,
            room_type,
            (data.get("bed") or "").strip(),
            checkin_date,
            checkout_date,
            (data.get("source") or "manual").strip(),
            (data.get("payment_method") or "").strip(),
            float(data.get("amount") or 0),
            (data.get("status") or "pending").strip(),
        )
    )

    reservation_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": reservation_id}), 201


@reservations_bp.route("/reservations/<int:reservation_id>", methods=["PATCH"])
@require_auth
def update_reservation(hostel_id, reservation_id):
    data = request.get_json() or {}

    conn = get_connection()
    cursor = conn.cursor()

    # confirma que a reserva pertence a este hostel antes de tocar nela
    cursor.execute(
        "SELECT id FROM reservations WHERE id = ? AND hostel_id = ?",
        (reservation_id, hostel_id)
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Reservation not found."}), 404

    if "status" in data:
        cursor.execute(
            "UPDATE reservations SET status = ? WHERE id = ? AND hostel_id = ?",
            (data["status"], reservation_id, hostel_id)
        )

    conn.commit()
    conn.close()

    return jsonify({"success": True})