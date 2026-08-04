from flask import Blueprint, request, jsonify

from database import (
    create_section,
    get_sections,
    create_staff_shift,
    get_staff_shifts,
    get_on_duty_staff,
    request_shift_coverage,
    accept_shift_coverage,
)
from utils.tenant import require_permission

scheduling_bp = Blueprint("scheduling", __name__)


@scheduling_bp.route("/scheduling/sections", methods=["GET"])
@require_permission("scheduling")
def list_sections_route(hostel_id):
    department = request.args.get("department")
    return jsonify(get_sections(hostel_id, department=department))


@scheduling_bp.route("/scheduling/sections", methods=["POST"])
@require_permission("scheduling")
def create_section_route(hostel_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    department = (data.get("department") or "").strip()

    if not name or not department:
        return jsonify({"success": False, "message": "name and department are required."}), 400

    section_id = create_section(hostel_id, name, department)
    return jsonify({"success": True, "id": section_id}), 201


@scheduling_bp.route("/scheduling/shifts", methods=["GET"])
@require_permission("scheduling")
def list_shifts_route(hostel_id):
    """
    Grade semanal (linha=funcionario, coluna=dia) - filtra por periodo
    via start_date/end_date (YYYY-MM-DD) na query string.
    """
    return jsonify(get_staff_shifts(
        hostel_id,
        start_date=request.args.get("start_date"),
        end_date=request.args.get("end_date"),
    ))


@scheduling_bp.route("/scheduling/shifts", methods=["POST"])
@require_permission("scheduling")
def create_shift_route(hostel_id):
    data = request.get_json() or {}
    required = ["membership_id", "department", "shift_date", "start_time", "end_time"]
    missing = [field for field in required if not data.get(field)]

    if missing:
        return jsonify({"success": False, "message": f"Campos obrigatórios faltando: {', '.join(missing)}."}), 400

    shift_id = create_staff_shift(
        hostel_id, data["membership_id"], data["department"],
        data["shift_date"], data["start_time"], data["end_time"],
        section_id=data.get("section_id"),
    )
    return jsonify({"success": True, "id": shift_id}), 201


@scheduling_bp.route("/scheduling/on-duty", methods=["GET"])
@require_permission("scheduling")
def get_on_duty_route(hostel_id):
    department = request.args.get("department")
    if not department:
        return jsonify({"success": False, "message": "department is required."}), 400

    section_id = request.args.get("section_id", type=int)
    return jsonify(get_on_duty_staff(hostel_id, department, section_id=section_id))


@scheduling_bp.route("/scheduling/shifts/<int:shift_id>/coverage-request", methods=["POST"])
@require_permission("scheduling")
def request_shift_coverage_route(hostel_id, shift_id):
    data = request.get_json() or {}
    requested_by_membership_id = data.get("requested_by_membership_id")

    if not requested_by_membership_id:
        return jsonify({"success": False, "message": "requested_by_membership_id is required."}), 400

    request_id = request_shift_coverage(shift_id, requested_by_membership_id)
    return jsonify({"success": True, "id": request_id}), 201


@scheduling_bp.route("/scheduling/coverage-requests/<int:request_id>/accept", methods=["POST"])
@require_permission("scheduling")
def accept_shift_coverage_route(hostel_id, request_id):
    data = request.get_json() or {}
    covering_membership_id = data.get("covering_membership_id")

    if not covering_membership_id:
        return jsonify({"success": False, "message": "covering_membership_id is required."}), 400

    ok = accept_shift_coverage(request_id, covering_membership_id)
    if not ok:
        return jsonify({"success": False, "message": "Pedido de cobertura não encontrado ou já resolvido."}), 404
    return jsonify({"success": True})
