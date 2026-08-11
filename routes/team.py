import secrets

from flask import Blueprint, request, jsonify

from utils.tenant import require_permission
from routes.auth import hash_password
from database import (
    get_roles,
    get_role,
    create_role,
    update_role,
    delete_role,
    get_team_members,
    invite_to_hostel,
    update_membership_role,
    set_membership_override,
    deactivate_membership,
    reactivate_membership,
    get_membership_by_id,
    get_permission_detail,
    check_seat_limit,
)

team_bp = Blueprint("team", __name__)


def _role_in_hostel(role_id, hostel_id):
    role = get_role(role_id)
    if not role or role["hostel_id"] != hostel_id:
        return None
    return role


def _membership_in_hostel(membership_id, hostel_id):
    membership = get_membership_by_id(membership_id)
    if not membership or membership["hostel_id"] != hostel_id:
        return None
    return membership


@team_bp.route("/roles", methods=["GET"])
@require_permission("team")
def list_roles(hostel_id):
    return jsonify({"success": True, "roles": get_roles(hostel_id)})


@team_bp.route("/roles", methods=["POST"])
@require_permission("team")
def create_role_route(hostel_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    permissions = data.get("permissions") or []

    if not name:
        return jsonify({"success": False, "message": "Role name is required."}), 400

    try:
        role_id = create_role(hostel_id, name, permissions)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409

    return jsonify({"success": True, "role": get_role(role_id)}), 201


@team_bp.route("/roles/<int:role_id>", methods=["PATCH"])
@require_permission("team")
def update_role_route(hostel_id, role_id):
    if not _role_in_hostel(role_id, hostel_id):
        return jsonify({"success": False, "message": "Role not found."}), 404

    data = request.get_json() or {}
    name = data.get("name")
    permissions = data.get("permissions")

    try:
        update_role(role_id, name=name, permissions_list=permissions)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409

    return jsonify({"success": True, "role": get_role(role_id)})


@team_bp.route("/roles/<int:role_id>", methods=["DELETE"])
@require_permission("team")
def delete_role_route(hostel_id, role_id):
    if not _role_in_hostel(role_id, hostel_id):
        return jsonify({"success": False, "message": "Role not found."}), 404

    try:
        delete_role(role_id)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409

    return jsonify({"success": True})


@team_bp.route("/team", methods=["GET"])
@require_permission("team")
def list_team(hostel_id):
    return jsonify({"success": True, "members": get_team_members(hostel_id)})


@team_bp.route("/team/invite", methods=["POST"])
@require_permission("team")
def invite_team_member(hostel_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    role_id = data.get("role_id")

    if not name:
        return jsonify({"success": False, "message": "Name is required."}), 400
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    if not role_id:
        return jsonify({"success": False, "message": "role_id is required."}), 400

    if not _role_in_hostel(role_id, hostel_id):
        return jsonify({"success": False, "message": "Role not found."}), 404

    allowed, limit_message = check_seat_limit(hostel_id, additional=1)
    if not allowed:
        return jsonify({"success": False, "message": limit_message}), 402

    temp_password = secrets.token_urlsafe(9)
    password_hash = hash_password(temp_password)

    try:
        result = invite_to_hostel(hostel_id, name, email, role_id, password_hash=password_hash)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409

    return jsonify({
        "success": True,
        "membership_id": result["membership_id"],
        "temporary_password": temp_password,
        "message": "Compartilhe essa senha temporaria com a pessoa - ela sera obrigada a troca-la no primeiro acesso. Esta senha nao sera mostrada novamente."
    }), 201


@team_bp.route("/team/<int:membership_id>/role", methods=["PATCH"])
@require_permission("team")
def change_member_role(hostel_id, membership_id):
    if not _membership_in_hostel(membership_id, hostel_id):
        return jsonify({"success": False, "message": "Team member not found."}), 404

    data = request.get_json() or {}
    new_role_id = data.get("role_id")

    if not new_role_id:
        return jsonify({"success": False, "message": "role_id is required."}), 400

    try:
        update_membership_role(membership_id, new_role_id)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409

    return jsonify({"success": True})


@team_bp.route("/team/<int:membership_id>/permissions", methods=["PATCH"])
@require_permission("team")
def change_member_permission(hostel_id, membership_id):
    if not _membership_in_hostel(membership_id, hostel_id):
        return jsonify({"success": False, "message": "Team member not found."}), 404

    data = request.get_json() or {}
    permission_key = data.get("permission_key")
    allowed = data.get("allowed")

    if not permission_key or allowed is None:
        return jsonify({"success": False, "message": "permission_key and allowed are required."}), 400

    try:
        set_membership_override(membership_id, permission_key, allowed)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409

    return jsonify({"success": True})


@team_bp.route("/team/<int:membership_id>/deactivate", methods=["PATCH"])
@require_permission("team")
def deactivate_member(hostel_id, membership_id):
    if not _membership_in_hostel(membership_id, hostel_id):
        return jsonify({"success": False, "message": "Team member not found."}), 404

    try:
        deactivate_membership(membership_id)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 409

    return jsonify({"success": True})


@team_bp.route("/team/<int:membership_id>/reactivate", methods=["PATCH"])
@require_permission("team")
def reactivate_member(hostel_id, membership_id):
    if not _membership_in_hostel(membership_id, hostel_id):
        return jsonify({"success": False, "message": "Team member not found."}), 404

    allowed, limit_message = check_seat_limit(hostel_id, additional=1)
    if not allowed:
        return jsonify({"success": False, "message": limit_message}), 402

    reactivate_membership(membership_id)

    return jsonify({"success": True})


@team_bp.route("/permissions/catalog", methods=["GET"])
@require_permission("team")
def permissions_catalog(hostel_id):
    from database import get_hostel
    from utils.permissions import PERMISSION_LABELS, permissions_for_account_kind

    account_kind = (get_hostel(hostel_id) or {}).get("account_kind", "lodging")
    # "Hospedes" vira "PAX" aqui tambem pra bater com o rotulo que a
    # agencia ja ve no menu lateral (ver dashboard.html hydrateUserUI).
    catalog = [{
        "key": k,
        "label": "PAX" if k == "guests" and account_kind == "agency" else PERMISSION_LABELS.get(k, k),
    } for k in permissions_for_account_kind(account_kind)]
    return jsonify({"success": True, "permissions": catalog})


@team_bp.route("/team/<int:membership_id>/permissions-detail", methods=["GET"])
@require_permission("team")
def member_permissions_detail(hostel_id, membership_id):
    if not _membership_in_hostel(membership_id, hostel_id):
        return jsonify({"success": False, "message": "Team member not found."}), 404
    return jsonify({"success": True, "permissions": get_permission_detail(membership_id)})
