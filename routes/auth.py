from flask import Blueprint, request, jsonify, session
import sqlite3
import bcrypt

from database import (
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
)

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


def build_session_payload(user_id, hostel_id):
    """
    Monta a resposta completa de sessao - login com hostel unico,
    select-hostel e /me usam a mesma forma.
    """
    user = get_user_by_id(user_id)
    membership = get_membership(user_id, hostel_id)

    if not user or not membership:
        return None

    hostel = get_hostel(hostel_id)
    permissions = get_effective_permissions(user_id, hostel_id)
    hostels = get_user_hostels(user_id)

    return {
        "success": True,
        "needs_hostel_selection": False,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "must_change_password": bool(user["must_change_password"]),
        },
        "hostel_id": hostel_id,
        "hostel_name": hostel["name"] if hostel else None,
        "role_name": membership["role_name"],
        "permissions": permissions,
        "hostels": hostels,
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    hostel_name = data.get("hostel_name", "").strip()
    admin_name = data.get("admin_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

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

    if get_user_by_email(email):
        return jsonify({"success": False, "message": "This email is already registered."}), 409

    password_hash = hash_password(password)

    try:
        result = create_identity_and_hostel(
            admin_name, email, password_hash, hostel_name, email
        )
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "This email is already registered."}), 409

    start_new_session(result["user_id"], result["hostel_id"])

    return jsonify({"success": True, "message": "Hostel created successfully."})


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

    payload = build_session_payload(session_data["user_id"], session_data["hostel_id"])

    if not payload:
        session.clear()
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    return jsonify(payload)
