# app/api/routes/tags.py
from fastapi import APIRouter, Body, HTTPException
from app.db.sqlite_db import list_tags, create_tag

router = APIRouter()

@router.get('/tags')
def api_list_tags():
    return list_tags()

@router.post('/tags')
def api_create_tag(payload: dict = Body(...)):
    name = payload.get('name')
    tag_type = payload.get('tag_type')
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    tid = create_tag(name, tag_type)
    return {'id': tid, 'name': name, 'tag_type': tag_type}
