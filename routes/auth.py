from flask import Blueprint, request, jsonify, session
import sqlite3
import bcrypt

from database import (
    AGENCY_CATEGORIES,
    get_hostel,
    get_user_by_email,
    get_user_by_id,
    get_user_hostels,
    get_membership,
    get_effective_permissions,
    create_identity_and_hostel,
    create_session,
    get_valid_session,
    update_session_hostel,
    revoke_session_by_id,
    log_login_attempt,
    count_recent_failed_logins,
    is_user_totp_enabled,
    get_user_totp_secret,
    create_totp_challenge,
    get_totp_challenge,
    increment_totp_challenge_attempts,
    delete_totp_challenge,
    get_unused_totp_backup_codes,
    mark_totp_backup_code_used,
)
from services.totp_service import verify_totp_code, normalize_backup_code
from utils.permissions import ALL_PERMISSIONS
from utils.tenant import is_stayflow_admin_email

# Protecao basica contra forca bruta: 5 tentativas erradas pro MESMO
# email trava por 15 minutos. Bloqueia por email (nao por IP) porque
# login_attempts ja grava o email tentado mesmo pra conta inexistente -
# cobre o cenario mais realista (alguem com o email certo tentando
# adivinhar a senha), sem precisar de infraestrutura nova.
LOGIN_MAX_FAILED_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

auth_bp = Blueprint("auth", __name__)


def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def check_password(password, password_hash):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def start_new_session(user_id, hostel_id):
    """
    Cria uma sessao nova no servidor (linha em sessions) e guarda so o
    token opaco no cookie assinado do Flask - nunca user_id/hostel_id
    direto. hostel_id pode ser None (estado "pending", login
    multi-hostel antes da escolha).
    """
    session.clear()
    user_agent = request.headers.get("User-Agent", "")
    session_id = create_session(user_id, hostel_id, user_agent)
    session["session_id"] = session_id
    return session_id


def build_session_payload(user_id, hostel_id, impersonating_from_hostel_id=None):
    """
    Monta a resposta completa de sessao - login com hostel unico,
    select-hostel e /me usam a mesma forma.

    impersonating_from_hostel_id != None significa que essa sessao esta
    "em visita" (admin StayFlow dentro do dashboard de outra conta, ver
    routes/stayflow_admin.py /impersonate) - nesse caso nao existe uma
    hostel_memberships real pra (user_id, hostel_id), entao pula essa
    exigencia e libera permissao completa, igual utils/tenant.py faz
    pro resto das rotas via is_impersonating().
    """
    user = get_user_by_id(user_id)
    if not user:
        return None

    hostel = get_hostel(hostel_id)

    if impersonating_from_hostel_id:
        role_name = "Visitante StayFlow"
        permissions = ALL_PERMISSIONS
    else:
        membership = get_membership(user_id, hostel_id)
        if not membership:
            return None
        role_name = membership["role_name"]
        permissions = get_effective_permissions(user_id, hostel_id)

    hostels = get_user_hostels(user_id)
    origin_hostel = get_hostel(impersonating_from_hostel_id) if impersonating_from_hostel_id else None

    return {
        "success": True,
        "needs_hostel_selection": False,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "must_change_password": bool(user["must_change_password"]),
        },
        "is_stayflow_admin": is_stayflow_admin_email(user["email"]),
        "hostel_id": hostel_id,
        "hostel_name": hostel["name"] if hostel else None,
        "account_kind": hostel["account_kind"] if hostel else "lodging",
        "role_name": role_name,
        "permissions": permissions,
        "hostels": hostels,
        "impersonating": bool(impersonating_from_hostel_id),
        "impersonating_from_hostel_name": origin_hostel["name"] if origin_hostel else None,
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    hostel_name = data.get("hostel_name", "").strip()
    admin_name = data.get("admin_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    account_kind = data.get("account_kind", "lodging").strip() or "lodging"
    agency_category = (data.get("agency_category") or "").strip() or None

    if not hostel_name:
        return jsonify({"success": False, "message": "Hostel name is required."}), 400
    if not admin_name:
        return jsonify({"success": False, "message": "Administrator name is required."}), 400
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    if not password:
        return jsonify({"success": False, "message": "Password is required."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters."}), 400
    if account_kind not in ("lodging", "agency"):
        return jsonify({"success": False, "message": "Tipo de estabelecimento inválido."}), 400
    if account_kind == "agency" and agency_category not in AGENCY_CATEGORIES:
        return jsonify({"success": False, "message": "Categoria de agência inválida."}), 400
    if account_kind == "lodging":
        agency_category = None

    if get_user_by_email(email):
        return jsonify({"success": False, "message": "This email is already registered."}), 409

    password_hash = hash_password(password)

    try:
        result = create_identity_and_hostel(
            admin_name, email, password_hash, hostel_name, email,
            account_kind=account_kind, agency_category=agency_category
        )
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "This email is already registered."}), 409

    start_new_session(result["user_id"], result["hostel_id"])

    return jsonify({"success": True, "message": "Hostel created successfully."})


def _complete_login(user, email):
    """
    Ultima etapa do login (sessao de verdade) - usada tanto por /login
    direto (sem 2FA) quanto por /login/2fa (depois do codigo confirmado).
    Isolada em funcao propria pra nao duplicar a logica de escolha de
    hostel/log de tentativa nos dois caminhos.
    """
    hostels = get_user_hostels(user["id"])

    if not hostels:
        log_login_attempt(user["id"], None, email, False)
        return jsonify({
            "success": False,
            "message": "This account has no active hostel access. Contact your administrator."
        }), 403

    if len(hostels) == 1:
        start_new_session(user["id"], hostels[0]["hostel_id"])
        log_login_attempt(user["id"], hostels[0]["hostel_id"], email, True)
        payload = build_session_payload(user["id"], hostels[0]["hostel_id"])
        return jsonify(payload)

    # Mais de um hostel: cria uma sessao real (pending, hostel_id None)
    # - e uma sessao de verdade na tabela, so ainda sem hostel escolhido.
    # Nenhuma rota protegida por @require_auth/@require_permission
    # libera acesso nesse estado (hostel_id None = bloqueado).
    start_new_session(user["id"], None)
    log_login_attempt(user["id"], None, email, True)

    return jsonify({
        "success": True,
        "needs_hostel_selection": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        },
        "hostels": hostels,
    })


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if email and count_recent_failed_logins(email, LOGIN_LOCKOUT_MINUTES) >= LOGIN_MAX_FAILED_ATTEMPTS:
        return jsonify({
            "success": False,
            "message": f"Too many failed login attempts. Try again in {LOGIN_LOCKOUT_MINUTES} minutes."
        }), 429

    user = get_user_by_email(email)

    if not user or not user["password"] or not check_password(password, user["password"]):
        log_login_attempt(user["id"] if user else None, None, email, False)
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    # Senha certa, mas essa conta tem 2FA ativado - a sessao de verdade
    # so nasce depois do codigo confirmado em /login/2fa. Nao loga
    # login_attempt aqui ainda (login nao terminou de verdade) - quem
    # loga sucesso/falha e o proprio /login/2fa.
    if is_user_totp_enabled(user["id"]):
        challenge_token = create_totp_challenge(user["id"])
        return jsonify({"success": True, "needs_2fa": True, "challenge_token": challenge_token})

    return _complete_login(user, email)


