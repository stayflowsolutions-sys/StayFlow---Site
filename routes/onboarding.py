from flask import Blueprint, jsonify, request

from database import mark_onboarding_feature_seen, dismiss_onboarding
from utils.tenant import require_auth, get_current_user_id

onboarding_bp = Blueprint("onboarding", __name__)


@onboarding_bp.route("/onboarding/seen", methods=["POST"])
@require_auth
def mark_seen_route():
    """
    Marca UM item do tour como ja visto (slide inicial do dashboard ou
    dica de um item do menu clicado pela primeira vez) - idempotente,
    marcar de novo o mesmo feature_key nao faz nada (UNIQUE no banco).
    """
    data = request.get_json() or {}
    feature_key = (data.get("feature_key") or "").strip()
    if not feature_key:
        return jsonify({"success": False, "message": "feature_key é obrigatório."}), 400

    mark_onboarding_feature_seen(get_current_user_id(), feature_key)
    return jsonify({"success": True})


@onboarding_bp.route("/onboarding/dismiss", methods=["POST"])
@require_auth
def dismiss_route():
    """
    "Não mostrar novamente" - desliga o tour inteiro (slides + dicas de
    menu) pra essa pessoa, pra sempre, em qualquer dispositivo que ela
    logar depois (é por usuário, não por navegador).
    """
    dismiss_onboarding(get_current_user_id())
    return jsonify({"success": True})
