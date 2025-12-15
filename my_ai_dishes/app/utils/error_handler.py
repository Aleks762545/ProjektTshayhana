"""
Обработка ошибок в пайплайне
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime

class PipelineErrorHandler:
    """Обработчик ошибок для пайплайна"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def log_error(self, stage: str, error: Exception, context: Dict = None):
        """Логирование ошибки"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.errors.append(error_data)
        print(f"[ERROR] {stage}: {error}")
    
    def log_warning(self, stage: str, message: str, context: Dict = None):
        """Логирование предупреждения"""
        warning_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "message": message,
            "context": context or {}
        }
        self.warnings.append(warning_data)
        print(f"[WARNING] {stage}: {message}")
    
    def get_fallback_response(self, user_query: str, error: Exception = None) -> Dict[str, Any]:
        """Возвращает fallback ответ при ошибке"""
        return {
            "dishes": [],
            "count": 0,
            "query_analysis": {"error": str(error) if error else "Неизвестная ошибка"},
            "metadata": {
                "summary": f"Извините, возникла ошибка при обработке запроса: '{user_query}'",
                "error": True,
                "suggestions": ["Попробуйте переформулировать запрос", "Повторите попытку позже"]
            }
        }
    
    def get_no_results_response(self, user_query: str) -> Dict[str, Any]:
        """Возвращает ответ когда ничего не найдено"""
        return {
            "dishes": [],
            "count": 0,
            "query_analysis": {"info": "Ничего не найдено"},
            "metadata": {
                "summary": f"По запросу '{user_query}' ничего не найдено",
                "error": False,
                "suggestions": [
                    "Попробуйте изменить формулировку",
                    "Используйте более общие термины",
                    "Уточните ингредиенты"
                ]
            }
        }
    
    def clear(self):
        """Очистка логов"""
        self.errors.clear()
        self.warnings.clear()