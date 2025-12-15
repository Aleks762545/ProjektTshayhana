# app/api/routes/orders.py
from fastapi import APIRouter, HTTPException, Body
from app.db.sqlite_db import find_or_create_guest_by_phone, create_order, list_orders

router = APIRouter()

@router.post('/orders')
def api_create_order(payload: dict = Body(...)):
    table = payload.get('table_number')
    items = payload.get('items', [])
    guest_phone = payload.get('guest_phone')
    guest_name = payload.get('guest_name') or payload.get('name')
    guest_id = find_or_create_guest_by_phone(guest_phone, guest_name) if guest_phone else None

    if not table:
        raise HTTPException(status_code=400, detail="table_number is required")
    if not items or not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items must be a non-empty list")

    # validate items minimally
    for it in items:
        if 'dish_id' not in it or 'quantity' not in it:
            raise HTTPException(status_code=400, detail="each item must contain dish_id and quantity")

    oid = create_order(guest_id, table, items)
    return {'order_id': oid}

@router.get('/orders')
def api_list_orders():
    return list_orders()
# app/api/routes/orders.py (дополнение)
from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional
from app.db.sqlite_db import (
    find_or_create_guest_by_phone, 
    create_order, 
    list_orders,
    # Новые импорты:
    get_order_with_items,
    update_order_status,
    delete_order_if_completed,
    list_orders_filtered
)

router = APIRouter()

# Существующий POST /orders - БЕЗ ИЗМЕНЕНИЙ
@router.post('/orders')
def api_create_order(payload: dict = Body(...)):
    table = payload.get('table_number')
    items = payload.get('items', [])
    guest_phone = payload.get('guest_phone')
    guest_name = payload.get('guest_name') or payload.get('name')
    guest_id = find_or_create_guest_by_phone(guest_phone, guest_name) if guest_phone else None

    if not table:
        raise HTTPException(status_code=400, detail="table_number is required")
    if not items or not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items must be a non-empty list")

    # validate items minimally
    for it in items:
        if 'dish_id' not in it or 'quantity' not in it:
            raise HTTPException(status_code=400, detail="each item must contain dish_id and quantity")

    oid = create_order(guest_id, table, items)
    return {'order_id': oid}

# Обновленный GET /orders с обратной совместимостью
@router.get('/orders')
def api_list_orders(status: Optional[str] = Query(None)):
    """Получить заказы, с опциональной фильтрацией по статусу"""
    
    # Для обратной совместимости: если статус не указан, работает как раньше
    if status is None:
        return list_orders()
    
    # Если статус указан, используем фильтрацию
    valid_statuses = ['ожидает', 'готовится', 'готов', 'выдан']
    if status not in valid_statuses:
        # Мягкая валидация: если статус невалидный, все равно возвращаем все заказы
        return list_orders()
    
    return list_orders_filtered(status)

# НОВЫЙ: Детали заказа с блюдами
@router.get('/orders/{order_id}/details')
def api_get_order_details(order_id: int):
    """Получить детальную информацию о заказе с блюдами"""
    order = get_order_with_items(order_id)
    if not order:
        raise HTTPException(404, detail="Order not found")
    return order

# НОВЫЙ: Обновление статуса
@router.put('/orders/{order_id}/status')
def api_update_order_status(order_id: int, payload: dict = Body(...)):
    """Обновить статус заказа"""
    status = payload.get('status')
    valid_statuses = ['ожидает', 'готовится', 'готов', 'выдан']
    
    if not status:
        raise HTTPException(400, detail="Field 'status' is required")
    
    if status not in valid_statuses:
        raise HTTPException(400, detail=f"Status must be one of: {valid_statuses}")
    
    success = update_order_status(order_id, status)
    if not success:
        raise HTTPException(404, detail="Order not found")
    
    return {'ok': True, 'order_id': order_id, 'new_status': status}

# НОВЫЙ: Удаление заказа
@router.delete('/orders/{order_id}')
def api_delete_order(order_id: int):
    """Удалить заказ (только со статусом 'выдан')"""
    success = delete_order_if_completed(order_id)
    if not success:
        raise HTTPException(400, detail="Order cannot be deleted (must have status 'выдан')")
    
    return {'ok': True, 'deleted_order_id': order_id}