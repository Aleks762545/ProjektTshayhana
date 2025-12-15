# app/core/scoring.py
from typing import List
import logging
from app.models.schemas import DishWithScore
from app.utils.advanced_llm_client import AdvancedLLMClient
import math
import json

logger = logging.getLogger("scoring")
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

DEFAULT_WEIGHTS = {"vector": 0.6, "lexical": 0.3, "llm": 0.1}


def _norm_score(x):
    try:
        if x is None:
            return 0.0
        if 0.0 <= x <= 1.0:
            return float(x)
        # sigmoid fallback
        return 1.0 / (1.0 + math.exp(-float(x)))
    except Exception:
        return 0.0


def compute_relevance(dish: DishWithScore, weights: dict = None, requested_category: str | None = None) -> float:
    """
    Вычисляет relevance и применяет небольшой штраф, если категория блюда не совпадает с requested_category.
    requested_category: строка, например 'Салаты' или None.
    """
    w = weights or DEFAULT_WEIGHTS
    v = _norm_score(getattr(dish, "vector_score", 0.0))
    l = _norm_score(getattr(dish, "lexical_score", 0.0))
    llm = _norm_score(getattr(dish, "llm_rerank_score", 0.0))
    score = w.get("vector", 0.6) * v + w.get("lexical", 0.3) * l + w.get("llm", 0.1) * llm

    # Применяем штраф за несоответствие категории (умножаем на 0.75)
    try:
        if requested_category and getattr(dish, "category", None):
            dish_cat = str(getattr(dish, "category", "")).lower()
            if requested_category.lower() not in dish_cat:
                score = score * 0.75
    except Exception:
        # в случае ошибки — не применять штраф
        pass

    dish.relevance_score = float(score)
    return dish.relevance_score


def apply_reranker_llm(dishes: List[DishWithScore], llm_client: AdvancedLLMClient, timeout: int = 15) -> List[DishWithScore]:
    if not dishes:
        return dishes
    
    items = []
    for i, d in enumerate(dishes):
        # Используем только поля, доступные в новой БД
        item = {
            "idx": i,
            "name": d.name,
            "category": d.category if d.category else "",
            "price": d.price,
            "spiciness": d.spiciness.value,  # Используем свойство spiciness
            "vegan": d.vegan,  # Используем свойство vegan
            "vector_score": getattr(d, "vector_score", 0.0),
            "lexical_score": getattr(d, "lexical_score", 0.0)
        }
        items.append(item)
    
    prompt = (
        "Ранжируй список блюд по релевантности запросу. "
        "Вход: JSON array объектов с полями idx, name, category, price, spiciness, vegan, vector_score, lexical_score. "
        "Выход: JSON array объектов {\"idx\":int, \"score\":float} где score в диапазоне 0..1."
    )
    
    messages = [
        {"role": "system", "content": "Ты — кулинарный ранкер. Оцени релевантность каждого блюда на основе его характеристик."},
        {"role": "user", "content": f"{prompt}\n\nДанные: {json.dumps(items, ensure_ascii=False)}"}
    ]
    
    try:
        raw = llm_client.call(messages, temperature=0.0, force_json=True, timeout=timeout)
    except Exception as e:
        logger.warning("LLM reranker failed: %s", e)
        return dishes
    
    try:
        parsed = json.loads(raw)
        logger.debug("[scoring] reranker raw parsed: %s", parsed if isinstance(parsed, list) else str(parsed)[:1000])
        if isinstance(parsed, list):
            for entry in parsed:
                try:
                    idx = int(entry.get("idx"))
                    score = float(entry.get("score", 0.0))
                    if 0 <= idx < len(dishes):
                        try:
                            setattr(dishes[idx], "llm_rerank_score", max(0.0, min(1.0, score)))
                        except Exception:
                            try:
                                dishes[idx].__dict__["llm_rerank_score"] = max(0.0, min(1.0, score))
                            except Exception:
                                pass
                except Exception:
                    continue
    except Exception as e:
        logger.warning("Failed to parse reranker output: %s. Raw: %s", e, raw[:1000])
    
    return dishes