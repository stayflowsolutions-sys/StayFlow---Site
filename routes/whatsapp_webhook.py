import os

from flask import Blueprint, request, jsonify

from database import (
    get_hostel_id_by_whatsapp_phone_number_id,
    get_hostel_whatsapp_config,
    get_or_create_guest,
    save_guest_document,
)
from routes.chat import process_incoming_message
from services.whatsapp_service import download_whatsapp_media, send_whatsapp_message
from services.memory_service import save_message
from services.message_service import save_message_db
from utils.webhook_security import verify_meta_signature

whatsapp_webhook_bp = Blueprint("whatsapp_webhook", __name__)

# Token que VOCÊ escolhe e cadastra tanto aqui (via variável de ambiente)
# quanto no painel da Meta, na hora de configurar o webhook. É só uma
# senha combinada pra Meta confirmar que está falando com o servidor certo.
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "stayflow-verify-token")


def handle_incoming_document_image(hostel_id, guest_phone, image_data):
    """
    Processa uma foto enviada pelo hospede (ex: documento de
    identidade) - baixa o arquivo de verdade da API da Meta (2 passos:
    URL temporaria, depois o arquivo), grava no disco e no banco, e
    confirma o recebimento por texto direto (sem passar pela IA de
    conversa, ja que ela nao analisa o conteudo da imagem).
    """
    media_id = image_data.get("id")
    if not media_id:
        return

    guest_id = get_or_create_guest(hostel_id, guest_phone)
    phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)

    file_bytes, mime_type = download_whatsapp_media(media_id, access_token)

    if not file_bytes:
        send_whatsapp_message(
            phone_number_id, access_token, guest_phone,
            "Não consegui receber sua foto agora, pode tentar mandar de novo?"
        )
        return

    save_guest_document(hostel_id, guest_id, file_bytes, mime_type, whatsapp_media_id=media_id)

    # Registra na conversa normal (visivel no historico/Chats), igual
    # uma mensagem de texto - so pra equipe saber que uma foto chegou
    # sem precisar abrir a pasta de documentos.
    placeholder = "[Hóspede enviou uma foto de documento]"
    save_message(hostel_id, guest_phone, "user", placeholder)
    save_message_db(hostel_id, guest_phone, "user", placeholder)

    send_whatsapp_message(
        phone_number_id, access_token, guest_phone,
        "Recebi seu documento, obrigado! 📄✅"
    )


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
    if not verify_meta_signature(request):
        print("Webhook WhatsApp: assinatura invalida, payload rejeitado.")
        return "Invalid signature", 403

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
        message_type = incoming.get("type")
        text = incoming.get("text", {}).get("body", "")

        hostel_id = get_hostel_id_by_whatsapp_phone_number_id(phone_number_id)

        if not hostel_id:
            print(f"Webhook recebido de phone_number_id desconhecido: {phone_number_id}")
            return jsonify({"status": "unknown_hostel"}), 200

        if message_type == "image":
            handle_incoming_document_image(hostel_id, guest_phone, incoming.get("image", {}))
        elif text:
            process_incoming_message(hostel_id, guest_phone, text, channel="whatsapp", send_reply=True)

    except Exception as error:
        print("Erro ao processar webhook do WhatsApp:", error)

    # Sempre responde 200 rápido pra Meta, mesmo se algo interno falhar —
    # senão a Meta acha que o webhook está com problema e pode desativar.
    return jsonify({"status": "ok"}), 200