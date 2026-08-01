"""
Envio de mensagem pelo Instagram Direct - mesmo contrato de
services/whatsapp_service.py:send_whatsapp_message e
services/messenger_service.py:send_messenger_message (nunca levanta
excecao, retorna bool), mas usando o host/endpoint/autenticacao do
"Instagram API with Instagram Login" (services/meta_oauth_service.py):
graph.instagram.com em vez de graph.facebook.com, endpoint
/<IG_BUSINESS_ID>/messages em vez de /me/messages, e token no header
Authorization em vez de query param.
"""

import requests

API_BASE = "https://graph.instagram.com/v20.0"
REQUEST_TIMEOUT = 10


def send_instagram_message(access_token, instagram_business_id, igsid, message):
    """Retorna True se enviou com sucesso, False se falhou - nunca levanta excecao."""
    if not access_token or not instagram_business_id:
        print("Instagram não configurado para este hostel — mensagem gerada mas não enviada.")
        return False

    url = f"{API_BASE}/{instagram_business_id}/messages"
    payload = {
        "recipient": {"id": igsid},
        "message": {"text": message},
    }

    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao enviar mensagem Instagram:", response.status_code, response.text)
            return False
        return True
    except requests.RequestException as error:
        print("Erro de conexão ao enviar Instagram:", error)
        return False


def get_instagram_user_profile(access_token, igsid):
    """
    Tentativa best-effort de buscar nome/username de quem mandou a
    mensagem no Direct - diferente do Messenger, a documentacao da Meta
    nao confirma um endpoint de perfil equivalente pra esse fluxo
    (Instagram Login, sem Pagina). Se a chamada falhar por qualquer
    motivo (endpoint nao existir, permissao faltando, etc), devolve
    (None, None) e a IA simplesmente pergunta o nome, igual ja faz no
    WhatsApp - nunca levanta excecao, nunca bloqueia o fluxo.
    """
    if not access_token:
        return None, None

    try:
        response = requests.get(
            f"{API_BASE}/{igsid}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"fields": "name,username"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao buscar perfil do Instagram (endpoint pode não existir para este fluxo):", response.status_code, response.text)
            return None, None
        data = response.json()
        return data.get("name"), data.get("username")
    except requests.RequestException as error:
        print("Erro de conexão ao buscar perfil do Instagram:", error)
        return None, None


def download_instagram_attachment(url):
    """
    Baixa uma foto/arquivo enviado pelo hospede no Instagram Direct - o
    webhook ja entrega uma URL pronta pra baixar direto, mesmo padrao
    do Messenger. Retorna (bytes, mime_type), com (None, None) se
    falhar - nunca levanta excecao.
    """
    if not url:
        return None, None

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code >= 400:
            print("Erro ao baixar anexo do Instagram:", response.status_code)
            return None, None
        mime_type = response.headers.get("Content-Type", "").split(";")[0].strip() or "image/jpeg"
        return response.content, mime_type
    except requests.RequestException as error:
        print("Erro de conexão ao baixar anexo do Instagram:", error)
        return None, None
