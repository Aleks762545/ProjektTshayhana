from fastapi import APIRouter
from app.services.search_pipeline import search
router = APIRouter()

@router.post('/search')
def api_search(body: dict):
    q = body.get('q','')
    top_k = int(body.get('top_k',5))
    filters = body.get('filters', None)
    return search(q, top_k=top_k, filters=filters)
