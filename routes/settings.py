from flask import Blueprint, jsonify, request
from database import get_connection, get_hostel_whatsapp_config, save_hostel_whatsapp_config
from utils.tenant import require_auth
import bcrypt


settings_bp = Blueprint("settings", __name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


@settings_bp.route("/settings/whatsapp", methods=["GET"])
@require_auth
def get_whatsapp_settings(hostel_id):
    phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)

    return jsonify({
        "phone_number_id": phone_number_id or "",
        # Nunca devolve o token de verdade pro frontend por segurança —
        # só indica se já existe um configurado.
        "has_access_token": bool(access_token)
    })


@settings_bp.route("/settings/whatsapp", methods=["POST"])
@require_auth
def update_whatsapp_settings(hostel_id):
    data = request.get_json() or {}

    phone_number_id = (data.get("phone_number_id") or "").strip()
    access_token = (data.get("access_token") or "").strip()

    if not phone_number_id:
        return jsonify({"success": False, "message": "phone_number_id is required."}), 400

    # se o campo de token vier vazio, mantém o token já salvo
    # (evita que o admin precise colar o token de novo toda vez
    # que só quiser trocar o phone_number_id).
    if not access_token:
        _, existing_token = get_hostel_whatsapp_config(hostel_id)
        access_token = existing_token

    save_hostel_whatsapp_config(hostel_id, phone_number_id, access_token)

    return jsonify({"success": True})


@settings_bp.route("/settings", methods=["GET"])
@require_auth
def get_settings(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hostel_name, hostel_type, checkin, checkout
        FROM settings
        WHERE hostel_id = ?
    """, (hostel_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "hostel_name": row["hostel_name"],
            "hostel_type": row["hostel_type"],
            "checkin": row["checkin"],
            "checkout": row["checkout"]
        })

    return jsonify({})


@settings_bp.route("/settings", methods=["POST"])
@require_auth
def update_settings(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    data = request.json or {}

    cursor.execute("SELECT id FROM settings WHERE hostel_id = ?", (hostel_id,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("""
            UPDATE settings SET
                hostel_name = ?,
                hostel_type = ?,
                checkin = ?,
                checkout = ?
            WHERE hostel_id = ?
        """, (
            data.get("hostel_name"),
            data.get("hostel_type"),
            data.get("checkin"),
            data.get("checkout"),
            hostel_id
        ))
    else:
        cursor.execute("""
            INSERT INTO settings (hostel_id, hostel_name, hostel_type, checkin, checkout)
            VALUES (?, ?, ?, ?, ?)
        """, (
            hostel_id,
            data.get("hostel_name"),
            data.get("hostel_type"),
            data.get("checkin"),
            data.get("checkout")
        ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


@settings_bp.route("/users", methods=["POST"])
@require_auth
def create_user(hostel_id):
    """
    Cria um novo usuário de equipe para o hostel do usuário logado.
    """
    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "staff").strip().lower()

    if not name:
        return jsonify({"success": False, "message": "Name is required."}), 400
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    if not password:
        return jsonify({"success": False, "message": "Password is required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = ? AND hostel_id = ?",
        (email, hostel_id)
    )
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "This email is already registered for this hostel."}), 409

    password_hash = hash_password(password)

    cursor.execute(
        """
        INSERT INTO users
          (hostel_id, name, email, password, role, must_change_password)
        VALUES (?,?,?,?,?,?)
        """,
        (hostel_id, name, email, password_hash, role, 1)
    )

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "User created successfully.",
        "user": {
            "id": user_id,
            "hostel_id": hostel_id,
            "name": name,
            "email": email,
            "role": role,
            "must_change_password": True
        }
    }), 201


@settings_bp.route("/users", methods=["GET"])
@require_auth
def list_users(hostel_id):
    """
    Lista todos os usuários da equipe do hostel do usuário logado.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, email, role, must_change_password
        FROM users
        WHERE hostel_id = ?
        ORDER BY id ASC
        """,
        (hostel_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    users = [
        {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"],
            "must_change_password": bool(row["must_change_password"]),
        }
        for row in rows
    ]

    return jsonify({"success": True, "users": users})