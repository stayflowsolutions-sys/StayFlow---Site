from flask import Blueprint, request, jsonify, session
import bcrypt

from database import get_connection

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


def start_session(user):
    """
    Cria a sessão de servidor do usuário logado.
    Todo o resto da aplicação confia nesses valores — nunca em
    algo que o cliente possa enviar diretamente.
    """
    session["user_id"] = user["id"]
    session["hostel_id"] = user["hostel_id"]
    session["role"] = user["role"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["hostel_name"] = user.get("hostel_name")
    session["hostel_email"] = user.get("hostel_email")


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

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "This email is already registered."}), 409

    password_hash = hash_password(password)

    cursor.execute(
        """
        INSERT INTO hostels (name,email)
        VALUES (?,?)
        """,
        (hostel_name, email)
    )

    hostel_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO users
        (hostel_id,name,email,password,role,must_change_password)
        VALUES (?,?,?,?,?,?)
        """,
        (hostel_id, admin_name, email, password_hash, "admin", 1)
    )

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    start_session({
        "id": user_id,
        "hostel_id": hostel_id,
        "role": "admin",
        "name": admin_name,
        "email": email,
        "hostel_name": hostel_name,
        "hostel_email": email
    })

    return jsonify({"success": True, "message": "Hostel created successfully."})


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            u.id,
            u.hostel_id,
            u.name,
            u.email,
            u.password,
            u.role,
            u.must_change_password,
            h.name AS hostel_name,
            h.email AS hostel_email
        FROM users u
        INNER JOIN hostels h
            ON h.id = u.hostel_id
        WHERE u.email = ?
        """,
        (email,)
    )

    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    if not check_password(password, user["password"]):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    user_data = {
        "id": user["id"],
        "hostel_id": user["hostel_id"],
        "hostel_name": user["hostel_name"],
        "hostel_email": user["hostel_email"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "must_change_password": bool(user["must_change_password"])
    }

    start_session(user_data)

    return jsonify({
        "success": True,
        "user": user_data
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    """
    Permite ao frontend confirmar quem está logado e para qual hostel,
    sem precisar guardar essa informação em localStorage.
    """
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    return jsonify({
        "success": True,
        "user": {
            "id": session.get("user_id"),
            "hostel_id": session.get("hostel_id"),
            "hostel_name": session.get("hostel_name"),
            "hostel_email": session.get("hostel_email"),
            "role": session.get("role"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
        }
    })