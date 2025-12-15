"""
Вторая ИИшка: Формирование финального ответа
Работает с DishWithScore и QueryAnalysis
"""
from typing import List, Dict, Any
from ..models.schemas import DishWithScore, PipelineContext
from ..utils.advanced_llm_client import AdvancedLLMClient


class ResponseFormatter:
    """Вторая ИИшка в цепочке"""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        if use_llm:
            self.llm_client = AdvancedLLMClient()
        print(f"[Formatter] ИИшка №2 инициализирована (LLM: {'ВКЛ' if use_llm else 'ВЫКЛ'})")
    
    def format_response(
        self,
        context: PipelineContext,
        selected_dishes: List[DishWithScore]
    ) -> Dict[str, Any]:
        """
        Формирует финальный ответ с помощью второй ИИшки
        """
        if not selected_dishes:
            return self._format_empty_response(context)
        
        if self.use_llm and hasattr(self, 'llm_client'):
            try:
                # Конвертируем DishWithScore в dict для LLM
                dishes_dicts = []
                for dish in selected_dishes:
                    dish_dict = dish.dict()
                    # Конвертируем SpicinessLevel enum в строку
                    dish_dict["spiciness"] = dish.spiciness.value
                    dishes_dicts.append(dish_dict)
                
                # Получаем мини-контекст из анализа
                mini_context = ""
                if context.analysis_result:
                    mini_context = context.analysis_result.mini_context
                
                # Используем вторую ИИшку
                response = self.llm_client.create_final_response(
                    user_query=context.original_query,
                    mini_context=mini_context,
                    dishes=dishes_dicts
                )
                
                return response
                
            except Exception as e:
                print(f"[Formatter] Ошибка LLM форматирования: {e}")
                return self._format_simple(context, selected_dishes)
        else:
            return self._format_simple(context, selected_dishes)
    
    def _format_simple(
        self,
        context: PipelineContext,
        dishes: List[DishWithScore]
    ) -> Dict[str, Any]:
        """Простой форматирование без LLM"""
        # Собираем статистику
        categories = list(set(d.category for d in dishes))
        vegan_count = sum(1 for d in dishes if d.vegan)
        
        # Определяем уровень остроты
        spiciness_levels = [d.spiciness.value for d in dishes]
        most_common_spiciness = max(set(spiciness_levels), key=spiciness_levels.count) if spiciness_levels else "неизвестно"
        
        return {
            "summary": f"Найдено {len(dishes)} блюд по запросу '{context.original_query}'",
            "recommendations": [
                {
                    "dish_name": dish.name,
                    "why_recommend": f"{dish.category} с оценкой релевантности {dish.relevance_score:.2f}. {dish.description[:80]}..."
                }
                for dish in dishes[:3]
            ],
            "total_found": len(dishes),
            "notes": "Используется упрощенный режим ответа",
            "dishes_count": len(dishes),
            "categories": categories,
            "vegan_options": vegan_count,
            "avg_spiciness": most_common_spiciness,
            "query_understood": context.analysis_result.mini_context if context.analysis_result else "да"
        }
    
    def _format_empty_response(self, context: PipelineContext) -> Dict[str, Any]:
        """Форматирование пустого ответа"""
        return {
            "summary": f"По запросу '{context.original_query}' ничего не найдено",
            "recommendations": [],
            "total_found": 0,
            "notes": "Попробуйте изменить формулировку запроса",
            "dishes_count": 0,
            "query_understood": context.analysis_result.mini_context if context.analysis_result else "нет"
        }