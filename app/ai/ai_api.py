
import sys, os
from pathlib import Path
from typing import Dict, Any

# Ensure project root is in path so we can import local my_ai_dishes package
repo_root = str(Path(__file__).resolve().parents[3])  # project_main
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app.ai import response as ai_response

try:
    from my_ai_dishes.app.core.universal_pipeline import UniversalPipeline
    from my_ai_dishes.app.models.schemas import SearchResponse
except Exception as e:
    # if import fails, raise for visibility
    raise

# Initialize pipeline singleton
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = UniversalPipeline()
    return _pipeline

def handle_ai_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming message dict and return a structured response for frontend.

    Expects payload: { message: str, cart?: list, guest_phone?: str, guest_name?: str, top_k?: int }
    Returns: { success: True, data: { message, suggestions, parsed } }
    """
    if not payload or 'message' not in payload:
        return {'success': False, 'error': "Field 'message' is required"}

    msg = str(payload.get('message') or "").strip()
    top_k = int(payload.get('top_k') or payload.get('max_results') or 6)
    try:
        pipeline = get_pipeline()
        result = pipeline.process_query(msg, max_results=top_k)
        # result is a Pydantic model SearchResponse
        try:
            raw_suggestions = result.dict().get('dishes', [])
        except Exception:
            # fallback: if result is dict-like
            raw_suggestions = getattr(result, 'dishes', []) or []
        parsed = {
            'text': msg,
            'analysis': getattr(result, 'query_analysis', {}) or {}
        }
        resp = ai_response.build_response(parsed, raw_suggestions)
        return {'success': True, 'data': resp}
    except Exception as e:
        return {'success': False, 'error': str(e)}
