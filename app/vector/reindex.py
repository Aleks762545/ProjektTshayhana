# app/vector/reindex.py
from app.db import sqlite_db
from app.vector.embeddings import get_embedding  # <-- Важно: импорт здесь
import logging

logger = logging.getLogger(__name__)

def build_doc_for_dish(did):
    """
    Возвращает словарь, содержащий поля для векторного индекса:
    { id: int, text: 'name description ingredients tags', metadata: {...} }
    """
    d = sqlite_db.get_dish(did)
    if not d:
        return None
    # flatten ingredients names
    ing_names = []
    for ing in d.get('ingredients', []):
        # ing can be dict with ingredient_name or ingredient_id etc.
        if isinstance(ing, dict):
            name = ing.get('ingredient_name') or ing.get('name')
            if name: ing_names.append(str(name))
    tag_names = [t.get('name') for t in d.get('tags', []) if isinstance(t, dict)]
    text = " ".join(filter(None, [d.get('name'), d.get('description'), " ".join(ing_names), " ".join(tag_names)]))
    metadata = {
        'id': d.get('id'),
        'price': d.get('price'),
        'category': d.get('category_name'),
        'image_path': d.get('image_path'),
        'is_vegan': d.get('is_vegan'),
    }
    return {'id': d.get('id'), 'text': text, 'metadata': metadata}

def reindex_dish(did):
    doc = build_doc_for_dish(did)
    if not doc:
        return False
    try:
        from app.vector.vector_store import VECTOR_STORE
    except Exception:
        VECTOR_STORE = None
    
    if VECTOR_STORE:
        try:
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: получаем embedding из текста
            text_for_embedding = doc['text']
            embedding = get_embedding(text_for_embedding)  # <-- Теперь работает правильно
            
            # Передаем embedding, а не текст
            VECTOR_STORE.upsert(doc['id'], embedding, doc['metadata'])
            logger.info(f"Successfully reindexed dish {did}")
            return True
        except Exception as e:
            logger.exception(f"Failed to upsert dish {did} into VECTOR_STORE: {e}")
            return False
    else:
        logger.info("VECTOR_STORE not available; reindex skipped for dish %s", did)
        return False

def reindex_all():
    dishes = sqlite_db.list_dishes({'is_available':1})
    n = 0
    for d in dishes:
        if reindex_dish(d['id']):
            n += 1
        else:
            logger.warning(f"Failed to reindex dish {d['id']}: {d.get('name')}")
    logger.info(f"Reindex completed: {n}/{len(dishes)} dishes indexed")
    return n