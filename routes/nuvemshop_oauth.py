import secrets
from urllib.parse import quote

from flask import Blueprint, redirect, request

import services.nuvemshop_service as nuvemshop_service
from database import (
    save_hostel_nuvemshop_oauth_state,
    consume_hostel_nuvemshop_oauth_state,
    save_hostel_nuvemshop_config,
)
from utils.tenant import require_permission

nuvemshop_oauth_bp = Blueprint("nuvemshop_oauth", __name__)


def _back_to_settings(success, message=""):
    """Mesmo padrao de redirect de tela cheia de routes/meta_oauth.py - reaproveita o handler generico ja existente no frontend (handleMetaOAuthReturn le qualquer valor de meta_oauth, nao so facebook/instagram)."""
    status = "success" if success else "error"
    url = f"/app?meta_oauth=nuvemshop&status={status}"
    if message:
        url += f"&message={quote(message)}"
    return redirect(url)


def _sync_all_products(hostel_id, store_id, access_token):
    """
    Sincronizacao inicial - roda uma vez, logo apos conectar, sem
    esperar o primeiro webhook. Paginado; para quando uma pagina vem
    vazia. Nunca levanta excecao (mesmo principio dos services de
    integracao) - falha aqui nao deve derrubar o fluxo de conexao, que
    ja terminou com sucesso do ponto de vista do lojista.
    """
    try:
        page = 1
        while True:
            products = nuvemshop_service.list_products(store_id, access_token, page=page)
            if not products:
                break
            for product in products:
                nuvemshop_service.map_and_upsert_product(hostel_id, product)
            page += 1
    except Exception as error:
        print("Erro na sincronização inicial de produtos (Nuvemshop):", error)


@nuvemshop_oauth_bp.route("/oauth/nuvemshop/connect", methods=["GET"])
@require_permission("settings")
def connect_nuvemshop(hostel_id):
    if not nuvemshop_service.is_nuvemshop_configured():
        return _back_to_settings(False, "Integração com Nuvemshop/Tiendanube ainda não configurada pelo StayFlow.")

    state = secrets.token_urlsafe(32)
    save_hostel_nuvemshop_oauth_state(hostel_id, state)

    return redirect(nuvemshop_service.get_authorize_url(state))


@nuvemshop_oauth_bp.route("/oauth/nuvemshop/callback", methods=["GET"])
@require_permission("settings")
def nuvemshop_callback(hostel_id):
    oauth_error = request.args.get("error")
    if oauth_error:
        return _back_to_settings(False, request.args.get("error_description", oauth_error))

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state or not consume_hostel_nuvemshop_oauth_state(hostel_id, state):
        return _back_to_settings(False, "Solicitação inválida ou expirada — tente conectar de novo.")

    store_id, access_token, error = nuvemshop_service.exchange_code_for_store(code)
    if error:
        return _back_to_settings(False, error)

    save_hostel_nuvemshop_config(hostel_id, store_id, access_token)

    callback_url = f"{request.url_root.rstrip('/')}/webhook/nuvemshop"
    nuvemshop_service.register_webhooks(store_id, access_token, callback_url)
    _sync_all_products(hostel_id, store_id, access_token)

    return _back_to_settings(True)
