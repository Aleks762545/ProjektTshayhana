from fastapi import APIRouter, HTTPException
from fastapi import status
from app.db.sqlite_db import find_or_create_guest_by_phone

router = APIRouter(prefix="/guests", tags=["Guests"])

@router.post("/find_or_create")
def find_or_create_guest(payload: dict):
    phone = payload.get("phone")
    name = payload.get("name", "")
    if not phone:
        raise HTTPException(status_code=400, detail="phone required")
    gid = find_or_create_guest_by_phone(phone, name)
    if not gid:
        raise HTTPException(status_code=500, detail="failed to create guest")
    return {"success": True, "data": {"id": gid, "phone": phone, "name": name}}