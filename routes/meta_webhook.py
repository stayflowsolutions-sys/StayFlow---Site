import os

from flask import Blueprint, request, jsonify

from database import get_hostel_id_by_facebook_page_id, get_hostel_facebook_config
from routes.chat import process_incoming_message
from services.messenger_service import get_messenger_user_profile

meta_webhook_bp = Blueprint("meta_webhook", __name__)

# Mesma ideia do WHATSAPP_VERIFY_TOKEN (routes/whatsapp_webhook.py) -
# senha combinada com o painel da Meta na hora de configurar o webhook
# do Messenger/Instagram. Variavel propria (nao reaproveita a do
# WhatsApp) porque e uma inscricao de webhook separada na Meta, mesmo
# que o valor escolhido possa ser o mesmo texto.
VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "stayflow-verify-token")


@meta_webhook_bp.route("/webhook/meta", methods=["GET"])
def verify_webhook():
    """
    A Meta chama essa rota UMA VEZ, no momento em que voce configura o
    webhook do Messenger/Instagram no painel dela - mesmo handshake
    generico usado em /webhook/whatsapp (nao e especifico de produto).
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


@meta_webhook_bp.route("/webhook/meta", methods=["POST"])
def receive_message():
    """
    Webhook real do Messenger (Facebook) - Instagram Direct entra numa
    rodada seguinte, quando o Instagram Login estiver conectado. Formato
    do payload: {"entry": [{"id": <page_id ou instagram_id>, "messaging":
    [{"sender": {"id": psid}, "message": {"text": "..."}}]}]}. Sempre
    responde 200 rapido pra Meta, mesmo se algo interno falhar - senao a
    Meta pode desativar o webhook.
    """
    payload = request.get_json(silent=True) or {}

    try:
        entries = payload.get("entry", [])

        for entry in entries:
            page_id = entry.get("id")
            hostel_id = get_hostel_id_by_facebook_page_id(page_id)

            if not hostel_id:
                print(f"Webhook Meta: page_id desconhecido: {page_id}")
                continue

            for event in entry.get("messaging", []):
                # Eventos sem "message" (delivery/read receipts,
                # postbacks de botao, etc) sao ignorados por enquanto -
                # so texto de verdade e processado nesta rodada.
                message = event.get("message")
                if not message or message.get("is_echo"):
                    continue

                psid = event.get("sender", {}).get("id")
                text = message.get("text")

                if psid and text:
                    # Busca o nome do perfil do Messenger a cada mensagem -
                    # so e realmente GRAVADO na primeira vez (get_or_create_
                    # guest_by_channel so usa "name" ao CRIAR o hospede), o
                    # custo de buscar de novo em mensagens seguintes e so
                    # uma chamada a mais ao Graph, sem persistir nada errado.
                    _, access_token = get_hostel_facebook_config(hostel_id)
                    first_name, last_name = get_messenger_user_profile(access_token, psid)
                    guest_name = " ".join(part for part in [first_name, last_name] if part) or None

                    process_incoming_message(
                        hostel_id, psid, text, channel="messenger", send_reply=True, name=guest_name
                    )

    except Exception as error:
        print("Erro ao processar webhook do Meta (Messenger):", error)

    return jsonify({"status": "ok"}), 200
