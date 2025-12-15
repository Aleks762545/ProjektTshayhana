"""
УНИВЕРСАЛЬНЫЙ ПАЙПЛАЙН - исправленная версия
Использует ЕДИНЫЕ имена из словаря сущностей
"""
from typing import Dict, Any
from ..models.schemas import PipelineContext, SearchResponse, DishWithScore, QueryAnalysis
from .smart_analyzer import SmartAnalyzer
from .task_decomposer import TaskDecomposer
from .embedding_search import EmbeddingSearch
from .dish_selector import DishSelector
from .response_formatter import ResponseFormatter
from ..utils.error_handler import PipelineErrorHandler


class UniversalPipeline:
    """
    Универсальный пайплайн для обработки запросов
    
    Архитектура:
    1. SmartAnalyzer (ИИ №1) → QueryAnalysis + mini_context
    2. TaskDecomposer → List[SearchTask]
    3. EmbeddingSearch → поиск блюд
    4. DishSelector → выбор лучших
    5. ResponseFormatter (ИИ №2) → финальный ответ
    """
    
    def __init__(self, use_llm_for_formatting: bool = True):
        print("[Pipeline] Инициализация с исправленными типами...")
        
        # Компоненты (из словаря)
        self.analyzer = SmartAnalyzer()
        self.decomposer = TaskDecomposer()
        self.searcher = EmbeddingSearch()
        self.selector = DishSelector()
        self.formatter = ResponseFormatter(use_llm_for_formatting)
        self.error_handler = PipelineErrorHandler()
        
        # Статистика
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "avg_processing_time": 0
        }
        
        # Проверка работы analyzer
        try:
            test_query = "тестовый запрос на анализ"
            test_result = self.analyzer.analyze(test_query)
            
            if isinstance(test_result, QueryAnalysis):
                print("[Pipeline] ✅ SmartAnalyzer возвращает QueryAnalysis")
                print(f"[Pipeline] Тест: мини-контекст = '{test_result.mini_context}'")
            else:
                print(f"[Pipeline] ⚠️ SmartAnalyzer возвращает {type(test_result)}")
                
        except Exception as e:
            print(f"[Pipeline] ⚠️ Ошибка теста: {e}")
    
    def process_query(self, user_query: str, max_results: int = 10) -> SearchResponse:
        """Обработка запроса пользователя"""
        import time
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        print(f"\n{'='*70}")
        print(f"[Pipeline] Начало обработки: '{user_query}'")
        print(f"{'='*70}")
        
        # Инициализируем контекст (PipelineContext из словаря)
        context = PipelineContext(original_query=user_query)
        
        try:
            # ========== ШАГ 1: Анализ запроса ==========
            print("\n[1/5] Анализ запроса...")
            analysis_result = self.analyzer.analyze(user_query)
            context.analysis_result = analysis_result  # QueryAnalysis
            
            print(f"   → Мини-контекст: '{analysis_result.mini_context}'")
            print(f"   → Тип запроса: {analysis_result.query_type}")
            print(f"   → Фильтры: {analysis_result.filters}")
            
            # ========== ШАГ 2: Декомпозиция ==========
            print("\n[2/5] Декомпозиция...")
            search_tasks = self.decomposer.decompose(analysis_result)
            context.search_tasks = search_tasks  # List[SearchTask] - ЕДИНОЕ имя!
            
            print(f"   → Создано задач: {len(search_tasks)}")
            for i, task in enumerate(search_tasks):
                print(f"     {i+1}. '{task.description}' → '{task.search_query}'")
            
            # ========== ШАГ 3: Поиск блюд ==========
            print("\n[3/5] Поиск блюд через эмбеддинги...")
            context.search_results = {}  # Dict[str, List[DishWithScore]]
            
            for task in search_tasks:
                # Используем константу EMBEDDING_TOP_K из settings.py
                found_dishes = self.searcher.search_for_task(task, top_k=50)
                context.search_results[task.id] = found_dishes
            
            total_found = sum(len(dishes) for dishes in context.search_results.values())
            print(f"   → Всего найдено блюд: {total_found}")
            
            # ========== ШАГ 4: Выбор лучших блюд ==========
            print("\n[4/5] Выбор лучших блюд...")
            
            # Применяем базовые фильтры
            filtered_dishes = self._apply_basic_filters(context.search_results, analysis_result)
            
            # Если после фильтрации мало блюд, берем больше
            if len(filtered_dishes) < max_results:
                filtered_dishes = self._get_more_dishes(context.search_results, max_results * 2)
            
            # Выбираем лучшие блюда с учетом мини-контекста
            selected_dishes = self.selector.select_dishes(
                context=context,
                mini_context=analysis_result.mini_context,
                max_dishes_per_task=2
            )
            
            # Применяем окончательную фильтрацию
            final_dishes = self._apply_final_filters(selected_dishes, analysis_result)
            context.selected_dishes = final_dishes[:max_results]
            
            print(f"   → Выбрано блюд: {len(final_dishes)}")
            
            # ========== ШАГ 5: Форматирование ответа ==========
            print("\n[5/5] Форматирование ответа...")
            
            formatted_response = self.formatter.format_response(
                context=context,
                selected_dishes=final_dishes[:max_results]
            )
            
            # ========== ЗАВЕРШЕНИЕ ==========
            processing_time = time.time() - start_time
            print(f"\n✅ Обработка завершена за {processing_time:.2f} секунд")
            print(f"{'='*70}\n")
            
            # Обновляем статистику
            self.stats["successful_queries"] += 1
            self.stats["avg_processing_time"] = (
                (self.stats["avg_processing_time"] * (self.stats["successful_queries"] - 1) + processing_time) /
                self.stats["successful_queries"]
            )
            
            # Формируем финальный ответ (SearchResponse из словаря)
            return SearchResponse(
                dishes=final_dishes[:max_results],
                count=len(final_dishes[:max_results]),
                query_analysis={
                    "original_query": user_query,
                    "mini_context": analysis_result.mini_context,
                    "query_type": analysis_result.query_type.value,
                    "filters": analysis_result.filters,
                    "category": analysis_result.category
                },
                metadata={
                    **formatted_response,
                    "processing_time": round(processing_time, 2),
                    "pipeline_version": "universal_v2.0",
                    "tasks_count": len(search_tasks),
                    "stats": {
                        "total_found": total_found,
                        "selected": len(final_dishes[:max_results])
                    }
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.error_handler.log_error("pipeline", e, {"query": user_query})
            
            print(f"\n❌ Ошибка: {e}")
            print(f"   Время: {processing_time:.2f} секунд\n")
            
            return SearchResponse(
                dishes=[],
                count=0,
                query_analysis={
                    "error": str(e),
                    "original_query": user_query,
                    "success": False
                },
                metadata={
                    "summary": f"Ошибка обработки запроса: {user_query}",
                    "error": True,
                    "processing_time": round(processing_time, 2)
                }
            )
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def _apply_basic_filters(self, search_results: dict, analysis_result: QueryAnalysis) -> list:
        """Применяет базовые фильтры перед селектором"""
        all_dishes = []
        for task_id, dishes in search_results.items():
            for dish in dishes:
                if self._dish_matches_filters(dish, analysis_result):
                    all_dishes.append(dish)
        
        return all_dishes
    
    def _dish_matches_filters(self, dish: DishWithScore, analysis_result: QueryAnalysis) -> bool:
        """Проверяет соответствие блюда фильтрам"""
        filters = analysis_result.filters
        
        # Фильтр по вегану
        if "vegan" in filters and filters["vegan"] != dish.vegan:
            return False
        
        # Фильтр по остроте
        if "spiciness" in filters:
            requested_spiciness = filters["spiciness"]
            dish_spiciness = dish.spiciness.value  # SpicinessLevel enum
            
            # Маппинг остроты
            spiciness_levels = {
                "низкая": 1,
                "средняя": 2,
                "высокая": 3
            }
            
            req_level = spiciness_levels.get(requested_spiciness, 0)
            dish_level = spiciness_levels.get(dish_spiciness, 0)
            
            # Если запрошена высокая острота, а у блюда низкая - пропускаем
            if requested_spiciness == "высокая" and dish_spiciness != "высокая":
                return False
        
        # Фильтр по категории (если указана)
        if analysis_result.category and dish.category != analysis_result.category:
            return False
        
        return True
    
    def _get_more_dishes(self, search_results: dict, min_count: int) -> list:
        """Получает больше блюд если мало после фильтрации"""
        all_dishes = []
        for task_id, dishes in search_results.items():
            all_dishes.extend(dishes)
        
        # Сортируем по релевантности
        all_dishes.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_dishes[:min_count]
    
    def _apply_final_filters(self, dishes: list, analysis_result: QueryAnalysis) -> list:
        """Окончательная фильтрация"""
        filtered = []
        for dish in dishes:
            if self._dish_matches_filters(dish, analysis_result):
                filtered.append(dish)
        
        # Сортируем по релевантности
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)
        return filtered
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы пайплайна"""
        return {
            **self.stats,
            "architecture": "SmartAnalyzer → TaskDecomposer → EmbeddingSearch → DishSelector → ResponseFormatter",
            "components": {
                "SmartAnalyzer": "ИИ №1: анализ + мини-контекст",
                "TaskDecomposer": "создание поисковых задач",
                "EmbeddingSearch": "векторный поиск блюд",
                "DishSelector": "выбор лучших блюд",
                "ResponseFormatter": "ИИ №2: формирование ответа"
            }
        }