import base64

from flask import Blueprint, request, jsonify

from utils.tenant import require_auth, get_current_user_id
from database import get_ask_history, save_ask_message
from services.ask_agent_service import ask_agent

ask_bp = Blueprint("ask", __name__)

_ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@ask_bp.route("/ask", methods=["GET"])
@require_auth
def ask_history(hostel_id):
    user_id = get_current_user_id()
    history = get_ask_history(hostel_id, user_id)
    return jsonify({"success": True, "history": history})


@ask_bp.route("/ask", methods=["POST"])
@require_auth
def ask(hostel_id):
    user_id = get_current_user_id()

    # Foto/arquivo da galeria (documento, lista de compra escrita a mao
    # etc.) vem como multipart, nao JSON - so nesse caso o form-data e
    # usado, pra nao mudar o formato da chamada de texto puro que ja
    # funciona. So imagem por enquanto (nao PDF): e o formato que a
    # camera do celular gera, e e o unico que o modelo consegue "ver"
    # direto via image_url no chat completions.
    file = request.files.get("file")
    if file and file.filename:
        if file.mimetype not in _ALLOWED_IMAGE_MIME_TYPES:
            return jsonify({"success": False, "message": "Formato não suportado. Envie uma foto (JPG, PNG ou WEBP)."}), 400
        encoded = base64.b64encode(file.read()).decode("ascii")
        image_data_url = f"data:{file.mimetype};base64,{encoded}"
        message = (request.form.get("message") or "").strip()
        lang = request.form.get("lang", "pt")
    else:
        data = request.get_json() or {}
        message = (data.get("message") or "").strip()
        lang = data.get("lang", "pt")
        image_data_url = None

    if not message and not image_data_url:
        return jsonify({"success": False, "message": "message is required."}), 400

    history = get_ask_history(hostel_id, user_id)
    history_for_ai = [{"role": h["role"], "content": h["content"]} for h in history]

    save_ask_message(hostel_id, user_id, "user", message or "[imagem enviada]")

    reply = ask_agent(hostel_id, user_id, history_for_ai, message, lang=lang, image_data_url=image_data_url)

    save_ask_message(hostel_id, user_id, "assistant", reply)

    return jsonify({"success": True, "reply": reply})
