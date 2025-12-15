# app/api/routes/ingredients.py
from fastapi import APIRouter, Body, HTTPException
from app.db.sqlite_db import list_ingredients, create_ingredient

router = APIRouter()

@router.get('/ingredients')
def api_list_ingredients():
    return list_ingredients()

@router.post('/ingredients')
def api_create_ingredient(payload: dict = Body(...)):
    name = payload.get('name')
    description = payload.get('description')
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    iid = create_ingredient(name, description)
    return {'id': iid, 'name': name, 'description': description}
