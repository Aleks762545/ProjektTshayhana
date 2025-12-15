# app/models/schemas.py
"""
Pydantic модели с поддержкой инструментов (modifiers)
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


class QueryType(str, Enum):
    EXACT = "точный"
    VAGUE = "размытый"
    MENU = "меню"
    COMPLEX = "сложный"


class SpicinessLevel(str, Enum):
    LOW = "низкая"
    MEDIUM = "средняя"
    HIGH = "высокая"
    
    @classmethod
    def from_int(cls, spice_level: int) -> 'SpicinessLevel':
        """Конвертирует spice_level (int) в SpicinessLevel enum"""
        if spice_level == 0:
            return cls.LOW
        elif spice_level == 1:
            return cls.MEDIUM
        else:  # 2 и выше
            return cls.HIGH


class DishBase(BaseModel):
    # Обязательные поля из meta.json
    name: str
    category: Optional[str] = None  # В meta.json может быть null
    
    # Поля, которые нужно адаптировать
    price: float = 0.0  # В meta.json это float, не int!
    spice_level: int = 0  # Новое поле из meta.json
    is_vegan: int = 0  # Новое поле из meta.json (0/1)
    
    # Поля, которых нет в meta.json - оставляем с дефолтами
    description: str = ""
    ingredients: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Вычисляемые свойства для совместимости со старой системой
    @property
    def spiciness(self) -> SpicinessLevel:
        """Для совместимости со старой системой"""
        return SpicinessLevel.from_int(self.spice_level)
    
    @property
    def vegan(self) -> bool:
        """Для совместимости со старой системой"""
        return bool(self.is_vegan)
    
    class Config:
        # Разрешаем использование свойств @property в модели
        keep_untouched = (property,)


class DishWithScore(DishBase):
    relevance_score: float = 0.0
    vector_score: float = 0.0
    lexical_score: float = 0.0
    llm_rerank_score: float = 0.0


# Остальные классы остаются без изменений...
class ComponentSpec(BaseModel):
    """
    Компонент запроса, который ИИ создаёт для embedding-поиска.
    modifiers — это инструменты, которыми ИИ управляет поиском.
    """
    name: str
    search_text: str = ""
    constraints: Dict[str, Any] = Field(default_factory=dict)
    modifiers: Dict[str, float] = Field(default_factory=dict)
    count: int = 1
    priority: int = 1


class QueryAnalysis(BaseModel):
    query_type: QueryType = QueryType.VAGUE
    ingredients: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    mini_context: str = ""
    search_text: str = ""
    needs_decomposition: bool = False
    components_needed: List[ComponentSpec] = Field(default_factory=list)


class SearchTask(BaseModel):
    id: str
    search_query: str
    description: str
    priority: int = 1


class PipelineContext(BaseModel):
    original_query: str
    analysis_result: Optional[QueryAnalysis] = None
    search_tasks: List[SearchTask] = Field(default_factory=list)
    search_results: Dict[str, List[DishWithScore]] = Field(default_factory=dict)
    selected_dishes: List[DishWithScore] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    text: str
    max_results: int = 10


class SearchResponse(BaseModel):
    dishes: List[DishWithScore] = Field(default_factory=list)
    count: int = 0
    query_analysis: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)