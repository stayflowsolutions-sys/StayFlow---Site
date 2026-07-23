import json

from flask import Blueprint, jsonify, request
from database import (
    get_connection,
    get_hostel_whatsapp_config,
    save_hostel_whatsapp_config,
    apply_default_room_categories_if_needed,
)
from utils.tenant import require_permission


settings_bp = Blueprint("settings", __name__)

# Campos escalares simples (texto) do contrato de /settings - Empresa
# e Comunicacao dividem a mesma linha/tabela, cada um grava so os
# campos da sua propria aba. opportunity_generation e alert_channels
# tem tratamento proprio (bool/JSON) e ficam fora desta lista.
_SETTINGS_TEXT_FIELDS = [
    "hostel_name", "hostel_type", "legal_name", "tax_id", "address",
    "timezone", "currency", "checkin", "checkout", "logo_url",
    "quiet_hours_start", "quiet_hours_end",
]

_DEFAULT_ALERT_CHANNELS = ["dashboard"]

# Listas fechadas - timezone e currency nao sao categorias abertas
# (diferente de hostel_type), sao padroes IANA/ISO 4217 relevantes
# pros mercados do roadmap (Argentina, Chile, Brasil, Peru, Bolivia,
# Colombia). Mesma lista usada no <select> do frontend.
_VALID_TIMEZONES = {
    "America/Argentina/Buenos_Aires",
    "America/Santiago",
    "America/Sao_Paulo",
    "America/Lima",
    "America/La_Paz",
    "America/Bogota",
}

_VALID_CURRENCIES = {
    "ARS", "CLP", "BRL", "PEN", "BOB", "COP", "USD",
}


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
        SELECT hostel_name, hostel_type, legal_name, tax_id, address,
               timezone, currency, checkin, checkout, logo_url,
               opportunity_generation, alert_channels,
               quiet_hours_start, quiet_hours_end, ai_enabled
        FROM settings
        WHERE hostel_id = ?
    """, (hostel_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        payload = {field: None for field in _SETTINGS_TEXT_FIELDS}
        payload["opportunity_generation"] = True
        payload["alert_channels"] = _DEFAULT_ALERT_CHANNELS
        payload["ai_enabled"] = True
        payload["success"] = True
        return jsonify(payload)

    try:
        alert_channels = json.loads(row["alert_channels"]) if row["alert_channels"] else _DEFAULT_ALERT_CHANNELS
    except (TypeError, ValueError):
        alert_channels = _DEFAULT_ALERT_CHANNELS

    payload = {field: row[field] for field in _SETTINGS_TEXT_FIELDS}
    payload["opportunity_generation"] = bool(row["opportunity_generation"]) if row["opportunity_generation"] is not None else True
    payload["alert_channels"] = alert_channels
    payload["ai_enabled"] = bool(row["ai_enabled"]) if row["ai_enabled"] is not None else True
    payload["success"] = True

    return jsonify(payload)


@settings_bp.route("/settings", methods=["POST"])
@require_permission("settings")
def update_settings(hostel_id):
    data = request.get_json() or {}

    # So valida o campo se ele veio no body - upsert parcial nao pode
    # quebrar so porque timezone/currency nao foram enviados dessa vez.
    if "timezone" in data and data["timezone"] and data["timezone"] not in _VALID_TIMEZONES:
        return jsonify({"success": False, "message": "timezone inválido."}), 400

    if "currency" in data and data["currency"] and data["currency"] not in _VALID_CURRENCIES:
        return jsonify({"success": False, "message": "currency inválida."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM settings WHERE hostel_id = ?", (hostel_id,))
    exists = cursor.fetchone()

    # Upsert parcial de verdade: so entra na atualizacao o que veio no
    # body. Campos omitidos nao sao tocados - Empresa e Comunicacao sao
    # abas diferentes escrevendo na mesma linha, uma nao pode apagar o
    # que a outra ja salvou.
    updates = {}

    for field in _SETTINGS_TEXT_FIELDS:
        if field in data:
            updates[field] = data[field]

    if "opportunity_generation" in data:
        updates["opportunity_generation"] = 1 if data["opportunity_generation"] else 0

    if "ai_enabled" in data:
        updates["ai_enabled"] = 1 if data["ai_enabled"] else 0

    if "alert_channels" in data:
        updates["alert_channels"] = json.dumps(data["alert_channels"])

    if not updates:
        conn.close()
        return jsonify({"success": True})

    if exists:
        set_clause = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [hostel_id]
        cursor.execute(
            f"UPDATE settings SET {set_clause} WHERE hostel_id = ?",
            values
        )
    else:
        columns = ["hostel_id"] + list(updates.keys())
        placeholders = ", ".join("?" for _ in columns)
        values = [hostel_id] + list(updates.values())
        cursor.execute(
            f"INSERT INTO settings ({', '.join(columns)}) VALUES ({placeholders})",
            values
        )

    conn.commit()
    conn.close()

    if "hostel_type" in updates:
        apply_default_room_categories_if_needed(hostel_id, data.get("hostel_type"))

    return jsonify({"success": True})


