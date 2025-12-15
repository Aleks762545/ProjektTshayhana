# app/vector/embeddings.py
import requests
import numpy as np
import logging

logger = logging.getLogger(__name__)

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/embeddings"

def get_embedding(text: str):
    if not text:
        text = ""

    payload = {
        "input": text,
        "model": "text-embedding-all-minilm-l6-v2-embedding"
    }

    try:
        logger.debug(f"Requesting embedding for: {text[:50]}...")
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"LM Studio returned status {response.status_code}: {response.text[:200]}")
            raise ValueError(f"LM Studio error: {response.status_code}")
        
        data = response.json()
        
        # Извлекаем embedding
        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            embedding = data["data"][0].get("embedding")
            if embedding is None:
                # Если embedding нет в ключе 'embedding', возможно это сам массив
                embedding = data["data"][0]
        else:
            raise ValueError(f"Unexpected response format: {data}")
        
        logger.debug(f"Got embedding of length: {len(embedding)}")
        return np.array(embedding, dtype="float32")

    except Exception as e:
        logger.exception(f"LM Studio embedding error: {e}")
        # fallback: детерминированный псевдослучайный вектор
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(384).astype("float32")
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding