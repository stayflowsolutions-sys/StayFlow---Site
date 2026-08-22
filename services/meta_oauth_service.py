"""
OAuth com o App Meta do StayFlow - Facebook Login for Business (pro
Messenger), Instagram API with Instagram Login (pro Instagram Direct)
e WhatsApp Embedded Signup (pro WhatsApp Business).

App ID/Secret vem de variavel de ambiente - e um segredo do StayFlow
inteiro (um App so, nao um por hostel), mesmo padrao ja usado pro
WHATSAPP_VERIFY_TOKEN.

Confirmado testando ao vivo (ponto que o plano original deixou em
aberto): esse App usa "Facebook Login for Business" no modo com
Configuration - as permissoes (pages_show_list/pages_messaging/
pages_manage_metadata) ficam empacotadas numa "Configuracion" criada
no painel da Meta (nao mandadas soltas via `scope` na URL, como no
Facebook Login classico). A URL de autorizacao usa `config_id` em vez
de `scope`. FACEBOOK_CONFIG_ID e mais uma variavel de ambiente, mesmo
motivo de nao ser segredo por hostel.

O Instagram usa um produto DIFERENTE do App Meta ("API setup with
Instagram login"), com App ID/Secret PROPRIOS (INSTAGRAM_APP_ID/
INSTAGRAM_APP_SECRET - nao reaproveita META_APP_ID/META_APP_SECRET) e
uma stack de hosts inteiramente separada do Facebook Login for
Business: autorizacao em www.instagram.com (com `scope`, sem
`config_id` - a granularidade de permissao aqui e via escopo direto na
URL, nao via Configuration), troca de code por token em
api.instagram.com (POST, nao GET), e token de longa duracao +
descoberta da conta em graph.instagram.com. Vantagem real do metodo:
nao exige Pagina do Facebook vinculada.
"""

import os
import secrets
import requests

API_BASE = "https://graph.facebook.com/v20.0"
# Versao mais atual que a do Facebook/Messenger acima de proposito -
# investigacao de 02/08/2026 achou que a documentacao oficial da
# "Conversations API" do Instagram (graph.instagram.com) so usa
# exemplos em v25.0+; v20.0 (lancada em 05/2024) ainda responde sem
# erro de versao expirada, mas pode ter comportamento defasado em
# endpoints mais novos como o de conteudo de mensagem - suspeita
# levantada como possivel causa do "message_edit" com corpo vazio ao
# buscar por mid. Nao mexe na versao do Facebook (linha acima) de
# proposito - Messenger/WhatsApp ja funcionam, sem motivo pra arriscar.
INSTAGRAM_API_VERSION = "v25.0"
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


def _whatsapp_config_id():
    return os.getenv("WHATSAPP_CONFIG_ID")


def is_whatsapp_embedded_signup_configured():
    """
    Diferente de FACEBOOK_CONFIG_ID (so usado server-side, dentro da
    URL de autorizacao), WHATSAPP_CONFIG_ID precisa ser exposto pro
    FRONTEND tambem - o FB.login() do navegador chama a Meta
    diretamente, sem passar pelo backend. Nao e segredo (e um
    identificador publico de configuracao, comparavel a um client_id),
    so nao faz sentido mostrar se nao estiver configurado.
    """
    return bool(is_app_configured() and _whatsapp_config_id())


def _instagram_app_id():
    return os.getenv("INSTAGRAM_APP_ID")


def _instagram_app_secret():
    return os.getenv("INSTAGRAM_APP_SECRET")


def is_instagram_login_configured():
    return bool(_instagram_app_id() and _instagram_app_secret())


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


