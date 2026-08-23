"""
OAuth e chamadas de API com a Nuvemshop/Tiendanube (mesma empresa,
nome diferente por pais - Tiendanube na Argentina, Nuvemshop no
Brasil). App unico da plataforma (NUVEMSHOP_CLIENT_ID/SECRET), mesmo
principio de META_APP_ID - nao e credencial por hostel.

OAuth 2.0 restrito da Nuvemshop: so grant_type=authorization_code, o
token NAO expira (so invalida se o lojista desinstalar o app ou gerar
outro) - diferente do padrao Meta, aqui nao existe passo de "trocar
por token de longa duracao".

Dominio base da API: api.tiendanube.com e o documentado oficialmente
hoje pros dois paises. Se o primeiro teste com uma loja brasileira
real mostrar que precisa de api.nuvemshop.com.br, isso muda so aqui.
"""

import os
import requests

from database import upsert_portfolio_item_from_external

AUTH_BASE = "https://www.tiendanube.com"
# Versao datada exigida pela API (confirmado na documentacao oficial,
# nao e mais /v1/) - atualizar aqui se a Nuvemshop depreciar essa
# versao no futuro.
API_BASE = "https://api.tiendanube.com/2025-03"
REQUEST_TIMEOUT = 15


def _client_id():
    return os.getenv("NUVEMSHOP_CLIENT_ID")


def _client_secret():
    return os.getenv("NUVEMSHOP_CLIENT_SECRET")


def is_nuvemshop_configured():
    return bool(_client_id() and _client_secret())


def get_authorize_url(state):
    """
    Monta a URL de autorizacao - diferente de Facebook/Instagram, a
    Nuvemshop nao usa redirect_uri na URL de autorizacao (a URL de
    retorno e configurada uma vez no painel de parceiros ao criar o
    app, nao passada por parametro a cada chamada).
    """
    return f"{AUTH_BASE}/apps/{_client_id()}/authorize?state={state}"


def exchange_code_for_store(code):
    """
    Troca o `code` do callback por um token de acesso - a resposta ja
    vem com o `user_id` (ID da loja), sem precisar de uma chamada
    separada tipo /me/accounts (diferente do Facebook).

    Retorna (store_id, access_token, erro) - nunca levanta excecao,
    mesmo principio de services/meta_oauth_service.py.
    """
    try:
        res = requests.post(
            f"{AUTH_BASE}/apps/authorize/token",
            json={
                "client_id": _client_id(),
                "client_secret": _client_secret(),
                "grant_type": "authorization_code",
                "code": code,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code >= 400:
            print("Erro ao trocar code por token (Nuvemshop):", res.status_code, res.text)
            return None, None, "A Nuvemshop recusou o código de autorização."

        data = res.json()
        access_token = data.get("access_token")
        store_id = data.get("user_id")
        if not access_token or not store_id:
            print("Resposta incompleta (Nuvemshop):", res.text)
            return None, None, "Resposta da Nuvemshop não trouxe os dados esperados."

        return str(store_id), access_token, None
    except requests.RequestException as error:
        print("Erro de conexão ao trocar code por loja (Nuvemshop):", error)
        return None, None, "Erro de conexão com a Nuvemshop."


def _headers(access_token):
    # A Nuvemshop exige User-Agent identificando o app em toda chamada
    # (documentado oficialmente) - sem isso a API pode recusar o
    # pedido mesmo com o token certo.
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "StayFlow (stayflowsolutions@gmail.com)",
    }


def list_products(store_id, access_token, page=1, per_page=50):
    """Lista produtos da loja, uma pagina por vez - o caller decide quando parar (lista vazia = acabou)."""
    try:
        res = requests.get(
            f"{API_BASE}/{store_id}/products",
            headers=_headers(access_token),
            params={"page": page, "per_page": per_page},
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code >= 400:
            print("Erro ao listar produtos (Nuvemshop):", res.status_code, res.text)
            return []
        return res.json() or []
    except requests.RequestException as error:
        print("Erro de conexão ao listar produtos (Nuvemshop):", error)
        return []


def get_product(store_id, access_token, product_id):
    try:
        res = requests.get(
            f"{API_BASE}/{store_id}/products/{product_id}",
            headers=_headers(access_token),
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code >= 400:
            print("Erro ao buscar produto (Nuvemshop):", res.status_code, res.text)
            return None
        return res.json()
    except requests.RequestException as error:
        print("Erro de conexão ao buscar produto (Nuvemshop):", error)
        return None


def map_and_upsert_product(hostel_id, product):
    """
    Traduz o formato de produto da API da Nuvemshop pro schema de
    portfolio_items e faz o upsert (ver upsert_portfolio_item_from_external,
    database.py). name/description sao objetos por idioma (ex: {"pt":
    "...", "es": "..."}) - pega o primeiro valor disponivel, sem tentar
    casar com o idioma do hostel (item de catalogo, nao mensagem pro
    hospede). Preco vem na primeira variante (variants[0].price) -
    produto sem variante cadastrada e ignorado (nada pra sincronizar
    ainda).
    """
    name_field = product.get("name") or {}
    name = next(iter(name_field.values()), None) if isinstance(name_field, dict) else name_field
    if not name:
        return

    description_field = product.get("description") or {}
    description = next(iter(description_field.values()), None) if isinstance(description_field, dict) else description_field

    variants = product.get("variants") or []
    price = variants[0].get("price") if variants else None

    images = product.get("images") or []
    photo_url = images[0].get("src") if images else None

    upsert_portfolio_item_from_external(
        hostel_id, "nuvemshop", product.get("id"),
        name=name, description=description, photo_url=photo_url, price=price,
    )


def get_order(store_id, access_token, order_id):
    try:
        res = requests.get(
            f"{API_BASE}/{store_id}/orders/{order_id}",
            headers=_headers(access_token),
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code >= 400:
            print("Erro ao buscar pedido (Nuvemshop):", res.status_code, res.text)
            return None
        return res.json()
    except requests.RequestException as error:
        print("Erro de conexão ao buscar pedido (Nuvemshop):", error)
        return None


_WEBHOOK_EVENTS = ("product/created", "product/updated", "product/deleted", "order/paid")


def register_webhooks(store_id, access_token, callback_url):
    """
    Inscreve o app nos eventos relevantes - chamado uma vez depois do
    OAuth. Nao levanta excecao: se um evento falhar (ex: ja
    inscrito de uma conexao anterior), so avisa e segue pros outros.
    """
    for event in _WEBHOOK_EVENTS:
        try:
            res = requests.post(
                f"{API_BASE}/{store_id}/webhooks",
                headers=_headers(access_token),
                json={"event": event, "url": callback_url},
                timeout=REQUEST_TIMEOUT,
            )
            if res.status_code >= 400:
                print(f"Aviso: falha ao inscrever webhook '{event}' (Nuvemshop):", res.status_code, res.text)
        except requests.RequestException as error:
            print(f"Erro de conexão ao inscrever webhook '{event}' (Nuvemshop):", error)
