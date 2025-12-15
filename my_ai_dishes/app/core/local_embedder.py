# app/core/local_embedder.py
"""
Автопоиск локальной модели SentenceTransformer в указанных candidate путях.
Ищет подпапки, содержащие config.json с ключом model_type или файлы pytorch_model.bin / tf_model.h5.
Загружает модель через SentenceTransformer(..., local_files_only=True).
"""

from sentence_transformers import SentenceTransformer
from pathlib import Path
import logging
import sys
import json

logger = logging.getLogger("local_embedder")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# Ваши известные candidate пути (оставьте как есть)
CANDIDATE_PATHS = [
    Path(r"C:\Users\Aleksandr\.cache\huggingface\hub\models--intfloat--multilingual-e5-large"),
    Path(r"C:C:\Users\Aleksandr\.cache\huggingface\hub\models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2")
]

_model = None
_model_path_used = None

def _is_valid_model_dir(p: Path) -> bool:
    """
    Проверяет, содержит ли папка признаки модели: config.json с model_type
    или файлы pytorch_model.bin / tf_model.h5 / sentence_transformers_config.json
    """
    try:
        cfg = p / "config.json"
        if cfg.exists():
            try:
                data = json.loads(cfg.read_text(encoding="utf-8"))
                if isinstance(data, dict) and ("model_type" in data or "architectures" in data):
                    return True
            except Exception:
                pass
        # другие признаки
        if (p / "pytorch_model.bin").exists() or (p / "tf_model.h5").exists():
            return True
        if (p / "sentence_transformers_config.json").exists():
            return True
    except Exception:
        return False
    return False

def _find_candidate_subdir(root: Path) -> Path | None:
    """
    Рекурсивно ищет подпапку в root, которая выглядит как модель.
    Ограничиваем глубину поиска, чтобы не сканировать весь диск.
    """
    if not root.exists():
        return None
    # Быстрая проверка самого корня
    if _is_valid_model_dir(root):
        return root
    # Ищем в подпапках уровня 1 и 2
    try:
        for child in root.iterdir():
            if child.is_dir():
                if _is_valid_model_dir(child):
                    return child
                # уровень 2
                try:
                    for sub in child.iterdir():
                        if sub.is_dir() and _is_valid_model_dir(sub):
                            return sub
                except Exception:
                    continue
    except Exception:
        return None
    return None

def _try_load_from_path(p: Path) -> bool:
    """
    Попытка загрузить модель из папки p или её подходящей подпапки.
    """
    global _model, _model_path_used
    try:
        if not p.exists():
            return False
        logger.info("Searching for model under: %s", p)
        candidate = _find_candidate_subdir(p) or (p if _is_valid_model_dir(p) else None)
        if candidate is None:
            logger.info("No valid model subfolder found under %s", p)
            return False
        logger.info("Attempting to load SentenceTransformer from: %s", candidate)
        # local_files_only=True чтобы не обращаться в интернет
        _model = SentenceTransformer(str(candidate), local_files_only=True)
        _model_path_used = str(candidate)
        logger.info("Loaded local SentenceTransformer from %s", candidate)
        return True
    except Exception as e:
        logger.warning("Loading from path failed (%s): %s", p, e)
        _model = None
        return False

def _load_model():
    global _model
    if _model is not None:
        return _model

    # 1) Попробуем прямые candidate пути и их подпапки
    for p in CANDIDATE_PATHS:
        if _try_load_from_path(p):
            return _model

    # 2) Попробуем стандартные имена с local_files_only (использует кэш)
    candidates_names = [
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/distiluse-base-multilingual-cased-v2",
        "all-MiniLM-L6-v2",
        "distiluse-base-multilingual-cased-v2"
    ]
    for name in candidates_names:
        try:
            logger.info("Trying to load by name (local_files_only): %s", name)
            _model = SentenceTransformer(name, local_files_only=True)
            _model_path_used = name
            logger.info("Loaded SentenceTransformer by name: %s", name)
            return _model
        except Exception as e:
            logger.warning("Load by name failed (%s): %s", name, e)
            _model = None

    logger.warning("Local embedding model not found or failed to load. Embedding calls will fallback to zero-vector.")
    return None

def local_embed(text: str):
    """
    Возвращает вектор (list[float]) для текста.
    Если модель не загрузилась — возвращает None.
    """
    model = _load_model()
    if model is None:
        return None
    try:
        vec = model.encode(text, normalize_embeddings=True)
        return vec.tolist() if hasattr(vec, "tolist") else list(vec)
    except Exception as e:
        logger.exception("Error while encoding text with local model: %s", e)
        return None
