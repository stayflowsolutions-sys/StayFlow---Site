from flask import Blueprint, request, jsonify

from database import (
    get_hostel,
    get_hostel_id_by_number,
    get_hostel_whatsapp_config,
    get_hostel_facebook_config,
    get_or_create_guest_by_channel,
    is_guest_ai_paused_by_id,
    get_guest_language_by_id,
    get_guest_name_by_id,
    update_guest_name_by_id,
    update_guest_language_by_id,
    is_opportunity_generation_enabled,
    is_ai_enabled,
    get_hostel_type,
)
from services.ai_service import ask_ai
from services.memory_service import save_message, get_history
from services.lead_service import save_lead
from database import save_message_db_for_guest
from services.decision_engine import analyze_message
from services.whatsapp_service import send_whatsapp_message
from services.messenger_service import send_messenger_message

chat_bp = Blueprint("chat", __name__)


def _memory_key(channel, external_id):
    """
    Chave usada em services/memory_service.py (arquivo JSON, historico
    da IA) - pro WhatsApp fica exatamente o telefone puro (formato ja
    usado em producao, nao mexe pra nao invalidar historico existente).
    Pros outros canais, prefixa com o canal - evita qualquer colisao
    teorica entre um PSID/IGSID e um numero de telefone de verdade no
    mesmo hostel, sem precisar migrar o formato ja usado pelo WhatsApp.
    """
    return external_id if channel == "whatsapp" else f"{channel}:{external_id}"


def _dispatch_send(hostel_id, channel, external_id, answer):
    if channel == "whatsapp":
        phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)
        send_whatsapp_message(phone_number_id, access_token, external_id, answer)
    elif channel == "messenger":
        _page_id, access_token = get_hostel_facebook_config(hostel_id)
        send_messenger_message(access_token, external_id, answer)
    else:
        print(f"Sem envio configurado pro canal '{channel}' ainda.")


def process_incoming_message(hostel_id, external_id, text, channel="whatsapp", send_reply=False, name=None):
    """
    Núcleo do processamento de uma mensagem recebida — guest, memória,
    IA, persistência, lead e oportunidade. Reaproveitado pelo endpoint
    de teste manual (/message), pelo webhook do WhatsApp
    (/webhook/whatsapp) e pelo webhook do Facebook/Instagram
    (/webhook/meta), pra nunca ter duas versões da mesma lógica
    desalinhadas. `external_id` é o identificador do hóspede NO CANAL
    (telefone pro WhatsApp, PSID pro Messenger, IGSID pro Instagram).
    `name`, quando informado (Messenger/Instagram entregam o nome do
    perfil automaticamente), só é gravado na criação do hóspede - a IA
    já sabe usar sem perguntar de novo (ver guest_name em ask_ai).
    """
    guest_phone_for_record = external_id if channel == "whatsapp" else None
    guest_id = get_or_create_guest_by_channel(hostel_id, channel, external_id, phone=guest_phone_for_record, name=name)

    memory_key = _memory_key(channel, external_id)

    save_message(hostel_id, memory_key, "user", text)
    save_message_db_for_guest(guest_id, "user", text, channel=channel)

    save_lead(hostel_id, external_id, text)

    # Buscado uma vez só e reaproveitado tanto pra analise de oportunidade
    # quanto pra IA de atendimento logo abaixo - a analise agora avalia a
    # CONVERSA (nao a mensagem isolada), pra nao tratar cada mensagem nova
    # da mesma conversa como uma "oportunidade" separada.
    history = get_history(hostel_id, memory_key)

    opportunity = analyze_message(hostel_id, guest_id, text, history=history) if is_opportunity_generation_enabled(hostel_id) else None

    # Notificacao push de mensagem nova - tipo separado da oportunidade
    # (analyze_message acima so notifica em oportunidade NOVA de alta
    # urgencia; aqui e literalmente "chegou mensagem", pra quem quiser
    # saber de toda conversa). Desligado por padrao (get_push_notification_types)
    # porque pode ser bem barulhento numa hospedagem movimentada - so
    # manda de verdade se a equipe ligou esse tipo especifico nas
    # preferencias. Best-effort: falha no envio nunca deve quebrar o
    # processamento da mensagem em si.
    try:
        from services.push_service import send_push_to_hostel
        guest_name_for_push = get_guest_name_by_id(guest_id) or "Hóspede"
        send_push_to_hostel(
            hostel_id,
            title=f"💬 {guest_name_for_push}",
            body=text[:120],
            url="/app",
            notification_type="chat_message",
        )
    except Exception as error:
        print(f"AVISO: falha ao notificar nova mensagem por push: {error}")

    # Interruptor mestre: quando desligado, a mensagem do hospede e a
    # oportunidade (acima) ainda sao salvas normalmente - so a resposta
    # da IA (interna e o envio real) e que fica pulada, deixando o
    # atendimento inteiramente manual a partir daqui.
    # Interruptor mestre (hostel inteiro) OU essa conversa especifica foi
    # assumida manualmente pela equipe - nos dois casos, resposta da IA
    # fica pulada, mas mensagem/oportunidade continuam sendo salvas.
    if not is_ai_enabled(hostel_id) or is_guest_ai_paused_by_id(guest_id):
        return None, opportunity

    # O telefone só é passado pra IA quando a mensagem realmente veio do
    # WhatsApp de verdade (external_id != "unknown", usado no endpoint de
    # teste manual) - nos outros canais nunca existe telefone de verdade,
    # entao a IA pede o contato normalmente na conversa (mesmo texto que
    # ja usa quando nao tem telefone disponivel).
    guest_phone = external_id if channel == "whatsapp" and external_id != "unknown" else None
    guest_language = get_guest_language_by_id(guest_id)
    known_guest_name = get_guest_name_by_id(guest_id)
    hostel_record = get_hostel(hostel_id) or {}
    hostel_phone = hostel_record.get("phone")
    hostel_name = hostel_record.get("name")
    hostel_type = get_hostel_type(hostel_id)
    answer, guest_name, guest_language_detected = ask_ai(
        history, text, guest_phone=guest_phone, hostel_id=hostel_id,
        guest_language=guest_language, guest_id=guest_id, guest_name=known_guest_name,
        channel=channel, hostel_phone=hostel_phone, hostel_name=hostel_name, hostel_type=hostel_type
    )

    if guest_name:
        update_guest_name_by_id(guest_id, guest_name)

    if guest_language_detected and guest_language_detected != guest_language:
        update_guest_language_by_id(guest_id, guest_language_detected)

    save_message(hostel_id, memory_key, "assistant", answer)
    save_message_db_for_guest(guest_id, "assistant", answer, channel=channel)

    if send_reply:
        _dispatch_send(hostel_id, channel, external_id, answer)

    return answer, opportunity


@chat_bp.route("/message", methods=["POST"])
def message():
    """
    Endpoint de TESTE manual — não é o webhook real da Meta (esse é
    o /webhook/whatsapp). Útil pra testar o fluxo sem depender do
    WhatsApp de verdade. Não envia mensagem real (send_reply=False).
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
        hostel_id, phone, text, send_reply=False
    )

    return jsonify({
        "reply": answer,
        "opportunity": opportunity
    })
