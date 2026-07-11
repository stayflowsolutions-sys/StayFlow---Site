from database import get_or_create_guest as _get_or_create_guest
from database import update_guest_name as _update_guest_name


def get_or_create_guest(hostel_id, phone):
    return _get_or_create_guest(hostel_id, phone)


def update_guest_name(hostel_id, phone, name):
    return _update_guest_name(hostel_id, phone, name)
