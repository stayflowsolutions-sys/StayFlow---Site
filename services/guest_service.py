from database import get_or_create_guest as _get_or_create_guest
from database import update_guest_name as _update_guest_name
from database import get_guest_language as _get_guest_language
from database import update_guest_language as _update_guest_language


def get_or_create_guest(hostel_id, phone):
    return _get_or_create_guest(hostel_id, phone)


def update_guest_name(hostel_id, phone, name):
    return _update_guest_name(hostel_id, phone, name)


def get_guest_language(hostel_id, phone):
    return _get_guest_language(hostel_id, phone)


def update_guest_language(hostel_id, phone, language):
    return _update_guest_language(hostel_id, phone, language)
