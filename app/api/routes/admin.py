from fastapi import APIRouter
from app.db.sqlite_db import init_db
from app.config import settings
from app.vector.reindex import reindex_all
router = APIRouter()

@router.post('/admin/init_db')
def api_init_db():
    sql_path = 'db/init.sql'
    init_db(sql_path)
    return {'ok': True}

@router.post('/admin/reindex')
def api_reindex():
    n = reindex_all()
    return {'indexed': n}
