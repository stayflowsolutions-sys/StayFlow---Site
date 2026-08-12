from flask import Blueprint, jsonify, request

from database import (
    get_reservations_with_stats,
    get_cancelled_reservations,
    create_reservation_record,
    update_reservation_status_record,
    create_indefinite_stay,
    record_reservation_payment,
    list_reservation_payments,
    close_indefinite_stay,
)
from utils.tenant import require_permission

reservations_bp = Blueprint("reservations", __name__)


@reservations_bp.route("/reservations/import", methods=["POST"])
@require_permission("reservations")
def import_reservations_route(hostel_id):
    """
    Importa reservas historicas em lote a partir de uma planilha ja
    parseada no frontend (lista de {guest_name, phone, room_type,
    checkin_date, checkout_date, amount, status, payment_method}) -
    pra quem esta migrando de outro sistema e quer manter o historico
    de estadias. notify=False (ver create_reservation_record): reserva
    importada e historico, nao um evento acontecendo agora - nunca deve
    ecoar pro Beds24 nem disparar webhook de saida configurado pela
    hospedagem pra reserva NOVA de verdade.
    """
    data = request.get_json() or {}
    rows = data.get("rows", [])
    if not rows:
        return jsonify({"success": False, "message": "Nenhuma linha pra importar."}), 400

    created = 0
    errors = []
    for i, row in enumerate(rows):
        try:
            create_reservation_record(
                hostel_id,
                guest_name=row.get("guest_name"),
                room_type=row.get("room_type"),
                checkin_date=row.get("checkin_date"),
                checkout_date=row.get("checkout_date"),
                source="import",
                payment_method=row.get("payment_method"),
                amount=row.get("amount") or 0,
                status=row.get("status") or "confirmed",
                phone=row.get("phone"),
                notify=False,
            )
            created += 1
        except (ValueError, TypeError) as error:
            errors.append({"row": i + 1, "message": str(error)})

    return jsonify({"success": True, "created": created, "errors": errors}), 201


@reservations_bp.route("/reservations", methods=["GET"])
@require_permission("reservations")
def list_reservations(hostel_id):
    return jsonify(get_reservations_with_stats(hostel_id))


@reservations_bp.route("/reservations/cancelled", methods=["GET"])
@require_permission("reservations")
def list_cancelled_reservations(hostel_id):
    return jsonify(get_cancelled_reservations(hostel_id))


@reservations_bp.route("/reservations", methods=["POST"])
@require_permission("reservations")
def create_reservation(hostel_id):
    data = request.get_json() or {}

    try:
        reservation_id = create_reservation_record(
            hostel_id,
            guest_name=data.get("guest_name"),
            room_type=data.get("room_type"),
            bed=data.get("bed"),
            checkin_date=data.get("checkin_date"),
            checkout_date=data.get("checkout_date"),
            source=data.get("source"),
            payment_method=data.get("payment_method"),
            amount=data.get("amount"),
            status=data.get("status"),
            phone=data.get("phone"),
            email=data.get("email"),
            nationality=data.get("nationality"),
            bed_id=data.get("bed_id"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, "id": reservation_id}), 201


@reservations_bp.route("/reservations/<int:reservation_id>", methods=["PATCH"])
@require_permission("reservations")
def update_reservation(hostel_id, reservation_id):
    data = request.get_json() or {}

    if "status" in data:
        try:
            update_reservation_status_record(hostel_id, reservation_id, data["status"])
        except ValueError as error:
            return jsonify({"success": False, "message": str(error)}), 404

    return jsonify({"success": True})


@reservations_bp.route("/reservations/indefinite", methods=["POST"])
@require_permission("reservations")
def create_indefinite_stay_route(hostel_id):
    data = request.get_json() or {}

    try:
        reservation_id = create_indefinite_stay(
            hostel_id,
            guest_name=data.get("guest_name"),
            checkin_date=data.get("checkin_date"),
            daily_rate=data.get("daily_rate"),
            room_type=data.get("room_type"),
            bed_id=data.get("bed_id"),
            phone=data.get("phone"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, "id": reservation_id}), 201


@reservations_bp.route("/reservations/<int:reservation_id>/payments", methods=["GET"])
@require_permission("reservations")
def list_reservation_payments_route(hostel_id, reservation_id):
    return jsonify(list_reservation_payments(hostel_id, reservation_id))


@reservations_bp.route("/reservations/<int:reservation_id>/payments", methods=["POST"])
@require_permission("reservations")
def record_reservation_payment_route(hostel_id, reservation_id):
    data = request.get_json() or {}

    try:
        balance = record_reservation_payment(
            hostel_id, reservation_id,
            amount=data.get("amount"),
            method=data.get("method"),
            note=data.get("note"),
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, **balance})


@reservations_bp.route("/reservations/<int:reservation_id>/close-stay", methods=["POST"])
@require_permission("reservations")
def close_indefinite_stay_route(hostel_id, reservation_id):
    data = request.get_json() or {}

    try:
        balance = close_indefinite_stay(hostel_id, reservation_id, data.get("checkout_date"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({"success": True, **balance})