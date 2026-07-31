import secrets
from urllib.parse import quote

from flask import Blueprint, redirect, request

import services.meta_oauth_service as meta_oauth_service
from database import (
    save_hostel_facebook_oauth_state,
    consume_hostel_facebook_oauth_state,
    save_hostel_facebook_config,
)
from utils.tenant import require_permission

meta_oauth_bp = Blueprint("meta_oauth", __name__)


def _facebook_redirect_uri():
    return f"{request.url_root.rstrip('/')}/oauth/facebook/callback"


def _back_to_settings(channel, success, message=""):
    """
    Fim do fluxo OAuth (redirect de tela cheia, nao popup - diferente
    do WhatsApp Embedded Signup, que vira JS/popup numa rodada
    seguinte): volta pro dashboard com o resultado na query string, pra
    o card de Configuracoes mostrar a mensagem certa e recarregar o
    status da conexao.
    """
    status = "success" if success else "error"
    url = f"/app?meta_oauth={channel}&status={status}"
    if message:
        url += f"&message={quote(message)}"
    return redirect(url)


@meta_oauth_bp.route("/oauth/facebook/connect", methods=["GET"])
@require_permission("settings")
def connect_facebook(hostel_id):
    if not meta_oauth_service.is_facebook_login_configured():
        return _back_to_settings("facebook", False, "Integração com Facebook ainda não configurada pelo StayFlow.")

    state = secrets.token_urlsafe(32)
    save_hostel_facebook_oauth_state(hostel_id, state)

    url = meta_oauth_service.get_facebook_authorize_url(_facebook_redirect_uri(), state)
    return redirect(url)


@meta_oauth_bp.route("/oauth/facebook/callback", methods=["GET"])
@require_permission("settings")
def facebook_callback(hostel_id):
    oauth_error = request.args.get("error")
    if oauth_error:
        return _back_to_settings("facebook", False, request.args.get("error_description", oauth_error))

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state or not consume_hostel_facebook_oauth_state(hostel_id, state):
        return _back_to_settings("facebook", False, "Solicitação inválida ou expirada — tente conectar de novo.")

    page_id, page_access_token, page_name, error = meta_oauth_service.exchange_code_for_page(
        code, _facebook_redirect_uri()
    )
    if error:
        return _back_to_settings("facebook", False, error)

    save_hostel_facebook_config(hostel_id, page_id, page_access_token)
    return _back_to_settings("facebook", True, page_name or "")
