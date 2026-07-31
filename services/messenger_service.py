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
