# app/db/sqlite_db.py
import sqlite3, json
from app.config import settings
DB = settings['database']['sqlite_path']

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db(sql_path):
    conn = get_conn()
    cur = conn.cursor()
    with open(sql_path, 'r', encoding='utf-8') as f:
        cur.executescript(f.read())
    conn.commit()
    conn.close()

# Categories
def list_categories():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Tags
def list_tags():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM tags ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Ingredients
def list_ingredients():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM ingredients ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Dishes
def list_dishes(filters=None):
    conn = get_conn(); cur = conn.cursor()
    if filters is None:
        filters = {}
    q = "SELECT d.*, c.name as category_name, m.name as meal_time_name FROM dishes d LEFT JOIN categories c ON d.category_id = c.id LEFT JOIN meal_times m ON d.meal_time_id = m.id WHERE 1=1"
    params = []
    if 'category_id' in filters and filters['category_id']:
        q += " AND d.category_id = ?"; params.append(filters['category_id'])
    if 'spice_max' in filters and filters['spice_max'] is not None:
        q += " AND d.spice_level <= ?"; params.append(int(filters['spice_max']))
    if 'is_vegan' in filters and filters['is_vegan'] is not None:
        q += " AND d.is_vegan = ?"; params.append(1 if filters['is_vegan'] else 0)
    if 'is_available' in filters:
        q += " AND d.is_available = ?"; params.append(1 if filters['is_available'] else 0)
    if 'max_price' in filters and filters['max_price'] is not None:
        q += " AND d.price <= ?"; params.append(filters['max_price'])
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_dish(did):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT d.*, c.name as category_name, m.name as meal_time_name FROM dishes d LEFT JOIN categories c ON d.category_id = c.id LEFT JOIN meal_times m ON d.meal_time_id = m.id WHERE d.id = ?", (did,))
    r = cur.fetchone()
    if not r:
        conn.close(); return None
    dish = dict(r)
    # tags
    cur.execute("SELECT t.* FROM tags t JOIN dish_tags dt ON t.id = dt.tag_id WHERE dt.dish_id = ?", (did,))
    tags = [dict(x) for x in cur.fetchall()]
    # ingredients
    cur.execute("SELECT di.*, ing.name as ingredient_name, ing.description as ingredient_description FROM dish_ingredients di JOIN ingredients ing ON di.ingredient_id = ing.id WHERE di.dish_id = ?", (did,))
    ingredients = [dict(x) for x in cur.fetchall()]
    # assemble
    dish['tags'] = tags
    dish['ingredients'] = ingredients
    conn.close()
    return dish

def create_category(name):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit(); cid = cur.lastrowid; conn.close(); return cid

def create_tag(name, tag_type=None):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO tags (name, tag_type) VALUES (?,?)", (name, tag_type))
    conn.commit(); tid = cur.lastrowid; conn.close(); return tid

def create_ingredient(name, description=None):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO ingredients (name, description) VALUES (?,?)", (name, description))
    conn.commit(); iid = cur.lastrowid; conn.close(); return iid

def create_dish(d):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO dishes (name,description,price,category_id,meal_time_id,spice_level,is_vegan,cooking_time,image_path,is_available)
    VALUES (?,?,?,?,?,?,?,?,?,?)""", (d.get('name'), d.get('description',''), d.get('price'), d.get('category_id'),
    d.get('meal_time_id'), d.get('spice_level',0), 1 if d.get('is_vegan') else 0, d.get('cooking_time',0), d.get('image_path',''), 1 if d.get('is_available', True) else 0))
    conn.commit()
    did = cur.lastrowid
    # tags
    for t in d.get('tags', []):
        tid = t.get('Id') if isinstance(t, dict) and t.get('Id') else t if isinstance(t, int) else None
        if tid:
            cur.execute("INSERT INTO dish_tags (dish_id, tag_id) VALUES (?,?)", (did, tid))
    # ingredients
    for ing in d.get('ingredients', []):
        if isinstance(ing, dict):
            iid = ing.get('Id') or ing.get('id')
            qty = ing.get('quantity')
            is_primary = 1 if ing.get('is_primary') else 0
            if iid:
                cur.execute("INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, is_primary) VALUES (?,?,?,?)", (did, iid, qty, is_primary))
        else:
            cur.execute("SELECT id FROM ingredients WHERE name = ?", (ing,))
            row = cur.fetchone()
            if row:
                iid = row['id']
            else:
                cur.execute("INSERT INTO ingredients (name) VALUES (?)", (ing,))
                iid = cur.lastrowid
            cur.execute("INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, is_primary) VALUES (?,?,?,?)", (did, iid, None, 0))
    conn.commit()
    conn.close()
    return did

def update_dish(did, d):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""UPDATE dishes SET name=?,description=?,price=?,category_id=?,meal_time_id=?,spice_level=?,is_vegan=?,cooking_time=?,image_path=?,is_available=?
    WHERE id=?""", (d.get('name'), d.get('description',''), d.get('price'), d.get('category_id'),
    d.get('meal_time_id'), d.get('spice_level',0), 1 if d.get('is_vegan') else 0, d.get('cooking_time',0), d.get('image_path',''), 1 if d.get('is_available', True) else 0, did))
    # update tags -> delete old and insert new
    cur.execute("DELETE FROM dish_tags WHERE dish_id = ?", (did,))
    for t in d.get('tags', []):
        tid = t.get('Id') if isinstance(t, dict) and t.get('Id') else t if isinstance(t, int) else None
        if tid:
            cur.execute("INSERT INTO dish_tags (dish_id, tag_id) VALUES (?,?)", (did, tid))
    # update ingredients -> delete and recreate
    cur.execute("DELETE FROM dish_ingredients WHERE dish_id = ?", (did,))
    for ing in d.get('ingredients', []):
        if isinstance(ing, dict):
            iid = ing.get('Id') or ing.get('id')
            qty = ing.get('quantity')
            is_primary = 1 if ing.get('is_primary') else 0
            if iid:
                cur.execute("INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, is_primary) VALUES (?,?,?,?)", (did, iid, qty, is_primary))
        else:
            cur.execute("SELECT id FROM ingredients WHERE name = ?", (ing,))
            row = cur.fetchone()
            if row:
                iid = row['id']
            else:
                cur.execute("INSERT INTO ingredients (name) VALUES (?)", (ing,))
                iid = cur.lastrowid
            cur.execute("INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, is_primary) VALUES (?,?,?,?)", (did, iid, None, 0))
    conn.commit()
    conn.close()

