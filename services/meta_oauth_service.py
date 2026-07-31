"""
OAuth com o App Meta do StayFlow (Facebook Login for Business, pro
Messenger) - troca o `code` do callback por um token de usuario, troca
esse token por um de longa duracao, e descobre a Pagina do Facebook
conectada (junto com o token proprio dela, que a API ja devolve em
/me/accounts). Instagram Login e WhatsApp Embedded Signup entram em
rodadas seguintes.

App ID/Secret vem de variavel de ambiente (META_APP_ID/META_APP_SECRET)
- e um segredo do StayFlow inteiro (um App so, nao um por hostel), nao
tem por que guardar em banco, mesmo padrao ja usado pro
WHATSAPP_VERIFY_TOKEN.

Confirmado testando ao vivo (ponto que o plano original deixou em
aberto): esse App usa "Facebook Login for Business" no modo com
Configuration - as permissoes (pages_show_list/pages_messaging/
pages_manage_metadata) ficam empacotadas numa "Configuracion" criada
no painel da Meta (nao mandadas soltas via `scope` na URL, como no
Facebook Login classico). A URL de autorizacao usa `config_id` em vez
de `scope`. FACEBOOK_CONFIG_ID e mais uma variavel de ambiente, mesmo
motivo de nao ser segredo por hostel.
"""

import os
import requests

API_BASE = "https://graph.facebook.com/v20.0"
REQUEST_TIMEOUT = 15


def _app_id():
    return os.getenv("META_APP_ID")


def _app_secret():
    return os.getenv("META_APP_SECRET")


def _facebook_config_id():
    return os.getenv("FACEBOOK_CONFIG_ID")


def is_app_configured():
    return bool(_app_id() and _app_secret())


def is_facebook_login_configured():
    return bool(is_app_configured() and _facebook_config_id())


def get_facebook_authorize_url(redirect_uri, state):
    """
    Monta a URL de autorizacao do Facebook Login for Business - o
    hostel clica um botao no StayFlow, vai pra essa URL, autoriza na
    tela de consentimento da propria Meta (usando a Configuracion
    identificada por FACEBOOK_CONFIG_ID, que ja traz as permissoes
    certas empacotadas), e a Meta redireciona de volta pro redirect_uri
    com um `code`.
    """
    return (
        "https://www.facebook.com/v20.0/dialog/oauth"
        f"?client_id={_app_id()}&redirect_uri={redirect_uri}"
        f"&state={state}&config_id={_facebook_config_id()}"
        "&response_type=code&override_default_response_type=true"
    )


def exchange_code_for_page(code, redirect_uri):
    """
    Troca o `code` do callback por uma Pagina do Facebook conectada,
    pronta pra mandar/receber mensagem no Messenger.

    Retorna (page_id, page_access_token, page_name, erro) - erro vem
    preenchido (e os tres primeiros None) se qualquer etapa falhar.
    Nunca levanta excecao, mesmo principio de services/beds24_service.py.
    """
    try:
        token_res = requests.get(
            f"{API_BASE}/oauth/access_token",
            params={
                "client_id": _app_id(),
                "client_secret": _app_secret(),
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if token_res.status_code >= 400:
            print("Erro ao trocar code por token (Facebook):", token_res.status_code, token_res.text)
            return None, None, None, "A Meta recusou o código de autorização."

        short_token = token_res.json().get("access_token")
        if not short_token:
            print("Resposta sem access_token (Facebook):", token_res.text)
            return None, None, None, "Resposta da Meta não trouxe um token de acesso."

        long_res = requests.get(
            f"{API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": _app_id(),
                "client_secret": _app_secret(),
                "fb_exchange_token": short_token,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if long_res.status_code >= 400:
            print("Erro ao trocar por token de longa duração (Facebook):", long_res.status_code, long_res.text)
            return None, None, None, "Não foi possível obter um token de longa duração."

        long_token = long_res.json().get("access_token", short_token)

        pages_res = requests.get(
            f"{API_BASE}/me/accounts",
            params={"access_token": long_token},
            timeout=REQUEST_TIMEOUT,
        )
        if pages_res.status_code >= 400:
            print("Erro ao buscar Páginas (Facebook):", pages_res.status_code, pages_res.text)
            return None, None, None, "Não foi possível listar as Páginas dessa conta."

        pages = pages_res.json().get("data", [])
        if not pages:
            return None, None, None, "Nenhuma Página do Facebook encontrada nessa conta — crie uma Página antes de conectar."

        # Pega a primeira Pagina que o usuario administra. A maioria dos
        # hostels tem uma so; se um dia precisar escolher entre varias,
        # isso vira um passo extra na UI (nao implementado agora).
        page = pages[0]
        return page.get("id"), page.get("access_token"), page.get("name"), None
    except requests.RequestException as error:
        print("Erro de conexão ao trocar code por Página (Facebook):", error)
        return None, None, None, "Erro de conexão com a Meta."
