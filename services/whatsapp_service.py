"""
Serviço de envio de mensagens pelo WhatsApp Business (Meta Cloud API).

Antes desse arquivo existir, o StayFlow só GERAVA a resposta da IA
e devolvia no corpo da requisição HTTP — ninguém de fato entregava
essa resposta pro hóspede no WhatsApp. Esse arquivo fecha essa lacuna.
"""

import requests

GRAPH_API_VERSION = "v20.0"


def send_whatsapp_message(phone_number_id, access_token, to, message):
    """
    Envia uma mensagem de texto pelo WhatsApp Business.

    Retorna True se enviou com sucesso, False se falhou (por falta de
    configuração ou erro da API) — nunca levanta exceção, porque uma
    falha de envio não pode derrubar o processamento da mensagem.
    """
    if not phone_number_id or not access_token:
        print(
            "WhatsApp não configurado para este hostel — "
            "mensagem gerada mas não enviada."
        )
        return False

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code >= 400:
            print(
                "Erro ao enviar mensagem WhatsApp:",
                response.status_code,
                response.text
            )
            return False

        return True

    except Exception as error:
        print("Erro de conexão ao enviar WhatsApp:", error)
        return False


def send_whatsapp_image(phone_number_id, access_token, to, image_link, caption=""):
    """
    Envia uma foto pelo WhatsApp Business - a API exige um link publico
    HTTPS que os servidores da Meta conseguem buscar sozinhos (nao um
    upload direto de bytes), por isso quem chama monta a URL publica do
    media (ver rota /media/chat/<token> em app.py) antes de chegar aqui.
    Mesmo contrato de send_whatsapp_message (nunca levanta excecao).
    """
    if not phone_number_id or not access_token:
        print("WhatsApp não configurado para este hostel — foto gerada mas não enviada.")
        return False

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    image_payload = {"link": image_link}
    if caption:
        image_payload["caption"] = caption
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": image_payload,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code >= 400:
            print("Erro ao enviar foto WhatsApp:", response.status_code, response.text)
            return False
        return True
    except Exception as error:
        print("Erro de conexão ao enviar foto WhatsApp:", error)
        return False


def download_whatsapp_media(media_id, access_token):
    """
    Baixa uma midia recebida do WhatsApp (ex: foto de documento) - e
    sempre em 2 passos na API da Meta: primeiro pega a URL temporaria
    de download (expira rapido), depois baixa o arquivo de verdade
    dessa URL, sempre autenticado com o mesmo token.

    Retorna (bytes, mime_type) ou (None, None) se falhar - nunca
    levanta excecao, mesmo motivo do send_whatsapp_message.
    """
    if not access_token:
        print("WhatsApp não configurado para este hostel — não foi possível baixar a mídia.")
        return None, None

    try:
        info_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{media_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        info_response = requests.get(info_url, headers=headers, timeout=10)
        if info_response.status_code >= 400:
            print("Erro ao buscar URL da mídia do WhatsApp:", info_response.status_code, info_response.text)
            return None, None

        info = info_response.json()
        media_url = info.get("url")
        mime_type = info.get("mime_type", "application/octet-stream")

        if not media_url:
            print("Resposta da Meta sem URL de mídia:", info)
            return None, None

        file_response = requests.get(media_url, headers=headers, timeout=20)
        if file_response.status_code >= 400:
            print("Erro ao baixar arquivo de mídia do WhatsApp:", file_response.status_code)
            return None, None

        return file_response.content, mime_type

    except Exception as error:
        print("Erro de conexão ao baixar mídia do WhatsApp:", error)
        return None, None