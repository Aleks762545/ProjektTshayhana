"""
Конфигурация для УНИВЕРСАЛЬНОГО ПАЙПЛАЙНА
Импортирует настройки из settings.py и добавляет логику инициализации
"""
from pathlib import Path
import requests
from .settings import *  # Импортируем ВСЕ константы из settings.py


# ========== ИНИЦИАЛИЗАЦИЯ ==========

# Проверяем наличие директорий
for path in [DATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)


def check_lm_studio() -> bool:
    """Проверяет доступность LM Studio"""
    try:
        response = requests.get(f"{LM_STUDIO_URL}/models", timeout=5)
        if response.status_code == 200:
            print("[INFO] LM Studio доступен для Universal Pipeline")
            return True
    except Exception as e:
        print(f"[WARNING] LM Studio недоступен: {e}")
        print("[INFO] Система будет использовать fallback режимы")
    return False


# Инициализируем проверку
LM_STUDIO_AVAILABLE = check_lm_studio()


# ========== ВЫВОД НАСТРОЕК ==========

print(f"[CONFIG] Universal Pipeline настроен:")
print(f"  • LM Studio: {'доступен' if LM_STUDIO_AVAILABLE else 'недоступен'}")
print(f"  • Локальные эмбеддинги: {'используются' if not USE_LM_STUDIO_FOR_EMBEDDINGS else 'отключены'}")
print(f"  • LLM для форматирования: {'включен' if USE_LLM_FOR_FINAL_RESPONSE else 'выключен'}")
print(f"  • Таймаут LLM: {LLM_TIMEOUT} секунд")
print(f"  • Top K для поиска: {EMBEDDING_TOP_K}")