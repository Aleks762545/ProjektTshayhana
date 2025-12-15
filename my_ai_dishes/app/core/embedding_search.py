"""
Поиск блюд через эмбединги - исправленная версия
Убрана избыточная сортировка
"""
import numpy as np
from typing import List, Dict, Any
from ..models.schemas import DishWithScore, SearchTask
from .embeddings import EmbeddingService
from .vector_store import VectorStore


class EmbeddingSearch:
    """Поиск блюд через векторные эмбединги"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService(use_lm_studio=False)
        self.vector_store = VectorStore()
        
        # Загружаем векторную базу
        if not self.vector_store.load():
            print("[EmbeddingSearch] ⚠️ Не удалось загрузить векторную базу")
            print("[EmbeddingSearch] Проверьте наличие файлов:")
            print(f"  - embeddings.npy: {self.vector_store.embeddings_path}")
            print(f"  - meta.json: {self.vector_store.meta_path}")
            # Fallback: пытаемся создать базу из старого формата (опционально)
            # self.embedding_service.prepare_dishes_with_embeddings()
            # self.vector_store.load()
    
    def search_for_task(self, task: SearchTask, top_k: int = 50) -> List[DishWithScore]:
        """Ищет блюда для конкретной задачи"""
        
        print(f"[Search] Задача: '{task.description}' → '{task.search_query}'")
        
        # Генерируем эмбеддинг для поискового запроса
        query_embedding = self.embedding_service.get_embedding(task.search_query)
        
        if not query_embedding:
            print(f"[WARNING] Не удалось создать эмбеддинг для: {task.search_query}")
            return []
        
        # Ищем в векторной базе
        vector_results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # Конвертируем в DishWithScore
        dishes_with_scores = []
        for result in vector_results:
            dish_data = result["dish"]
            
            # Создаем DishWithScore напрямую из данных meta.json
            # DishWithScore сам позаботится о конвертации spice_level и is_vegan
            dish = DishWithScore(
                # Обязательные поля
                name=dish_data.get("name", ""),
                category=dish_data.get("category", ""),
                price=dish_data.get("price", 0.0),  # Теперь float
                
                # Новые поля из meta.json
                spice_level=dish_data.get("spice_level", 0),
                is_vegan=dish_data.get("is_vegan", 0),
                
                # Поля, которых нет в meta.json
                description=dish_data.get("description", ""),
                ingredients=dish_data.get("ingredients", []),
                tags=dish_data.get("tags", []),
                
                # Счета релевантности
                relevance_score=float(result.get("vector_score", 0)),
                vector_score=float(result.get("vector_score", 0)),
                lexical_score=0.0
            )
            
            dishes_with_scores.append(dish)
        
        print(f"[Search] Найдено: {len(dishes_with_scores)} блюд")
        if dishes_with_scores:
            print(f"[Search] Лучшее: {dishes_with_scores[0].name} ({dishes_with_scores[0].relevance_score:.3f})")
            print(f"[Search] Категория: {dishes_with_scores[0].category}, Цена: {dishes_with_scores[0].price}")
            print(f"[Search] Острота: {dishes_with_scores[0].spiciness.value} (spice_level={dishes_with_scores[0].spice_level})")
            print(f"[Search] Веган: {dishes_with_scores[0].vegan} (is_vegan={dishes_with_scores[0].is_vegan})")
        
        return dishes_with_scores[:top_k]