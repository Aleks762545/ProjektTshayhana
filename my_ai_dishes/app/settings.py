"""
Базовые настройки для проекта - только константы, без импортов
"""
import os
from pathlib import Path

# ========== ПУТИ ==========
BASE_DIR = Path(__file__).parent.parent  # my_ai_dishes/
DATA_DIR = BASE_DIR / "app" / "data"

# Старые пути (для обратной совместимости)
DISHES_JSON_PATH = DATA_DIR / "dishes.json"
DISHES_WITH_EMBEDDINGS_PATH = DATA_DIR / "dishes_with_embeddings.json"

# НОВЫЕ ПУТИ к векторной базе данных
# Исправляем путь: из my_ai_dishes/ в project_main/data/vector_store/
# Было: PROJECT_ROOT = BASE_DIR.parent.parent  # project_main/
# Проблема: BASE_DIR = my_ai_dishes/, parent.parent = ProjektTshayhana/0.17/
# Нужно: parent.parent.parent = ProjektTshayhana/0.17/project_main/

# Правильный путь: поднимаемся на 3 уровня вверх от BASE_DIR
PROJECT_MAIN_DIR = BASE_DIR.parent  # project_main/ (из my_ai_dishes/ подняться на 1 уровень)
VECTOR_STORE_DIR = PROJECT_MAIN_DIR / "data" / "vector_store"

EMBEDDINGS_NPY_PATH = VECTOR_STORE_DIR / "embeddings.npy"
META_JSON_PATH = VECTOR_STORE_DIR / "meta.json"

print(f"[SETTINGS] Путь к vector_store: {VECTOR_STORE_DIR}")
print(f"[SETTINGS] Путь к embeddings: {EMBEDDINGS_NPY_PATH}")
print(f"[SETTINGS] Путь к meta: {META_JSON_PATH}")

# ========== LM STUDIO ==========
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
LM_CHAT_URL = f"{LM_STUDIO_URL}/chat/completions"
LM_EMBEDDING_URL = f"{LM_STUDIO_URL}/embeddings"

# ========== МОДЕЛИ ==========
LM_MODEL = "qwen2.5-1.5b-instruct"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

# ========== ПАРАМЕТРЫ СИСТЕМЫ ==========
MAX_SEARCH_RESULTS = 10
EMBEDDING_TOP_K = 50                       # ЕДИНСТВЕННОЕ значение
MAX_TOKENS_PER_RESPONSE = 1000

# ========== НАСТРОЙКИ ПАЙПЛАЙНА ==========
USE_LLM_FOR_FINAL_RESPONSE = True          # Использовать LLM для форматирования ответа
USE_LM_STUDIO_FOR_EMBEDDINGS = False       # Локальные эмбеддинги быстрее
USE_LLM_FOR_SELECTION = True               # LLM для выбора блюд
USE_LLM_FOR_ANALYSIS = True                # LLM для анализа запроса

# ========== ТАЙМАУТЫ ==========
LLM_TIMEOUT = 40                           # Таймаут для LLM вызовов
REQUEST_TIMEOUT = 30                       # Общий таймаут запросов

# ========== КОНФИГИ КОМПОНЕНТОВ ==========
SMART_ANALYZER_CONFIG = {
    "max_mini_context_words": 15,
    "temperature": 0.1,
    "enable_fallback": True
}

DISH_SELECTOR_CONFIG = {
    "max_dishes_per_task": 3,
    "temperature": 0.2,
    "use_mini_context": True
}

RESPONSE_FORMATTER_CONFIG = {
    "use_llm": True,
    "temperature": 0.3,
    "max_dishes_in_prompt": 5
}