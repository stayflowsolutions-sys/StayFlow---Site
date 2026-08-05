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
    get_user_by_id,
    set_user_totp_secret,
    enable_user_totp,
    disable_user_totp,
    get_user_totp_secret,
    is_user_totp_enabled,
    save_totp_backup_codes,
    count_unused_totp_backup_codes,
)
from services.totp_service import (
    generate_secret,
    get_provisioning_uri,
    generate_qr_code_data_uri,
    verify_totp_code,
    generate_backup_codes,
    normalize_backup_code,
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


@security_bp.route("/security/2fa/status", methods=["GET"])
@require_auth
def totp_status(hostel_id):
    user_id = get_current_user_id()
    return jsonify({
        "success": True,
        "enabled": is_user_totp_enabled(user_id),
        "backup_codes_remaining": count_unused_totp_backup_codes(user_id),
    })


@security_bp.route("/security/2fa/setup", methods=["POST"])
@require_auth
def totp_setup(hostel_id):
    """
    Gera um secret NOVO (sem habilitar ainda) e devolve o QR code +
    a chave manual - a pessoa escaneia/digita no app autenticador e
    confirma com um codigo em /security/2fa/confirm. Chamar de novo
    antes de confirmar simplesmente substitui o secret anterior (nunca
    ficou habilitado, sem risco).
    """
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    if not user or not user.get("email"):
        return jsonify({"success": False, "message": "Não foi possível identificar seu email."}), 400

    secret = generate_secret()
    set_user_totp_secret(user_id, secret)

    uri = get_provisioning_uri(secret, user["email"])
    qr_code = generate_qr_code_data_uri(uri)

    return jsonify({"success": True, "secret": secret, "qr_code": qr_code})


@security_bp.route("/security/2fa/confirm", methods=["POST"])
@require_auth
def totp_confirm(hostel_id):
    data = request.get_json() or {}
    code = data.get("code", "")

    user_id = get_current_user_id()
    secret = get_user_totp_secret(user_id)

    if not secret or not verify_totp_code(secret, code):
        return jsonify({"success": False, "message": "Código inválido."}), 400

    enable_user_totp(user_id)

    backup_codes = generate_backup_codes()
    save_totp_backup_codes(user_id, [hash_password(normalize_backup_code(c)) for c in backup_codes])

    return jsonify({"success": True, "backup_codes": backup_codes})


@security_bp.route("/security/2fa/disable", methods=["POST"])
@require_auth
def totp_disable(hostel_id):
    data = request.get_json() or {}
    password = data.get("password", "")

    user_id = get_current_user_id()
    current_hash = get_user_password_hash(user_id)

    if not current_hash or not check_password(password, current_hash):
        return jsonify({"success": False, "message": "Senha incorreta."}), 401

    disable_user_totp(user_id)

    return jsonify({"success": True})


@security_bp.route("/security/2fa/backup-codes/regenerate", methods=["POST"])
@require_auth
def totp_regenerate_backup_codes(hostel_id):
    """Invalida todos os codigos de backup antigos e gera um lote novo - util se a pessoa acha que perdeu a lista anterior."""
    data = request.get_json() or {}
    password = data.get("password", "")

    user_id = get_current_user_id()

    if not is_user_totp_enabled(user_id):
        return jsonify({"success": False, "message": "2FA não está ativado."}), 400

    current_hash = get_user_password_hash(user_id)
    if not current_hash or not check_password(password, current_hash):
        return jsonify({"success": False, "message": "Senha incorreta."}), 401

    backup_codes = generate_backup_codes()
    save_totp_backup_codes(user_id, [hash_password(normalize_backup_code(c)) for c in backup_codes])

    return jsonify({"success": True, "backup_codes": backup_codes})
