"""
FastAPI приложение для УНИВЕРСАЛЬНОГО ПАЙПЛАЙНА
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager

from .models.schemas import SearchRequest, SearchResponse
from .core.universal_pipeline import UniversalPipeline
from .settings import MAX_SEARCH_RESULTS  # Импорт из settings.py

# Глобальный экземпляр пайплайна
pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global pipeline
    
    # Запуск при старте
    print("\n" + "="*70)
    print("[INFO] Запуск Universal Pipeline...")
    print("[INFO] Архитектура: SmartAnalyzer → TaskDecomposer → EmbeddingSearch → DishSelector → ResponseFormatter")
    print("="*70)
    
    # Инициализируем пайплайн с настройками
    pipeline = UniversalPipeline(
        use_llm_for_formatting=True  # Использовать LLM для красивого форматирования
    )
    
    stats = pipeline.get_stats()
    print(f"[INFO] Pipeline готов. Статистика: {stats}")
    
    yield
    
    # Очистка при завершении
    print("[INFO] Завершение работы Universal Pipeline...")

# Создаем FastAPI приложение
app = FastAPI(
    title="AI Кулинарный Помощник - Universal Pipeline",
    description="Универсальная ИИ система для поиска блюд по сложным запросам",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # Кастомная документация
    redoc_url=None
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ENDPOINTS ==========

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "AI Кулинарный Помощник - Universal Pipeline API",
        "version": "2.0.0",
        "architecture": "SmartAnalyzer → TaskDecomposer → EmbeddingSearch → DishSelector → ResponseFormatter",
        "endpoints": {
            "search": "POST /search",
            "docs": "GET /docs",
            "health": "GET /health",
            "stats": "GET /stats",
            "pipeline_info": "GET /pipeline/info"
        },
        "documentation": "Откройте /docs для интерактивной документации"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if not pipeline:
            return {"status": "starting", "service": "universal_pipeline"}
        
        stats = pipeline.get_stats()
        return {
            "status": "healthy",
            "service": "universal_pipeline",
            "total_queries": stats.get("total_queries", 0),
            "successful_queries": stats.get("successful_queries", 0),
            "avg_processing_time": f"{stats.get('avg_processing_time', 0):.2f} сек",
            "architecture": stats.get("architecture", "")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/search", response_model=SearchResponse)
async def search_dishes(request: SearchRequest):
    """
    Основной endpoint для поиска блюд
    
    Обрабатывает сложные запросы через универсальный пайплайн:
    1. Анализ + мини-контекст (ИИ №1)
    2. Декомпозиция на задачи
    3. Поиск через эмбеддинги
    4. Выбор с учетом мини-контекста
    5. Форматирование ответа (ИИ №2)
    """
    try:
        if not pipeline:
            raise HTTPException(status_code=503, detail="Сервис не готов")
        
        max_results = request.max_results or MAX_SEARCH_RESULTS
        
        print(f"\n[API] Новый запрос: '{request.text}' (max_results: {max_results})")
        
        # Обрабатываем запрос через универсальный пайплайн
        result = pipeline.process_query(request.text, max_results)
        
        print(f"[API] Запрос обработан. Найдено блюд: {result.count}")
        
        return result
        
    except Exception as e:
        print(f"[API ERROR] Ошибка обработки запроса: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка обработки запроса: {str(e)}"
        )

@app.get("/stats")
async def get_stats():
    """Получить статистику системы"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Сервис не готов")
    
    try:
        stats = pipeline.get_stats()
        return {
            "status": "ok",
            "pipeline_stats": {
                "total_queries": stats.get("total_queries", 0),
                "successful_queries": stats.get("successful_queries", 0),
                "avg_processing_time": f"{stats.get('avg_processing_time', 0):.2f} сек",
                "success_rate": f"{(stats.get('successful_queries', 0) / stats.get('total_queries', 1) * 100):.1f}%"
            },
            "architecture": stats.get("architecture", ""),
            "components": stats.get("components", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка получения статистики: {str(e)}"
        )

@app.get("/pipeline/info")
async def get_pipeline_info():
    """Получить информацию о пайплайне"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Сервис не готов")
    
    return {
        "pipeline": "Universal Pipeline v2.0",
        "description": "Универсальная архитектура для обработки сложных запросов",
        "components": [
            {
                "name": "SmartAnalyzer",
                "purpose": "Анализ запроса + создание мини-контекста (5-10 слов)",
                "output": "QueryAnalysis с mini_context"
            },
            {
                "name": "TaskDecomposer",
                "purpose": "Декомпозиция на поисковые задачи",
                "output": "List[SearchTask]"
            },
            {
                "name": "EmbeddingSearch",
                "purpose": "Поиск блюд через векторные эмбеддинги",
                "output": "Dict[task_id → List[DishWithScore]]"
            },
            {
                "name": "DishSelector",
                "purpose": "Выбор лучших блюд с учетом мини-контекста",
                "input": "mini_context + найденные блюда",
                "output": "List[DishWithScore]"
            },
            {
                "name": "ResponseFormatter",
                "purpose": "Форматирование финального ответа с помощью ИИ",
                "output": "SearchResponse"
            }
        ],
        "key_features": [
            "Мини-контекст для экономии токенов",
            "Два вызова LLM: анализ и форматирование",
            "Векторный поиск через эмбеддинги",
            "Единая модель данных (Pydantic)",
            "Graceful degradation при ошибках"
        ],
        "data_models": [
            "QueryAnalysis", "SearchTask", "DishWithScore", 
            "PipelineContext", "SearchRequest", "SearchResponse"
        ]
    }

# Кастомная Swagger UI документация
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="AI Кулинарный Помощник - Universal Pipeline API",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )