"""
Первая ИИшка: Анализирует запрос и создает мини-контекст
Использует AdvancedLLMClient.analyze_query() и возвращает QueryAnalysis
"""
from ..models.schemas import QueryAnalysis, QueryType
from ..utils.advanced_llm_client import AdvancedLLMClient


class SmartAnalyzer:
    """Первая ИИшка - возвращает QueryAnalysis"""
    
    def __init__(self):
        self.llm_client = AdvancedLLMClient()
        print("[Analyzer] ИИшка №1 инициализирована")
    
    def analyze(self, user_query: str) -> QueryAnalysis:
        """Главный метод - возвращает QueryAnalysis"""
        print(f"[Analyzer] Анализируем: '{user_query}'")
        
        try:
            # Используем LLM для анализа
            llm_result = self.llm_client.analyze_query(user_query)
            
            # Конвертируем QueryType
            query_type_str = llm_result.get("query_type", "размытый")
            query_type = self._parse_query_type(query_type_str)
            
            # Проверяем нужна ли декомпозиция
            needs_decomposition = query_type in [QueryType.MENU, QueryType.COMPLEX]
            
            # Получаем компоненты для декомпозиции (если есть)
            components_needed = []
            if needs_decomposition:
                components_needed = self._create_components_from_analysis(llm_result)
            
            # Создаем QueryAnalysis
            analysis = QueryAnalysis(
                query_type=query_type,
                ingredients=llm_result.get("ingredients", []),
                category=llm_result.get("category"),
                filters=llm_result.get("filters", {}),
                mini_context=llm_result.get("mini_context", ""),
                search_text=llm_result.get("search_text_for_embeddings", user_query),
                needs_decomposition=needs_decomposition,
                components_needed=components_needed
            )
            
            print(f"[Analyzer] Мини-контекст: '{analysis.mini_context}'")
            print(f"[Analyzer] Тип запроса: {analysis.query_type}")
            print(f"[Analyzer] Декомпозиция: {'ДА' if needs_decomposition else 'НЕТ'}")
            
            return analysis
            
        except Exception as e:
            print(f"[Analyzer] Ошибка: {e}. Используем fallback...")
            return self._fallback_analysis(user_query)
    
    def _parse_query_type(self, query_type_str: str) -> QueryType:
        """Конвертирует строку в QueryType (из словаря)"""
        query_type_str = query_type_str.lower().strip()
        
        type_map = {
            "точный": QueryType.EXACT,
            "exact": QueryType.EXACT,
            "меню": QueryType.MENU,
            "menu": QueryType.MENU,
            "сложный": QueryType.COMPLEX,
            "complex": QueryType.COMPLEX,
            "размытый": QueryType.VAGUE,
            "vague": QueryType.VAGUE
        }
        
        return type_map.get(query_type_str, QueryType.VAGUE)
    
    def _create_components_from_analysis(self, llm_result: dict) -> list:
        """Создает компоненты для декомпозиции на основе анализа"""
        components = []
        
        # Если это меню (обед/ужин), создаем типовые компоненты
        if "обед" in llm_result.get("mini_context", "").lower():
            components = [
                {
                    "component_type": "закуска",
                    "description": "легкая закуска или салат",
                    "search_query_suggestion": "легкий салат или закуска"
                },
                {
                    "component_type": "основное",
                    "description": "основное блюдо",
                    "search_query_suggestion": llm_result.get("search_text_for_embeddings", "основное блюдо")
                },
                {
                    "component_type": "десерт", 
                    "description": "десерт",
                    "search_query_suggestion": "десерт"
                }
            ]
        elif "ужин" in llm_result.get("mini_context", "").lower():
            components = [
                {
                    "component_type": "основное",
                    "description": "основное блюдо для ужина",
                    "search_query_suggestion": llm_result.get("search_text_for_embeddings", "ужин")
                }
            ]
        
        return components
    
    def _fallback_analysis(self, user_query: str) -> QueryAnalysis:
        """Простой fallback анализ"""
        query_lower = user_query.lower()
        
        filters = {}
        if "веган" in query_lower:
            filters["vegan"] = True
        if "острый" in query_lower:
            filters["spiciness"] = "высокая"
        
        # Определяем тип (из словаря)
        query_type = QueryType.VAGUE
        if any(word in query_lower for word in ["обед", "ужин", "завтрак", "меню"]):
            query_type = QueryType.MENU
            needs_decomposition = True
        else:
            needs_decomposition = False
        
        # Мини-контекст (5-10 слов)
        words = [w for w in query_lower.split() if len(w) > 3]
        mini_context = ", ".join(words[:5]) if words else "общий запрос"
        
        return QueryAnalysis(
            query_type=query_type,
            ingredients=[],
            category=None,
            filters=filters,
            mini_context=mini_context,
            search_text=user_query,
            needs_decomposition=needs_decomposition,
            components_needed=[]
        )