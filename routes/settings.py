import json

from flask import Blueprint, jsonify, request
from database import (
    get_connection,
    get_hostel,
    get_hostel_whatsapp_config,
    save_hostel_whatsapp_config,
    apply_default_room_categories_if_needed,
    get_hostel_beds24_property_id,
    save_hostel_beds24_property_id,
    get_channel_room_mappings,
    save_channel_room_mapping,
    delete_channel_room_mapping,
    get_room_category_id_by_beds24_room_id,
    get_hostel_outbound_webhook,
    save_hostel_outbound_webhook_url,
    regenerate_hostel_outbound_webhook_secret,
    clear_hostel_outbound_webhook,
)
import services.beds24_service as beds24_service
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


@settings_bp.route("/settings/beds24", methods=["GET"])
@require_permission("settings")
def get_beds24_settings(hostel_id):
    return jsonify({
        "master_account_ready": beds24_service.is_master_account_configured(),
        "property_id": get_hostel_beds24_property_id(hostel_id) or "",
    })


@settings_bp.route("/settings/beds24/activate", methods=["POST"])
@require_permission("settings")
def activate_beds24(hostel_id):
    if get_hostel_beds24_property_id(hostel_id):
        return jsonify({"success": False, "message": "A integração com canais já está ativada pra este hostel."}), 400

    if not beds24_service.is_master_account_configured():
        return jsonify({"success": False, "message": "Conta master do Beds24 ainda não foi configurada pelo StayFlow."}), 400

    hostel = get_hostel(hostel_id)
    if not hostel:
        return jsonify({"success": False, "message": "Hostel não encontrado."}), 404

    data = request.get_json(silent=True) or {}
    currency = (data.get("currency") or "USD").strip().upper()

    property_id, error = beds24_service.create_property(hostel["name"], currency=currency)
    if error:
        return jsonify({"success": False, "message": error}), 502

    save_hostel_beds24_property_id(hostel_id, property_id)

    return jsonify({"success": True, "property_id": property_id})


@settings_bp.route("/settings/beds24/room-mapping", methods=["GET"])
@require_permission("settings")
def get_beds24_room_mapping(hostel_id):
    property_id = get_hostel_beds24_property_id(hostel_id)
    if not property_id:
        return jsonify({"success": False, "message": "Integração com canais ainda não foi ativada pra este hostel."}), 400

    beds24_rooms, error = beds24_service.get_property_rooms(property_id)
    if error:
        return jsonify({"success": False, "message": error}), 502

    categories = get_channel_room_mappings(hostel_id)
    mapped_ids = {c["beds24_room_id"] for c in categories if c.get("beds24_room_id")}
    unused_rooms = [r for r in beds24_rooms if r["id"] not in mapped_ids]

    return jsonify({
        "success": True,
        "categories": categories,
        "beds24_rooms": beds24_rooms,
        "unused_rooms": unused_rooms,
    })


@settings_bp.route("/settings/beds24/room-mapping", methods=["POST"])
@require_permission("settings")
def save_beds24_room_mapping(hostel_id):
    if not get_hostel_beds24_property_id(hostel_id):
        return jsonify({"success": False, "message": "Integração com canais ainda não foi ativada pra este hostel."}), 400

    data = request.get_json() or {}
    room_category_id = data.get("room_category_id")
    beds24_room_id = (data.get("beds24_room_id") or "").strip()

    if not room_category_id or not beds24_room_id:
        return jsonify({"success": False, "message": "room_category_id e beds24_room_id são obrigatórios."}), 400

    try:
        save_channel_room_mapping(hostel_id, int(room_category_id), beds24_room_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True})


@settings_bp.route("/settings/beds24/room-mapping/<int:room_category_id>", methods=["DELETE"])
@require_permission("settings")
def delete_beds24_room_mapping(hostel_id, room_category_id):
    delete_channel_room_mapping(hostel_id, room_category_id)
    return jsonify({"success": True})


