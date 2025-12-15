# app/ai/response.py
from typing import List

def format_dish_card(dish: dict) -> dict:
    """
    Приводим блюдо к удобному для фронта виду.
    """
    return {
        'id': dish.get('id'),
        'name': dish.get('name'),
        'description': dish.get('description'),
        'price': dish.get('price'),
        'image_url': dish.get('image_url') or (dish.get('image_path') and f"/static{dish.get('image_path')}") or None,
        'is_vegan': bool(dish.get('is_vegan')),
        'spice_level': dish.get('spice_level'),
        'category': dish.get('category_name') or dish.get('category_id'),
        'cooking_time': dish.get('cooking_time'),
        'score': dish.get('_score', 0)
    }

def build_short_text(parsed, suggestions: List[dict]) -> str:
    """
    Короткий текстовый ответ для чата.
    """
    if not suggestions:
        return "К сожалению, по вашему запросу ничего подходящего не найдено. Могу предложить посмотреть все наши блюда или уточнить запрос?"

    lines = []
    lines.append("Я нашёл несколько подходящих вариантов:")
    for d in suggestions[:5]:
        name = d.get('name')
        price = d.get('price')
        veg = ' (веган)' if d.get('is_vegan') else ''
        lines.append(f"• {name}{veg} — {price}₽")
    lines.append("Если хотите, могу добавить их в корзину или собрать комплект на обед/ужин.")
    return "\n".join(lines)

def build_response(parsed, raw_suggestions):
    # map dishes to cards
    suggestions = [format_dish_card(d) for d in raw_suggestions]
    text = build_short_text(parsed, suggestions)
    return {
        'message': text,
        'suggestions': suggestions,
        'parsed': parsed
    }
