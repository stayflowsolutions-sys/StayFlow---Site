import hashlib
import hmac
import os


def verify_meta_signature(request):
    """
    Confirma que um POST de webhook (Messenger/Instagram/WhatsApp)
    realmente veio da Meta, validando o header X-Hub-Signature-256
    (HMAC-SHA256 do corpo bruto da requisicao, assinado com o App
    Secret). Sem isso, qualquer pessoa que descobrisse a URL do
    webhook podia forjar uma mensagem "de hospede" sem credencial
    nenhuma.

    Testa contra os DOIS App Secrets que a StayFlow usa (META_APP_SECRET,
    do app "StayFlow AI" usado pelo Facebook/Messenger/WhatsApp, e
    INSTAGRAM_APP_SECRET, do app separado do "Instagram API with
    Instagram Login" - services/meta_oauth_service.py ja documenta que
    sao credenciais distintas, nao dá pra reaproveitar uma pela outra).
    A Meta assina cada webhook com o secret do app dono da inscricao;
    como so recebemos o corpo bruto aqui, sem saber ainda de qual canal
    veio, aceitar qualquer um dos dois secrets configurados e seguro
    (sao os dois nossos) e evita ter que decidir isso antes de validar.

    Bug real corrigido (05/08/2026): antes so testava META_APP_SECRET -
    todo webhook do Instagram chegava, a inscricao estava ativa, e
    mesmo assim caia em "assinatura invalida" porque a Meta assina com
    INSTAGRAM_APP_SECRET, nunca comparado ate agora.

    Usa request.get_data() (bytes brutos, antes de qualquer parse) -
    a assinatura so bate se calculada sobre o corpo exatamente como
    chegou, byte a byte; comparar depois de um json.dumps re-serializado
    quebraria a verificacao mesmo com payload legitimo.

    Falha aberta (retorna True) SO quando NENHUM dos dois secrets esta
    configurado - evita derrubar webhook em ambiente local/dev. Em
    producao pelo menos um já está configurado, entao na pratica isso
    fecha o buraco real.
    """
    secrets = [s for s in (os.getenv("META_APP_SECRET"), os.getenv("INSTAGRAM_APP_SECRET")) if s]
    if not secrets:
        print("AVISO: nenhum App Secret configurado (META_APP_SECRET/INSTAGRAM_APP_SECRET) - assinatura do webhook nao verificada.")
        return True

    signature_header = request.headers.get("X-Hub-Signature-256", "")
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header.split("sha256=", 1)[1]
    raw_body = request.get_data()

    for app_secret in secrets:
        computed_signature = hmac.new(
            app_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(expected_signature, computed_signature):
            return True

    return False
