import os

from flask import Blueprint, request, jsonify

from database import (
    get_hostel_id_by_facebook_page_id,
    get_hostel_facebook_config,
    get_hostel_id_by_instagram_id,
    get_hostel_instagram_config,
    get_or_create_guest_by_channel,
    save_guest_document,
    save_message_db_for_guest,
)
from routes.chat import process_incoming_message
from services.memory_service import save_message
from services.messenger_service import get_messenger_user_profile, download_messenger_attachment, send_messenger_message
from services.instagram_service import get_instagram_user_profile, download_instagram_attachment, send_instagram_message

meta_webhook_bp = Blueprint("meta_webhook", __name__)

# Mesma ideia do WHATSAPP_VERIFY_TOKEN (routes/whatsapp_webhook.py) -
# senha combinada com o painel da Meta na hora de configurar o webhook
# do Messenger/Instagram. Variavel propria (nao reaproveita a do
# WhatsApp) porque e uma inscricao de webhook separada na Meta, mesmo
# que o valor escolhido possa ser o mesmo texto.
VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "stayflow-verify-token")


def _messenger_config(hostel_id):
    _, access_token = get_hostel_facebook_config(hostel_id)
    return {"access_token": access_token}


def _messenger_send(config, recipient_id, message):
    return send_messenger_message(config["access_token"], recipient_id, message)


def _messenger_profile(config, recipient_id):
    first_name, last_name = get_messenger_user_profile(config["access_token"], recipient_id)
    return " ".join(part for part in [first_name, last_name] if part) or None


def _instagram_config(hostel_id):
    instagram_business_id, access_token = get_hostel_instagram_config(hostel_id)
    return {"access_token": access_token, "instagram_business_id": instagram_business_id}


def _instagram_send(config, recipient_id, message):
    return send_instagram_message(config["access_token"], config["instagram_business_id"], recipient_id, message)


def _instagram_profile(config, recipient_id):
    name, username = get_instagram_user_profile(config["access_token"], recipient_id)
    return name or username or None


def _messenger_download(url):
    return download_messenger_attachment(url)


def _instagram_download(url):
    return download_instagram_attachment(url)


def _resolve_messenger_hostel(entry_id):
    return get_hostel_id_by_facebook_page_id(entry_id)


# TEMPORARIO/HARDCODED (so pra esta conta): confirmado ao vivo que a
# O bug do ID classico vs ID de escopo de app ja foi corrigido na raiz
# (services/meta_oauth_service.py agora salva o ID classico direto,
# confirmado - hostels.instagram_business_id ja esta com "1784...").
# Ainda sobra este mapeamento pra UM caso: quando a conta de TESTE do
# proprio desenvolvedor (usada como segunda testadora, pra poder testar
# sem "cuenta privada") manda mensagem, o entry.id do webhook vem com o
# ID dela mesma, nao o do hostel - comportamento de sandbox entre duas
# contas testadoras do mesmo app, so deve acontecer em modo
# desenvolvimento (sem App Review). Mapeia pro ID JA CORRIGIDO do
# hostel (nao mais o antigo 2800...).
_DEV_MODE_INSTAGRAM_ID_ALIASES = {
    "17841477942485091": "17841416924089707",  # conta de teste do dev -> stayflowsolutions
}


