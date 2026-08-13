"""
Envio de mensagem pelo Messenger (Facebook) - mesmo contrato de
services/whatsapp_service.py:send_whatsapp_message (nunca levanta
excecao, retorna bool). Usa o token da PROPRIA Pagina (obtido no OAuth,
services/meta_oauth_service.py) via a Send API do Graph.
"""

import requests

API_BASE = "https://graph.facebook.com/v20.0"
REQUEST_TIMEOUT = 10


def send_messenger_message(page_access_token, psid, message):
    """Retorna True se enviou com sucesso, False se falhou - nunca levanta excecao."""
    if not page_access_token:
        print("Messenger não configurado para este hostel — mensagem gerada mas não enviada.")
        return False

    url = f"{API_BASE}/me/messages"
    payload = {
        "recipient": {"id": psid},
        "message": {"text": message},
        "messaging_type": "RESPONSE",
    }

    try:
        response = requests.post(
            url,
            params={"access_token": page_access_token},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao enviar mensagem Messenger:", response.status_code, response.text)
            return False
        return True
    except requests.RequestException as error:
        print("Erro de conexão ao enviar Messenger:", error)
        return False


def send_messenger_image(page_access_token, psid, image_link):
    """Retorna True se enviou com sucesso, False se falhou - nunca levanta excecao."""
    if not page_access_token:
        print("Messenger não configurado para este hostel — foto gerada mas não enviada.")
        return False

    url = f"{API_BASE}/me/messages"
    payload = {
        "recipient": {"id": psid},
        "message": {"attachment": {"type": "image", "payload": {"url": image_link, "is_reusable": False}}},
        "messaging_type": "RESPONSE",
    }

    try:
        response = requests.post(
            url,
            params={"access_token": page_access_token},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao enviar foto Messenger:", response.status_code, response.text)
            return False
        return True
    except requests.RequestException as error:
        print("Erro de conexão ao enviar foto Messenger:", error)
        return False


def get_messenger_user_profile(page_access_token, psid):
    """
    Busca nome do perfil do Messenger pelo PSID - a conversa ja chega
    identificada (diferente do WhatsApp, onde so se tem o numero de
    telefone), entao a IA nao precisa perguntar o nome de novo.
    Retorna (first_name, last_name), com None em qualquer campo que
    nao vier - nunca levanta excecao.
    """
    if not page_access_token:
        return None, None

    try:
        response = requests.get(
            f"{API_BASE}/{psid}",
            params={"fields": "first_name,last_name", "access_token": page_access_token},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao buscar perfil do Messenger:", response.status_code, response.text)
            return None, None
        data = response.json()
        return data.get("first_name"), data.get("last_name")
    except requests.RequestException as error:
        print("Erro de conexão ao buscar perfil do Messenger:", error)
        return None, None


def download_messenger_attachment(url):
    """
    Baixa uma foto/arquivo enviado pelo hospede no Messenger - a Send
    API entrega uma URL da CDN da Meta ja pronta pra baixar direto
    (diferente do WhatsApp, que exige um passo intermediario pra trocar
    media_id por URL temporaria antes). Retorna (bytes, mime_type), com
    (None, None) se falhar - nunca levanta excecao.
    """
    if not url:
        return None, None

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code >= 400:
            print("Erro ao baixar anexo do Messenger:", response.status_code)
            return None, None
        mime_type = response.headers.get("Content-Type", "").split(";")[0].strip() or "image/jpeg"
        return response.content, mime_type
    except requests.RequestException as error:
        print("Erro de conexão ao baixar anexo do Messenger:", error)
        return None, None
