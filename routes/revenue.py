from flask import Blueprint, jsonify, request
from database import get_connection
from utils.tenant import require_permission

revenue_bp = Blueprint("revenue", __name__)


@revenue_bp.route("/revenue", methods=["GET"])
@require_permission("revenue")
def revenue(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Catálogo de experiências/upsells que o hostel oferece
    cursor.execute("""
        SELECT id, type, name, price
        FROM offerings
        WHERE hostel_id = ?
        ORDER BY type, name
    """, (hostel_id,))
    offerings = [dict(row) for row in cursor.fetchall()]

    # Oportunidades reais que a IA já classificou como tour/upsell
    cursor.execute("""
        SELECT o.id, o.type, o.description, o.estimated_value, o.next_action, g.phone
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open' AND o.type IN ('tour', 'upsell')
        ORDER BY o.estimated_value DESC
    """, (hostel_id,))
    opportunities = [dict(row) for row in cursor.fetchall()]

    extra_revenue = sum(o["estimated_value"] or 0 for o in opportunities)

    conn.close()

    return jsonify({
        "offerings": offerings,
        "opportunities": opportunities,
        "extra_revenue": extra_revenue
    })


@revenue_bp.route("/offerings", methods=["POST"])
@require_permission("revenue")
def create_offering(hostel_id):
    data = request.get_json() or {}

    offering_type = (data.get("type") or "").strip()
    name = (data.get("name") or "").strip()

    if not offering_type:
        return jsonify({"success": False, "message": "type is required."}), 400
    if not name:
        return jsonify({"success": False, "message": "name is required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO offerings (hostel_id, type, name, price)
        VALUES (?, ?, ?, ?)
        """,
        (hostel_id, offering_type, name, float(data.get("price") or 0))
    )

    offering_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": offering_id}), 201


@revenue_bp.route("/offerings/<int:offering_id>", methods=["DELETE"])
@require_permission("revenue")
def delete_offering(hostel_id, offering_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM offerings WHERE id = ? AND hostel_id = ?",
        (offering_id, hostel_id)
    )

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"success": False, "message": "Offering not found."}), 404

    return jsonify({"success": True})