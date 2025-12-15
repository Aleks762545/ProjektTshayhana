// ==============================
// ФУНКЦИОНАЛ ИИ-ОФИЦИАНТА - ОТЛАДОЧНАЯ ВЕРСИЯ v2
// ==============================

console.log('🚀 === ЗАГРУЖЕН ОТЛАДОЧНЫЙ СКРИПТ ai_waiter_debug.js ===');

// Состояние
let allDishes = []; // Кэш всех блюд (как в menu.js)

// ==============================
// УТИЛИТЫ ПОИСКА
// ==============================

/**
 * Ищет блюдо в основной БД по названию
 */
function findDishByName(dishName) {
    if (!dishName || !allDishes.length) {
        console.log(`🔍 Поиск блюда "${dishName}": нет названия или пустой кэш`);
        return null;
    }
    
    const cleanName = dishName.toLowerCase().trim();
    console.log(`🔍 Ищу блюдо "${cleanName}" в ${allDishes.length} блюдах`);
    
    // 1. Точное совпадение (без учета регистра)
    let dish = allDishes.find(d => {
        if (!d.name) return false;
        return d.name.toLowerCase().trim() === cleanName;
    });
    
    if (dish) {
        console.log(`✅ Найдено точное совпадение: "${dish.name}"`);
        return dish;
    }
    
    // 2. Частичное совпадение (название содержит искомое)
    dish = allDishes.find(d => {
        if (!d.name) return false;
        return d.name.toLowerCase().includes(cleanName);
    });
    
    if (dish) {
        console.log(`✅ Найдено частичное совпадение: "${dish.name}" содержит "${cleanName}"`);
        return dish;
    }
    
    // 3. Ищем по ключевым словам
    const searchWords = cleanName.split(' ').filter(word => word.length > 2);
    
    if (searchWords.length > 0) {
        dish = allDishes.find(d => {
            if (!d.name) return false;
            const dName = d.name.toLowerCase();
            return searchWords.some(word => dName.includes(word));
        });
        
        if (dish) {
            console.log(`✅ Найдено по ключевым словам: "${dish.name}" содержит одно из [${searchWords.join(', ')}]`);
            return dish;
        }
    }
    
    // 4. Ищем в описании
    dish = allDishes.find(d => {
        if (!d.name && !d.description) return false;
        const dDesc = (d.description || '').toLowerCase();
        return dDesc.includes(cleanName);
    });
    
    if (dish) {
        console.log(`✅ Найдено в описании: "${dish.name}" (в описании есть "${cleanName}")`);
        return dish;
    }
    
    console.log(`❌ Блюдо "${dishName}" не найдено в основной БД`);
    return null;
}

// ==============================
// ЗАГРУЗКА ДАННЫХ (как в menu.js)
// ==============================

/**
 * Загрузка всех блюд из БД (аналогично menu.js)
 */