@settings_bp.route("/settings/beds24/rooms/<beds24_room_id>", methods=["DELETE"])
@require_permission("settings")
def delete_beds24_room(hostel_id, beds24_room_id):
    """
    Apaga um quarto direto no Beds24 (limpeza de duplicado/sem uso).
    Duas travas antes de tentar: (1) não deixa apagar quarto que ainda
    está vinculado a uma modalidade - força desvincular primeiro; (2)
    confere contra a lista real da propriedade que esse quarto
    realmente pertence a ESTE hostel, já que a conta master é
    compartilhada entre todos os clientes do StayFlow.
    """
    property_id = get_hostel_beds24_property_id(hostel_id)
    if not property_id:
        return jsonify({"success": False, "message": "Integração com canais ainda não foi ativada pra este hostel."}), 400

    if get_room_category_id_by_beds24_room_id(hostel_id, beds24_room_id):
        return jsonify({"success": False, "message": "Esse quarto está vinculado a uma modalidade. Desvincula antes de apagar."}), 400

    beds24_rooms, error = beds24_service.get_property_rooms(property_id)
    if error:
        return jsonify({"success": False, "message": error}), 502
    if not any(r["id"] == beds24_room_id for r in beds24_rooms):
        return jsonify({"success": False, "message": "Esse quarto não pertence à sua propriedade."}), 403

    success, error = beds24_service.delete_room_type(property_id, beds24_room_id)
    if not success:
        return jsonify({"success": False, "message": error}), 502

    return jsonify({"success": True})


@settings_bp.route("/settings/beds24/create-room", methods=["POST"])
@require_permission("settings")
def create_beds24_room(hostel_id):
    property_id = get_hostel_beds24_property_id(hostel_id)
    if not property_id:
        return jsonify({"success": False, "message": "Integração com canais ainda não foi ativada pra este hostel."}), 400

    data = request.get_json() or {}
    room_category_id = data.get("room_category_id")
    room_name = (data.get("room_name") or "").strip()

    if not room_category_id or not room_name:
        return jsonify({"success": False, "message": "room_category_id e room_name são obrigatórios."}), 400

    beds24_room_id, error = beds24_service.create_room_type(property_id, room_name)
    if error:
        return jsonify({"success": False, "message": error}), 502

    try:
        save_channel_room_mapping(hostel_id, int(room_category_id), beds24_room_id)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, "beds24_room_id": beds24_room_id})


@settings_bp.route("/settings/outbound-webhook", methods=["GET"])
@require_permission("settings")
def get_outbound_webhook_settings(hostel_id):
    url, secret = get_hostel_outbound_webhook(hostel_id)
    return jsonify({
        "url": url or "",
        "secret": secret or "",
        "enabled": bool(url),
    })


@settings_bp.route("/settings/outbound-webhook", methods=["POST"])
@require_permission("settings")
def update_outbound_webhook_settings(hostel_id):
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()

    if not url.startswith("http://") and not url.startswith("https://"):
        return jsonify({"success": False, "message": "A URL precisa começar com http:// ou https://."}), 400

    secret = save_hostel_outbound_webhook_url(hostel_id, url)
    return jsonify({"success": True, "secret": secret})


@settings_bp.route("/settings/outbound-webhook/regenerate-secret", methods=["POST"])
@require_permission("settings")
def regenerate_outbound_webhook_secret(hostel_id):
    url, _ = get_hostel_outbound_webhook(hostel_id)
    if not url:
        return jsonify({"success": False, "message": "Cadastre a URL do webhook antes de gerar uma chave."}), 400

    secret = regenerate_hostel_outbound_webhook_secret(hostel_id)
    return jsonify({"success": True, "secret": secret})


@settings_bp.route("/settings/outbound-webhook", methods=["DELETE"])
@require_permission("settings")
def delete_outbound_webhook_settings(hostel_id):
    clear_hostel_outbound_webhook(hostel_id)
    return jsonify({"success": True})


