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
    nenhuma - o mesmo App Secret ja usado pro OAuth (META_APP_SECRET)
    e o que a Meta usa pra assinar, nao precisa de segredo novo.

    Usa request.get_data() (bytes brutos, antes de qualquer parse) -
    a assinatura so bate se calculada sobre o corpo exatamente como
    chegou, byte a byte; comparar depois de um json.dumps re-serializado
    quebraria a verificacao mesmo com payload legitimo.

    Falha aberta (retorna True) SO quando META_APP_SECRET nao esta
    configurado - evita derrubar webhook em ambiente local/dev onde
    esse env var normalmente nao existe. Em producao o segredo ja esta
    configurado (mesmo usado pelo OAuth do Facebook/Instagram, que ja
    funciona), entao na pratica isso ja fecha o buraco real.
    """
    app_secret = os.getenv("META_APP_SECRET")
    if not app_secret:
        print("AVISO: META_APP_SECRET nao configurado - assinatura do webhook nao verificada.")
        return True

    signature_header = request.headers.get("X-Hub-Signature-256", "")
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header.split("sha256=", 1)[1]
    computed_signature = hmac.new(
        app_secret.encode("utf-8"),
        request.get_data(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, computed_signature)
