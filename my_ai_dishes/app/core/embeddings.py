"""
Генерация эмбеддингов для блюд
"""
import json
import numpy as np
from typing import List, Dict, Any
import requests
from sentence_transformers import SentenceTransformer
from ..config import (
    DISHES_JSON_PATH,
    DISHES_WITH_EMBEDDINGS_PATH,
    LM_EMBEDDING_URL,
    EMBEDDING_MODEL
)


class EmbeddingService:
    """Сервис для работы с эмбеддингами"""
    
    def __init__(self, use_lm_studio: bool = False):
        self.use_lm_studio = use_lm_studio
        
        if not use_lm_studio:
            # Используем локальную модель
            print(f"[EmbeddingService] Загрузка локальной модели: {EMBEDDING_MODEL}")
            self.local_model = SentenceTransformer(EMBEDDING_MODEL)
        else:
            self.local_model = None
    
    def generate_local_embedding(self, text: str) -> List[float]:
        """Генерация эмбеддинга локальной моделью"""
        if self.local_model:
            embedding = self.local_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        return []
    
    def generate_lm_studio_embedding(self, text: str) -> List[float]:
        """Генерация эмбеддинга через LM Studio"""
        try:
            response = requests.post(
                LM_EMBEDDING_URL,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": text
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            print(f"[ERROR] Ошибка при получении эмбеддинга от LM Studio: {e}")
            return []
    
    def get_embedding(self, text: str) -> List[float]:
        """Основной метод получения эмбеддинга"""
        if self.use_lm_studio:
            return self.generate_lm_studio_embedding(text)
        else:
            return self.generate_local_embedding(text)
    
    def calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Косинусная схожесть"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(v1, v2) / (norm1 * norm2))
    
    def prepare_dishes_with_embeddings(self) -> List[Dict[str, Any]]:
        """Создание файла с эмбеддингами блюд"""
        print("[INFO] Загрузка блюд из JSON...")
        with open(DISHES_JSON_PATH, 'r', encoding='utf-8') as f:
            dishes = json.load(f)
        
        dishes_with_embeddings = []
        
        for i, dish in enumerate(dishes):
            print(f"[INFO] Обработка блюда {i+1}/{len(dishes)}: {dish['name']}")
            
            # Создаем текстовое представление для эмбеддинга
            dish_text = (
                f"{dish['name']}. {dish['description']}. "
                f"Ингредиенты: {', '.join(dish['ingredients'])}. "
                f"Категория: {dish['category']}. "
                f"Теги: {', '.join(dish['tags'])}"
            )
            
            # Генерируем эмбеддинг
            embedding = self.get_embedding(dish_text)
            
            if embedding:
                dish_with_embedding = dish.copy()
                dish_with_embedding['embedding'] = embedding
                dishes_with_embeddings.append(dish_with_embedding)
            else:
                print(f"[WARNING] Не удалось создать эмбеддинг для: {dish['name']}")
        
        # Сохраняем результат
        print(f"[INFO] Сохранение {len(dishes_with_embeddings)} блюд с эмбеддингами...")
        with open(DISHES_WITH_EMBEDDINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(dishes_with_embeddings, f, ensure_ascii=False, indent=2)
        
        print("[SUCCESS] Файл dishes_with_embeddings.json создан!")
        return dishes_with_embeddings
    
    def load_dishes_with_embeddings(self) -> List[Dict[str, Any]]:
        """Загрузка блюд с эмбеддингами"""
        if not DISHES_WITH_EMBEDDINGS_PATH.exists():
            print("[INFO] Файл с эмбеддингами не найден. Создаем...")
            return self.prepare_dishes_with_embeddings()
        
        with open(DISHES_WITH_EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
            dishes = json.load(f)
        
        print(f"[INFO] Загружено {len(dishes)} блюд с эмбеддингами")
        return dishes