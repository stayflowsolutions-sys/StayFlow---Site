from flask import Blueprint, jsonify, request

from database import (
    count_push_subscriptions,
    delete_push_subscription,
    has_push_subscription,
    save_push_subscription,
)
from services.push_service import get_vapid_public_key, is_push_configured
from utils.tenant import get_current_user_id, require_auth

push_bp = Blueprint("push", __name__)


@push_bp.route("/push/status", methods=["GET"])
@require_auth
def push_status(hostel_id):
    """
    Estado geral de push pra essa hospedagem - se o servidor tem chaves
    VAPID configuradas (sem isso o recurso fica escondido na UI), a
    chave publica (pra pushManager.subscribe), quantos dispositivos ja
    estao inscritos no total, e se O DISPOSITIVO QUE ESTA PERGUNTANDO
    agora (endpoint passado por query param, se o navegador ja tinha
    uma inscricao salva localmente) esta entre eles.
    """
    endpoint = request.args.get("endpoint") or ""
    user_id = get_current_user_id()

    return jsonify({
        "configured": is_push_configured(),
        "public_key": get_vapid_public_key(),
        "subscription_count": count_push_subscriptions(hostel_id),
        "this_device_subscribed": bool(endpoint) and has_push_subscription(user_id, endpoint),
    })


@push_bp.route("/push/subscribe", methods=["POST"])
@require_auth
def push_subscribe(hostel_id):
    data = request.get_json() or {}
    endpoint = (data.get("endpoint") or "").strip()
    keys = data.get("keys") or {}
    p256dh = (keys.get("p256dh") or "").strip()
    auth = (keys.get("auth") or "").strip()

    if not endpoint or not p256dh or not auth:
        return jsonify({"success": False, "message": "Inscricao push invalida."}), 400

    user_agent = request.headers.get("User-Agent", "")[:255]
    save_push_subscription(hostel_id, get_current_user_id(), endpoint, p256dh, auth, user_agent)

    return jsonify({"success": True})


@push_bp.route("/push/subscribe", methods=["DELETE"])
@require_auth
def push_unsubscribe(hostel_id):
    data = request.get_json() or {}
    endpoint = (data.get("endpoint") or "").strip()

    if not endpoint:
        return jsonify({"success": False, "message": "endpoint e obrigatorio."}), 400

    delete_push_subscription(hostel_id, endpoint)
    return jsonify({"success": True})
