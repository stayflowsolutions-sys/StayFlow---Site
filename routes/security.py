from flask import Blueprint, request, jsonify

from utils.tenant import require_auth, get_current_user_id, get_current_session_id
from routes.auth import hash_password, check_password
from database import (
    get_user_password_hash,
    update_user_password,
    get_user_sessions,
    revoke_session,
    revoke_other_sessions,
    get_login_attempts,
)

security_bp = Blueprint("security", __name__)


@security_bp.route("/security/change-password", methods=["POST"])
@require_auth
def change_password(hostel_id):
    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"success": False, "message": "current_password and new_password are required."}), 400

    if len(new_password) < 8:
        return jsonify({"success": False, "message": "A nova senha precisa ter pelo menos 8 caracteres."}), 400

    user_id = get_current_user_id()
    current_hash = get_user_password_hash(user_id)

    if not current_hash or not check_password(current_password, current_hash):
        return jsonify({"success": False, "message": "Senha atual incorreta."}), 401

    update_user_password(user_id, hash_password(new_password))

    current_session_id = get_current_session_id()
    revoke_other_sessions(user_id, current_session_id)

    return jsonify({
        "success": True,
        "message": "Senha alterada. Outros dispositivos foram desconectados."
    })


@security_bp.route("/security/sessions", methods=["GET"])
@require_auth
def list_sessions(hostel_id):
    user_id = get_current_user_id()
    current_session_id = get_current_session_id()

    sessions = get_user_sessions(user_id)
    for s in sessions:
        s["is_current"] = (s["id"] == current_session_id)

    return jsonify({"success": True, "sessions": sessions})


@security_bp.route("/security/sessions/<session_id>", methods=["DELETE"])
@require_auth
def revoke_session_route(hostel_id, session_id):
    user_id = get_current_user_id()
    revoked = revoke_session(session_id, user_id)

    if not revoked:
        return jsonify({"success": False, "message": "Session not found."}), 404

    return jsonify({"success": True})


@security_bp.route("/security/login-attempts", methods=["GET"])
@require_auth
def list_login_attempts(hostel_id):
    user_id = get_current_user_id()
    attempts = get_login_attempts(user_id)
    return jsonify({"success": True, "attempts": attempts})
