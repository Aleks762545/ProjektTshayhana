import time
from app.utils.normalizer import normalize_text, standardize_terms
from app.vector.embeddings import get_embedding
from app.vector.vector_store import VECTOR_STORE
from app.config import settings

def search(query, top_k=5, filters=None):
    t0 = time.time()
    q = normalize_text(query)
    q = standardize_terms(q)
    emb = get_embedding(q)
    candidates = VECTOR_STORE.query(emb, top_k = max(top_k, settings['search']['top_k']))
    # apply simple filters
    results = []
    for c in candidates:
        md = c['metadata']
        ok = True
        if filters:
            if 'category' in filters and filters['category']:
                ok = ok and (md.get('category') == filters['category'])
            if 'spice_max' in filters and filters['spice_max'] is not None:
                ok = ok and (md.get('spice_level',0) <= int(filters['spice_max']))
            if 'is_vegan' in filters and filters['is_vegan'] is not None:
                ok = ok and (md.get('is_vegan',0) == (1 if filters['is_vegan'] else 0))
        if ok:
            results.append({'id': c['id'], 'name': md.get('name'), 'price': md.get('price'), 'image_path': md.get('image_path',''), 'description': md.get('description',''), 'category': md.get('category'), 'spice_level': md.get('spice_level'), 'is_vegan': md.get('is_vegan'), '_score': c['score']})
    elapsed = int((time.time()-t0)*1000)
    return {'query': query, 'time_ms': elapsed, 'results': results[:top_k]}
