# app/api/routes/ai_chat.py
from fastapi import APIRouter, Body, HTTPException
from app.ai import ai_api
from typing import Dict

router = APIRouter()

@router.post('/ai/chat')
def api_ai_chat(payload: Dict = Body(...)):
    """
    POST /api/ai/chat
    body: { message: str, cart: [...], guest_phone, guest_name, top_k }
    """
    if not payload or 'message' not in payload:
        raise HTTPException(status_code=400, detail="Field 'message' is required")
    try:
        r = ai_api.handle_ai_message(payload)
        return r
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
