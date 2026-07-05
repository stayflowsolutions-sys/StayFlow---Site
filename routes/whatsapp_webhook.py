import os

from flask import Blueprint, request, jsonify

from database import get_hostel_id_by_whatsapp_phone_number_id
from routes.chat import process_incoming_message

whatsapp_webhook_bp = Blueprint("whatsapp_webhook", __name__)

# Token que VOCÊ escolhe e cadastra tanto aqui (via variável de ambiente)
# quanto no painel da Meta, na hora de configurar o webhook. É só uma
# senha combinada pra Meta confirmar que está falando com o servidor certo.
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "stayflow-verify-token")


@whatsapp_webhook_bp.route("/webhook/whatsapp", methods=["GET"])
def verify_webhook():
    """
    A Meta chama essa rota UMA VEZ, no momento em que você configura
    o webhook no painel dela — só pra confirmar que o servidor é seu.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


@whatsapp_webhook_bp.route("/webhook/whatsapp", methods=["POST"])
def receive_message():
    """
    Webhook real do WhatsApp Business (Meta Cloud API). O formato do
    payload é bem mais aninhado que o nosso /message de teste — essa
    rota traduz o formato da Meta pro processamento interno.
    """
    payload = request.get_json(silent=True) or {}

    try:
        entry = payload.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})

        phone_number_id = value.get("metadata", {}).get("phone_number_id")
        messages = value.get("messages")

        # A Meta também manda notificações de status (entregue, lido,
        # falhou), sem "messages" — antes isso era ignorado sem logar
        # nada. Agora imprimimos o conteúdo pra debug.
        if not messages:
            statuses = value.get("statuses")
            if statuses:
                print("STATUS UPDATE DO WHATSAPP:", statuses)
            else:
                print("WEBHOOK SEM MESSAGES NEM STATUSES:", payload)
            return jsonify({"status": "ignored"}), 200

        incoming = messages[0]
        guest_phone = incoming.get("from")
        text = incoming.get("text", {}).get("body", "")

        hostel_id = get_hostel_id_by_whatsapp_phone_number_id(phone_number_id)

        if not hostel_id:
            print(f"Webhook recebido de phone_number_id desconhecido: {phone_number_id}")
            return jsonify({"status": "unknown_hostel"}), 200

        if text:
            process_incoming_message(hostel_id, guest_phone, text, send_to_whatsapp=True)

    except Exception as error:
        print("Erro ao processar webhook do WhatsApp:", error)

    # Sempre responde 200 rápido pra Meta, mesmo se algo interno falhar —
    # senão a Meta acha que o webhook está com problema e pode desativar.
    return jsonify({"status": "ok"}), 200