from flask import Blueprint, request, jsonify

from database import get_hostel_id_by_number, get_hostel_whatsapp_config, is_opportunity_generation_enabled, is_ai_enabled, is_guest_ai_paused
from services.ai_service import ask_ai
from services.memory_service import save_message, get_history
from services.guest_service import get_or_create_guest, update_guest_name
from services.lead_service import save_lead
from services.message_service import save_message_db
from services.decision_engine import analyze_message
from services.whatsapp_service import send_whatsapp_message

chat_bp = Blueprint("chat", __name__)


def process_incoming_message(hostel_id, phone, text, send_to_whatsapp=False):
    """
    Núcleo do processamento de uma mensagem recebida — guest, memória,
    IA, persistência, lead e oportunidade. Reaproveitado tanto pelo
    endpoint de teste manual (/message) quanto pelo webhook real do
    WhatsApp (/webhook/whatsapp), pra nunca ter duas versões da mesma
    lógica desalinhadas.
    """
    get_or_create_guest(hostel_id, phone)

    save_message(hostel_id, phone, "user", text)
    save_message_db(hostel_id, phone, "user", text)

    save_lead(hostel_id, phone, text)

    opportunity = analyze_message(hostel_id, phone, text) if is_opportunity_generation_enabled(hostel_id) else None

    # Interruptor mestre: quando desligado, a mensagem do hospede e a
    # oportunidade (acima) ainda sao salvas normalmente - so a resposta
    # da IA (interna e o envio real pelo WhatsApp) e que fica pulada,
    # deixando o atendimento inteiramente manual a partir daqui.
    # Interruptor mestre (hostel inteiro) OU essa conversa especifica foi
    # assumida manualmente pela equipe - nos dois casos, resposta da IA
    # fica pulada, mas mensagem/oportunidade continuam sendo salvas.
    if not is_ai_enabled(hostel_id) or is_guest_ai_paused(hostel_id, phone):
        return None, opportunity

    history = get_history(hostel_id, phone)

    # O telefone só é passado pra IA quando a mensagem realmente veio do
    # WhatsApp de verdade (phone != "unknown", usado no endpoint de teste
    # manual). Isso evita a IA tratar um telefone de teste como contato real.
    guest_phone = phone if phone != "unknown" else None
    answer, guest_name = ask_ai(history, text, guest_phone=guest_phone, hostel_id=hostel_id)

    if guest_name:
        update_guest_name(hostel_id, phone, guest_name)

    save_message(hostel_id, phone, "assistant", answer)
    save_message_db(hostel_id, phone, "assistant", answer)

    if send_to_whatsapp:
        phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)
        send_whatsapp_message(phone_number_id, access_token, phone, answer)

    return answer, opportunity


@chat_bp.route("/message", methods=["POST"])
def message():
    """
    Endpoint de TESTE manual — não é o webhook real da Meta (esse é
    o /webhook/whatsapp). Útil pra testar o fluxo sem depender do
    WhatsApp de verdade. Não envia mensagem real (send_to_whatsapp=False).
    """
    data = request.get_json() or {}

    phone = data.get("phone", "unknown")
    text = data.get("message", "")

    hostel_phone = data.get("to") or data.get("hostel_phone")
    hostel_id = get_hostel_id_by_number(hostel_phone) if hostel_phone else None

    if not hostel_id:
        return jsonify({
            "error": "Não foi possível identificar o hostel desta mensagem. "
                     "Verifique se o campo 'to' (número do hostel) está "
                     "sendo enviado e cadastrado em hostels.phone."
        }), 400

    answer, opportunity = process_incoming_message(
        hostel_id, phone, text, send_to_whatsapp=False
    )

    return jsonify({
        "reply": answer,
        "opportunity": opportunity
    })