async function loadAllDishes() {
    console.log('🔄 === НАЧАЛО ЗАГРУЗКИ БЛЮД ===');
    try {
        console.log('📡 Импортирую database.js...');
        const { default: db } = await import('/db/database.js?v=' + Date.now());
        console.log('✅ database.js загружен');

        console.log('📡 Запрашиваю блюда через db.getDishes()...');
        const dishesResponse = await db.getDishes();
        console.log('📦 Структура ответа:', typeof dishesResponse);
        
        if (!dishesResponse) {
            throw new Error('Пустой ответ от сервера');
        }
        
        let loadedDishes = [];
        
        // Обработка разных форматов ответа
        if (Array.isArray(dishesResponse)) {
            console.log('📊 Ответ - массив');
            loadedDishes = dishesResponse;
        } else if (dishesResponse.data && Array.isArray(dishesResponse.data)) {
            console.log('📊 Ответ - объект с data-массивом');
            loadedDishes = dishesResponse.data;
        } else if (dishesResponse.success && dishesResponse.data && Array.isArray(dishesResponse.data)) {
            console.log('📊 Ответ - объект с success и data');
            loadedDishes = dishesResponse.data;
        } else if (typeof dishesResponse === 'object') {
            console.log('📊 Ответ - простой объект');
            loadedDishes = Object.values(dishesResponse);
        } else {
            console.warn('⚠️ Неизвестный формат ответа:', dishesResponse);
        }
        
        console.log(`📊 Загружено элементов: ${loadedDishes.length}`);
        
        // Нормализация данных
        loadedDishes = loadedDishes.map((d, index) => {
            const normalized = {
                ...d,
                // Стандартизируем ID
                Id: d.Id || d.id || d.dish_id,
                id: d.id || d.Id || d.dish_id,
                // Стандартизируем название
                name: d.name || d.Name || '',
                // Стандартизируем пути к изображениям
                image_url: d.image_url || d.imageUrl || d.image,
                image_path: d.image_path || d.imagePath || d.img_path
            };
            
            // Логируем первые 3 блюда для отладки
            if (index < 3) {
                console.log(`🍽️ Блюдо ${index + 1}: "${normalized.name}"`);
                console.log(`   ID: ${normalized.id}, Id: ${normalized.Id}`);
                console.log(`   image_url: "${normalized.image_url}"`);
                console.log(`   image_path: "${normalized.image_path}"`);
            }
            
            return normalized;
        });
        
        allDishes = loadedDishes;
        console.log(`✅ Успешно загружено ${allDishes.length} блюд`);
        console.log('🏁 === ЗАВЕРШЕНО ЗАГРУЗКИ БЛЮД ===\n');
        return allDishes;
        
    } catch (error) {
        console.error('❌ ОШИБКА ЗАГРУЗКИ БЛЮД:', error);
        console.error('🔧 Стек ошибки:', error.stack);
        return [];
    }
}

// ==============================
// ОСНОВНЫЕ ФУНКЦИИ ЧАТА
// ==============================

/**
 * Добавление сообщения в чат
 */
function appendMessage(text, who = 'bot') {
    const messagesEl = document.getElementById('messages');
    if (!messagesEl) {
        console.error('❌ Не найден элемент #messages');
        return;
    }
    
    const el = document.createElement('div');
    el.className = 'message ' + (who === 'user' ? 'user' : 'bot');
    el.innerText = text;
    
    // Добавляем время сообщения
    const now = new Date();
    const timeString = now.toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    el.setAttribute('data-time', timeString);
    
    messagesEl.appendChild(el);
    
    // Плавная прокрутка
    messagesEl.scrollTo({
        top: messagesEl.scrollHeight,
        behavior: 'smooth'
    });
}

/**
 * Отправка сообщения ИИ
 */
