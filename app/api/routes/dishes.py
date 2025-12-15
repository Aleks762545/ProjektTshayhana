# app/api/routes/dishes.py
from fastapi import APIRouter, HTTPException, Body
from app.db.sqlite_db import list_dishes, get_dish, create_dish, update_dish, delete_dish
from app.vector.reindex import reindex_dish

router = APIRouter()

# =========================================================
# 🟢 ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: добавляем image_url
# =========================================================
def add_image_url(dish: dict):
    """
    Преобразует image_path из БД (формат: '/images/name.jpg') 
    в image_url для фронтенда (формат: '/static/images/name.jpg')
    """
    raw = dish.get("image_path", "")

    if raw:
        # Убираем ведущий слэш если есть, чтобы избежать дублирования
        path_without_leading_slash = raw.lstrip("/")
        # Преобразуем /images/name.jpg -> /static/images/name.jpg
        dish["image_url"] = f"/static/{path_without_leading_slash}"
    else:
        # Заглушка если нет картинки
        dish["image_url"] = "/static/images/no-image.png"

    return dish


# =========================================================
# 🟢 GET /dishes — список блюд
# =========================================================
@router.get('/dishes')
def api_list_dishes(category_id: int = None, spice_max: int = None,
                    is_vegan: bool = None, max_price: float = None):

    filters = {
        'category_id': category_id,
        'spice_max': spice_max,
        'is_vegan': is_vegan,
        'is_available': 1,
        'max_price': max_price
    }

    dishes = list_dishes(filters)

    # 🔥 ДОБАВЛЯЕМ image_url К КАЖДОМУ БЛЮДУ
    return [add_image_url(d) for d in dishes]


# =========================================================
# 🟢 GET /dishes/{id} — одно блюдо
# =========================================================
@router.get('/dishes/{id}')
def api_get_dish(id: int):
    d = get_dish(id)
    if not d:
        raise HTTPException(status_code=404, detail='not found')

    return add_image_url(d)


# =========================================================
# 🟢 POST /dishes — создать новое блюдо
# =========================================================
@router.post('/dishes')
def api_create_dish(payload: dict = Body(...)):
    if "name" not in payload or not payload["name"]:
        raise HTTPException(status_code=400, detail="Field 'name' is required")

    did = create_dish(payload)

    # reindex for semantic search
    try:
        reindex_dish(did)
    except Exception:
        pass

    dish = {"id": did, **payload}
    return add_image_url(dish)


# =========================================================
# 🟢 PUT /dishes/{id} — обновить блюдо
# =========================================================
@router.put('/dishes/{id}')
def api_update_dish(id: int, payload: dict = Body(...)):
    if not get_dish(id):
        raise HTTPException(status_code=404, detail='not found')

    update_dish(id, payload)

    try:
        reindex_dish(id)
    except Exception:
        pass

    dish = {"id": id, **payload}
    return add_image_url(dish)


# =========================================================
# 🟢 DELETE /dishes/{id} — удалить блюдо
# =========================================================
@router.delete('/dishes/{id}')
def api_delete_dish(id: int):
    delete_dish(id)
    from app.vector.vector_store import VECTOR_STORE
    try:
        VECTOR_STORE.delete(id)
    except Exception:
        pass

    return {'ok': True}
