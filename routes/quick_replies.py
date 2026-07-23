from flask import Blueprint, request, jsonify

from utils.tenant import require_permission
from database import get_quick_replies, create_quick_reply, delete_quick_reply

quick_replies_bp = Blueprint("quick_replies", __name__)


@quick_replies_bp.route("/quick-replies", methods=["GET"])
@require_permission("chats")
def list_quick_replies(hostel_id):
    return jsonify({"success": True, "quick_replies": get_quick_replies(hostel_id)})


@quick_replies_bp.route("/quick-replies", methods=["POST"])
@require_permission("settings")
def create_quick_reply_route(hostel_id):
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"success": False, "message": "text is required."}), 400

    quick_reply_id = create_quick_reply(hostel_id, text)

    return jsonify({"success": True, "id": quick_reply_id}), 201


@quick_replies_bp.route("/quick-replies/<int:quick_reply_id>", methods=["DELETE"])
@require_permission("settings")
def delete_quick_reply_route(hostel_id, quick_reply_id):
    deleted = delete_quick_reply(quick_reply_id, hostel_id)

    if not deleted:
        return jsonify({"success": False, "message": "Quick reply not found."}), 404

    return jsonify({"success": True})