async function sendMessage() {
    console.log('📤 === ОТПРАВКА СООБЩЕНИЯ ИИ ===');
    const inputEl = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    
    if (!inputEl || !sendBtn) {
        console.error('❌ Не найдены элементы чата');
        return;
    }
    
    const text = inputEl.value.trim();
    console.log('📝 Текст сообщения:', text);
    if (!text) return;
    
    // Блокируем кнопку на время отправки
    sendBtn.disabled = true;
    sendBtn.textContent = 'Отправка...';
    
    appendMessage(text, 'user');
    inputEl.value = '';
    inputEl.style.height = 'auto';
    
    try {
        console.log('📡 Отправляю запрос к /api/ai/chat...');
        const res = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, top_k: 3 })
        });
        
        console.log('📦 Статус ответа:', res.status, res.statusText);
        
        if (!res.ok) throw new Error('Ошибка сети: ' + res.status);
        const payload = await res.json();
        
        console.log('📦 Полный ответ от ИИ:', payload);
        
        if (!payload || !payload.success) {
            console.error('❌ ИИ вернул ошибку:', payload);
            appendMessage('ИИ временно недоступен. Попробуйте позже.', 'bot');
            return;
        }

        const data = payload.data || {};
        const message = data.message || 'Готово.';
        console.log('💬 Текстовый ответ ИИ:', message);
        appendMessage(message, 'bot');

        const suggestions = Array.isArray(data.suggestions) ? data.suggestions : [];
        console.log('🎯 Рекомендации от ИИ (suggestions):', suggestions);
        console.log('🎯 Количество рекомендаций:', suggestions.length);
        
        if (suggestions.length > 0) {
            // Показываем детали каждой рекомендации
            suggestions.forEach((suggestion, index) => {
                console.log(`🎯 Рекомендация ${index + 1}:`, suggestion);
                if (suggestion && typeof suggestion === 'object') {
                    console.log(`   Поля:`, Object.keys(suggestion));
                }
            });
            
            await renderRecommendations(suggestions.slice(0, 3));
            expandRecs();
        } else {
            console.log('⚠️ Нет рекомендаций');
            collapseRecs();
        }

    } catch (err) {
        console.error('❌ ОШИБКА ПРИ ОБРАЩЕНИИ К СЕРВЕРУ:', err);
        appendMessage('Произошла ошибка при обращении к серверу.', 'bot');
    } finally {
        // Восстанавливаем кнопку
        sendBtn.disabled = false;
        sendBtn.textContent = 'Отправить';
        console.log('🏁 === ЗАВЕРШЕНО ОТПРАВКИ СООБЩЕНИЯ ===\n');
    }
}

/**
 * Отображение рекомендаций (с загрузкой полных данных)
 */
