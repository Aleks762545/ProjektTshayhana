-- db/init.sql (перевённый под нормализованную структуру)
PRAGMA foreign_keys = ON;

-- DROP (безопасно при разработке)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS guests;
DROP TABLE IF EXISTS dish_ingredients;
DROP TABLE IF EXISTS dish_tags;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS dishes;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS meal_times;
DROP TABLE IF EXISTS available_ingredients;
DROP TABLE IF EXISTS ingredients_hierarchy;
DROP TABLE IF EXISTS cache_entries;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meal_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tag_type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    category_id INTEGER,
    meal_time_id INTEGER,
    spice_level INTEGER NOT NULL DEFAULT 0,
    is_vegan INTEGER NOT NULL DEFAULT 0,
    cooking_time INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT,
    is_available INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY(meal_time_id) REFERENCES meal_times(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS dish_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id INTEGER,
    tag_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dish_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id INTEGER,
    ingredient_id INTEGER,
    quantity TEXT,
    is_primary INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    FOREIGN KEY(ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE,
    name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id INTEGER,
    table_number TEXT,
    total REAL,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guest_id) REFERENCES guests(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    dish_id INTEGER,
    quantity INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ingredients_hierarchy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    child_id INTEGER,
    FOREIGN KEY(parent_id) REFERENCES ingredients(id),
    FOREIGN KEY(child_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS available_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER,
    quantity TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS cache_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,
    value TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT
);

-- Initial categories (ids fixed so mapping is predictable)
INSERT OR IGNORE INTO categories (id, name, created_at) VALUES
(1,'Холодные закуски','2024-01-15T10:00:00Z'),
(2,'Горячие закуски','2024-01-15T10:00:00Z'),
(3,'Основные блюда','2024-01-15T10:00:00Z'),
(4,'Шашлыки','2024-01-15T10:00:00Z'),
(5,'Супы','2024-01-15T10:00:00Z'),
(6,'Десерты','2024-01-15T10:00:00Z'),
(7,'Напитки','2024-01-15T10:00:00Z');

-- meal times
INSERT OR IGNORE INTO meal_times (id, name) VALUES
(1,'Lunch'),
(2,'Dinner'),
(3,'Breakfast');

-- tags (keep the same basic tags)
INSERT OR IGNORE INTO tags (id, name, tag_type) VALUES
(1,'острое','spice'),
(2,'вегетарианское','diet'),
(3,'новинка','special'),
(4,'хит','special'),
(5,'постное','diet');

-- base ingredients (existing ones) and additional ones used by dishes
-- Explicit ids to make dish_ingredients easier to compose
INSERT OR IGNORE INTO ingredients (id, name, description) VALUES
(1,'Баранина','Мясо молодого барашка'),
(2,'Рис','Рис для плова'),
(3,'Морковь','Свежая морковь'),
(4,'Лук','Репчатый лук'),
(5,'Помидоры','Спелые помидоры'),
(6,'Зелень','Свежая зелень'),
(7,'Говядина','Мясо говядины'),
(8,'Барбарис','Сухие ягоды барбариса'),
(9,'Изюм','Сушёный виноград'),
(10,'Нут','Нут (нутовая крупа)'),
(11,'Лапша','Домашняя лапша'),
(12,'Соевое мясо','Соевые кусочки/субститут'),
(13,'Баклажан','Баклажан'),
(14,'Болгарский перец','Сладкий перец'),
(15,'Тыква','Тыква для фарша'),
(16,'Картофель','Картофель'),
(17,'Курица','Куриное мясо'),
(18,'Тесто','Тесто для самсы/пирожков'),
(19,'Перец острый','Острый перец/чили'),
(20,'Чечевица','Чечевица'),
(21,'Кокосовое молоко','Кокосовое молоко'),
(22,'Огурец','Огурец'),
(23,'Укроп','Укроп'),
(24,'Петрушка','Петрушка'),
(25,'Чеснок','Чеснок'),
(26,'Мёд','Мёд'),
(27,'Сахар','Сахар'),
(28,'Яблоко','Яблоко'),
(29,'Виноград','Виноград'),
(30,'Дыня','Дыня'),
(31,'Молоко','Молоко'),
(32,'Закваска','Закваска'),
(33,'Чай','Чай');

-- Now insert dishes using new schema.
-- We'll keep the original dish order and assign explicit ids 1..30 to match earlier references.
-- Mapping rules used:
-- 'main' -> category_id 3 (Основные блюда)
-- 'soup' -> category_id 5 (Супы)
-- 'salad' -> category_id 1 (Холодные закуски)
-- 'snack' -> category_id 2 (Горячие закуски)
-- 'dessert' -> category_id 6 (Десерты)
-- 'drink' -> category_id 7 (Напитки)
-- 'shashlik' or 'shashlik' items mapped to 4 (Шашлыки)
-- meal_time_id default = 1 (Lunch); adjust later via admin UI if needed
INSERT OR IGNORE INTO dishes (id, name, description, price, category_id, meal_time_id, spice_level, is_vegan, cooking_time, image_path, is_available) VALUES
(1,'Самаркандский плов','Классический узбекский плов с морковью, барбарисом и сочным мясом.',12.5,3,1,1,0,40,'/images/plov_samarkand.jpg',1),
(2,'Ферганский плов','Рассыпчатый плов с большим количеством моркови и специй.',13.0,3,1,1,0,45,'/images/plov_fergana.jpg',1),
(3,'Плов с изюмом','Сладковатый плов с изюмом и зирой.',11.0,3,1,0,1,40,'/images/plov_raisin.jpg',1),
(4,'Плов с нута','Плов с нутом и нежными овощами.',11.5,3,1,0,1,40,'/images/plov_nut.jpg',1),
(5,'Лагман классический','Жареная лапша с овощами и говядиной в ароматной подливе.',10.5,3,1,2,0,30,'/images/lagman.jpg',1),
(6,'Вегетарианский лагман','Овощной лагман с соевой поджаркой.',9.0,3,1,1,1,30,'/images/lagman_veg.jpg',1),
(7,'Гуйру лагман','Острая версия лагмана с большим количеством овощей.',12.0,3,1,3,0,35,'/images/guiru_lagman.jpg',1),
(8,'Манты с тыквой','Нежные манты с ароматной сладкой тыквой.',8.5,3,1,0,1,50,'/images/manty_pumpkin.jpg',1),
(9,'Манты с мясом','Классические манты с сочной бараниной.',9.5,3,1,1,0,50,'/images/manty_meat.jpg',1),
(10,'Шашлык из курицы','Нежный куриный шашлык на мангале.',9.0,4,1,1,0,25,'/images/shashlik_chicken.jpg',1),
(11,'Шашлык из баранины','Сочный шашлык из баранины с ароматными специями.',12.0,4,1,2,0,30,'/images/shashlik_lamb.jpg',1),
(12,'Шурпа','Бульонный суп с мясом и овощами.',7.5,5,1,1,0,60,'/images/shurpa.jpg',1),
(13,'Мастава','Густой суп с рисом и томатами.',7.0,5,1,1,0,50,'/images/mastava.jpg',1),
(14,'Веган шурпа','Легкая версия шурпы без мяса.',6.5,5,1,0,1,40,'/images/shurpa_veg.jpg',1),
(15,'Чечевичный карри','Острый карри из красной чечевицы.',8.0,3,1,2,1,30,'/images/curry_lentil.jpg',1),
(16,'Куриное карри','Нежное куриное карри в кокосовом молоке.',10.0,3,1,1,0,35,'/images/curry_chicken.jpg',1),
(17,'Рис с овощами','Легкое вегетарианское блюдо.',6.5,3,1,0,1,20,'/images/rice_veg.jpg',1),
(18,'Ачичук','Традиционный узбекский салат из томатов и лука.',4.0,1,1,0,1,10,'/images/achuchuk.jpg',1),
(19,'Свежий салат','Овощной микс из огурцов, томатов и зелени.',3.5,1,1,0,1,8,'/images/salad_fresh.jpg',1),
(20,'Салат с курицей','Сытный салат из курицы, овощей и зелени.',5.5,1,1,0,0,12,'/images/salad_chicken.jpg',1),
(21,'Самса с мясом','Самса с рубленой бараниной.',3.0,2,1,1,0,25,'/images/samsa_meat.jpg',1),
(22,'Самса с картошкой','Вегетарианская самса с картофелем.',2.5,2,1,0,1,25,'/images/samsa_potato.jpg',1),
(23,'Куриные крылышки острые','Маленькая порция острых крылышек.',6.5,2,1,3,0,20,'/images/wings_spicy.jpg',1),
(24,'Хумус с лавашем','Восточная закуска из нута.',4.5,2,1,0,1,5,'/images/hummus.jpg',1),
(25,'Чак-чак','Сладкое восточное лакомство с медом.',5.0,6,1,0,1,0,'/images/chakchak.jpg',1),
(26,'Холодный рисовый пудинг','Рисовый десерт с кокосовым молоком.',4.5,6,1,0,1,0,'/images/rice_pudding.jpg',1),
(27,'Фруктовая тарелка','Сезонные фрукты.',4.0,6,1,0,1,0,'/images/fruits.jpg',1),
(28,'Кумыс','Освежающий традиционный напиток.',3.5,7,3,0,0,0,'/images/kumys.jpg',1),
(29,'Зеленый чай','Классический заваренный чай.',2.0,7,3,0,1,0,'/images/tea_green.jpg',1),
(30,'Черный чай','Крепкий черный чай.',2.0,7,3,0,1,0,'/images/tea_black.jpg',1);

-- dish_tags: minimal mapping (preserve earlier example tags where applicable)
-- previous mapping lines referenced dishes 1..6 and tags; we include those and leave others empty by default
INSERT OR IGNORE INTO dish_tags (dish_id, tag_id) VALUES
(1,4),(2,1),(3,4),(4,3),(5,2),(5,5);

-- dish_ingredients: map ingredients to dishes
-- We'll add basic ingredient relations. Quantities left nullable where not specified.
-- Dish 1: Самаркандский плов
INSERT OR IGNORE INTO dish_ingredients (dish_id, ingredient_id, quantity, is_primary) VALUES
(1,1,'300 г',1),(1,2,'200 г',1),(1,3,'150 г',0),

-- Dish 2: Ферганский плов
(2,2,'200 г',1),(2,3,'150 г',0),(2,7,'200 г',1),

-- Dish 3: Плов с изюмом
(3,2,'200 г',1),(3,9,'50 г',0),(3,3,'100 г',0),

-- Dish 4: Плов с нута
(4,2,'180 г',1),(4,10,'120 г',1),(4,3,'80 г',0),

-- Dish 5: Лагман классический
(5,11,'200 г',1),(5,7,'150 г',1),(5,14,'80 г',0),(5,5,'100 г',0),

-- Dish 6: Вегетарианский лагман
(6,11,'200 г',1),(6,12,'150 г',1),(6,13,'80 г',0),(6,3,'60 г',0),

-- Dish 7: Гуйру лагман
(7,11,'200 г',1),(7,7,'150 г',1),(7,19,'20 г',0),(7,5,'80 г',0),

-- Dish 8: Манты с тыквой
(8,16,'150 г',1),(8,4,'20 г',0),(8,18,'50 г',0),

-- Dish 9: Манты с мясом
(9,1,'200 г',1),(9,4,'20 г',0),(9,25,'2 зубчика',0),

-- Dish 10: Шашлык из курицы
(10,17,'200 г',1),(10,4,'30 г',0),(10,25,'2 зубчика',0),

-- Dish 11: Шашлык из баранины
(11,1,'220 г',1),(11,4,'30 г',0),(11,8,'5 г',0),

-- Dish 12: Шурпа
(12,1,'150 г',1),(12,3,'80 г',0),(12,16,'100 г',0),(12,4,'40 г',0),

-- Dish 13: Мастава
(13,2,'100 г',1),(13,5,'80 г',0),(13,3,'60 г',0),(13,7,'120 г',1),

-- Dish 14: Веган шурпа
(14,3,'100 г',1),(14,16,'100 г',0),(14,4,'40 г',0),

-- Dish 15: Чечевичный карри
(15,20,'150 г',1),(15,25,'5 г',0),(15,5,'50 г',0),

-- Dish 16: Куриное карри
(16,17,'180 г',1),(16,21,'100 мл',0),(16,25,'3 г',0),

-- Dish 17: Рис с овощами
(17,2,'120 г',1),(17,3,'50 г',0),(17,14,'40 г',0),

-- Dish 18: Ачичук
(18,5,'100 г',1),(18,4,'30 г',0),(18,24,'5 г',0),

-- Dish 19: Свежий салат
(19,22,'80 г',1),(19,5,'60 г',0),(19,23,'5 г',0),(19,24,'5 г',0),

-- Dish 20: Салат с курицей
(20,17,'120 г',1),(20,22,'50 г',0),(20,5,'40 г',0),(20,24,'5 г',0),

-- Dish 21: Самса с мясом
(21,1,'150 г',1),(21,4,'20 г',0),(21,18,'50 г',0),

-- Dish 22: Самса с картошкой
(22,16,'150 г',1),(22,4,'20 г',0),(22,18,'50 г',0),

-- Dish 23: Куриные крылышки острые
(23,17,'250 г',1),(23,19,'5 г',0),

-- Dish 24: Хумус с лавашем
(24,10,'120 г',1),(24,26,'1 ч.л.',0),(24,25,'1 зубчик',0),

-- Dish 25: Чак-чак
(25,18,'150 г',1),(25,26,'10 г',0),

-- Dish 26: Холодный рисовый пудинг
(26,2,'120 г',1),(26,21,'80 мл',0),(26,27,'10 г',0),

-- Dish 27: Фруктовая тарелка
(27,28,NULL,0),(27,29,NULL,0),(27,30,NULL,0),

-- Dish 28: Кумыс
(28,31,'250 мл',1),(28,32,'5 г',0),

-- Dish 29: Зеленый чай
(29,33,'200 мл',1),

-- Dish 30: Черный чай
(30,33,'200 мл',1);

-- Sample guests and orders (preserve earlier examples)
INSERT OR IGNORE INTO guests (id, phone, name) VALUES
(1,'+79991234567','Иван Иванов'),
(2,'+79997654321','Мария Петрова');

INSERT OR IGNORE INTO orders (id, guest_id, table_number, total, status) VALUES
(1,1,'5',1050,'completed'),
(2,2,'2',520,'pending');

INSERT OR IGNORE INTO order_items (order_id, dish_id, quantity) VALUES
(1,1,2),(1,6,1),(2,3,1),(2,5,1);