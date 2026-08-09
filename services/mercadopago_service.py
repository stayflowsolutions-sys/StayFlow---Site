"""
Mercado Pago "Split de Pagos" - cada hostel conecta a propria conta MP
via OAuth (marketplace), e toda cobranca gerada (routes/guest_charges.py)
usa o token DESSE hostel pra criar a preferencia de pagamento - o
dinheiro cai direto na conta do hostel, com a comissao da StayFlow
descontada automaticamente no ato via `marketplace_fee`.

MERCADOPAGO_CLIENT_ID/MERCADOPAGO_CLIENT_SECRET sao segredo unico da
StayFlow (a aplicacao registrada no painel de desenvolvedor do Mercado
Pago), mesmo papel de META_APP_ID/META_APP_SECRET - nao e credencial
por hostel.

Nunca levanta excecao, mesmo principio de services/meta_oauth_service.py:
toda funcao que fala com a API devolve uma tupla terminando em `erro`
(None quando deu certo).
"""

import os
import requests

API_BASE = "https://api.mercadopago.com"
AUTHORIZE_URL = "https://auth.mercadopago.com/authorization"
REQUEST_TIMEOUT = 15


def _client_id():
    return os.getenv("MERCADOPAGO_CLIENT_ID")


def _client_secret():
    return os.getenv("MERCADOPAGO_CLIENT_SECRET")


def is_configured():
    return bool(_client_id() and _client_secret())


def get_authorize_url(redirect_uri, state):
    """
    Monta a URL de autorizacao do Mercado Pago (fluxo OAuth de
    marketplace) - o hostel clica um botao no StayFlow, autoriza na
    tela de consentimento do proprio Mercado Pago, e volta pro
    redirect_uri com um `code`.
    """
    return (
        f"{AUTHORIZE_URL}"
        f"?client_id={_client_id()}&response_type=code&platform_id=mp"
        f"&redirect_uri={redirect_uri}&state={state}"
    )


def exchange_code_for_token(code, redirect_uri):
    """
    Troca o `code` do callback pelos tokens da conta MP do hostel.
    Retorna (mp_user_id, access_token, refresh_token, public_key, erro).
    """
    try:
        res = requests.post(
            f"{API_BASE}/oauth/token",
            data={
                "client_id": _client_id(),
                "client_secret": _client_secret(),
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code >= 400:
            print("Erro ao trocar code por token (Mercado Pago):", res.status_code, res.text)
            return None, None, None, None, "O Mercado Pago recusou o código de autorização."

        data = res.json()
        access_token = data.get("access_token")
        if not access_token:
            print("Resposta sem access_token (Mercado Pago):", res.text)
            return None, None, None, None, "Resposta do Mercado Pago não trouxe um token de acesso."

        return (
            str(data.get("user_id")) if data.get("user_id") is not None else None,
            access_token,
            data.get("refresh_token"),
            data.get("public_key"),
            None,
        )
    except requests.RequestException as error:
        print("Erro de conexão ao trocar code por token (Mercado Pago):", error)
        return None, None, None, None, "Erro de conexão com o Mercado Pago."


def refresh_access_token(refresh_token):
    """
    Renova o access_token de um hostel usando o refresh_token salvo.
    Retorna (access_token, refresh_token, erro) - o Mercado Pago manda
    um refresh_token NOVO a cada renovação, o antigo para de funcionar
    (por isso a rota chamadora precisa persistir os dois de novo).
    """
    try:
        res = requests.post(
            f"{API_BASE}/oauth/token",
            data={
                "client_id": _client_id(),
                "client_secret": _client_secret(),
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code >= 400:
            print("Erro ao renovar token (Mercado Pago):", res.status_code, res.text)
            return None, None, "Não foi possível renovar a conexão com o Mercado Pago."

        data = res.json()
        access_token = data.get("access_token")
        new_refresh_token = data.get("refresh_token")
        if not access_token:
            print("Resposta sem access_token ao renovar (Mercado Pago):", res.text)
            return None, None, "Resposta do Mercado Pago não trouxe um token de acesso."

        return access_token, new_refresh_token, None
    except requests.RequestException as error:
        print("Erro de conexão ao renovar token (Mercado Pago):", error)
        return None, None, "Erro de conexão com o Mercado Pago."


def create_checkout_preference(seller_access_token, title, amount, currency,
                                marketplace_fee, external_reference, notification_url,
                                back_url):
    """
    Cria uma preferencia de Checkout Pro autenticada com o token do
    HOSTEL (nao da StayFlow) - e isso que faz o dinheiro cair na conta
    dele, com marketplace_fee (valor absoluto, na mesma moeda) sendo a
    fatia que o Mercado Pago desconta automaticamente pra StayFlow no
    ato do pagamento.

    Retorna (preference_id, init_point, erro). init_point e o link
    hospedado pronto pra mandar ao hospede (por WhatsApp, por exemplo).
    """
    try:
        res = requests.post(
            f"{API_BASE}/checkout/preferences",
            headers={"Authorization": f"Bearer {seller_access_token}"},
            json={
                "items": [{
                    "title": title,
                    "quantity": 1,
                    "unit_price": float(amount),
                    "currency_id": currency,
                }],
                "marketplace_fee": float(marketplace_fee),
                "external_reference": str(external_reference),
                "notification_url": notification_url,
                "back_urls": {
                    "success": back_url,
                    "pending": back_url,
                    "failure": back_url,
                },
                "auto_return": "approved",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code >= 400:
            print("Erro ao criar preferência de checkout (Mercado Pago):", res.status_code, res.text)
            return None, None, "Não foi possível gerar o link de pagamento no Mercado Pago."

        data = res.json()
        preference_id = data.get("id")
        init_point = data.get("init_point")
        if not preference_id or not init_point:
            print("Resposta sem id/init_point (Mercado Pago):", res.text)
            return None, None, "Resposta do Mercado Pago não trouxe um link de pagamento válido."

        return preference_id, init_point, None
    except requests.RequestException as error:
        print("Erro de conexão ao criar preferência de checkout (Mercado Pago):", error)
        return None, None, "Erro de conexão com o Mercado Pago."


def get_payment(access_token, payment_id):
    """
    Busca um pagamento pelo id, autenticado com o token do HOSTEL dono
    da preferencia que originou esse pagamento (payment ids sao
    escopados a conta que recebeu, nao dá pra consultar com um token
    de outro hostel). Retorna (status, transaction_amount,
    external_reference, erro).
    """
    try:
        res = requests.get(
            f"{API_BASE}/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code == 401:
            return None, None, None, "unauthorized"
        if res.status_code >= 400:
            print("Erro ao buscar pagamento (Mercado Pago):", res.status_code, res.text)
            return None, None, None, "Não foi possível consultar o pagamento no Mercado Pago."

        data = res.json()
        return data.get("status"), data.get("transaction_amount"), data.get("external_reference"), None
    except requests.RequestException as error:
        print("Erro de conexão ao buscar pagamento (Mercado Pago):", error)
        return None, None, None, "Erro de conexão com o Mercado Pago."
