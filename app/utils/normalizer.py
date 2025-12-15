import re
def normalize_text(text):
    if not text:
        return ''
    t = text.lower()
    t = t.replace('ё','е')
    t = re.sub(r'[^а-яa-z0-9\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def standardize_terms(text):
    # simple synonym replacement
    mapping = {
        'сладкое':'dessert',
        'веган':'vegan',
        'без мяса':'vegetarian',
        'острое':'spicy',
        'лапша':'noodles',
        'рис':'rice'
    }
    for k,v in mapping.items():
        text = text.replace(k, v)
    return text
