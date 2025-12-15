# app/ai/utils.py
def ensure_guest_info(payload):
    phone = payload.get('guest_phone') or payload.get('phone') or None
    name = payload.get('guest_name') or payload.get('name') or None
    return phone, name
