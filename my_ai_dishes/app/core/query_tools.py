# app/core/query_tools.py
"""
Инструменты для SmartAnalyzer:
- извлечение глобальных модификаторов из текста
- классификация типа запроса
- семантическая/структурная декомпозиция на компоненты
- построение ComponentSpec-подобных структур
- нормализация фильтров
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.schemas import QueryType
from app.core.semantic_tools import semantic_category, semantic_component, semantic_search_text

logger = logging.getLogger("query_tools")
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    from logging import Formatter
    h.setFormatter(Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)


# ===================== ГЛОБАЛЬНЫЕ МОДИФИКАТОРЫ ==============================

def extract_global_modifiers(user_query: str) -> Dict[str, float]:
    text = (user_query or "").lower()
    modifiers: Dict[str, float] = {}

    if any(p in text for p in ["не острый", "не остро", "не острые", "совсем не остро"]):
        modifiers["spiciness_level"] = 0.0
    elif any(p in text for p in ["очень острый", "супер острый", "максимально острый"]):
        modifiers["spiciness_level"] = 1.0
    elif any(p in text for p in ["острый", "острое", "острые", "пикантный"]):
        modifiers["spiciness_level"] = 0.8

    if any(p in text for p in ["веган", "веганский", "вегетарианский", "без мяса", "безмясной"]):
        modifiers["vegan"] = 1.0

    if any(p in text for p in ["дешевый", "подешевле", "недорогой", "подешевке", "бюджетный"]):
        modifiers["cheapness"] = 1.0
    if any(p in text for p in ["дорогой", "премиум", "люксовый", "элитный"]):
        modifiers.setdefault("cheapness", 0.0)

    return modifiers


# ===================== ТИП ЗАПРОСА ==========================================

def classify_query_type(user_query: str) -> QueryType:
    text = (user_query or "").lower()

    if any(w in text for w in ["обед", "ужин", "комбо", "набор", "сет", "меню"]):
        return QueryType.MENU

    if any(w in text for w in [" и ", " с ", " без ", " или "]) and any(
        w in text for w in ["суп", "салат", "десерт", "напиток", "основное", "закуска"]
    ):
        return QueryType.COMPLEX

    tokens = text.split()
    if len(tokens) <= 3:
        return QueryType.EXACT

    return QueryType.VAGUE


# ===================== КОМПОНЕНТЫ / ДЕКОМПОЗИЦИЯ ============================

def detect_components(
    user_query: str,
    query_type: QueryType,
    category: Optional[str],
    global_modifiers: Dict[str, float],
) -> Dict[str, Any]:
    """
    Семантический detect_components.

    Источники:
    - query_type (MENU / COMPLEX / EXACT / VAGUE)
    - semantic_category(user_query)
    - semantic_component(user_query)

    Правила:
    - MENU → несколько логических компонентов (основное, салат, напиток, десерт)
    - COMPLEX → пытаемся вычленить несколько компонентов, но без хардкода по словам
      (на данном этапе просто обозначаем минимальный набор)
    - EXACT / VAGUE → один главный компонент, определённый semantic_component
    """

    text = (user_query or "").strip()
    words = text.split()

    result: Dict[str, Any] = {
        "needs_decomposition": False,
        "components": [],
    }

    # Семантическая категория / компонент
    sem_cat = category or semantic_category(text)
    sem_comp, comp_score = semantic_component(text)

    # 1. Меню / обед / ужин → несколько компонентов (структурная логика)
    if query_type == QueryType.MENU:
        comps: List[str] = ["основное", "салат"]
        # напиток и десерт добавляем по желанию через текст
        lower = text.lower()
        if any(w in lower for w in ["напиток", "попить", "напитки", "мохито"]):
            comps.append("напиток")
        if any(w in lower for w in ["десерт", "сладкое", "что-то сладкое", "торт", "чизкейк", "тирамису"]):
            comps.append("десерт")

        result["needs_decomposition"] = True
        result["components"] = comps
        return result

    # 2. COMPLEX — несколько частей; пока не режем по словам, просто говорим: минимум основное + салат
    if query_type == QueryType.COMPLEX:
        # В будущем тут можно сделать семантический сплит по частям, но сейчас — структурный минимум
        result["needs_decomposition"] = True
        result["components"] = ["основное", "салат"]
        return result

    # 3. EXACT / VAGUE — один главный компонент по семантике
    # Если semantic_component дал что-то осмысленное (не "блюдо") — используем его
    if sem_comp != "блюдо" and comp_score >= 0.25:
        result["needs_decomposition"] = False
        result["components"] = [sem_comp]
        return result

    # 4. Если semantic_component не дал ничего уверенного → fallback на семантическую категорию
    if sem_cat:
        low_cat = sem_cat.lower()
        if "пицца" in low_cat:
            result["components"] = ["пицца"]
        elif "салат" in low_cat:
            result["components"] = ["салат"]
        elif "суп" in low_cat:
            result["components"] = ["суп"]
        elif "десерт" in low_cat:
            result["components"] = ["десерт"]
        elif "напиток" in low_cat:
            result["components"] = ["напиток"]
        else:
            result["components"] = ["основное"]

        result["needs_decomposition"] = False
        return result

    # 5. Короткие запросы (2–3 слова) — всё равно попробуем semantic_component
    if len(words) <= 3 and sem_comp:
        result["components"] = [sem_comp]
        result["needs_decomposition"] = False
        return result

    # 6. Fallback — один компонент "блюдо"
    result["components"] = ["блюдо"]
    result["needs_decomposition"] = False
    return result


def build_component_specs(
    component_names: List[str],
    user_query: str,
    global_modifiers: Dict[str, float],
    category: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Строит словари, совместимые с ComponentSpec:
    {name, search_text, constraints, modifiers, count, priority}

    Источники:
    - имя компонента (пицца / салат / суп / десерт / напиток / основное / закуска / блюдо)
    - semantic_search_text(user_query) — для общих запросов
    - global_modifiers (острое, веган, дешёвое)
    """

    text = (user_query or "").lower()
    specs: List[Dict[str, Any]] = []

    for idx, name in enumerate(component_names):
        base_name = name.strip().lower()

        # 1. Определяем базовый поисковый текст по типу компонента
        if base_name in ("пицца", "pizza"):
            search_text = "пицца"
        elif base_name in ("основное", "главное", "горячее", "main"):
            search_text = "основное блюдо"
        elif base_name in ("салат", "salad", "салаты"):
            search_text = "салат"
        elif base_name in ("напиток", "напитки", "drink"):
            search_text = "напиток"
        elif base_name in ("десерт", "desert", "десерты", "сладкое"):
            search_text = "десерт"
        elif base_name in ("суп", "soups", "супы"):
            search_text = "суп"
        elif base_name in ("закуска", "закуски", "snack"):
            search_text = "закуска"
        else:
            # fallback — semantic_search_text для всего запроса
            search_text = semantic_search_text(user_query, fallback=name)

        # 2. modifiers: стартуем с глобальных
        modifiers = dict(global_modifiers)

        # пример мягкого правила: для салата не форсить адскую остроту, если явно не просили
        if base_name == "салат" and "салат" in text:
            if "острый салат" not in text:
                if modifiers.get("spiciness_level", 0.0) > 0.7:
                    modifiers["spiciness_level"] = 0.4

        constraints: Dict[str, Any] = {}

        specs.append(
            {
                "name": name,
                "search_text": search_text,
                "constraints": constraints,
                "modifiers": modifiers,
                "count": 1,
                "priority": idx + 1,
            }
        )

    return specs


# ===================== ФИЛЬТРЫ ==============================================

def normalize_filters(raw_filters: Any, global_modifiers: Dict[str, float]) -> Dict[str, Any]:
    from app.core.validators import _normalize_filters as _base_norm

    try:
        base = _base_norm(raw_filters)
    except Exception:
        base = {}

    if "vegan" in global_modifiers and global_modifiers["vegan"] >= 0.5:
        base["vegan"] = True

    return base
