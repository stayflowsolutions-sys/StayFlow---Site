"""
Webhook de saida generico (Fase 6 da integracao de canais) - avisa o
sistema proprio de um cliente StayFlow toda vez que uma reserva e
criada/alterada/cancelada, sem exigir que ele adote o mapa de quartos
do StayFlow como fonte de verdade (uso tipico: cliente que so usa o
StayFlow pra atendimento via IA/WhatsApp).

Sem assinatura HMAC nativa de terceiro pra confiar aqui (diferente do
Beds24) - o segredo e gerado pelo proprio StayFlow na hora que o
cliente cadastra a URL, e o cliente usa esse mesmo segredo do lado dele
pra validar que o POST realmente veio do StayFlow.
"""

import hashlib
import hmac
import json
import time

import requests

REQUEST_TIMEOUT = 5


def send_webhook(url, secret, event_type, reservation):
    """
    Retorna (sucesso, detalhe) - nunca levanta excecao (mesmo principio
    de services/whatsapp_service.py e services/beds24_service.py): uma
    falha ao notificar o cliente nao pode derrubar a acao real no
    StayFlow.
    """
    body = json.dumps({
        "event": event_type,
        "reservation": reservation,
        "sent_at": int(time.time()),
    }, default=str)

    signature = hmac.new((secret or "").encode(), body.encode(), hashlib.sha256).hexdigest()

    try:
        response = requests.post(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-StayFlow-Event": event_type,
                "X-StayFlow-Signature": f"sha256={signature}",
            },
            timeout=REQUEST_TIMEOUT,
        )
        return (response.ok, response.status_code)
    except requests.RequestException as error:
        return (False, str(error))
