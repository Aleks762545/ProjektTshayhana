# app/core/validators.py
"""
Валидация и нормализация результата анализа запроса (QueryAnalysis).
Цели:
- Унифицировать имена полей (search_text_for_embeddings -> search_text)
- Надёжно нормализовать тип запроса, фильтры и компоненты
- Возвращать Pydantic-модель QueryAnalysis или корректный fallback
"""

from typing import Any, Dict, List
import logging
import sys
from pydantic import ValidationError
from app.models.schemas import QueryAnalysis

logger = logging.getLogger("validators")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Карта возможных значений типов запросов к каноническим
_QUERY_TYPE_MAP = {
    "search": "размытый",
    "vague": "размытый",
    "вэг": "размытый",
    "точный": "точный",
    "exact": "точный",
    "menu": "меню",
    "меню": "меню",
    "complex": "сложный",
    "сложный": "сложный",
    "размытый": "размытый"
}


def _normalize_query_type(value: Any) -> str:
    if not value:
        return "размытый"
    if isinstance(value, str):
        v = value.strip().lower()
        return _QUERY_TYPE_MAP.get(v, "размытый")
    return "размытый"


def _normalize_filters(value: Any) -> Dict[str, Any]:
    """
    Нормализует filters в словарь вида {"vegan": bool, "spiciness": "низкая"|"средняя"|"высокая", ...}
    Поддерживает вход в виде dict, list или str.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        out = dict(value)
        # Привести булевы/строковые представления к ожидаемым
        if "vegan" in out and isinstance(out["vegan"], str):
            out["vegan"] = out["vegan"].strip().lower() in ("true", "1", "yes", "да")
        if "spiciness" in out and isinstance(out["spiciness"], str):
            sp = out["spiciness"].strip().lower()
            if sp.startswith("выс") or "hot" in sp:
                out["spiciness"] = "высокая"
            elif "сред" in sp or "medium" in sp:
                out["spiciness"] = "средняя"
            else:
                out["spiciness"] = "низкая"
        return out
    if isinstance(value, list):
        out: Dict[str, Any] = {}
        for item in value:
            if isinstance(item, str):
                k = item.strip().lower()
                if k in ("vegan", "веган", "веганский"):
                    out["vegan"] = True
                elif k in ("spicy", "острый", "остр"):
                    out["spiciness"] = "высокая"
                else:
                    out[k] = True
        return out
    if isinstance(value, str):
        s = value.strip().lower()
        out: Dict[str, Any] = {}
        if "вег" in s or "vegan" in s:
            out["vegan"] = True
        if "остр" in s or "spicy" in s or "hot" in s:
            out["spiciness"] = "высокая"
        return out
    return {}


def _normalize_components(components: Any) -> List[Dict[str, Any]]:
    """
    Корректная нормализация components_needed:
    - Если LLM вернул список словарей — НЕ трогаем, только приводим ключи к str.
    - Если строки — превращаем в простые компоненты.
    - Никаких description/search_query_suggestion — это старый формат.
    """
    if not components:
        return []

    out = []

    if isinstance(components, list):
        for item in components:
            # ✅ LLM вернул правильный компонент → оставляем как есть
            if isinstance(item, dict):
                # Приводим ключи к строкам, но НЕ удаляем поля
                clean = {str(k): v for k, v in item.items()}
                out.append(clean)
            # ✅ Если строка → делаем простой компонент
            elif isinstance(item, str):
                s = item.strip()
                out.append({
                    "name": s,
                    "search_text": s,
                    "constraints": {},
                    "modifiers": {},
                    "count": 1,
                    "priority": 1
                })
            else:
                # fallback
                s = str(item)
                out.append({
                    "name": s,
                    "search_text": s,
                    "constraints": {},
                    "modifiers": {},
                    "count": 1,
                    "priority": 1
                })
        return out

    # Если пришёл один объект
    if isinstance(components, dict):
        return [{str(k): v for k, v in components.items()}]

    # Если пришла одна строка
    s = str(components)
    return [{
        "name": s,
        "search_text": s,
        "constraints": {},
        "modifiers": {},
        "count": 1,
        "priority": 1
    }]


def validate_query_analysis(raw: Dict[str, Any], original_query: str = "") -> QueryAnalysis:
    """
    Нормализует и валидирует словарь, полученный от SmartAnalyzer (LLM).
    Возвращает экземпляр QueryAnalysis. В случае ошибок возвращает безопасный fallback.
    """
    try:
        if not isinstance(raw, dict):
            raw = {}

        # Совместимость: старое имя поля -> новое
        if "search_text_for_embeddings" in raw and "search_text" not in raw:
            raw["search_text"] = raw.pop("search_text_for_embeddings")

        raw_qt = raw.get("query_type") or raw.get("type") or raw.get("kind")
        raw["query_type"] = _normalize_query_type(raw_qt)

        raw_filters = raw.get("filters", {})
        raw["filters"] = _normalize_filters(raw_filters)

        # components_needed normalization
        raw_components = raw.get("components_needed", [])
        raw["components_needed"] = _normalize_components(raw_components)

        # Trim and unify mini_context / search_text
        if "mini_context" in raw and isinstance(raw["mini_context"], str):
            raw["mini_context"] = raw["mini_context"].strip()
        if "search_text" in raw and isinstance(raw["search_text"], str):
            raw["search_text"] = raw["search_text"].strip()

        if not isinstance(raw.get("components_needed", []), list):
            raw["components_needed"] = []

        nd = raw.get("needs_decomposition")
        raw["needs_decomposition"] = bool(nd) if nd is not None else False

        # Ensure minimal fields for Pydantic model
        raw.setdefault("mini_context", "")
        raw.setdefault("search_text", "")
        raw.setdefault("ingredients", [])
        raw.setdefault("category", None)

        qa = QueryAnalysis(**raw)

        # Fill missing derived fields from original_query
        if not qa.mini_context:
            qa.mini_context = (raw.get("mini_context") or original_query or "").strip()
        if not qa.search_text:
            qa.search_text = qa.mini_context or original_query or ""

        return qa

    except ValidationError as e:
        logger.warning("QueryAnalysis validation failed: %s. Raw: %s", e, str(raw)[:800])
        try:
            fallback = QueryAnalysis(
                query_type="размытый",
                mini_context=(raw.get("mini_context") or original_query or "запрос"),
                search_text=(raw.get("search_text") or raw.get("mini_context") or original_query or ""),
                filters=raw.get("filters", {}) if isinstance(raw.get("filters", {}), dict) else {},
                needs_decomposition=True,
                components_needed=[]
            )
            return fallback
        except Exception as e2:
            logger.exception("Failed to build fallback QueryAnalysis: %s", e2)
            return QueryAnalysis(
                query_type="размытый",
                mini_context=original_query or "запрос",
                search_text=original_query or "",
                filters={},
                needs_decomposition=True,
                components_needed=[]
            )
    except Exception as e:
        logger.exception("Unexpected error validating QueryAnalysis: %s", e)
        return QueryAnalysis(
            query_type="размытый",
            mini_context=original_query or "запрос",
            search_text=original_query or "",
            filters={},
            needs_decomposition=True,
            components_needed=[]
        )
