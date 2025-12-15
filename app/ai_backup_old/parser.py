# app/ai/parser.py
import re

# Простая стоп-слова и сигнальные слова
MEAL_TIME_MAP = {
    'breakfast': ['breakfast', 'завтрак', 'утром'],
    'lunch': ['lunch', 'обед', 'днем', 'днем', 'днем'],
    'dinner': ['dinner', 'ужин', 'вечером']
}

DIET_TAGS = {
    'vegan': ['веган', 'вегетариан', 'вегетарианское', 'веганское'],
    'no_meat': ['постное', 'без мяса', 'безмясо', 'пост'],
    'spicy': ['остро', 'острый', 'специи']
}

def normalize_text(text: str) -> str:
    if not text:
        return ''
    t = text.lower()
    # keep letters, numbers, spaces, commas
    t = re.sub(r"[^a-zа-я0-9\s,]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def extract_ingredients_terms(text: str):
    """
    Выдираем сущности похожие на ингредиенты — слова/фразы после 'с', 'содержит', 'включая' и т.п.
    Также возвращаем набор токенов (однословных) для LIKE-поиска.
    """
    t = normalize_text(text)
    tokens = set(t.split())
    # ищем конструкции "с <x,y,z>" или "с <x>"
    ingreds = set()
    patterns = [
        r"с ([a-я0-9 ,]+)",
        r"состав(?:ляет|ляет)?[:\s]*([a-я0-9 ,]+)",
        r"(?:содержит|включает) ([a-я0-9 ,]+)"
    ]
    for p in patterns:
        for m in re.findall(p, t):
            parts = [x.strip() for x in re.split(r"[,\s]+", m) if x.strip()]
            for ppart in parts:
                if len(ppart) > 1:
                    ingreds.add(ppart)
    # additionally, treat single tokens that look like ingredient names (heuristic)
    return list(ingreds), list(tokens)

def detect_meal_time(text: str):
    t = normalize_text(text)
    for mt, variants in MEAL_TIME_MAP.items():
        for v in variants:
            if v in t:
                return mt
    return None

def detect_dietary_preferences(text: str):
    t = normalize_text(text)
    prefs = []
    for key, variants in DIET_TAGS.items():
        for v in variants:
            if v in t:
                prefs.append(key)
                break
    return prefs

def is_order_intent(text: str):
    t = normalize_text(text)
    return any(w in t for w in ['закажи', 'заказать', 'заказ', 'оформить', 'хочу', 'положите', 'добавь'])

def parse_user_message(text: str):
    """
    Возвращает dict:
      {
        'raw': text,
        'normalized': ...,
        'ingredients': [...],
        'tokens': [...],
        'meal_time': 'lunch'|'dinner'|... or None,
        'diet_prefs': [...],
        'is_order': bool
      }
    """
    norm = normalize_text(text)
    ingreds, tokens = extract_ingredients_terms(text)
    meal_time = detect_meal_time(text)
    diet_prefs = detect_dietary_preferences(text)
    order_intent = is_order_intent(text)
    return {
        'raw': text,
        'normalized': norm,
        'ingredients': ingreds,
        'tokens': tokens,
        'meal_time': meal_time,
        'diet_prefs': diet_prefs,
        'is_order': order_intent
    }
