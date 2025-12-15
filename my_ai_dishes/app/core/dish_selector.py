"""
Упрощенный селектор - только базовый выбор
Работает с DishWithScore и QueryAnalysis
"""
import json
from typing import List, Dict, Any
from ..models.schemas import DishWithScore, PipelineContext
from ..utils.advanced_llm_client import AdvancedLLMClient


class DishSelector:
    """
    Упрощенный селектор с fallback на простой выбор
    """
    
    def __init__(self):
        self.llm_client = AdvancedLLMClient()
        print("[Selector] Упрощенный селектор инициализирован")
    
    def select_dishes(
        self,
        context: PipelineContext,
        mini_context: str,
        max_dishes_per_task: int = 3
    ) -> List[DishWithScore]:
        """
        Простой выбор блюд с fallback
        """
        if not context.search_results:
            return []
        
        print(f"[Selector] Мини-контекст: '{mini_context}'")
        
        # Пробуем использовать LLM
        try:
            selected_names = self._try_llm_selection(context, mini_context)
            if selected_names:
                dishes = self._find_dishes_by_names(selected_names, context)
                if dishes:
                    print(f"[Selector] LLM выбрал {len(dishes)} блюд")
                    return dishes[:max_dishes_per_task * 2]
        except Exception as e:
            print(f"[Selector] LLM выбор не удался: {e}")
        
        # Fallback: простой выбор по релевантности
        return self._simple_fallback_selection(context, max_dishes_per_task)
    
    def _try_llm_selection(self, context: PipelineContext, mini_context: str) -> List[str]:
        """Пробуем использовать LLM для выбора"""
        
        # Готовим данные для LLM (адаптировано для новой БД)
        dish_data = []
        for task_id, dishes in context.search_results.items():
            for dish in dishes[:8]:  # Ограничиваем
                # Используем только поля из новой БД
                dish_info = {
                    "name": dish.name,
                    "category": dish.category if dish.category else "Без категории",
                    "relevance": round(dish.relevance_score, 3),
                    "vegan": "веганское" if dish.vegan else "не веганское",
                    "spiciness": dish.spiciness.value,  # Используем свойство spiciness
                    "price": f"{dish.price:.2f} руб.",
                    # description нет в новой БД, используем комбинацию других полей
                    "details": f"{dish.category or 'Блюдо'}, {dish.spiciness.value} острота, {'веганское' if dish.vegan else 'не веганское'}"
                }
                dish_data.append(dish_info)
        
        system_message = """Ты - кулинарный эксперт. Выбери лучшие блюда по запросу.
        Верни ТОЛЬКО JSON массив с названиями выбранных блюд."""
        
        prompt = f"""
        Запрос пользователя: {context.original_query}
        
        Ключевые требования: {mini_context}
        
        Доступные блюда ({len(dish_data)} штук):
        {json.dumps(dish_data, ensure_ascii=False, indent=2)}
        
        Выбери 3-5 самых подходящих блюд. Учитывай:
        1. Релевантность запросу
        2. Соответствие ключевым требованиям
        3. Разнообразие категорий
        4. Цену (если это важно для запроса)
        
        Верни ТОЛЬКО JSON массив, например: ["Название1", "Название2"]
        """
        
        response = self.llm_client.call(
                messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                force_json=True
        )
        
        # Парсим результат
        try:
            selected = json.loads(response)
            if isinstance(selected, list):
                return selected[:5]
        except Exception as e:
            print(f"[Selector] Ошибка парсинга LLM ответа: {e}")
        
        return []
    
    def _find_dishes_by_names(self, names: List[str], context: PipelineContext) -> List[DishWithScore]:
        """Находит блюда по названиям"""
        found = []
        
        # Создаем словарь для быстрого поиска
        dish_map = {}
        for task_id, dishes in context.search_results.items():
            for dish in dishes:
                dish_map[dish.name.lower()] = dish
        
        # Ищем блюда по именам
        for name in names:
            lower_name = name.lower()
            if lower_name in dish_map:
                found.append(dish_map[lower_name])
            else:
                # Поиск частичного совпадения
                for dish_key, dish in dish_map.items():
                    if lower_name in dish_key or dish_key in lower_name:
                        found.append(dish)
                        break
        
        # Убираем дубликаты
        unique_dishes = []
        seen_names = set()
        for dish in found:
            if dish.name not in seen_names:
                seen_names.add(dish.name)
                unique_dishes.append(dish)
        
        return unique_dishes
    
    def _simple_fallback_selection(self, context: PipelineContext, max_count: int) -> List[DishWithScore]:
        """Простой выбор по релевантности"""
        all_dishes = []
        for task_id, dishes in context.search_results.items():
            all_dishes.extend(dishes)
        
        # Сортируем по релевантности
        all_dishes.sort(key=lambda x: x.relevance_score, reverse=True)
        
        selected = all_dishes[:max_count * 2]
        print(f"[Selector] Fallback выбрал {len(selected)} блюд")
        return selected