async function renderRecommendations(items) {
    console.log('🚀 === НАЧАЛО RENDER RECOMMENDATIONS ===');
    console.log('📦 Получены рекомендации от ИИ (items):', items);
    console.log('📦 Тип items:', typeof items, 'Длина:', items ? items.length : 0);
    
    const recCards = document.getElementById('recCards');
    const miniSubtitle = document.getElementById('miniSubtitle');
    
    if (!recCards) {
        console.error('❌ Не найден элемент #recCards');
        return;
    }
    
    recCards.innerHTML = '';
    
    if (!items || items.length === 0) {
        console.warn('⚠️ Рекомендации пусты или items не массив');
        const emptyMsg = document.createElement('div');
        emptyMsg.className = 'empty-recommendations';
        emptyMsg.innerHTML = '<p>Рекомендации будут отображаться здесь</p>';
        recCards.appendChild(emptyMsg);
        return;
    }

    console.log('🛒 Кэш всех блюд (allDishes):', allDishes);
    console.log('🛒 Длина кэша allDishes:', allDishes.length);
    
    // Если кэш пуст, попробуем загрузить снова
    if (allDishes.length === 0) {
        console.log('🔄 Кэш блюд пуст, пытаюсь загрузить...');
        await loadAllDishes();
        console.log('✅ После перезагрузки длина кэша:', allDishes.length);
    }

    // Выводим список всех блюд в кэше для отладки
    console.log('📋 Список всех блюд в кэше:');
    allDishes.forEach((dish, index) => {
        console.log(`   ${index + 1}. "${dish.name}" (ID: ${dish.id || dish.Id})`);
    });

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        console.log(`\n📌 === ОБРАБОТКА РЕКОМЕНДАЦИИ ${i + 1}/${items.length} ===`);
        console.log('📝 Тип элемента:', typeof item);
        console.log('📝 Значение элемента:', item);

        // Обработка строковых рекомендаций
        if (typeof item === 'string') {
            console.log(`📛 Элемент ${i} - строка: "${item}"`);
            const box = document.createElement('div');
            box.className = 'dish-card';
            box.innerHTML = `
              <div class="body">
                <h4>${escapeHtml(item)}</h4>
                <p>Рекомендованное блюдо</p>
                <div class="row">
                  <div class="price">—</div>
                  <button class="more-btn">Подробнее</button>
                </div>
              </div>
            `;
            recCards.appendChild(box);
            continue;
        }

        const dish = item.dish || item;
        console.log(`🍽️ Блюдо ${i}:`, dish);
        console.log(`🔑 Все поля блюда ${i}:`, Object.keys(dish));
        
        // Нормализуем ID из данных ИИ
        const rawId = dish.id || dish.Id || dish.dish_id || dish.key;
        console.log(`🆔 ID от ИИ: rawId = "${rawId}" (тип: ${typeof rawId})`);
        
        const dishIdFromAI = rawId ? Number(rawId) : null;
        console.log(`🆔 ID от ИИ после преобразования: ${dishIdFromAI}`);
        
        // Ищем блюдо в основной БД
        let fullDish = null;
        let foundById = false;
        
        if (dishIdFromAI) {
            // Пробуем найти по ID
            console.log(`🔍 Ищу блюдо по ID=${dishIdFromAI} в основной БД...`);
            fullDish = allDishes.find(d => {
                const dId = d.Id || d.id || d.dish_id;
                return dId == dishIdFromAI;
            });
            
            if (fullDish) {
                foundById = true;
                console.log(`✅ Найдено по ID: "${fullDish.name}"`);
            } else {
                console.log(`❌ Не найдено по ID ${dishIdFromAI}, пробую по названию`);
            }
        }
        
        // Если не нашли по ID, ищем по названию
        if (!fullDish && dish.name) {
            console.log(`🔍 Ищу блюдо "${dish.name}" по названию...`);
            fullDish = findDishByName(dish.name);
        }
        
        // Используем полные данные если нашли, иначе базовые от ИИ
        const finalDish = fullDish || dish;
        const finalDishId = fullDish ? (fullDish.Id || fullDish.id) : dishIdFromAI;
        
        console.log(`🎯 Использую данные:`, fullDish ? 'ИЗ ОСНОВНОЙ БД' : 'ОТ ИИ');
        console.log(`🎯 Финальный ID: ${finalDishId}`);
        console.log(`🎯 Найден по:`, foundById ? 'ID' : (fullDish ? 'названию' : 'не найден'));
        
        const dishName = finalDish.name || 'Блюдо';
        const dishPrice = finalDish.price !== undefined ? Math.round(finalDish.price) : '';
        const dishDescription = finalDish.description || dish.category || '';
        
        // ОТЛАДКА ИЗОБРАЖЕНИЙ
        console.log(`🖼️ Поиск пути к изображению для блюда "${dishName}"...`);
        
        // Проверяем разные поля с изображениями
        console.log(`  🔎 Поле image_url: "${finalDish.image_url}"`);
        console.log(`  🔎 Поле image_path: "${finalDish.image_path}"`);
        console.log(`  🔎 Поле image: "${finalDish.image}"`);
        
        let imageUrl = '../static/images/no-image.png';
        
        // Правильная логика определения пути к изображению
        if (finalDish.image_url && finalDish.image_url !== 'null' && finalDish.image_url !== 'undefined') {
            // Если image_url начинается с /static/, добавляем .. для относительного пути
            if (finalDish.image_url.startsWith('/static/')) {
                imageUrl = `..${finalDish.image_url}`;
            } else if (finalDish.image_url.startsWith('http')) {
                imageUrl = finalDish.image_url;
            } else {
                imageUrl = finalDish.image_url;
            }
            console.log(`  ✅ Использую image_url: ${imageUrl}`);
        } else if (finalDish.image_path) {
            // image_path обычно начинается с /images/
            if (finalDish.image_path.startsWith('/images/')) {
                imageUrl = `../static${finalDish.image_path}`;
            } else if (finalDish.image_path.startsWith('images/')) {
                imageUrl = `../static/${finalDish.image_path}`;
            } else {
                imageUrl = `../static/images/${finalDish.image_path}`;
            }
            console.log(`  ✅ Использую image_path: ${imageUrl}`);
        } else if (finalDishId) {
            // Стандартные пути по ID
            const possiblePaths = [
                `../static/images/dishes/${finalDishId}.jpg`,
                `../static/images/dishes/${finalDishId}.png`,
                `../static/images/${finalDishId}.jpg`
            ];
            
            console.log(`  🔎 Пробую стандартные пути:`, possiblePaths);
            imageUrl = possiblePaths[0];
            console.log(`  ✅ Использую стандартный путь: ${imageUrl}`);
        } else {
            console.warn(`  ⚠️ Нет информации об изображении, использую заглушку`);
        }
        
        console.log(`  🖼️ Итоговый путь к изображению: ${imageUrl}`);

        const card = document.createElement('div');
        card.className = 'dish-card';
        
        // Добавляем data-атрибут для обратной связи
        if (finalDishId) {
            card.setAttribute('data-dish-id', finalDishId);
            console.log(`  🏷️ Добавлен data-атрибут data-dish-id="${finalDishId}"`);
        } else {
            console.warn(`  ⚠️ Не могу добавить data-dish-id - нет ID`);
        }
        
        card.innerHTML = `
            <div class="img" style="background-image:url('${escapeAttr(imageUrl)}'); background-color: var(--color-primary);" 
                 onerror="console.error('❌ Ошибка загрузки изображения для блюда ${finalDishId || 'без ID'}:', this.style.backgroundImage); this.style.backgroundImage='url(\'../static/images/no-image.png\')';">
            </div>
            <div class="body">
              <h4>${escapeHtml(dishName)}</h4>
              <p>${escapeHtml(dishDescription)}</p>
              <div class="row">
                <div class="price">${dishPrice ? dishPrice + ' ₽' : ''}</div>
                <div style="display:flex;gap:8px;">
                  <button class="add-btn" aria-label="Добавить ${escapeHtml(dishName)} в корзину"
                          ${finalDishId ? '' : 'disabled'}
                          data-dish-id="${finalDishId || ''}">
                    ${finalDishId ? 'Заказать' : 'Недоступно'}
                  </button>
                  ${finalDishId ? `<button class="more-btn" aria-label="Подробнее о ${escapeHtml(dishName)}">Подробнее</button>` : ''}
                </div>
              </div>
            </div>
        `;

        // Настройка кнопок
        if (finalDishId) {
            const addBtn = card.querySelector('.add-btn');
            const moreBtn = card.querySelector('.more-btn');
            
            addBtn.addEventListener('click', async function() {
                console.log(`🛒 НАЖАТА КНОПКА "ЗАКАЗАТЬ"`);
                console.log(`  ID блюда: ${finalDishId}`);
                console.log(`  Название: ${dishName}`);
                console.log(`  Цена: ${dishPrice}`);
                console.log(`  Источник данных: ${fullDish ? 'основная БД' : 'ИИ'}`);
                
                // Проверяем, есть ли глобальная функция addToCart
                if (typeof window.addToCart === 'function') {
                    console.log(`  Вызываю window.addToCart(${finalDishId}, "${dishName}", ${dishPrice})`);
                    await window.addToCart(finalDishId, dishName, dishPrice);
                    appendMessage('Добавил "' + dishName + '" в корзину ✓', 'bot');
                } else {
                    console.error('❌ Функция addToCart не найдена!');
                    alert('Ошибка: функция добавления в корзину недоступна');
                }
            });
            
            if (moreBtn) {
                moreBtn.addEventListener('click', () => {
                    console.log(`🔍 Открытие деталей блюда ID=${finalDishId}`);
                    openDishDetails(finalDishId);
                });
            }
        } else {
            const addBtn = card.querySelector('.add-btn');
            addBtn.disabled = true;
            addBtn.title = 'ID блюда не найден';
            console.warn(`  ⚠️ Кнопка "Заказать" отключена - нет ID`);
        }

        recCards.appendChild(card);
        console.log(`✅ Карточка для "${dishName}" создана\n`);
    }
    
    console.log('🏁 === ЗАВЕРШЕНО RENDER RECOMMENDATIONS ===\n');
    
    // Обновляем подзаголовок
    if (miniSubtitle) {
        const count = items.length;
        const wordForm = getRussianWordForm(count, ['рекомендация', 'рекомендации', 'рекомендаций']);
        miniSubtitle.textContent = `${count} ${wordForm}`;
    }
}

