# app/ai/ai_api.py
from app.ai import parser, semantic_search, response, utils
from app.db import sqlite_db
from typing import Dict

def handle_ai_message(payload: Dict):
    """
    payload expects:
      {
         'message': str,
         'cart': [{id, quantity, name, price}] optional,
         'guest_phone': optional,
         'guest_name': optional,
         'top_k': optional
      }
    returns dict { success, message, suggestions: [...], parsed: {...} }
    """
    msg = payload.get('message') or ''
    top_k = int(payload.get('top_k') or 6)
    parsed = parser.parse_user_message(msg)

    # If user directly wants to order and provided cart, try to create order hint
    # But main flow: search for dishes based on parsed
    candidates = semantic_search.search_dishes_by_query(parsed, top_k=top_k)

    resp = response.build_response(parsed, candidates)

    # If user intends to order, hint how to order (front will send /orders)
    if parsed.get('is_order'):
        resp['message'] += "\n\nПохоже, вы хотите сделать заказ. Чтобы подтвердить — пришлите 'закажи' с указанием номера столика или воспользуйтесь кнопкой Оформить заказ."
        resp['order_hint'] = True

    return {'success': True, 'data': resp}
