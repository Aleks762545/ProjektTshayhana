"""
Модуль для работы с векторной базой данных
"""
import json
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
from ..config import EMBEDDINGS_NPY_PATH, META_JSON_PATH


class VectorStore:
    """Класс для работы с векторной базой блюд"""
    
    def __init__(self, 
                 embeddings_path: Path = EMBEDDINGS_NPY_PATH,
                 meta_path: Path = META_JSON_PATH):
        self.embeddings_path = embeddings_path
        self.meta_path = meta_path
        self.dishes_meta = {}  # Словарь {id: dish_data}
        self.embeddings = []
        self.dish_ids = []  # Сохраняем IDs для связи с метаданными
        
    def load(self) -> bool:
        """Загрузка векторной базы из embeddings.npy и meta.json"""
        try:
            # Проверяем существование файлов
            if not self.embeddings_path.exists():
                print(f"[VectorStore] Файл embeddings не найден: {self.embeddings_path}")
                return False
            
            if not self.meta_path.exists():
                print(f"[VectorStore] Файл meta не найден: {self.meta_path}")
                return False
            
            # 1. Загружаем эмбеддинги
            print(f"[VectorStore] Загрузка эмбеддингов из: {self.embeddings_path}")
            self.embeddings = np.load(self.embeddings_path)
            print(f"[VectorStore] Загружено {len(self.embeddings)} векторов, размерность: {self.embeddings.shape[1]}")
            
            # 2. Загружаем метаданные
            print(f"[VectorStore] Загрузка метаданных из: {self.meta_path}")
            with open(self.meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            # Преобразуем метаданные в нужный формат
            self.dishes_meta = {}
            self.dish_ids = []
            
            for dish_id, dish_data in meta_data.items():
                # Сохраняем ID для связи с эмбеддингами (по индексу)
                self.dish_ids.append(dish_id)
                
                # Обогащаем данные: добавляем ID и приводим к нужному формату
                enriched_dish = {
                    "id": dish_id,
                    "name": dish_data.get("name", ""),
                    "category": dish_data.get("category"),
                    "price": dish_data.get("price", 0.0),
                    "spice_level": dish_data.get("spice_level", 0),
                    "is_vegan": dish_data.get("is_vegan", 0),
                    # Поля, которых нет в meta.json - заполняем пустыми значениями
                    "description": "",
                    "ingredients": [],
                    "tags": []
                }
                self.dishes_meta[dish_id] = enriched_dish
            
            print(f"[VectorStore] Загружено {len(self.dishes_meta)} блюд из meta.json")
            
            # 3. Проверяем соответствие количества
            if len(self.embeddings) != len(self.dish_ids):
                print(f"[WARNING] Несоответствие: {len(self.embeddings)} эмбеддингов vs {len(self.dish_ids)} блюд")
                # Берем минимум для безопасности
                min_len = min(len(self.embeddings), len(self.dish_ids))
                self.embeddings = self.embeddings[:min_len]
                self.dish_ids = self.dish_ids[:min_len]
                print(f"[VectorStore] Исправлено до {min_len} записей")
            
            return True
            
        except Exception as e:
            print(f"[VectorStore] Ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query_vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        """Поиск ближайших векторов"""
        if len(self.embeddings) == 0 or len(self.dish_ids) == 0:
            return []
        
        # Конвертируем в numpy
        query_vec = np.array(query_vector)
        
        # Нормализуем для косинусного расстояния
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        embeddings_norm = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-10)
        
        # Вычисляем косинусные сходства
        similarities = np.dot(embeddings_norm, query_norm)
        
        # Получаем индексы топ-K
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Формируем результаты
        results = []
        for idx in top_indices:
            dish_id = self.dish_ids[idx]
            dish_data = self.dishes_meta[dish_id].copy()
            
            results.append({
                "dish": dish_data,
                "vector_score": float(similarities[idx])
            })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика векторной базы"""
        return {
            "total_dishes": len(self.dishes_meta),
            "dishes_with_embeddings": len(self.embeddings),
            "embedding_dimension": self.embeddings.shape[1] if len(self.embeddings) > 0 else 0,
            "embeddings_path": str(self.embeddings_path),
            "meta_path": str(self.meta_path)
        }