def _exchange_code_for_long_lived_token(code, redirect_uri=None):
    """
    Passo comum aos fluxos de Facebook e WhatsApp Embedded Signup (o
    Instagram usa hosts/verbos diferentes, ver exchange_code_for_instagram_account):
    troca `code` por token curto, depois troca esse token curto por um
    de longa duracao. `redirect_uri` e omitido no fluxo do WhatsApp
    Embedded Signup (JS SDK, sem redirect de pagina inteira - a Meta
    nao exige esse parametro nesse caso).

    Retorna (long_token, erro) - nunca levanta excecao.
    """
    try:
        token_params = {
            "client_id": _app_id(),
            "client_secret": _app_secret(),
            "code": code,
        }
        if redirect_uri:
            token_params["redirect_uri"] = redirect_uri

        token_res = requests.get(f"{API_BASE}/oauth/access_token", params=token_params, timeout=REQUEST_TIMEOUT)
        if token_res.status_code >= 400:
            print("Erro ao trocar code por token (Meta):", token_res.status_code, token_res.text)
            return None, "A Meta recusou o código de autorização."

        short_token = token_res.json().get("access_token")
        if not short_token:
            print("Resposta sem access_token (Meta):", token_res.text)
            return None, "Resposta da Meta não trouxe um token de acesso."

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
            print("Erro ao trocar por token de longa duração (Meta):", long_res.status_code, long_res.text)
            return None, "Não foi possível obter um token de longa duração."

        return long_res.json().get("access_token", short_token), None
    except requests.RequestException as error:
        print("Erro de conexão ao trocar code por token (Meta):", error)
        return None, "Erro de conexão com a Meta."


def exchange_code_for_page(code, redirect_uri):
    """
    Troca o `code` do callback por uma Pagina do Facebook conectada,
    pronta pra mandar/receber mensagem no Messenger.

    Retorna (page_id, page_access_token, page_name, erro) - erro vem
    preenchido (e os tres primeiros None) se qualquer etapa falhar.
    Nunca levanta excecao, mesmo principio de services/beds24_service.py.
    """
    try:
        long_token, error = _exchange_code_for_long_lived_token(code, redirect_uri)
        if error:
            return None, None, None, error

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


def get_whatsapp_embedded_signup_config():
    """App ID + config_id pro frontend montar a chamada FB.login() diretamente - nenhum dos dois e segredo."""
    return {"app_id": _app_id(), "config_id": _whatsapp_config_id()}


def exchange_whatsapp_embedded_signup(code, phone_number_id, waba_id):
    """
    Fecha o WhatsApp Embedded Signup: troca o `code` (recebido no
    callback JS do FB.login()) por um token de longa duracao, registra
    o numero pra Cloud API (exige um PIN de 6 digitos - gerado aqui,
    nunca visto/reutilizado pelo usuario, e so exigencia tecnica da
    API) e inscreve o App da StayFlow nos webhooks dessa WABA (pra
    mensagem cair no /webhook/whatsapp que ja existe).

    Retorna (access_token, erro) - nunca levanta excecao, mesmo
    principio dos outros dois fluxos. `redirect_uri` nao e passado na
    troca de token porque esse fluxo roda via SDK JS embutido, nao
    redirect de pagina inteira.
    """
    long_token, error = _exchange_code_for_long_lived_token(code)
    if error:
        return None, error

    try:
        register_res = requests.post(
            f"{API_BASE}/{phone_number_id}/register",
            params={"access_token": long_token},
            json={"messaging_product": "whatsapp", "pin": f"{secrets.randbelow(1_000_000):06d}"},
            timeout=REQUEST_TIMEOUT,
        )
        if register_res.status_code >= 400:
            print("Erro ao registrar número (WhatsApp Embedded Signup):", register_res.status_code, register_res.text)
            return None, "Não foi possível registrar o número na Cloud API."

        subscribe_res = requests.post(
            f"{API_BASE}/{waba_id}/subscribed_apps",
            params={"access_token": long_token},
            timeout=REQUEST_TIMEOUT,
        )
        if subscribe_res.status_code >= 400:
            print("Erro ao inscrever app na WABA (WhatsApp Embedded Signup):", subscribe_res.status_code, subscribe_res.text)
            return None, "Número registrado, mas não foi possível ativar o recebimento de mensagens."

        return long_token, None
    except requests.RequestException as error:
        print("Erro de conexão no WhatsApp Embedded Signup:", error)
        return None, "Erro de conexão com a Meta."