/**
 * Развернуть панель рекомендаций
 */
function expandRecs() {
    const recPanel = document.getElementById('recPanel');
    const toggleRecs = document.getElementById('toggleRecs');
    const aiChatCard = document.querySelector('.ai-chat-card');
    
    if (recPanel && toggleRecs) {
        recPanel.classList.add('open');
        recPanel.setAttribute('aria-hidden', 'false');
        toggleRecs.textContent = 'Свернуть';
        toggleRecs.setAttribute('aria-expanded', 'true');
        
        if (aiChatCard) {
            aiChatCard.classList.add('with-recs');
        }
    }
}

/**
 * Свернуть панель рекомендаций
 */
function collapseRecs() {
    const recPanel = document.getElementById('recPanel');
    const toggleRecs = document.getElementById('toggleRecs');
    const aiChatCard = document.querySelector('.ai-chat-card');
    
    if (recPanel && toggleRecs) {
        recPanel.classList.remove('open');
        recPanel.setAttribute('aria-hidden', 'true');
        toggleRecs.textContent = 'Развернуть';
        toggleRecs.setAttribute('aria-expanded', 'false');
        
        if (aiChatCard) {
            aiChatCard.classList.remove('with-recs');
        }
    }
}

/**
 * Открыть подробности блюда
 */
