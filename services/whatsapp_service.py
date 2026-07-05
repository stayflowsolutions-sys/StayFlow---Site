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