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
)

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


def start_full_session(user_id, hostel_id):
    """
    Finaliza a sessao de servidor com pessoa + hostel escolhidos.
    A sessao guarda so o minimo (user_id, hostel_id) - nome, role e
    permissoes sao sempre recalculados do banco a cada requisicao,
    nunca ficam desatualizados se o admin mudar algo.
    """
    session.clear()
    session["user_id"] = user_id
    session["hostel_id"] = hostel_id


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

    if get_user_by_email(email):
        return jsonify({"success": False, "message": "This email is already registered."}), 409

    password_hash = hash_password(password)

    try:
        result = create_identity_and_hostel(
            admin_name, email, password_hash, hostel_name, email
        )
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "This email is already registered."}), 409

    start_full_session(result["user_id"], result["hostel_id"])

    return jsonify({"success": True, "message": "Hostel created successfully."})


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = get_user_by_email(email)

    if not user or not user["password"] or not check_password(password, user["password"]):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    hostels = get_user_hostels(user["id"])

    if not hostels:
        return jsonify({
            "success": False,
            "message": "This account has no active hostel access. Contact your administrator."
        }), 403

    if len(hostels) == 1:
        start_full_session(user["id"], hostels[0]["hostel_id"])
        payload = build_session_payload(user["id"], hostels[0]["hostel_id"])
        return jsonify(payload)

    # Mais de um hostel: confirma quem e a pessoa, mas nao finaliza a
    # sessao completa ainda - o frontend precisa perguntar qual hostel
    # usar antes de qualquer rota protegida por hostel_id ficar
    # acessivel.
    session.clear()
    session["pending_user_id"] = user["id"]

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
    multiplos hostels, ou para trocar de hostel estando ja logado
    (equivalente a troca de conta/workspace).
    """
    data = request.get_json() or {}
    hostel_id = data.get("hostel_id")

    if not hostel_id:
        return jsonify({"success": False, "message": "hostel_id is required."}), 400

    user_id = session.get("pending_user_id") or session.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    membership = get_membership(user_id, hostel_id)

    if not membership:
        return jsonify({
            "success": False,
            "message": "You do not have access to this hostel."
        }), 403

    start_full_session(user_id, hostel_id)
    payload = build_session_payload(user_id, hostel_id)

    return jsonify(payload)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    hostel_id = session.get("hostel_id")

    if not user_id or not hostel_id:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    payload = build_session_payload(user_id, hostel_id)

    if not payload:
        session.clear()
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    return jsonify(payload)
