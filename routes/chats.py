from flask import Blueprint, jsonify
from database import get_chats_list
from utils.tenant import require_permission

chats_bp = Blueprint("chats", __name__)


@chats_bp.route("/chats", methods=["GET"])
@require_permission("chats")
def chats(hostel_id):
    return jsonify(get_chats_list(hostel_id))
