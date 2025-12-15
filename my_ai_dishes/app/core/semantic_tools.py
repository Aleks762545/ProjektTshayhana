# app/core/semantic_tools.py
"""
semantic_tools — семантические утилиты поверх EmbeddingSearch.

Задачи:
- semantic_category: укрупнённая категория запроса (Пицца / Суп / Салат / Десерт / Напиток / Основное блюдо)
- semantic_component: компонент запроса (пицца / суп / салат / десерт / напиток / основное / блюдо)
- semantic_search_text: компактный текст для эмбеддинг-поиска
- semantic_kind_for_dish: семантический тип блюда (pizza, soup, salad, dessert, drink, main, snack, other)
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional, Tuple

from app.core.embedding_search import EmbeddingSearch

logger = logging.getLogger("semantic_tools")
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    from logging import Formatter
    h.setFormatter(Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)


# ====== СИНГЛТОН ДОСТУП К EMBEDDINGSEARCH ===================================

@lru_cache(maxsize=1)
def get_embedding_search() -> EmbeddingSearch:
    """
    Ленивая инициализация EmbeddingSearch, чтобы не плодить экземпляры.
    """
    try:
        from app.core.local_embedder import local_embed
        es = EmbeddingSearch(local_model_callable=local_embed)
        logger.info("semantic_tools: EmbeddingSearch singleton инициализирован")
        return es
    except Exception as e:
        logger.exception("semantic_tools: не удалось инициализировать EmbeddingSearch: %s", e)
        return EmbeddingSearch(local_model_callable=None)


# ====== ВИРТУАЛЬНЫЕ КАТЕГОРИИ / ЯКОРЯ =======================================

_CATEGORY_ANCHORS = {
    "Пицца": "итальянская пицца, сырная корочка, пицца маргарита",
    "Суп": "горячий суп, тарелка супа, бульон",
    "Салат": "овощной салат, греческий салат, салат цезарь",
    "Десерт": "сладкий десерт, торт, чизкейк, тирамису",
    "Напиток": "напиток, чай, кофе, лимонад, коктейль, сок",
    "Основное блюдо": "горячее основное блюдо, мясо, рыба, паста, бургер, шаверма, буррито, лапша",
}

_COMPONENT_ANCHORS = {
    "пицца": "итальянская пицца, пицца маргарита, сырная пицца",
    "суп": "горячий суп, борщ, том ям, мисо суп",
    "салат": "свежий салат, овощной салат, греческий салат, салат цезарь",
    "десерт": "сладкий десерт, торт, чизкейк, тирамису, панна котта",
    "напиток": "напиток, лимонад, сок, чай, кофе, мохито",
    "основное": "основное блюдо, бургер, стейк, буррито, пад тай, фалафель, рататуй",
    "закуска": "закуска, сэндвич, кимчи, тапас, анти пасти",
    "блюдо": "какое-нибудь блюдо, еда, что-то поесть",
}

_DISH_KIND_ANCHORS = {
    "pizza": "пицца, итальянская пицца, маргарита, пицца пепперони",
    "soup": "суп, борщ, том ям, мисо суп, гаспачо",
    "salad": "салат, греческий салат, салат цезарь",
    "dessert": "десерт, чизкейк, тирамису, панна котта, торт",
    "drink": "напиток, лимонад, мохито, сок, чай, кофе",
    "main": "основное горячее блюдо, стейк, паста, буррито, пад тай, рататуй, фалафель, чаша будды",
    "snack": "закуска, сэндвич, тапас, кимчи, закуски к вину",
}


def _cosine(a, b):
    import numpy as np
    if a is None or b is None:
        return 0.0
    if a.size == 0 or b.size == 0:
        return 0.0
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(a @ b / (na * nb))


# ====== ОСНОВНЫЕ СЕМАНТИЧЕСКИЕ ФУНКЦИИ ======================================

def semantic_category(query: str) -> Optional[str]:
    """
    Возвращает одну из виртуальных категорий:
    'Пицца','Суп','Салат','Десерт','Напиток','Основное блюдо'
    или None, если ничего не похоже.
    Работает только на эмбеддингах.
    """
    text = (query or "").strip()
    if not text:
        return None

    es = get_embedding_search()
    qv = es.embed_text(text)
    if qv is None or qv.size == 0:
        return None

    best_cat = None
    best_score = 0.0

    for cat, anchor_text in _CATEGORY_ANCHORS.items():
        av = es.embed_text(anchor_text)
        score = _cosine(qv, av)
        if score > best_score:
            best_score = score
            best_cat = cat

    if best_score < 0.25:
        return None

    logger.info("semantic_tools: semantic_category '%s' -> %s (score=%.3f)", text, best_cat, best_score)
    return best_cat


def semantic_component(query: str) -> Tuple[str, float]:
    """
    Возвращает (имя_компонента, score).
    Компоненты: 'пицца','суп','салат','десерт','напиток','основное','закуска','блюдо'.
    Если ничего не похоже — fallback 'блюдо'.
    """
    text = (query or "").strip()
    if not text:
        return "блюдо", 0.0

    es = get_embedding_search()
    qv = es.embed_text(text)
    if qv is None or qv.size == 0:
        return "блюдо", 0.0

    best_comp = "блюдо"
    best_score = 0.0

    for name, anchor_text in _COMPONENT_ANCHORS.items():
        av = es.embed_text(anchor_text)
        score = _cosine(qv, av)
        if score > best_score:
            best_score = score
            best_comp = name

    logger.info("semantic_tools: semantic_component '%s' -> %s (score=%.3f)", text, best_comp, best_score)
    return best_comp, best_score


def semantic_search_text(query: str, fallback: str = "") -> str:
    """
    Пытается подобрать более осмысленный search_text для эмбеддинг-поиска.
    Стратегия минималистична: если запрос явно про пиццы/супы/салаты — возвращаем короткую формулировку.
    Если нет — возвращаем fallback или сам query.
    """
    text = (query or "").strip()
    low = text.lower()

    # простые явные случаи
    if "пицц" in low:
        return "пицца"
    if "суп" in low or "борщ" in low or "том ям" in low or "том-ям" in low or "гаспачо" in low:
        return "суп"
    if "салат" in low:
        return "салат"
    if "десерт" in low or "тирамису" in low or "чизкейк" in low or "панна котта" in low:
        return "десерт"
    if "чай" in low or "кофе" in low or "напиток" in low or "мохито" in low:
        return "напиток"

    if fallback:
        return fallback.strip()
    return text or "блюдо"


def semantic_kind_for_dish(dish_name: str, dish_description: str, dish_tags: list[str]) -> str:
    """
    Семантический тип блюда:
    'pizza','soup','salad','dessert','drink','main','snack','other'.
    Основан на эмбеддингах имени+описания+тегов.
    Не зависит от dish.category.
    """
    text_parts = [dish_name or "", dish_description or ""]
    if dish_tags:
        text_parts.extend(dish_tags)
    full_text = " ".join(text_parts).strip()
    if not full_text:
        return "other"

    es = get_embedding_search()
    qv = es.embed_text(full_text)
    if qv is None or qv.size == 0:
        return "other"

    best_kind = "other"
    best_score = 0.0

    for kind, anchor_text in _DISH_KIND_ANCHORS.items():
        av = es.embed_text(anchor_text)
        score = _cosine(qv, av)
        if score > best_score:
            best_score = score
            best_kind = kind

    logger.info("semantic_tools: semantic_kind_for_dish '%s' -> %s (score=%.3f)", dish_name, best_kind, best_score)
    return best_kind
