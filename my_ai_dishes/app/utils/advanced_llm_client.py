# app/utils/advanced_llm_client.py
"""
Унифицированный клиент для LLM (LM Studio / совместимые API).
Этот модуль предоставляет единый интерфейс для всех компонентов пайплайна:
- analyze(user_query) / analyze_query(user_query)  -> dict (анализ запроса)
- create_final_response(user_query, mini_context, dishes) -> dict (финальный ответ)
- call(messages, ...) -> str (низкоуровневый вызов, возвращает текст или JSON-строку при force_json=True)

Ключевые цели:
- Надёжная обработка разных форматов ответа от сервера (body["choices"]... или raw text)
- force_json: извлечение и валидация JSON из произвольного текста
- fallback-логика при недоступности LLM
- логирование входов/выходов для отладки
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
import requests

# Конфигурационные константы импортируются из app.config или app.settings в проекте.
# Если у вас другие имена — замените импорты в проекте или здесь.
try:
    from ..config import LM_CHAT_URL, LM_MODEL, LM_STUDIO_AVAILABLE
except Exception:
    # Безопасные дефолты, если импорт не удался при раннем этапе тестирования
    LM_CHAT_URL = "http://localhost:8000/v1/chat/completions"
    LM_MODEL = "local-model"
    LM_STUDIO_AVAILABLE = False

logger = logging.getLogger("advanced_llm_client")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class AdvancedLLMClient:
    """
    Универсальный клиент для LLM.
    Используйте методы:
      - analyze(user_query) -> Dict[str, Any]
      - create_final_response(user_query, mini_context, dishes) -> Dict[str, Any]
      - call(messages, temperature=..., force_json=False, timeout=...) -> str
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        available: Optional[bool] = None,
    ):
        self.session = session or requests.Session()
        self.model = model or LM_MODEL or "local-model"
        self.base_url = base_url or LM_CHAT_URL
        # Флаг доступности LLM можно переопределить извне (например, при тестах)
        self.available = LM_STUDIO_AVAILABLE if available is None else bool(available)
        logger.info("AdvancedLLMClient initialized (base_url=%s, model=%s, available=%s)", self.base_url, self.model, self.available)

    # ----------------- Высокоуровневые адаптеры -----------------

    def analyze(self, user_query: str) -> Dict[str, Any]:
        """Совместимый адаптер: вызывает analyze_query и возвращает dict."""
        return self.analyze_query(user_query)

    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        Первая ИИшка: анализ запроса. Возвращает словарь с ключами:
          - query_type
          - ingredients
          - category
          - filters
          - search_text (унифицированное поле для поиска эмбеддингами)
          - mini_context
          - components_needed (опционально)
          - needs_decomposition (опционально)
        Если LLM недоступен или ответ некорректен — возвращается fallback-анализ.
        """
        logger.info("[LLM] analyze_query: %s", user_query)
        if not self.available:
            logger.warning("[LLM] analyze_query: LLM not available, using fallback")
            return self._fallback_analysis(user_query)

        system_message = (
            "Ты анализируешь кулинарные запросы. ВЕРНИ ТОЛЬКО JSON.\n\n"
            "ПОЛЯ (строго):\n"
            " - query_type: one of ['точный','размытый','меню']\n"
            " - ingredients: list of strings\n"
            " - category: string or null\n"
            " - filters: object, e.g. {\"vegan\": true, \"spiciness\": \"высокая\"}\n"
            " - search_text: короткая фраза для поиска эмбеддингами (2-4 слова)\n"
            " - mini_context: 3-5 ключевых слов через запятую\n"
            " - components_needed: optional list of components (each string or object)\n"
            " - needs_decomposition: optional boolean\n\n"
            "Примеры входа/выхода:\n"
            ' "острый суп" -> {"query_type":"точный","ingredients":["суп"],"category":null,'
            '"filters":{"vegan":false,"spiciness":"высокая"},"search_text":"острый суп","mini_context":"острый, суп"}\n\n'
            "ВЕРНИ ТОЛЬКО JSON БЕЗ ЛИШНЕГО ТЕКСТА."
        )

        user_prompt = f'Запрос: "{user_query}"\n\nСтрого верни JSON, соответствующий описанной схеме.'

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw = self.call(messages, temperature=0.1, force_json=True, timeout=20)
            logger.debug("[LLM] analyze_query raw: %s", raw[:2000])
            parsed = json.loads(raw)
            # Унификация: если LLM вернул старое имя поля — переименуем
            if "search_text_for_embeddings" in parsed and "search_text" not in parsed:
                parsed["search_text"] = parsed.pop("search_text_for_embeddings")
            # Минимальная валидация обязательных полей
            if not isinstance(parsed, dict) or "query_type" not in parsed or "mini_context" not in parsed:
                logger.warning("[LLM] analyze_query: invalid structure, using fallback")
                return self._fallback_analysis(user_query)
            # Гарантируем поля
            parsed.setdefault("ingredients", [])
            parsed.setdefault("category", None)
            parsed.setdefault("filters", {"vegan": False, "spiciness": "низкая"})
            parsed.setdefault("search_text", parsed.get("mini_context") or user_query)
            parsed.setdefault("components_needed", [])
            parsed.setdefault("needs_decomposition", False)
            # Небольшие исправления по ключевым словам
            qlow = user_query.lower()
            if "веган" in qlow:
                parsed["filters"]["vegan"] = True
            if "остр" in qlow:
                parsed["filters"]["spiciness"] = parsed["filters"].get("spiciness", "низкая") or "высокая"
            # Возвращаем унифицированный результат
            return parsed
        except Exception as e:
            logger.exception("[LLM] analyze_query failed: %s", e)
            return self._fallback_analysis(user_query)

    def create_final_response(self, user_query: str, mini_context: str, dishes: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("[LLM] create_final_response for: %s", user_query)
        if not self.available:
            logger.warning("[LLM] create_final_response: LLM not available, using fallback")
            return self._fallback_response(user_query, dishes)

        # Подготовка компактной информации о блюдах (топ-3)
        dishes_info = []
        for d in (dishes or [])[:3]:
            dishes_info.append({
                "name": d.get("name", ""),
                "category": d.get("category", ""),
                "description": (d.get("description") or "")[:120],
                "vegan": bool(d.get("vegan", False)),
                "spiciness": d.get("spiciness", "низкая"),
                "relevance": round(float(d.get("relevance_score", 0.0)), 2) if d.get("relevance_score") is not None else 0.0
            })

        system_message = (
            "Ты кулинарный помощник. ВЕРНИ ТОЛЬКО JSON со следующей схемой:\n"
            "{'summary': str, 'recommendations': [{'dish_name': str, 'why_recommend': str}], 'total_found': int, 'notes': str}\n"
            "Пример: {\"summary\":\"...\",\"recommendations\":[{\"dish_name\":\"...\",\"why_recommend\":\"...\"}],\"total_found\":2,\"notes\":\"\"}\n"
            "Если не можешь — верни пустой объект с полем 'status':'fallback'."
        )

        user_prompt = (
            f"Запрос: {user_query}\n"
            f"Контекст: {mini_context}\n"
            f"Найденные блюда: {json.dumps(dishes_info, ensure_ascii=False)}\n\n"
            "Сформируй краткий полезный ответ в указанном JSON-формате."
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        # Параметры: сначала умеренная температура и нормальный таймаут
        try:
            raw = self.call(messages, temperature=0.2, force_json=True, timeout=30)
            logger.debug("[LLM] create_final_response raw (attempt1): %s", raw[:2000])
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "summary" in parsed:
                parsed["dishes_count"] = len(dishes or [])
                parsed["query_understood"] = mini_context or "да"
                return parsed
            # если структура невалидна — логируем и пробуем retry
            logger.warning("[LLM] create_final_response: invalid structure on attempt1. Raw snippet: %s", raw[:800])
        except Exception as e:
            logger.warning("[LLM] create_final_response attempt1 failed: %s", e)

        # --- Retry: упрощённый prompt, нулевая температура, увеличенный таймаут ---
        try:
            retry_system = "Ты кулинарный помощник. ВЕРНИ СТРОГО JSON с полем 'summary' и 'recommendations'. БЕЗ ЛИШНЕГО ТЕКСТА."
            retry_user = f"Коротко: запрос: {user_query}. Контекст: {mini_context}. Блюда: {json.dumps(dishes_info, ensure_ascii=False)}"
            retry_messages = [
                {"role": "system", "content": retry_system},
                {"role": "user", "content": retry_user}
            ]
            raw2 = self.call(retry_messages, temperature=0.0, force_json=True, timeout=40)
            logger.debug("[LLM] create_final_response raw (retry): %s", raw2[:2000])
            parsed2 = json.loads(raw2)
            if isinstance(parsed2, dict) and "summary" in parsed2:
                parsed2["dishes_count"] = len(dishes or [])
                parsed2["query_understood"] = mini_context or "да"
                return parsed2
            logger.warning("[LLM] create_final_response: invalid structure on retry. Raw snippet: %s", raw2[:800])
        except Exception as e:
            logger.warning("[LLM] create_final_response retry failed: %s", e)

        # Если оба варианта не сработали — возвращаем fallback, но логируем оба ответа (если есть)
        logger.warning("[LLM] create_final_response: both attempts failed, returning fallback")
        return self._fallback_response(user_query, dishes)

    # ----------------- Низкоуровневые вызовы -----------------

    def _post_payload(self, payload: Dict[str, Any], timeout: int = 60) -> str:
        """
        Отправляет payload на self.base_url и возвращает текстовый контент.
        Поддерживает разные форматы ответа (OpenAI-like или raw text).
        """
        resp = self.session.post(self.base_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        body = resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else None
        if isinstance(body, dict):
            # Попробуем стандартную структуру
            try:
                return body["choices"][0]["message"]["content"].strip()
            except Exception:
                # fallback: если структура другая — вернуть текстовое тело
                return json.dumps(body, ensure_ascii=False)
        return resp.text.strip()

    def _extract_json_from_text(self, text: str) -> str:
        """
        Надёжный извлекатель JSON-объекта или JSON-массива из произвольного текста.
        Ищет первый '{' или '[' и затем находит соответствующую закрывающую скобку по балансу.
        Возвращает JSON-строку или fallback JSON при неудаче.
        """
        if not text or not isinstance(text, str):
            return '{"status":"fallback","message":"Empty response from LLM"}'

        # Убираем управляющие пробелы в начале/конце
        txt = text.strip()

        # Найдём все возмож стартовые позиции для '{' и '['
        starts = []
        obj_pos = txt.find('{')
        arr_pos = txt.find('[')
        if obj_pos != -1:
            starts.append((obj_pos, '{', '}'))
        if arr_pos != -1:
            starts.append((arr_pos, '[', ']'))

        # Если ничего не найдено — fallback
        if not starts:
            logger.warning("[LLM] _extract_json_from_text: no JSON start found. Snippet: %s", txt[:300])
            return '{"status":"fallback","message":"Не удалось извлечь JSON"}'

        # Попробуем каждый старт (объект/массив), начиная с ближайшего к началу
        for start_idx, open_ch, close_ch in sorted(starts, key=lambda x: x[0]):
            depth = 0
            for i in range(start_idx, len(txt)):
                ch = txt[i]
                if ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        candidate = txt[start_idx:i+1]
                        try:
                            # Проверяем валидность JSON
                            json.loads(candidate)
                            return candidate
                        except Exception:
                            # если невалиден — продолжаем искать (возможно вложенные структуры)
                            continue
            # если цикл закончился без возврата — пробуем следующий старт
        logger.warning("[LLM] _extract_json_from_text: failed to parse JSON from response. Snippet: %s", txt[:400])
        return '{"status":"fallback","message":"Не удалось извлечь JSON"}'

    def call(self, messages: List[Dict[str, Any]], temperature: float = 0.1,
             max_tokens: int = 500, force_json: bool = False, timeout: int = 60) -> str:
        """
        Универсальный вызов LLM.
        - messages: список сообщений в формате {"role": "...", "content": "..."}
        - force_json: если True — пытаемся извлечь JSON из ответа и вернуть JSON-строку
        Возвращает строку (либо текст, либо JSON-строку).
        """
        if not self.available:
            logger.warning("[LLM] call: LLM not available, returning fallback")
            return json.dumps({"error": "LLM недоступен"}, ensure_ascii=False)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        try:
            logger.debug("[LLM] call payload keys: %s", list(payload.keys()))
            content = self._post_payload(payload, timeout=timeout)
            logger.debug("[LLM] call received content length: %d", len(content) if content else 0)
            if force_json:
                return self._extract_json_from_text(content)
            return content
        except requests.exceptions.Timeout as e:
            logger.error("[LLM] call timeout after %s seconds", timeout)
            raise Exception(f"Таймаут {timeout} секунд при вызове LLM: {e}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            logger.error("[LLM] HTTP error: %s", status)
            raise
        except Exception as e:
            logger.exception("[LLM] call failed: %s", e)
            raise

    # ----------------- Вспомогательные fallback методы -----------------

    def _fallback_analysis(self, user_query: str) -> Dict[str, Any]:
        """Простой rule-based fallback для анализа запроса."""
        q = (user_query or "").lower()
        filters = {"vegan": False, "spiciness": "низкая"}
        if "веган" in q:
            filters["vegan"] = True
        if "остр" in q:
            filters["spiciness"] = "высокая"

        query_type = "размытый"
        if any(w in q for w in ["суп", "салат", "паста", "курица", "рис", "десерт", "пицца"]):
            query_type = "точный"
        if any(w in q for w in ["обед", "ужин", "завтрак", "меню"]):
            query_type = "меню"

        words = [w for w in q.split() if len(w) > 2]
        mini_context = ", ".join(words[:3]) if words else "запрос"
        search_words = [w for w in words if w not in ["веган", "острый", "легкий", "вкусный"]]
        search_text = " ".join(search_words[:3]) if search_words else q

        return {
            "query_type": query_type,
            "ingredients": [],
            "category": None,
            "filters": filters,
            "search_text": search_text,
            "mini_context": mini_context,
            "components_needed": [],
            "needs_decomposition": True
        }

    def _fallback_response(self, user_query: str, dishes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback форматирования ответа без LLM."""
        return {
            "summary": f"Найдено {len(dishes or [])} блюд по запросу '{user_query}'",
            "recommendations": [
                {
                    "dish_name": d.get("name", ""),
                    "why_recommend": f"{d.get('category', 'блюдо')} с оценкой {d.get('relevance_score', 0):.2f}"
                } for d in (dishes or [])[:3]
            ],
            "total_found": len(dishes or []),
            "notes": "Используется fallback режим"
        }

    # ----------------- Совместимость со старым API -----------------
    # Некоторые модули могут вызывать старые имена методов; оставляем алиасы.

    def call_llm(self, messages: List[Dict[str, Any]], temperature: float = 0.1,
                 max_tokens: int = 500, force_json: bool = False, timeout: int = 60) -> str:
        """Алиас для backward compatibility"""
        return self.call(messages, temperature=temperature, max_tokens=max_tokens, force_json=force_json, timeout=timeout)

    def analyze_query_legacy(self, user_query: str) -> Dict[str, Any]:
        """Алиас для backward compatibility"""
        return self.analyze_query(user_query)