@auth_bp.route("/login/2fa", methods=["POST"])
def login_2fa():
    data = request.get_json() or {}
    challenge_token = data.get("challenge_token", "")
    code = (data.get("code", "") or "").strip()

    challenge = get_totp_challenge(challenge_token)
    if not challenge:
        return jsonify({
            "success": False,
            "message": "Sessão de verificação expirada. Faça login novamente."
        }), 401

    user_id = challenge["user_id"]
    user = get_user_by_id(user_id)
    if not user:
        delete_totp_challenge(challenge_token)
        return jsonify({
            "success": False,
            "message": "Sessão de verificação expirada. Faça login novamente."
        }), 401

    secret = get_user_totp_secret(user_id)
    valid = verify_totp_code(secret, code)

    # Codigo TOTP nao bateu - tenta como codigo de backup de uso unico
    # antes de considerar invalido de verdade.
    if not valid:
        normalized = normalize_backup_code(code)
        for backup_code in get_unused_totp_backup_codes(user_id):
            if check_password(normalized, backup_code["code_hash"]):
                mark_totp_backup_code_used(backup_code["id"])
                valid = True
                break

    if not valid:
        increment_totp_challenge_attempts(challenge_token)
        return jsonify({"success": False, "message": "Código inválido."}), 401

    delete_totp_challenge(challenge_token)
    return _complete_login(user, user["email"])


@auth_bp.route("/select-hostel", methods=["POST"])
def select_hostel():
    """
    Finaliza a escolha de hostel - usado logo apos um login com
    multiplos hostels (saindo do estado pending), ou para trocar de
    hostel estando ja logado (equivalente a troca de conta/workspace).
    Sempre ATUALIZA o hostel_id da sessao existente (mesma linha,
    mesmo dispositivo) - nunca cria uma sessao nova.
    """
    data = request.get_json() or {}
    hostel_id = data.get("hostel_id")

    if not hostel_id:
        return jsonify({"success": False, "message": "hostel_id is required."}), 400

    session_id = session.get("session_id")
    session_data = get_valid_session(session_id) if session_id else None

    if not session_data:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    user_id = session_data["user_id"]
    membership = get_membership(user_id, hostel_id)

    if not membership:
        return jsonify({
            "success": False,
            "message": "You do not have access to this hostel."
        }), 403

    update_session_hostel(session_id, hostel_id)
    payload = build_session_payload(user_id, hostel_id)

    return jsonify(payload)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session_id = session.get("session_id")
    if session_id:
        revoke_session_by_id(session_id)
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    session_id = session.get("session_id")
    session_data = get_valid_session(session_id) if session_id else None

    # hostel_id None cobre tanto "sem sessao" quanto "sessao pending"
    # (login multi-hostel sem escolha ainda) - em ambos os casos, /me
    # nao tem um payload completo pra devolver.
    if not session_data or not session_data["hostel_id"]:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    payload = build_session_payload(
        session_data["user_id"], session_data["hostel_id"],
        impersonating_from_hostel_id=session_data.get("impersonating_from_hostel_id"),
    )

    if not payload:
        session.clear()
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    return jsonify(payload)
