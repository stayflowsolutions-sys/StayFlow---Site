"""
Canal de suporte da hospedagem/agencia com a propria StayFlow - 1
thread continuo por hostel_id, sem departamentos nem categorias (ver
comentario da tabela support_messages em database.py). Do lado do
painel interno, ver routes/stayflow_admin.py ("Suporte").
"""

from flask import Blueprint, jsonify, request

from database import (
    create_support_message,
    get_support_messages,
    mark_support_seen_by_hostel,
    count_unread_support_for_hostel,
)
from utils.tenant import require_auth

support_bp = Blueprint("support", __name__)


@support_bp.route("/support/thread", methods=["GET"])
@require_auth
def get_thread(hostel_id):
    messages = get_support_messages(hostel_id)
    mark_support_seen_by_hostel(hostel_id)
    return jsonify({"success": True, "messages": messages})


@support_bp.route("/support/thread/send", methods=["POST"])
@require_auth
def send_thread_message(hostel_id):
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"success": False, "message": "Mensagem vazia."}), 400

    create_support_message(hostel_id, "hostel", message)
    return jsonify({"success": True})


@support_bp.route("/support/unread-count", methods=["GET"])
@require_auth
def unread_count(hostel_id):
    return jsonify({"success": True, "unread": count_unread_support_for_hostel(hostel_id)})
