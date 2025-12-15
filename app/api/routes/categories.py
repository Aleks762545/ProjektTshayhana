# app/api/routes/categories.py
from fastapi import APIRouter, Body, HTTPException
from app.db.sqlite_db import list_categories, create_category

router = APIRouter()

@router.get('/categories')
def api_list_categories():
    return list_categories()

@router.post('/categories')
def api_create_category(payload: dict = Body(...)):
    name = payload.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    cid = create_category(name)
    return {'id': cid, 'name': name}
