# check_db.py - Проверяем БД напрямую
import sqlite3
import json
from datetime import datetime

def check_database():
    print("=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")
    
    # Подключаемся к БД
    conn = sqlite3.connect('db/tea_house.db')
    conn.row_factory = sqlite3.Row  # Чтобы получать данные как словарь
    cursor = conn.cursor()
    
    # 1. Проверяем структуру таблицы dishes
    print("\n1. Структура таблицы 'dishes':")
    cursor.execute("PRAGMA table_info(dishes)")
    columns = cursor.fetchall()
    
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        not_null = "NOT NULL" if col[3] else "NULL"
        pk = "PRIMARY KEY" if col[5] else ""
        print(f"   {col_name:20} {col_type:15} {not_null:10} {pk}")
    
    # 2. Проверяем последние 5 блюд
    print("\n2. Последние 5 блюд в БД:")
    cursor.execute("""
        SELECT id, name, image_path, created_at 
        FROM dishes 
        ORDER BY id DESC 
        LIMIT 5
    """)
    
    recent_dishes = cursor.fetchall()
    
    if not recent_dishes:
        print("   В таблице нет записей!")
    else:
        for dish in recent_dishes:
            print(f"   ID: {dish['id']:3} | Название: {dish['name'][:30]:30} | image_path: {dish['image_path'] or 'NULL'}")
    
    # 3. Проверяем конкретно блюда без image_path
    print("\n3. Блюда с пустым image_path:")
    cursor.execute("""
        SELECT id, name, category_id 
        FROM dishes 
        WHERE image_path IS NULL OR image_path = ''
    """)
    
    empty_path_dishes = cursor.fetchall()
    
    if not empty_path_dishes:
        print("   Все блюда имеют image_path ✓")
    else:
        print(f"   Найдено {len(empty_path_dishes)} блюд без image_path:")
        for dish in empty_path_dishes:
            print(f"   - ID: {dish['id']}, Название: '{dish['name']}'")
    
    # 4. Проверяем таблицу dishes_ingredients (связи)
    print("\n4. Проверяем связи блюд и ингредиентов:")
    cursor.execute("SELECT dish_id, COUNT(*) as cnt FROM dishes_ingredients GROUP BY dish_id LIMIT 5")
    ingredient_counts = cursor.fetchall()
    
    for row in ingredient_counts:
        print(f"   Блюдо {row['dish_id']} имеет {row['cnt']} ингредиентов")
    
    # 5. Создаем тестовую запись напрямую
    print("\n5. Тест: создаем блюдо напрямую в БД...")
    
    test_dish = {
        'name': f'ТЕСТ из скрипта {datetime.now().strftime("%H:%M:%S")}',
        'description': 'Тестовое блюдо созданное напрямую',
        'price': 99.99,
        'category_id': 1,
        'image_path': '/images/test_direct.jpg',  # Явно задаем путь
        'is_available': 1,
        'created_at': datetime.now().isoformat()
    }
    
    try:
        cursor.execute('''
            INSERT INTO dishes (name, description, price, category_id, image_path, is_available, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_dish['name'],
            test_dish['description'],
            test_dish['price'],
            test_dish['category_id'],
            test_dish['image_path'],  # Здесь должен записаться путь
            test_dish['is_available'],
            test_dish['created_at']
        ))
        
        test_id = cursor.lastrowid
        conn.commit()
        
        print(f"   ✓ Создано тестовое блюдо ID: {test_id}")
        
        # Проверяем, что записалось
        cursor.execute("SELECT image_path FROM dishes WHERE id = ?", (test_id,))
        saved_dish = cursor.fetchone()
        print(f"   Сохраненный image_path: '{saved_dish['image_path']}'")
        
    except Exception as e:
        print(f"   ✗ Ошибка при создании: {e}")
    
    # 6. Проверяем общее количество
    cursor.execute("SELECT COUNT(*) as total FROM dishes")
    total = cursor.fetchone()['total']
    print(f"\n6. Всего блюд в БД: {total}")
    
    conn.close()
    
    print("\n=== РЕКОМЕНДАЦИИ ===")
    
    # Анализируем проблему
    cursor.execute("SELECT COUNT(*) as with_path FROM dishes WHERE image_path IS NOT NULL AND image_path != ''")
    with_path = cursor.fetchone()['with_path']
    
    if with_path == 0:
        print("❌ Ни одно блюдо не имеет image_path!")
        print("   Возможные причины:")
        print("   1. Фронтенд отправляет 'image_url' вместо 'image_path'")
        print("   2. Функция create_dish() не сохраняет image_path")
        print("   3. В payload нет поля image_path")
    elif with_path < total:
        print(f"⚠️  Только {with_path} из {total} блюд имеют image_path")
        print("   Некоторые блюда создаются без изображений")
    else:
        print("✓ Все блюда имеют image_path - проблема в отображении?")

def check_frontend_payload():
    """Симулируем то, что отправляет фронтенд"""
    print("\n=== СИМУЛЯЦИЯ ФРОНТЕНДА ===")
    
    # То, что отправляет menu.html (collectDishForm)
    frontend_payload = {
        "name": "Тестовое блюдо",
        "price": 250.00,
        "category_id": "1",
        "tag_ids": ["1", "2"],
        "ingredient_ids": ["1", "2", "3"],
        "description": "Описание тестового блюда",
        "image_url": "/images/test_image.jpg"  # <-- ВНИМАНИЕ: image_url, не image_path!
    }
    
    print("Фронтенд отправляет (collectDishForm):")
    for key, value in frontend_payload.items():
        print(f"  {key}: {value}")
    
    print("\nПроблема: фронтенд отправляет 'image_url', а БД ждет 'image_path'!")
    print("Решение: в функции collectDishForm() заменить:")
    print("  const image_url = qs('#dish_image_url').value.trim();")
    print("  на:")
    print("  const image_path = qs('#dish_image_url').value.trim();")

if __name__ == "__main__":
    check_database()
    check_frontend_payload()