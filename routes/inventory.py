from flask import Blueprint, jsonify, request
from database import get_connection
from utils.tenant import require_auth

inventory_bp = Blueprint("inventory", __name__)


def build_reorder_message(item, supplier):
    """
    Monta uma sugestão de mensagem pra reposição — texto pronto que o
    gestor pode revisar e mandar pro fornecedor (WhatsApp, email, etc).
    Hoje é só o texto sugerido; o envio automático fica pra quando
    houver integração de WhatsApp com fornecedores.
    """
    if not supplier:
        return (
            f"Nenhum fornecedor cadastrado para '{item['name']}'. "
            f"Cadastre um fornecedor pra receber a sugestão de contato."
        )

    quantity_to_order = item["reorder_quantity"] or item["min_threshold"] or 1

    return (
        f"Olá {supplier['name']}, tudo bem? Nosso estoque de "
        f"'{item['name']}' está em {item['quantity']} {item['unit']}, "
        f"abaixo do mínimo de {item['min_threshold']}. "
        f"Poderia providenciar mais {quantity_to_order} {item['unit']}?"
    )


# ===== FORNECEDORES =====

@inventory_bp.route("/suppliers", methods=["GET"])
@require_auth
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
@require_auth
def create_supplier(hostel_id):
    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "message": "name is required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO suppliers (hostel_id, name, phone, email)
        VALUES (?, ?, ?, ?)
        """,
        (
            hostel_id,
            name,
            (data.get("phone") or "").strip(),
            (data.get("email") or "").strip()
        )
    )

    supplier_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": supplier_id, "name": name}), 201


# ===== ITENS DE ESTOQUE =====

@inventory_bp.route("/inventory", methods=["GET"])
@require_auth
def list_inventory(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.id, i.category, i.name, i.quantity, i.min_threshold,
            i.reorder_quantity, i.unit, i.supplier_id,
            s.name AS supplier_name, s.phone AS supplier_phone,
            s.email AS supplier_email
        FROM inventory_items i
        LEFT JOIN suppliers s ON s.id = i.supplier_id
        WHERE i.hostel_id = ?
        ORDER BY i.category, i.name
    """, (hostel_id,))

    items = [dict(row) for row in cursor.fetchall()]

    by_category = {}
    alerts = []

    for item in items:
        by_category.setdefault(item["category"], []).append(item)

        if item["quantity"] <= item["min_threshold"]:
            supplier = None
            if item["supplier_id"]:
                supplier = {
                    "name": item["supplier_name"],
                    "phone": item["supplier_phone"],
                    "email": item["supplier_email"]
                }

            alerts.append({
                "id": item["id"],
                "name": item["name"],
                "category": item["category"],
                "quantity": item["quantity"],
                "min_threshold": item["min_threshold"],
                "unit": item["unit"],
                "supplier": supplier,
                "suggested_message": build_reorder_message(item, supplier)
            })

    conn.close()

    return jsonify({
        "items": items,
        "by_category": by_category,
        "alerts": alerts
    })


@inventory_bp.route("/inventory", methods=["POST"])
@require_auth
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
@require_auth
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
@require_auth
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