function openDishDetails(dishId) {
    if (!dishId) return;
    // Используем тот же путь что и в menu.js
    window.location.href = '/menu/dishes/' + dishId;
}

// ==============================
// УТИЛИТЫ
// ==============================

/**
 * Экранирование HTML
 */
function escapeHtml(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

/**
 * Экранирование атрибутов
 */
function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, '&#39;').replace(/"/g, '&#34;');
}

/**
 * Получение правильной формы слова для русского языка
 */
function getRussianWordForm(number, words) {
    const cases = [2, 0, 1, 1, 1, 2];
    return words[(number % 100 > 4 && number % 100 < 20) ? 2 : cases[Math.min(number % 10, 5)]];
}

// ==============================
// ИНИЦИАЛИЗАЦИЯ
// ==============================

/**
 * Инициализация страницы
 */
async function initializeAIChat() {
    console.log('🎬 === ИНИЦИАЛИЗАЦИЯ ИИ-ЧАТА ===');
    
    // Загружаем все блюда
    await loadAllDishes();
    
    // Находим элементы
    const inputEl = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const toggleRecs = document.getElementById('toggleRecs');
    
    if (!inputEl || !sendBtn) {
        console.error('❌ Не найдены элементы чата!');
        return;
    }
    
    console.log('✅ Элементы чата найдены');
    
    // Авторесайз текстового поля
    inputEl.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Фокус на поле ввода при загрузке
    setTimeout(() => inputEl.focus(), 100);

    // Инициализация
    appendMessage('Привет! Я — Aiгерим. Спроси меня о блюдах, диетах или вариантах для заказа.', 'bot');

    // Слушатели
    sendBtn.addEventListener('click', sendMessage);
    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    if (toggleRecs) {
        toggleRecs.addEventListener('click', () => {
            const recPanel = document.getElementById('recPanel');
            if (recPanel && recPanel.classList.contains('open')) {
                collapseRecs();
            } else {
                expandRecs();
            }
        });
    }
    
    console.log('✅ ИИ-чат инициализирован');
    console.log('🏁 === ЗАВЕРШЕНО ИНИЦИАЛИЗАЦИИ ===\n');
}

// Запускаем инициализацию при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM загружен, запускаю инициализацию ИИ-чата...');
    initializeAIChat();
});

// Экспорт для внешних сценариев
window.aiWaiterDebug = { 
    renderRecommendations, 
    sendMessage,
    loadAllDishes,
    findDishByName
};

console.log('✅ Отладочный скрипт ai_waiter_debug.js полностью загружен');