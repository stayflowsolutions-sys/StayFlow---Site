import datetime

from flask import Blueprint, jsonify, request

from database import (
    get_billing_info,
    count_rooms,
    count_active_seats,
    get_active_addons,
    set_billing_plan,
    set_billing_addon,
    set_commission_pct,
    PLAN_ROOM_LIMITS,
    PLAN_SEAT_LIMITS,
)
from utils.tenant import require_permission, require_stayflow_admin

billing_bp = Blueprint("billing", __name__)


def _trial_days_left(billing):
    if billing["status"] != "trialing" or not billing["trial_ends_at"]:
        return None
    ends_at = datetime.datetime.fromisoformat(billing["trial_ends_at"])
    remaining = (ends_at - datetime.datetime.utcnow()).days
    return max(remaining, 0)


@billing_bp.route("/billing", methods=["GET"])
@require_permission("billing")
def get_billing_route(hostel_id):
    billing = get_billing_info(hostel_id)
    plan_name = billing["plan_name"]

    room_limit = PLAN_ROOM_LIMITS.get(plan_name)
    seat_base_limit = PLAN_SEAT_LIMITS.get(plan_name)
    seat_limit = None if seat_base_limit is None else seat_base_limit + (billing["extra_seats"] or 0)

    return jsonify({
        "success": True,
        "plan_name": plan_name,
        "status": billing["status"],
        "trial_days_left": _trial_days_left(billing),
        "rooms_used": count_rooms(hostel_id),
        "room_limit": room_limit,
        "seats_used": count_active_seats(hostel_id),
        "seat_limit": seat_limit,
        "addons": sorted(get_active_addons(hostel_id)),
    })


@billing_bp.route("/billing/admin/set-plan", methods=["POST"])
@require_stayflow_admin
def admin_set_plan_route():
    data = request.get_json() or {}
    hostel_id = data.get("hostel_id")
    plan_name = data.get("plan_name")
    status = data.get("status")

    if not hostel_id or not plan_name:
        return jsonify({"success": False, "message": "hostel_id e plan_name são obrigatórios."}), 400

    if plan_name not in PLAN_ROOM_LIMITS:
        return jsonify({"success": False, "message": "plan_name inválido."}), 400

    set_billing_plan(hostel_id, plan_name, status=status)
    return jsonify({"success": True})


@billing_bp.route("/billing/admin/set-addon", methods=["POST"])
@require_stayflow_admin
def admin_set_addon_route():
    data = request.get_json() or {}
    hostel_id = data.get("hostel_id")
    addon_key = data.get("addon_key")
    active = data.get("active", True)

    if not hostel_id or not addon_key:
        return jsonify({"success": False, "message": "hostel_id e addon_key são obrigatórios."}), 400

    set_billing_addon(hostel_id, addon_key, active)
    return jsonify({"success": True})


@billing_bp.route("/billing/admin/set-commission", methods=["POST"])
@require_stayflow_admin
def admin_set_commission_route():
    """Sobrescreve a comissão de guest_charges (tour/rental/reservation) de uma hospedagem específica. Sem override = usa DEFAULT_COMMISSION_PCT."""
    data = request.get_json() or {}
    hostel_id = data.get("hostel_id")
    charge_type = data.get("charge_type")
    commission_pct = data.get("commission_pct")

    if not hostel_id or not charge_type or commission_pct is None:
        return jsonify({"success": False, "message": "hostel_id, charge_type e commission_pct são obrigatórios."}), 400

    if charge_type not in ("tour", "rental", "reservation"):
        return jsonify({"success": False, "message": "charge_type inválido."}), 400

    set_commission_pct(hostel_id, charge_type, commission_pct)
    return jsonify({"success": True})
