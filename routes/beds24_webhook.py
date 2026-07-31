"""
Webhook de entrada do Beds24 (channel manager) - recebe notificacao de
reserva vinda de Booking.com/Airbnb/Hostelworld em tempo real, tanto na
criacao quanto em qualquer alteracao (confirmado testando ao vivo: a
Beds24 manda um webhook novo a CADA mudanca na reserva, nao so na
criacao - o mesmo booking.id chega mais de uma vez, cada vez com um
modifiedTime diferente).

Autenticacao: token secreto no proprio path da URL (Beds24 nao manda
assinatura HMAC nativa como o WhatsApp/Meta manda) - configurado uma
unica vez no painel do Beds24, nunca exposto em nenhum lugar publico.

Formato real do payload (confirmado com webhook de teste real,
Versao 2 "com dados pessoais"):
{
  "timeStamp": "...",
  "booking": { "id": ..., "propertyId": ..., "roomId": ..., "status": ...,
               "arrival": "YYYY-MM-DD", "departure": "YYYY-MM-DD",
               "firstName": ..., "lastName": ..., "phone": ...,
               "modifiedTime": "...", "channel": ..., "apiSource": ..., ... },
  "invoiceItems": [...], "infoItems": [...], "messages": [...]
}
Payload cru sempre gravado em channel_webhook_events antes de qualquer
interpretacao - mesmo se algum campo mudar de nome no futuro, nenhuma
reserva se perde, so fica pra corrigir o parsing depois.
"""

import os
import json

from flask import Blueprint, request, jsonify

from database import (
    get_hostel_id_by_beds24_property_id,
    get_hostel_id_by_beds24_room_id,
    get_room_category_id_by_beds24_room_id,
    get_reservation_id_by_external_booking_id,
    try_claim_webhook_event,
    finalize_webhook_event,
    create_reservation_from_channel,
    update_reservation_from_channel,
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

    # A Beds24 pode mandar um evento so ou uma lista - trata os dois.
    items = payload if isinstance(payload, list) else [payload]

    for item in items:
        if isinstance(item, dict):
            try:
                _process_single_booking(item)
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


def _process_single_booking(raw_item):
    # Os dados da reserva ficam dentro de uma chave "booking" - o nivel
    # de cima ("timeStamp", "invoiceItems" etc) nao tem o id da reserva.
    booking = raw_item.get("booking") if isinstance(raw_item.get("booking"), dict) else raw_item

    booking_id = _first_present(booking, "id", "bookId", "bookingId", "booking_id")
    if not booking_id:
        print("Webhook Beds24: item sem id de reserva reconhecido, ignorando:", raw_item)
        return
    booking_id = str(booking_id)

    room_id = _first_present(booking, "roomId", "room_id")
    property_id = _first_present(booking, "propertyId", "property_id")

    hostel_id = None
    if property_id:
        hostel_id = get_hostel_id_by_beds24_property_id(str(property_id))
    if not hostel_id and room_id:
        hostel_id = get_hostel_id_by_beds24_room_id(str(room_id))

    if not hostel_id:
        # Sem hostel resolvido nem da pra gravar o evento com FK valida -
        # loga cru pra nao perder o rastro, mas nao ha reserva StayFlow
        # nenhuma pra criar sem saber de qual cliente e.
        print("Webhook Beds24: nao foi possivel identificar o hostel dono dessa reserva:", raw_item)
        return

    # Chave de idempotencia inclui o modifiedTime - cada alteracao real
    # na reserva (comprovado testando: nome/telefone preenchidos depois
    # da criacao chegam como um evento novo) precisa ser processada,
    # so uma reentrega EXATA do mesmo estado deve ser ignorada.
    modified_time = _first_present(booking, "modifiedTime", "bookingTime") or ""
    event_key = f"{booking_id}:{modified_time}" if modified_time else booking_id

    payload_json = json.dumps(raw_item, ensure_ascii=False)
    existing_reservation_id = get_reservation_id_by_external_booking_id(hostel_id, booking_id)
    event_type = "update" if existing_reservation_id else "booking"

    if not try_claim_webhook_event(event_key, hostel_id, event_type, payload_json):
        print(f"Webhook Beds24: evento {event_key} ja processado antes (reentrega exata), ignorando.")
        return

    status = (_first_present(booking, "status") or "").lower()
    first_name = _first_present(booking, "firstName", "guestFirstName") or ""
    last_name = _first_present(booking, "lastName", "guestLastName") or ""
    guest_name = f"{first_name} {last_name}".strip() or _first_present(booking, "guestName") or "Hospede (OTA)"
    guest_phone = _first_present(booking, "mobile", "phone", "guestPhone") or ""
    checkin_date = _first_present(booking, "arrival", "checkIn", "firstNight", "arrivalDate")
    checkout_date = _first_present(booking, "departure", "checkOut", "lastNight", "departureDate")
    channel = (_first_present(booking, "channel", "referer", "apiSource") or "beds24").lower()

    if "cancel" in status or status == "deleted":
        if existing_reservation_id:
            update_reservation_from_channel(
                hostel_id, booking_id, guest_name, guest_phone,
                str(checkin_date or ""), str(checkout_date or ""), status,
            )
            finalize_webhook_event(event_key, "processed", reservation_id=existing_reservation_id)
            print(f"Webhook Beds24: reserva {booking_id} marcada como cancelada (reservation_id={existing_reservation_id}).")
        else:
            finalize_webhook_event(event_key, "ignored", error_message="Cancelamento de reserva que o StayFlow nunca chegou a criar.")
        return

    if not checkin_date or not checkout_date:
        finalize_webhook_event(event_key, "failed", error_message="Payload sem data de check-in/check-out reconhecida - ver payload_json pra ajustar o parsing.")
        return

    try:
        if existing_reservation_id:
            reservation_id = update_reservation_from_channel(
                hostel_id, booking_id, guest_name, guest_phone,
                str(checkin_date), str(checkout_date), status,
            )
            print(f"Webhook Beds24: reserva {booking_id} atualizada (reservation_id={reservation_id}).")
        else:
            room_category_id = get_room_category_id_by_beds24_room_id(hostel_id, str(room_id)) if room_id else None
            if not room_category_id:
                finalize_webhook_event(event_key, "failed", error_message=f"Quarto do Beds24 (roomId={room_id}) nao esta mapeado a nenhuma modalidade do StayFlow.")
                return

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
            print(f"Webhook Beds24: reserva {booking_id} criada como reservation_id={reservation_id} (hostel_id={hostel_id}).")

        finalize_webhook_event(event_key, "processed", reservation_id=reservation_id)
    except Exception as error:
        finalize_webhook_event(event_key, "failed", error_message=str(error))
        print(f"Webhook Beds24: falha ao processar evento {booking_id}:", error)
