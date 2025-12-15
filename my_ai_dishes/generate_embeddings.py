# generate_embeddings.py
"""
Скрипт для пересоздания файла dishes_with_embeddings.json
Запуск:
    python generate_embeddings.py
"""

import sys
import os

# Добавляем путь проекта, чтобы Python видел пакет app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# ✅ Импорт строго по твоей структуре:
#    app/core/embeddings.py
from app.core.embeddings import EmbeddingService


def main():
    print("====================================================")
    print("   ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ ДЛЯ БЛЮД")
    print("====================================================")

    # Если хочешь использовать LM Studio — поставь True
    use_lm_studio = False

    service = EmbeddingService(use_lm_studio=use_lm_studio)

    print("[INFO] Начинаю генерацию...")
    service.prepare_dishes_with_embeddings()

    print("====================================================")
    print("✅ Готово! Файл dishes_with_embeddings.json обновлён.")
    print("====================================================")


if __name__ == "__main__":
    main()
