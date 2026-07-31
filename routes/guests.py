from flask import Blueprint, jsonify, request, send_file
from database import (
    get_guests_list,
    get_guest_profile,
    set_guest_ai_paused,
    send_message_to_guest_now,
    get_guest_document_file,
    update_guest_profile,
    save_guest_document,
)
from services.translation_service import translate_opportunity_fields
from utils.tenant import require_permission

guests_bp = Blueprint("guests", __name__)

_ALLOWED_DOCUMENT_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


@guests_bp.route("/guests", methods=["GET"])
@require_permission("guests")
def list_guests(hostel_id):
    return jsonify(get_guests_list(hostel_id))


@guests_bp.route("/guests/<int:guest_id>", methods=["GET"])
@require_permission("guests")
def guest_profile(hostel_id, guest_id):
    profile = get_guest_profile(hostel_id, guest_id)

    if not profile:
        return jsonify({"error": "Guest not found"}), 404

    lang = request.args.get("lang", "pt")
    if profile.get("opportunities"):
        profile["opportunities"] = translate_opportunity_fields(profile["opportunities"], lang)

    return jsonify(profile)


@guests_bp.route("/guests/<int:guest_id>/toggle-ai", methods=["POST"])
@require_permission("chats")
def toggle_guest_ai(hostel_id, guest_id):
    data = request.get_json() or {}

    try:
        result = set_guest_ai_paused(hostel_id, guest_id, bool(data.get("paused")))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404

    return jsonify({"success": True, **result})


@guests_bp.route("/guests/<int:guest_id>/send-message", methods=["POST"])
@require_permission("chats")
def send_message_to_guest_route(hostel_id, guest_id):
    data = request.get_json() or {}

    try:
        result = send_message_to_guest_now(hostel_id, guest_id, data.get("message"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    if not result["sent"]:
        return jsonify({"success": False, "message": "WhatsApp não configurado para este hostel — mensagem não enviada."}), 502

    return jsonify({"success": True, **result})


@guests_bp.route("/guests/documents/<int:document_id>/file", methods=["GET"])
@require_permission("guests")
def get_guest_document_file_route(hostel_id, document_id):
    document = get_guest_document_file(hostel_id, document_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    return send_file(document["file_path"], mimetype=document["mime_type"])


@guests_bp.route("/guests/<int:guest_id>", methods=["PATCH"])
@require_permission("guests")
def update_guest_profile_route(hostel_id, guest_id):
    data = request.get_json() or {}

    try:
        update_guest_profile(hostel_id, guest_id, **data)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True})


@guests_bp.route("/guests/<int:guest_id>/documents", methods=["POST"])
@require_permission("guests")
def upload_guest_document_route(hostel_id, guest_id):
    if not get_guest_profile(hostel_id, guest_id):
        return jsonify({"success": False, "message": "Hóspede não encontrado."}), 404

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado."}), 400

    mime_type = file.mimetype
    if mime_type not in _ALLOWED_DOCUMENT_MIME_TYPES:
        return jsonify({"success": False, "message": "Formato não suportado. Envie JPG, PNG, WEBP ou PDF."}), 400

    try:
        result = save_guest_document(hostel_id, guest_id, file.read(), mime_type)
    except Exception as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, **result})