def delete_dish(did):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM dishes WHERE id = ?", (did,))
    conn.commit()
    conn.close()

# Guests and orders
def find_or_create_guest_by_phone(phone, name=None):
    if not phone:
        return None
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id FROM guests WHERE phone = ?", (phone,))
    row = cur.fetchone()
    if row:
        conn.close(); return row['id']
    cur.execute("INSERT INTO guests (phone, name) VALUES (?,?)", (phone, name))
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid

def create_order(guest_id, table_number, items):
    conn = get_conn(); cur = conn.cursor()
    total = 0.0
    for it in items:
        cur.execute("SELECT price FROM dishes WHERE id = ?", (it['dish_id'],))
        r = cur.fetchone()
        price = r['price'] if r else 0.0
        total += price * it['quantity']
    cur.execute("INSERT INTO orders (guest_id, table_number, total) VALUES (?,?,?)", (guest_id, table_number, total))
    order_id = cur.lastrowid
    for it in items:
        cur.execute("INSERT INTO order_items (order_id, dish_id, quantity) VALUES (?,?,?)", (order_id, it['dish_id'], it['quantity']))
    conn.commit()
    conn.close()
    return order_id

def list_orders():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT o.*, g.phone as guest_phone, g.name as guest_name FROM orders o LEFT JOIN guests g ON o.guest_id = g.id ORDER BY o.created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
# ==========================================================
# COMPATIBILITY LAYER for frontend & route imports
# ==========================================================

# backend routes expect this name
get_db_conn = get_conn

# frontend expects this name exactly
def findOrCreateGuest(phone, name=None):
    return find_or_create_guest_by_phone(phone, name)
# ==========================================================
# НОВЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ СО СТАТУСАМИ ЗАКАЗОВ
# ==========================================================

def get_order_with_items(order_id):
    """Получить заказ с деталями блюд (дополнение к list_orders)"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Основная информация о заказе (совместимо с list_orders)
    cur.execute("""
        SELECT o.*, g.phone as guest_phone, g.name as guest_name 
        FROM orders o 
        LEFT JOIN guests g ON o.guest_id = g.id 
        WHERE o.id = ?
    """, (order_id,))
    
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    
    order = dict(row)
    
    # Блюда в заказе (расширяем существующую логику)
    cur.execute("""
        SELECT oi.*, d.name as dish_name, d.price as dish_price, 
               d.image_path as dish_image_path
        FROM order_items oi
        JOIN dishes d ON oi.dish_id = d.id
        WHERE oi.order_id = ?
    """, (order_id,))
    
    items = []
    for item in cur.fetchall():
        item_dict = dict(item)
        # Совместимость: добавляем только новые поля
        if item_dict.get('dish_image_path'):
            item_dict['dish_image_url'] = f"/static/{item_dict['dish_image_path'].lstrip('/')}"
        items.append(item_dict)
    
    order['items'] = items
    conn.close()
    return order

def update_order_status(order_id, status):
    """Обновить статус заказа"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Проверяем, что заказ существует
    cur.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
    if not cur.fetchone():
        conn.close()
        return False
    
    # Обновляем статус (поле уже есть в таблице)
    cur.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    
    # Дополнительно: если статус "выдан", ставим дату завершения
    # (поле completed_at должно существовать, если нет - это опционально)
    if status == 'выдан':
        try:
            from datetime import datetime
            cur.execute("UPDATE orders SET completed_at = ? WHERE id = ?", 
                       (datetime.now().isoformat(), order_id))
        except:
            pass  # Если поля нет, игнорируем
    
    conn.commit()
    conn.close()
    return True

def delete_order_if_completed(order_id):
    """Удалить заказ только если он имеет статус 'выдан'"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Проверяем статус заказа
    cur.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    
    if not row or row['status'] != 'выдан':
        conn.close()
        return False
    
    # Удаляем элементы заказа
    cur.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    # Удаляем заказ
    cur.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    
    conn.commit()
    conn.close()
    return True

def list_orders_filtered(status=None):
    """Получить заказы с фильтрацией (совместимо с list_orders)"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Базовый запрос такой же как в list_orders
    query = """
        SELECT o.*, g.phone as guest_phone, g.name as guest_name 
        FROM orders o 
        LEFT JOIN guests g ON o.guest_id = g.id 
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND o.status = ?"
        params.append(status)
    
    query += " ORDER BY o.created_at DESC"
    
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    
    # Добавляем items для каждого заказа (совместимо с текущим форматом)
    for order in rows:
        cur.execute("""
            SELECT oi.dish_id, oi.quantity
            FROM order_items oi
            WHERE oi.order_id = ?
        """, (order['id'],))
        order['items'] = [dict(item) for item in cur.fetchall()]
    
    conn.close()
    return rows