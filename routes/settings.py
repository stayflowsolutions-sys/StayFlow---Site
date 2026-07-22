from flask import Blueprint, jsonify, request
from database import get_connection, get_hostel_whatsapp_config, save_hostel_whatsapp_config
from utils.tenant import require_permission


settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings/whatsapp", methods=["GET"])
@require_permission("settings")
def get_whatsapp_settings(hostel_id):
    phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)

    return jsonify({
        "phone_number_id": phone_number_id or "",
        # Nunca devolve o token de verdade pro frontend por segurança —
        # só indica se já existe um configurado.
        "has_access_token": bool(access_token)
    })


@settings_bp.route("/settings/whatsapp", methods=["POST"])
@require_permission("settings")
def update_whatsapp_settings(hostel_id):
    data = request.get_json() or {}

    phone_number_id = (data.get("phone_number_id") or "").strip()
    access_token = (data.get("access_token") or "").strip()

    if not phone_number_id:
        return jsonify({"success": False, "message": "phone_number_id is required."}), 400

    # se o campo de token vier vazio, mantém o token já salvo
    # (evita que o admin precise colar o token de novo toda vez
    # que só quiser trocar o phone_number_id).
    if not access_token:
        _, existing_token = get_hostel_whatsapp_config(hostel_id)
        access_token = existing_token

    save_hostel_whatsapp_config(hostel_id, phone_number_id, access_token)

    return jsonify({"success": True})


@settings_bp.route("/settings", methods=["GET"])
@require_permission("settings")
def get_settings(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hostel_name, hostel_type, checkin, checkout, opportunity_generation
        FROM settings
        WHERE hostel_id = ?
    """, (hostel_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "hostel_name": row["hostel_name"],
            "hostel_type": row["hostel_type"],
            "checkin": row["checkin"],
            "checkout": row["checkout"],
            "opportunity_generation": bool(row["opportunity_generation"]) if row["opportunity_generation"] is not None else True
        })

    return jsonify({})


@settings_bp.route("/settings", methods=["POST"])
@require_permission("settings")
def update_settings(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    data = request.json or {}

    cursor.execute("SELECT id FROM settings WHERE hostel_id = ?", (hostel_id,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("""
            UPDATE settings SET
                hostel_name = ?,
                hostel_type = ?,
                checkin = ?,
                checkout = ?,
                opportunity_generation = ?
            WHERE hostel_id = ?
        """, (
            data.get("hostel_name"),
            data.get("hostel_type"),
            data.get("checkin"),
            data.get("checkout"),
            1 if data.get("opportunity_generation", True) else 0,
            hostel_id
        ))
    else:
        cursor.execute("""
            INSERT INTO settings (hostel_id, hostel_name, hostel_type, checkin, checkout, opportunity_generation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            hostel_id,
            data.get("hostel_name"),
            data.get("hostel_type"),
            data.get("checkin"),
            data.get("checkout"),
            1 if data.get("opportunity_generation", True) else 0
        ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


