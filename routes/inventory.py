from flask import Blueprint, jsonify, request
from database import get_connection, get_inventory_with_alerts, create_supplier_record
from utils.tenant import require_permission

inventory_bp = Blueprint("inventory", __name__)


# ===== FORNECEDORES =====

@inventory_bp.route("/suppliers", methods=["GET"])
@require_permission("inventory")
def list_suppliers(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, email
        FROM suppliers
        WHERE hostel_id = ?
        ORDER BY name
    """, (hostel_id,))

    suppliers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(suppliers)


@inventory_bp.route("/suppliers", methods=["POST"])
@require_permission("inventory")
def create_supplier(hostel_id):
    data = request.get_json() or {}

    try:
        supplier_id = create_supplier_record(
            hostel_id,
            name=data.get("name"),
            phone=data.get("phone"),
            email=data.get("email"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, "id": supplier_id, "name": (data.get("name") or "").strip()}), 201


# ===== ITENS DE ESTOQUE =====

@inventory_bp.route("/inventory", methods=["GET"])
@require_permission("inventory")
def list_inventory(hostel_id):
    return jsonify(get_inventory_with_alerts(hostel_id))


@inventory_bp.route("/inventory", methods=["POST"])
@require_permission("inventory")
def create_inventory_item(hostel_id):
    data = request.get_json() or {}

    category = (data.get("category") or "").strip()
    name = (data.get("name") or "").strip()

    if not category:
        return jsonify({"success": False, "message": "category is required."}), 400
    if not name:
        return jsonify({"success": False, "message": "name is required."}), 400

    supplier_id = data.get("supplier_id") or None

    conn = get_connection()
    cursor = conn.cursor()

    # confirma que o fornecedor (se informado) pertence a este hostel
    if supplier_id:
        cursor.execute(
            "SELECT id FROM suppliers WHERE id = ? AND hostel_id = ?",
            (supplier_id, hostel_id)
        )
        if not cursor.fetchone():
            supplier_id = None

    cursor.execute(
        """
        INSERT INTO inventory_items
        (hostel_id, category, name, quantity, min_threshold,
         reorder_quantity, unit, supplier_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            hostel_id,
            category,
            name,
            int(data.get("quantity") or 0),
            int(data.get("min_threshold") or 0),
            int(data.get("reorder_quantity") or 0),
            (data.get("unit") or "un").strip(),
            supplier_id
        )
    )

    item_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": item_id}), 201


@inventory_bp.route("/inventory/<int:item_id>", methods=["PATCH"])
@require_permission("inventory")
def update_inventory_item(hostel_id, item_id):
    data = request.get_json() or {}

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM inventory_items WHERE id = ? AND hostel_id = ?",
        (item_id, hostel_id)
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Item not found."}), 404

    editable_int_fields = ["quantity", "min_threshold", "reorder_quantity"]
    for field in editable_int_fields:
        if field in data and data[field] not in (None, ""):
            cursor.execute(
                f"UPDATE inventory_items SET {field} = ? WHERE id = ? AND hostel_id = ?",
                (int(data[field]), item_id, hostel_id)
            )

    if "name" in data and data["name"]:
        cursor.execute(
            "UPDATE inventory_items SET name = ? WHERE id = ? AND hostel_id = ?",
            (data["name"].strip(), item_id, hostel_id)
        )

    if "unit" in data and data["unit"]:
        cursor.execute(
            "UPDATE inventory_items SET unit = ? WHERE id = ? AND hostel_id = ?",
            (data["unit"].strip(), item_id, hostel_id)
        )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@inventory_bp.route("/inventory/<int:item_id>", methods=["DELETE"])
@require_permission("inventory")
def delete_inventory_item(hostel_id, item_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM inventory_items WHERE id = ? AND hostel_id = ?",
        (item_id, hostel_id)
    )

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"success": False, "message": "Item not found."}), 404

    return jsonify({"success": True})