def _fetch_instagram_message_text(mid, access_token):
    """
    Busca o conteudo de uma mensagem do Instagram pelo `mid` - usado
    como fallback quando o evento chega como "message_edit" em vez de
    "message" (ver comentario no loop de eventos). Retorna o texto ou
    None se nao conseguir. Loga a resposta bruta pra ajustar o nome do
    campo certo se a primeira tentativa nao acertar.
    """
    if not mid or not access_token:
        return None
    import requests as _requests
    try:
        res = _requests.get(
            f"https://graph.instagram.com/v20.0/{mid}",
            params={"fields": "from,to,message"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        print(f"Webhook Meta: busca de mensagem por mid - status={res.status_code} body={res.text}")
        if res.status_code >= 400:
            return None
        return res.json().get("message")
    except Exception as error:
        print("Webhook Meta: erro ao buscar mensagem por mid:", error)
        return None


def _resolve_instagram_hostel(entry_id):
    hostel_id = get_hostel_id_by_instagram_id(entry_id)
    if not hostel_id and entry_id in _DEV_MODE_INSTAGRAM_ID_ALIASES:
        hostel_id = get_hostel_id_by_instagram_id(_DEV_MODE_INSTAGRAM_ID_ALIASES[entry_id])
    return hostel_id


# Messenger e Instagram Direct chegam no MESMO endpoint, com o mesmo
# formato de payload (entry[].messaging[]) - o que muda por canal e so
# de onde vem a config (Pagina vs conta Instagram) e qual API chamar
# pra enviar/buscar perfil. Isso evita duplicar o loop de eventos
# inteiro uma vez por canal. Os valores do dict sao funcoes-wrapper (nao
# a referencia direta de send_messenger_message/download_messenger_
# attachment/etc) de proposito - um dict de modulo captura o OBJETO da
# funcao no momento em que e criado, entao um mock que substitui o nome
# no modulo depois (ex: em teste, patch("routes.meta_webhook.
# download_messenger_attachment")) nao teria efeito nenhum aqui dentro
# sem esse nivel de indirecao.
_CHANNEL_ADAPTERS = {
    "messenger": {
        "resolve_hostel": _resolve_messenger_hostel,
        "get_config": _messenger_config,
        "send": _messenger_send,
        "profile": _messenger_profile,
        "download": _messenger_download,
    },
    "instagram": {
        "resolve_hostel": _resolve_instagram_hostel,
        "get_config": _instagram_config,
        "send": _instagram_send,
        "profile": _instagram_profile,
        "download": _instagram_download,
    },
}


def handle_incoming_document_image(hostel_id, channel, external_id, attachment_url, adapter, config):
    """
    Processa uma foto enviada pelo hospede (ex: documento de
    identidade) - baixa o arquivo de verdade, grava no disco e no
    banco, e confirma o recebimento por texto direto (sem passar pela
    IA de conversa, ja que ela nao analisa o conteudo da imagem) -
    mesmo padrao ja usado pro WhatsApp
    (routes/whatsapp_webhook.py:handle_incoming_document_image).
    Generica por canal (Messenger/Instagram) via `adapter`.
    """
    file_bytes, mime_type = adapter["download"](attachment_url)

    if not file_bytes:
        adapter["send"](config, external_id, "Não consegui receber sua foto agora, pode tentar mandar de novo?")
        return

    guest_id = get_or_create_guest_by_channel(hostel_id, channel, external_id)
    save_guest_document(hostel_id, guest_id, file_bytes, mime_type)

    # Registra na conversa normal (visivel no historico/Chats), igual
    # uma mensagem de texto - so pra equipe saber que uma foto chegou
    # sem precisar abrir a pasta de documentos.
    placeholder = "[Hóspede enviou uma foto de documento]"
    save_message(hostel_id, f"{channel}:{external_id}", "user", placeholder)
    save_message_db_for_guest(guest_id, "user", placeholder, channel=channel)

    adapter["send"](config, external_id, "Recebi seu documento, obrigado! 📄✅")


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
    Webhook real do Messenger e do Instagram Direct (mesmo endpoint pra
    os dois). Formato do payload: {"object": "page"|"instagram",
    "entry": [{"id": <page_id ou instagram_business_id>, "messaging":
    [{"sender": {"id": psid_ou_igsid}, "message": {"text": "..."}}]}]}.
    O campo "object" indica o canal (nao 100% confirmado na doc
    primaria da Meta ate o primeiro teste ao vivo - por isso tem
    fallback abaixo tentando os dois lookups se vier ausente/
    inesperado). Sempre responde 200 rapido pra Meta, mesmo se algo
    interno falhar - senao a Meta pode desativar o webhook.
    """
    payload = request.get_json(silent=True) or {}
    print("Webhook Meta: payload bruto recebido:", payload)

    try:
        object_type = payload.get("object")
        entries = payload.get("entry", [])

        for entry in entries:
            entry_id = entry.get("id")

            channel = {"page": "messenger", "instagram": "instagram"}.get(object_type)
            hostel_id = _CHANNEL_ADAPTERS[channel]["resolve_hostel"](entry_id) if channel else None

            if not hostel_id:
                for candidate_channel, candidate_adapter in _CHANNEL_ADAPTERS.items():
                    resolved = candidate_adapter["resolve_hostel"](entry_id)
                    if resolved:
                        channel, hostel_id = candidate_channel, resolved
                        break

            if not hostel_id:
                print(f"Webhook Meta: id desconhecido (object={object_type}): {entry_id}")
                continue

            adapter = _CHANNEL_ADAPTERS[channel]

            for event in entry.get("messaging", []):
                message = event.get("message")

                # TEMPORARIO/investigacao: confirmado ao vivo que, pelo
                # menos entre duas contas testadoras do mesmo app (antes
                # do App Review), o Instagram as vezes entrega a mensagem
                # nova como um evento "message_edit" (num_edit=0) em vez
                # do evento "message" padrao - sem o texto, so o `mid`.
                # Busca o conteudo de verdade por esse mid via API como
                # fallback, so pro Instagram.
                message_edit = event.get("message_edit")
                if not message and message_edit and channel == "instagram":
                    mid = message_edit.get("mid")
                    fallback_sender_id = event.get("sender", {}).get("id")
                    if mid and fallback_sender_id:
                        fallback_config = adapter["get_config"](hostel_id)
                        fetched_text = _fetch_instagram_message_text(mid, fallback_config.get("access_token"))
                        if fetched_text:
                            message = {"text": fetched_text}

                # Eventos sem "message" (delivery/read receipts,
                # postbacks de botao, etc) sao ignorados por enquanto -
                # so texto/imagem de verdade sao processados nesta rodada.
                if not message or message.get("is_echo"):
                    continue

                sender_id = event.get("sender", {}).get("id")
                text = message.get("text")
                attachments = message.get("attachments") or []
                image_attachment = next((a for a in attachments if a.get("type") == "image"), None)

                if not sender_id:
                    continue

                config = adapter["get_config"](hostel_id)

                if image_attachment:
                    url = (image_attachment.get("payload") or {}).get("url")
                    if url:
                        handle_incoming_document_image(hostel_id, channel, sender_id, url, adapter, config)
                elif text:
                    # Busca o nome do perfil a cada mensagem - so e
                    # realmente GRAVADO na primeira vez (get_or_create_
                    # guest_by_channel so usa "name" ao CRIAR o
                    # hospede), o custo de buscar de novo em mensagens
                    # seguintes e so uma chamada a mais ao Graph, sem
                    # persistir nada errado.
                    guest_name = adapter["profile"](config, sender_id)
                    print(f"Webhook Meta: chamando process_incoming_message hostel_id={hostel_id} channel={channel} sender_id={sender_id} text={text!r} guest_name={guest_name!r}")

                    process_incoming_message(
                        hostel_id, sender_id, text, channel=channel, send_reply=True, name=guest_name
                    )
                    print("Webhook Meta: process_incoming_message terminou sem excecao")

    except Exception:
        import traceback
        print("Erro ao processar webhook do Meta (Messenger/Instagram):")
        traceback.print_exc()

    return jsonify({"status": "ok"}), 200
