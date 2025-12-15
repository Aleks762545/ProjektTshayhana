#!/usr/bin/env python3
"""
Точка входа для запуска Universal Pipeline API
Запуск: python run.py
"""
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Проверка зависимостей"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import requests
        import numpy
        import sentence_transformers
        print("[OK] Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"[ERROR] Не установлена зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False

def check_data_files():
    """Проверка наличия данных"""
    data_dir = project_root / "app" / "data"
    
    # Проверяем dishes.json
    dishes_path = data_dir / "dishes.json"
    if not dishes_path.exists():
        print(f"[ERROR] Файл не найден: {dishes_path}")
        print("Создайте файл dishes.json с данными о блюдах")
        return False
    
    print(f"[OK] Файл с блюдами найден: {dishes_path}")
    return True

def check_lm_studio():
    """Проверка доступности LM Studio"""
    try:
        import requests
        response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        if response.status_code == 200:
            print("[OK] LM Studio доступен на localhost:1234")
            return True
        else:
            print(f"[WARNING] LM Studio вернул код {response.status_code}")
            return True  # Все равно запускаемся
    except Exception as e:
        print(f"[WARNING] LM Studio недоступен: {e}")
        print("[INFO] Запускаемся в fallback режиме")
        return True  # Все равно запускаемся

def main():
    """Основная функция запуска"""
    print("\n" + "="*70)
    print("AI КУЛИНАРНЫЙ ПОМОЩНИК - UNIVERSAL PIPELINE")
    print("="*70)
    
    # Проверки
    if not check_dependencies():
        return 1
    
    if not check_data_files():
        return 1
    
    check_lm_studio()
    
    # Запуск сервера
    print("\n[INFO] Запуск FastAPI сервера...")
    print("[INFO] Документация: http://localhost:8000/docs")
    print("[INFO] API: http://localhost:8000")
    print("[INFO] Нажмите Ctrl+C для остановки\n")
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[INFO] Сервер остановлен")
        return 0
    except Exception as e:
        print(f"[ERROR] Ошибка запуска сервера: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())