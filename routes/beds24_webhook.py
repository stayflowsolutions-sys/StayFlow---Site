"""
Webhook de entrada do Beds24 (channel manager) - recebe notificacao de
reserva nova vinda de Booking.com/Airbnb/Hostelworld em tempo real.

Autenticacao: token secreto no proprio path da URL (Beds24 nao manda
assinatura HMAC nativa como o WhatsApp/Meta manda) - configurado uma
unica vez no painel do Beds24, nunca exposto em nenhum lugar publico.

Nota de honestidade tecnica: o formato exato do payload de reserva do
Beds24 nao foi confirmado contra um envio real ainda (documentacao
publica bloqueada, igual aconteceu com a API de propriedades/quartos
na Fase 1-2). Por isso o payload cru e SEMPRE gravado em
channel_webhook_events antes de qualquer tentativa de interpretar -
mesmo se a extracao de campo abaixo estiver errada, nenhum dado se
perde, e da pra corrigir o parsing depois olhando o payload real
guardado. So trata reserva nova (criacao) por enquanto - atualizacao e
cancelamento ficam pra quando confirmarmos o formato real com um
webhook de teste.
"""

import os
import json

from flask import Blueprint, request, jsonify

from database import (
    get_hostel_id_by_beds24_property_id,
    get_hostel_id_by_beds24_room_id,
    get_room_category_id_by_beds24_room_id,
    try_claim_webhook_event,
    finalize_webhook_event,
    create_reservation_from_channel,
)

beds24_webhook_bp = Blueprint("beds24_webhook", __name__)

WEBHOOK_SECRET = os.getenv("BEDS24_WEBHOOK_SECRET", "")


@beds24_webhook_bp.route("/webhook/beds24/<secret>", methods=["POST"])
def receive_beds24_webhook(secret):
    if not WEBHOOK_SECRET or secret != WEBHOOK_SECRET:
        return jsonify({"status": "forbidden"}), 403

    payload = request.get_json(silent=True)
    print("Webhook Beds24 recebido (payload cru):", payload)

    if payload is None:
        return jsonify({"status": "ignored", "reason": "sem corpo JSON"}), 200

    # A Beds24 pode mandar um booking so ou uma lista - trata os dois.
    bookings = payload if isinstance(payload, list) else [payload]

    for booking in bookings:
        if isinstance(booking, dict):
            try:
                _process_single_booking(booking)
            except Exception as error:
                print("Erro ao processar item do webhook Beds24:", error)

    # Sempre 200, mesmo com falha interna - evita a Beds24 marcar o
    # webhook como quebrado e parar de mandar (mesmo padrao ja usado
    # no webhook do WhatsApp).
    return jsonify({"status": "ok"}), 200


def _first_present(d, *keys):
    for key in keys:
        value = d.get(key)
        if value not in (None, ""):
            return value
    return None


def _process_single_booking(booking):
    booking_id = _first_present(booking, "bookId", "id", "bookingId", "booking_id")
    if not booking_id:
        print("Webhook Beds24: item sem id de reserva reconhecido, ignorando:", booking)
        return
    booking_id = str(booking_id)

    room_id = _first_present(booking, "roomId", "room_id")
    property_id = _first_present(booking, "propertyId", "property_id")

    hostel_id = None
    if property_id:
        hostel_id = get_hostel_id_by_beds24_property_id(str(property_id))
    if not hostel_id and room_id:
        hostel_id = get_hostel_id_by_beds24_room_id(str(room_id))

    payload_json = json.dumps(booking, ensure_ascii=False)

    if not hostel_id:
        # Sem hostel resolvido no nao da pra nem gravar o evento com FK
        # valida - loga cru pra nao perder o rastro, mas nao ha reserva
        # StayFlow nenhuma pra criar sem saber de qual cliente e.
        print("Webhook Beds24: nao foi possivel identificar o hostel dono dessa reserva:", booking)
        return

    if not try_claim_webhook_event(booking_id, hostel_id, "booking", payload_json):
        print(f"Webhook Beds24: evento {booking_id} ja processado antes (reentrega), ignorando.")
        return

    status = (_first_present(booking, "status") or "").lower()
    if status in ("cancelled", "canceled", "deleted"):
        finalize_webhook_event(booking_id, "ignored", error_message="Cancelamento ainda nao tratado (fica pra Fase 3b, apos confirmar formato real).")
        return

    room_category_id = get_room_category_id_by_beds24_room_id(hostel_id, str(room_id)) if room_id else None
    if not room_category_id:
        finalize_webhook_event(booking_id, "failed", error_message=f"Quarto do Beds24 (roomId={room_id}) nao esta mapeado a nenhuma modalidade do StayFlow.")
        return

    checkin_date = _first_present(booking, "arrival", "checkIn", "firstNight", "arrivalDate")
    checkout_date = _first_present(booking, "departure", "checkOut", "lastNight", "departureDate")
    if not checkin_date or not checkout_date:
        finalize_webhook_event(booking_id, "failed", error_message="Payload sem data de check-in/check-out reconhecida - ver payload_json pra ajustar o parsing.")
        return

    first_name = _first_present(booking, "firstName", "guestFirstName") or ""
    last_name = _first_present(booking, "lastName", "guestLastName") or ""
    guest_name = f"{first_name} {last_name}".strip() or _first_present(booking, "guestName") or "Hospede (OTA)"
    guest_phone = _first_present(booking, "mobile", "phone", "guestPhone") or ""
    channel = (_first_present(booking, "channel", "referer", "apiSource") or "beds24").lower()

    try:
        reservation_id = create_reservation_from_channel(
            hostel_id=hostel_id,
            room_category_id=room_category_id,
            guest_name=guest_name,
            guest_phone=guest_phone,
            checkin_date=str(checkin_date),
            checkout_date=str(checkout_date),
            external_booking_id=booking_id,
            source=channel,
        )
        finalize_webhook_event(booking_id, "processed", reservation_id=reservation_id)
        print(f"Webhook Beds24: reserva {booking_id} criada como reservation_id={reservation_id} (hostel_id={hostel_id}).")
    except Exception as error:
        finalize_webhook_event(booking_id, "failed", error_message=str(error))
        print(f"Webhook Beds24: falha ao criar reserva pro evento {booking_id}:", error)
