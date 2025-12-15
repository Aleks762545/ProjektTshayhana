"""
Декомпозитор - создает задачи поиска из анализа
"""
from typing import List
from ..models.schemas import QueryAnalysis, SearchTask


class TaskDecomposer:
    """Создает поисковые задачи из анализа запроса"""
    
    def decompose(self, analysis: QueryAnalysis) -> List[SearchTask]:
        """
        Разбивает сложный запрос на задачи поиска
        """
        print(f"[Decomposer] Декомпозиция запроса типа: {analysis.query_type}")
        
        tasks = []
        
        # Если есть готовые компоненты от анализатора
        if analysis.components_needed:
            for i, component in enumerate(analysis.components_needed[:5]):
                task = SearchTask(
                    id=f"task_{i}",
                    search_query=component.get("search_query_suggestion", 
                                             analysis.search_text),
                    description=component.get("description", f"компонент {i+1}"),
                    priority=i + 1
                )
                tasks.append(task)
                print(f"  → Задача {i+1}: {task.description} → '{task.search_query}'")
        
        # Если нет компонентов, создаем одну задачу
        elif analysis.needs_decomposition:
            # Для "обед из 3 блюд" создаем типовые задачи
            if "обед" in analysis.mini_context.lower():
                tasks = [
                    SearchTask(id="starter", search_query="легкий суп или салат", 
                             description="первое блюдо", priority=1),
                    SearchTask(id="main", search_query=analysis.search_text, 
                             description="основное блюдо", priority=2),
                    SearchTask(id="dessert", search_query="десерт", 
                             description="десерт", priority=3)
                ]
            else:
                # Одна задача на весь запрос
                tasks = [
                    SearchTask(id="main", search_query=analysis.search_text,
                             description="основное блюдо", priority=1)
                ]
        
        else:
            # Простой запрос - одна задача
            tasks = [
                SearchTask(id="main", search_query=analysis.search_text,
                         description="основное блюдо", priority=1)
            ]
        
        print(f"[Decomposer] Создано задач: {len(tasks)}")
        return tasks