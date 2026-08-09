import secrets
from urllib.parse import quote

from flask import Blueprint, redirect, request

import services.mercadopago_service as mercadopago_service
from database import (
    save_hostel_mercadopago_oauth_state,
    consume_hostel_mercadopago_oauth_state,
    save_hostel_mercadopago_config,
)
from utils.tenant import require_permission

mercadopago_oauth_bp = Blueprint("mercadopago_oauth", __name__)


def _redirect_uri():
    return f"{request.url_root.rstrip('/')}/oauth/mercadopago/callback"


def _back_to_settings(success, message=""):
    status = "success" if success else "error"
    url = f"/app?mp_oauth=mercadopago&status={status}"
    if message:
        url += f"&message={quote(message)}"
    return redirect(url)


@mercadopago_oauth_bp.route("/oauth/mercadopago/connect", methods=["GET"])
@require_permission("settings")
def connect_mercadopago(hostel_id):
    if not mercadopago_service.is_configured():
        return _back_to_settings(False, "Integração com Mercado Pago ainda não configurada pelo StayFlow.")

    state = secrets.token_urlsafe(32)
    save_hostel_mercadopago_oauth_state(hostel_id, state)

    url = mercadopago_service.get_authorize_url(_redirect_uri(), state)
    return redirect(url)


@mercadopago_oauth_bp.route("/oauth/mercadopago/callback", methods=["GET"])
@require_permission("settings")
def mercadopago_callback(hostel_id):
    oauth_error = request.args.get("error")
    if oauth_error:
        return _back_to_settings(False, request.args.get("error_description", oauth_error))

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state or not consume_hostel_mercadopago_oauth_state(hostel_id, state):
        return _back_to_settings(False, "Solicitação inválida ou expirada — tente conectar de novo.")

    mp_user_id, access_token, refresh_token, public_key, error = mercadopago_service.exchange_code_for_token(
        code, _redirect_uri()
    )
    if error:
        return _back_to_settings(False, error)

    save_hostel_mercadopago_config(hostel_id, mp_user_id, access_token, refresh_token, public_key)
    return _back_to_settings(True)
