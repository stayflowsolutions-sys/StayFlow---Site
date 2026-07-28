from flask import Blueprint, request, jsonify

from utils.tenant import require_auth, get_current_user_id
from database import get_ask_history, save_ask_message
from services.ask_agent_service import ask_agent

ask_bp = Blueprint("ask", __name__)


@ask_bp.route("/ask", methods=["GET"])
@require_auth
def ask_history(hostel_id):
    user_id = get_current_user_id()
    history = get_ask_history(hostel_id, user_id)
    return jsonify({"success": True, "history": history})


@ask_bp.route("/ask", methods=["POST"])
@require_auth
def ask(hostel_id):
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    lang = data.get("lang", "pt")

    if not message:
        return jsonify({"success": False, "message": "message is required."}), 400

    user_id = get_current_user_id()

    history = get_ask_history(hostel_id, user_id)
    history_for_ai = [{"role": h["role"], "content": h["content"]} for h in history]

    save_ask_message(hostel_id, user_id, "user", message)

    reply = ask_agent(hostel_id, user_id, history_for_ai, message, lang=lang)

    save_ask_message(hostel_id, user_id, "assistant", reply)

    return jsonify({"success": True, "reply": reply})