def get_instagram_authorize_url(redirect_uri, state):
    """
    Monta a URL de autorizacao do Instagram Login - diferente do
    Facebook Login for Business, aqui as permissoes vao soltas via
    `scope` (sem config_id), e os nomes de escopo tem o prefixo
    `instagram_` (a Meta descontinuou os nomes antigos sem prefixo em
    27/01/2025 - usar os nomes errados aqui derruba a autorizacao
    silenciosamente ou com erro da propria Meta).
    """
    scope = "instagram_business_basic,instagram_business_manage_messages"
    return (
        "https://www.instagram.com/oauth/authorize"
        f"?client_id={_instagram_app_id()}&redirect_uri={redirect_uri}"
        f"&scope={scope}&response_type=code&state={state}"
    )


def exchange_code_for_instagram_account(code, redirect_uri):
    """
    Troca o `code` do callback por uma conta Instagram Business/Creator
    conectada, pronta pra mandar/receber Direct.

    Retorna (instagram_business_id, access_token, username, erro) - erro
    vem preenchido (e os tres primeiros None) se qualquer etapa
    obrigatoria falhar. O username e best-effort: se a busca de perfil
    falhar, a conexao segue em frente so com o ID (username fica None),
    ja que o envio/recebimento de mensagem nao depende dele. Nunca
    levanta excecao, mesmo principio de exchange_code_for_page.
    """
    try:
        token_res = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": _instagram_app_id(),
                "client_secret": _instagram_app_secret(),
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if token_res.status_code >= 400:
            print("Erro ao trocar code por token (Instagram):", token_res.status_code, token_res.text)
            return None, None, None, "A Meta recusou o código de autorização do Instagram."

        token_data = token_res.json()
        short_token = token_data.get("access_token")
        if not short_token:
            print("Resposta sem access_token (Instagram):", token_res.text)
            return None, None, None, "Resposta do Instagram não trouxe um token de acesso válido."

        long_res = requests.get(
            "https://graph.instagram.com/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": _instagram_app_secret(),
                "access_token": short_token,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if long_res.status_code >= 400:
            print("Erro ao trocar por token de longa duração (Instagram):", long_res.status_code, long_res.text)
            return None, None, None, "Não foi possível obter um token de longa duração do Instagram."

        long_token = long_res.json().get("access_token", short_token)

        # O `user_id` devolvido na troca de code->token acima e um "ID
        # com escopo de app" (ex: 280...) - NAO e o mesmo ID que chega
        # de verdade no campo entry.id do payload de webhook nem o que
        # a Send API espera na URL (/{IG_ID}/messages). O ID certo pra
        # essas duas coisas e o "user_id" CLASSICO (ex: 1784...),
        # devolvido por /me?fields=user_id - confirmado testando ao vivo
        # (webhook chegou com o ID classico, nao com o de escopo de
        # app) e documentado em developers.facebook.com/docs/instagram-
        # platform/instagram-api-with-instagram-login/get-started
        # ("This ID is [the] value of the `id` field received in
        # webhook notifications for this account").
        profile_res = requests.get(
            f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/me",
            params={"fields": "user_id,username", "access_token": long_token},
            timeout=REQUEST_TIMEOUT,
        )
        if profile_res.status_code >= 400:
            print("Erro ao buscar user_id classico (Instagram):", profile_res.status_code, profile_res.text)
            return None, None, None, "Não foi possível confirmar a conta Instagram conectada."

        profile_data = profile_res.json()
        instagram_business_id = profile_data.get("user_id")
        username = profile_data.get("username")
        if not instagram_business_id:
            print("Resposta de /me sem user_id (Instagram):", profile_res.text)
            return None, None, None, "Não foi possível confirmar a conta Instagram conectada."

        return str(instagram_business_id), long_token, username, None
    except requests.RequestException as error:
        print("Erro de conexão ao trocar code por conta Instagram:", error)
        return None, None, None, "Erro de conexão com a Meta."
