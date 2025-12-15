# app/ai/semantic_search.py
from app.db import sqlite_db
from app.ai import parser
import sqlite3

# Scores weights
WEIGHT_ING = 3.0
WEIGHT_TAG = 2.0
WEIGHT_NAME_DESC = 1.0
WEIGHT_MEAL = 1.5
WEIGHT_VEG = 1.5

def _like_term(t):
    return f"%{t}%"

def search_dishes_by_query(parsed, top_k=6):
    """
    parsed = parse_user_message(...)
    returns list of dish dicts with added 'score' field
    """
    conn = sqlite_db.get_conn()
    cur = conn.cursor()

    # Fetch base candidates: dishes that match by ingredient name OR name/description LIKE
    tokens = parsed.get('tokens') or []
    ingreds = parsed.get('ingredients') or []
    meal_time = parsed.get('meal_time')
    diet_prefs = parsed.get('diet_prefs') or []

    # Build SQL that finds dishes with matching ingredients or name/description LIKE
    # We'll fetch a superset and compute score in Python.
    placeholders = []
    conditions = []
    params = []

    # name/description tokens
    if tokens:
        for t in tokens:
            conditions.append("(d.name LIKE ? OR d.description LIKE ?)")
            params.extend([_like_term(t), _like_term(t)])

    # ingredients match via dish_ingredients -> ingredients.name
    if ingreds:
        for ing in ingreds:
            conditions.append("EXISTS (SELECT 1 FROM dish_ingredients di JOIN ingredients i ON di.ingredient_id = i.id WHERE di.dish_id = d.id AND i.name LIKE ?)")
            params.append(_like_term(ing))

    where_clause = " OR ".join(conditions) if conditions else "1=1"
    q = f"SELECT d.* FROM dishes d WHERE ({where_clause}) AND d.is_available = 1 LIMIT 200"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]

    # Score each row heuristically
    scored = []
    for r in rows:
        score = 0.0
        name = (r.get('name') or '').lower()
        desc = (r.get('description') or '').lower()

        # name/desc tokens
        for t in tokens:
            if t in name or t in desc:
                score += WEIGHT_NAME_DESC

        # ingredient matches
        if ingreds:
            # query ingredients for this dish
            cur.execute("SELECT i.name FROM dish_ingredients di JOIN ingredients i ON di.ingredient_id = i.id WHERE di.dish_id = ?", (r['id'],))
            ing_rows = [x['name'].lower() for x in cur.fetchall()]
            for ing in ingreds:
                for iname in ing_rows:
                    if ing in iname or iname in ing:
                        score += WEIGHT_ING

        # tags
        cur.execute("SELECT t.name, t.tag_type FROM tags t JOIN dish_tags dt ON t.id = dt.tag_id WHERE dt.dish_id = ?", (r['id'],))
        trows = [x['name'].lower() for x in cur.fetchall()]
        for pref in diet_prefs:
            if pref == 'vegan':
                # if dish is vegan
                if r.get('is_vegan'):
                    score += WEIGHT_VEG
            else:
                # tag match
                for tn in trows:
                    if pref in tn:
                        score += WEIGHT_TAG

        # meal time
        if meal_time and r.get('meal_time_name') and meal_time.lower() in r.get('meal_time_name').lower():
            score += WEIGHT_MEAL

        # slight boost for price (prefer mid-range) - optional, skip

        r['_score'] = score
        scored.append(r)

    # If no scored results, fallback to simple name/desc LIKE search across all tokens
    if not scored:
        fallback_params = []
        fallback_conds = []
        for t in tokens:
            fallback_conds.append("(d.name LIKE ? OR d.description LIKE ?)")
            fallback_params.extend([_like_term(t), _like_term(t)])
        if fallback_conds:
            fq = f"SELECT d.* FROM dishes d WHERE {' OR '.join(fallback_conds)} AND d.is_available = 1 LIMIT 50"
            cur.execute(fq, fallback_params)
            for r in [dict(x) for x in cur.fetchall()]:
                r['_score'] = WEIGHT_NAME_DESC
                scored.append(r)

    conn.close()
    # sort by score desc, return top_k
    scored_sorted = sorted(scored, key=lambda x: x.get('_score', 0), reverse=True)[:top_k]
    return scored_sorted
