import json
import os

from pywebpush import WebPushException, webpush

_VAPID_CLAIMS_SUB = "mailto:stayflowsolutions@gmail.com"


def is_push_configured():
    """As chaves VAPID sao segredo de servidor (variaveis de ambiente, nunca no repositorio) - sem elas, push fica desligado em silencio (mesmo padrao ja usado pra META_APP_SECRET/webhook)."""
    return bool(os.getenv("VAPID_PRIVATE_KEY"))


def get_vapid_public_key():
    """Chave publica - essa sim pode ir pro frontend, e o que o navegador usa em pushManager.subscribe({applicationServerKey})."""
    return os.getenv("VAPID_PUBLIC_KEY", "")


def send_push_to_subscription(subscription, title, body, url=None):
    """
    Manda uma notificacao push pra UMA inscricao (um dispositivo)
    especifica. Devolve "ok", "expired" (404/410 - o proprio navegador
    ja cancelou essa inscricao, ex: usuario limpou dados do navegador ou
    desinstalou o app - quem chamar deve apagar do banco) ou "error"
    (falha temporaria, nao apaga - proxima notificacao tenta de novo).
    """
    private_key = os.getenv("VAPID_PRIVATE_KEY")
    if not private_key:
        return "error"

    payload = json.dumps({"title": title, "body": body, "url": url or "/app"})

    try:
        webpush(
            subscription_info={
                "endpoint": subscription["endpoint"],
                "keys": {"p256dh": subscription["p256dh"], "auth": subscription["auth"]},
            },
            data=payload,
            vapid_private_key=private_key,
            vapid_claims={"sub": _VAPID_CLAIMS_SUB},
        )
        return "ok"
    except WebPushException as error:
        status_code = getattr(error.response, "status_code", None)
        if status_code in (404, 410):
            return "expired"
        print(f"AVISO: falha ao enviar notificacao push: {error}")
        return "error"
    except Exception as error:
        print(f"AVISO: falha ao enviar notificacao push: {error}")
        return "error"


def send_push_to_hostel(hostel_id, title, body, url=None):
    """
    Manda pra todos os dispositivos inscritos daquela hospedagem (cada
    pessoa da equipe pode ter mais de um - PC e celular contam como
    inscricoes separadas). Respeita o horario de silencio configurado
    (nunca manda nada fora do horario definido pela propria hospedagem).
    Limpa do banco qualquer inscricao que o navegador ja invalidou.
    """
    if not is_push_configured():
        return

    from database import delete_push_subscription, get_push_subscriptions, is_within_quiet_hours

    if is_within_quiet_hours(hostel_id):
        return

    for subscription in get_push_subscriptions(hostel_id):
        result = send_push_to_subscription(subscription, title, body, url)
        if result == "expired":
            delete_push_subscription(hostel_id, subscription["endpoint"])
