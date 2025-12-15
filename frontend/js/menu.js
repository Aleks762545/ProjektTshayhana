/**
 * Страница меню - функционал (patched)
 * Загрузка категорий и блюд из БД, управление корзиной
 */

// ==============================
// НАСТРОЙКИ И КОНФИГУРАЦИЯ
// ==============================

const CONFIG = {
    CART: {
        STORAGE_KEY: 'tea_house_cart'
    }
};

// ==============================
// ПЕРЕМЕННЫЕ И ЭЛЕМЕНТЫ DOM
// ==============================

// Состояние приложения
let cart = [];
let isCartOpen = false;
let categories = [];
let dishes = [];
let currentOpenCategory = null;

// Элементы DOM
const categoriesContainer = document.getElementById('categoriesContainer');
const loadingElement = document.getElementById('loading');
const cartToggle = document.getElementById('cartToggle');
const cartSidebar = document.getElementById('cartSidebar');
const cartClose = document.getElementById('cartClose');
const cartItems = document.getElementById('cartItems');
const emptyCart = document.getElementById('emptyCart');
const cartCount = document.getElementById('cartCount');
const totalAmount = document.getElementById('totalAmount');
const checkoutBtn = document.getElementById('checkoutBtn');

// Элементы модального окна регистрации
const loginBtn = document.getElementById('loginBtn');
const authModal = document.getElementById('authModal');
const closeModal = document.getElementById('closeModal');
const authForm = document.getElementById('authForm');
const authMessage = document.getElementById('authMessage');

// ==============================
// ФУНКЦИИ ИНИЦИАЛИЗАЦИИ
// ==============================

/**
 * Инициализация страницы меню
 */
async function initializeMenu() {
    console.log('Инициализация страницы меню...');
    loadCart();
    setupEventListeners();
    await loadMenuData();
    updateCartUI();
}

/**
 * Настройка обработчиков событий
 */
function setupEventListeners() {
    // Корзина
    if (cartToggle) {
        cartToggle.addEventListener('click', toggleCart);
    }
    
    if (cartClose) {
        cartClose.addEventListener('click', closeCart);
    }
    
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', handleCheckout);
    }
    
    // Модальное окно регистрации
    if (loginBtn) {
        loginBtn.addEventListener('click', openAuthModal);
    }
    
    if (closeModal) {
        closeModal.addEventListener('click', closeAuthModal);
    }
    
    if (authModal) {
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) {
                closeAuthModal();
            }
        });
    }
    
    if (authForm) {
        authForm.addEventListener('submit', handleAuthSubmit);
    }
    
    // Закрытие по ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (authModal && authModal.classList.contains('active')) {
                closeAuthModal();
            }
            if (isCartOpen) {
                closeCart();
            }
        }
    });
}

// ==============================
// ФУНКЦИИ ЗАГРУЗКИ ДАННЫХ
// ==============================

/**
 * Загрузка данных меню из БД
 */
async function loadMenuData() {
    try {
        // Импортируем database adapter (frontend db module)
        const { default: db } = await import('/db/database.js?v=' + Date.now());

        
        // Загружаем категории
        const categoriesResponse = await db.getCategories();
        if (!categoriesResponse || !categoriesResponse.length && (!categoriesResponse.success && !categoriesResponse.data)) {
            // try older API shape { success, data }
            if (categoriesResponse && categoriesResponse.success && categoriesResponse.data) {
                categories = categoriesResponse.data;
            } else {
                throw new Error('Ошибка загрузки категорий (пустой ответ)');
            }
        } else if (Array.isArray(categoriesResponse)) {
            categories = categoriesResponse;
        } else if (categoriesResponse.data) {
            categories = categoriesResponse.data;
        } else {
            categories = categoriesResponse;
        }
        
        // Загружаем блюда
        const dishesResponse = await db.getDishes();
        if (!dishesResponse || (!dishesResponse.success && !dishesResponse.data && !Array.isArray(dishesResponse))) {
            if (dishesResponse && dishesResponse.success && dishesResponse.data) {
                dishes = dishesResponse.data;
            } else {
                throw new Error('Ошибка загрузки блюд (пустой ответ)');
            }
        } else if (Array.isArray(dishesResponse)) {
            dishes = dishesResponse;
        } else if (dishesResponse.data) {
            dishes = dishesResponse.data;
        } else {
            dishes = dishesResponse;
        }
        
        // Normalization: convert any { id -> Id } expectations
        categories = categories.map(c => {
            return Object.assign({}, c, { Id: c.Id || c.id });
        });
        dishes = dishes.map(d => {
            return Object.assign({}, d, { Id: d.Id || d.id });
        });
        
        // Отображаем меню
        displayMenu();
        
    } catch (error) {
        console.error('Ошибка загрузки меню:', error);
        showError('Не удалось загрузить меню. Пожалуйста, попробуйте позже.');
    }
}

/**
 * Отображение меню на странице
 */
function displayMenu() {
    if (!categoriesContainer) return;
    
    // Скрываем индикатор загрузки
    if (loadingElement) loadingElement.style.display = 'none';
    
    if (!categories || categories.length === 0) {
        showError('Категории не найдены');
        return;
    }
    
    // Создаем HTML для категорий
    const categoriesHTML = categories.map(category => {
        // Фильтруем блюда по категории
        const categoryDishes = dishes.filter(dish => dish && (dish.category_id === category.id || dish.category_id === category.Id));
        
        if (categoryDishes.length === 0) {
            return `
                <div class="category" data-category-id="${category.Id}">
                    <div class="category-header" onclick="toggleCategory(${category.Id})">
                        <h3 class="category-title">${category.name}</h3>
                        <span class="category-icon">▼</span>
                    </div>
                    <div class="category-content">
                        <div class="dishes-grid">
                            <p style="text-align: center; color: var(--text-muted); padding: 40px;">
                                Блюда временно отсутствуют
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="category" data-category-id="${category.Id}">
                <div class="category-header" onclick="toggleCategory(${category.Id})">
                    <h3 class="category-title">${category.name}</h3>
                    <span class="category-icon">▼</span>
                </div>
                <div class="category-content">
                    <div class="dishes-grid">
                        ${categoryDishes.map(dish => createDishCard(dish)).join('')}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    categoriesContainer.innerHTML = categoriesHTML;
}

/**
 * Создание карточки блюда
 */
function createDishCard(dish) {
    if (!dish) return '';

    const dishId = dish.Id || dish.id;
    const dishName = dish.name || 'Без названия';
    const dishDescription = dish.description || 'Описание отсутствует';
    const dishPrice = dish.price || 0;

    // если image_url нет — собираем из image_path
    const imageUrl = dish.image_url 
        ? dish.image_url 
        : (dish.image_path ? `/static${dish.image_path}` : '/static/images/no-image.png');

    return `
        <div class="dish-card" data-dish-id="${dishId}">
            <div class="dish-image">
                <img src="${imageUrl}" alt="${dishName}" onerror="this.src='/static/images/no-image.png'">
            </div>

            <div class="dish-info">
                <div class="dish-header">
                    <h4 class="dish-name">${dishName}</h4>
                    <p class="dish-description">${dishDescription}</p>
                </div>

                <div class="dish-footer">
                    <div class="dish-price">${dishPrice}₽</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${dishId}, '${dishName.replace(/'/g, "\\'")}', ${dishPrice})">
                        <span class="btn-icon">+</span> Добавить
                    </button>
                </div>
            </div>
        </div>
    `;
}


/**
 * Получение ингредиентов блюда (временная реализация)
 */
function getDishIngredients(dishId) {
    // Временная реализация - в реальности нужно загружать из dish_ingredients
    const ingredientsMap = {
        1: "Баранина, рис, морковь, лук, специи",
        2: "Говядина, лапша, овощи, зелень, специи", 
        3: "Баранина, лук, специи, зелень",
        4: "Курица, томаты, лук, специи, зелень",
        5: "Овощи свежие, зелень, соус фирменный",
        6: "Чай зеленый, жасмин"
    };
    
    return ingredientsMap[dishId] || "Свежие ингредиенты";
}

/**
 * Получение граммажа блюда (временная реализация)
 */
function getDishGrammage(dishId) {
    // Временная реализация - в реальности нужно загружать из БД
    const grammageMap = {
        1: "350г",
        2: "400г",
        3: "250г", 
        4: "300г",
        5: "200г",
        6: "500мл"
    };
    
    return grammageMap[dishId] || "стандартная порция";
}

/**
 * Показать сообщение об ошибке
 */
function showError(message) {
    if (!categoriesContainer) return;
    
    categoriesContainer.innerHTML = `
        <div class="error-message">
            <p>${message}</p>
        </div>
    `;
}

// ==============================
// ФУНКЦИИ УПРАВЛЕНИЯ КАТЕГОРИЯМИ
// ==============================

/**
 * Переключение категории (открытие/закрытие)
 */
function toggleCategory(categoryId) {
    const categoryElement = document.querySelector(`[data-category-id="${categoryId}"]`);
    
    if (!categoryElement) return;
    
    // Если категория уже открыта - закрываем её
    if (currentOpenCategory === categoryId) {
        categoryElement.classList.remove('open');
        currentOpenCategory = null;
        return;
    }
    
    // Закрываем предыдущую открытую категорию
    if (currentOpenCategory) {
        const previousCategory = document.querySelector(`[data-category-id="${currentOpenCategory}"]`);
        if (previousCategory) {
            previousCategory.classList.remove('open');
        }
    }
    
    // Открываем новую категорию
    categoryElement.classList.add('open');
    currentOpenCategory = categoryId;
}

// ==============================
// ФУНКЦИИ КОРЗИНЫ
// ==============================

/**
 * Загрузка корзины из localStorage
 */
function loadCart() {
    try {
        const savedCart = localStorage.getItem(CONFIG.CART.STORAGE_KEY);
        if (savedCart) {
            cart = JSON.parse(savedCart);
        }
    } catch (error) {
        console.error('Ошибка загрузки корзины:', error);
        cart = [];
    }
}

/**
 * Сохранение корзины в localStorage
 */
function saveCart() {
    try {
        localStorage.setItem(CONFIG.CART.STORAGE_KEY, JSON.stringify(cart));
    } catch (error) {
        console.error('Ошибка сохранения корзины:', error);
    }
}

/**
 * Открытие/закрытие корзины
 */
function toggleCart() {
    if (isCartOpen) {
        closeCart();
    } else {
        openCart();
    }
}

/**
 * Открытие корзины
 */
function openCart() {
    if (!cartSidebar) return;
    cartSidebar.classList.add('open');
    document.body.classList.add('cart-open');
    isCartOpen = true;
}

/**
 * Закрытие корзины
 */
function closeCart() {
    if (!cartSidebar) return;
    cartSidebar.classList.remove('open');
    document.body.classList.remove('cart-open');
    isCartOpen = false;
}

/**
 * Добавление товара в корзину
 */
function addToCart(dishId, dishName, price) {
    const existingItem = cart.find(item => item.id === dishId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: dishId,
            name: dishName,
            price: price,
            quantity: 1
        });
    }
    
    saveCart();
    updateCartUI();
    
    // Визуальный фидбек
    showAddToCartFeedback(dishId);
}

/**
 * Визуальный фидбек при добавлении в корзину
 */
function showAddToCartFeedback(dishId) {
    const dishCard = document.querySelector(`[data-dish-id="${dishId}"]`);
    if (dishCard) {
        dishCard.style.transform = 'scale(1.05)';
        dishCard.style.boxShadow = '0 8px 25px rgba(205, 127, 50, 0.4)';
        
        setTimeout(() => {
            dishCard.style.transform = '';
            dishCard.style.boxShadow = '';
        }, 300);
    }
}

/**
 * Обновление количества товара
 */
function updateCartItemQuantity(itemId, newQuantity) {
    const item = cart.find(item => item.id === itemId);
    
    if (item) {
        if (newQuantity <= 0) {
            removeFromCart(itemId);
        } else {
            item.quantity = newQuantity;
            saveCart();
            updateCartUI();
        }
    }
}

/**
 * Удаление товара из корзины
 */
function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    saveCart();
    updateCartUI();
}

/**
 * Очистка корзины
 */
function clearCart() {
    cart = [];
    saveCart();
    updateCartUI();
}

/**
 * Обновление интерфейса корзины
 */
function updateCartUI() {
    if (!cartCount || !cartItems || !emptyCart || !totalAmount || !checkoutBtn) return;
    
    // Обновляем счетчик
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    cartCount.textContent = totalItems;
    
    // Обновляем список товаров
    if (cart.length === 0) {
        emptyCart.style.display = 'block';
        cartItems.innerHTML = '';
    } else {
        emptyCart.style.display = 'none';
        
        const itemsHTML = cart.map(item => `
            <div class="cart-item" data-item-id="${item.id}">
                <div class="item-info">
                    <div class="item-name">${item.name || 'Неизвестный товар'}</div>
                    <div class="item-price">${item.price || 0}₽</div>
                </div>
                <div class="item-quantity">
                    <button class="quantity-btn minus" onclick="window.updateCartItemQuantity(${item.id}, ${item.quantity - 1})">-</button>
                    <span class="quantity-value">${item.quantity}</span>
                    <button class="quantity-btn plus" onclick="window.updateCartItemQuantity(${item.id}, ${item.quantity + 1})">+</button>
                </div>
                <button class="remove-btn" onclick="window.removeFromCart(${item.id})" title="Удалить">
                    ×
                </button>
            </div>
        `).join('');
        
        cartItems.innerHTML = itemsHTML;
    }
    
    // Обновляем итоговую сумму
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    totalAmount.textContent = `${total}₽`;
    
    // Активируем/деактивируем кнопку оформления
    checkoutBtn.disabled = cart.length === 0;
}

/**
 * Обработка оформления заказа
 */
async function handleCheckout() {
    if (cart.length === 0) return;
    
    try {
        // Интеграция с бэкендом через database.js
        const { default: db } = await import('/db/database.js?v=' + Date.now());

        
        // Подготовка items в форме [{dish_id, quantity}]
        const items = cart.map(i => ({ dish_id: i.id, quantity: i.quantity }));
        
        // Создаем заказ
        const orderData = {
            table_number: "0",
            items: items,
            guest_phone: localStorage.getItem('guest_phone') || null,
            guest_name: localStorage.getItem('guest_name') || null
        };
        
        const orderResponse = await db.createOrder(orderData);
        
        if (orderResponse && (orderResponse.success || orderResponse.order_id || orderResponse.id)) {
            alert('Заказ успешно оформлен! Скоро мы его приготовим.');
            clearCart();
            closeCart();
        } else {
            throw new Error((orderResponse && orderResponse.message) || 'Ошибка при создании заказа');
        }
        
    } catch (error) {
        console.error('Ошибка оформления заказа:', error);
        alert('Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.');
    }
}

// ==============================
// ФУНКЦИИ РЕГИСТРАЦИИ (общие)
// ==============================

/**
 * Открытие модального окна регистрации
 */
function openAuthModal() {
    if (authModal) {
        authModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Закрытие модального окна регистрации
 */
function closeAuthModal() {
    if (authModal) {
        authModal.classList.remove('active');
        document.body.style.overflow = '';
        resetAuthForm();
    }
}

/**
 * Сброс формы регистрации
 */
function resetAuthForm() {
    if (authForm) {
        authForm.reset();
    }
    hideAuthMessage();
}

/**
 * Показать сообщение об ошибке/успехе
 */
function showAuthMessage(message, type = 'error') {
    if (authMessage) {
        authMessage.textContent = message;
        authMessage.className = `auth-message ${type}`;
        authMessage.style.display = 'block';
    }
}

/**
 * Скрыть сообщение
 */
function hideAuthMessage() {
    if (authMessage) {
        authMessage.style.display = 'none';
    }
}

/**
 * Обработка отправки формы регистрации
 */
async function handleAuthSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(authForm);
    const phone = formData.get('phone').trim();
    const name = formData.get('name').trim();
    const email = formData.get('email').trim();
    
    // Валидация
    if (!phone || !name) {
        showAuthMessage('Пожалуйста, заполните обязательные поля', 'error');
        return;
    }
    
    // Базовая валидация телефона
    const phoneRegex = /^[\+]?[7-8]?[0-9\s\-\(\)]{10,15}$/;
    if (!phoneRegex.test(phone)) {
        showAuthMessage('Пожалуйста, введите корректный номер телефона', 'error');
        return;
    }
    
    try {
        // Импортируем database.js для работы с гостями
        const { default: db } = await import('/db/database.js?v=' + Date.now());

        
        // Создаем или находим гостя
        const guestResponse = await db.findOrCreateGuest(phone, name);
        
        if (guestResponse && (guestResponse.success || guestResponse.id || guestResponse.guest_id)) {
            showAuthMessage(`Добро пожаловать, ${name}! Регистрация успешна.`, 'success');
            // сохраняем в localstorage
            localStorage.setItem('guest_phone', phone);
            localStorage.setItem('guest_name', name);
            // Закрываем модальное окно через 2 секунды
            setTimeout(() => {
                closeAuthModal();
            }, 2000);
        } else {
            showAuthMessage((guestResponse && guestResponse.message) || 'Ошибка регистрации', 'error');
        }
    } catch (error) {
        console.error('Ошибка регистрации:', error);
        showAuthMessage('Произошла ошибка при регистрации', 'error');
    }
}

// ==============================
// ГЛОБАЛЬНЫЕ ФУНКЦИИ ДЛЯ HTML ONCLICK
// ==============================

// Эти функции должны быть в глобальной области видимости для работы onclick
window.toggleCategory = toggleCategory;
window.addToCart = addToCart;
window.updateCartItemQuantity = function(itemId, newQuantity) {
    const item = cart.find(item => item.id === itemId);
    
    if (item) {
        if (newQuantity <= 0) {
            window.removeFromCart(itemId);
        } else {
            item.quantity = newQuantity;
            saveCart();
            updateCartUI();
        }
    }
};

window.removeFromCart = function(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    saveCart();
    updateCartUI();
};

// ==============================
// ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
// ==============================

document.addEventListener('DOMContentLoaded', initializeMenu);

// ==============================
// ЭКСПОРТ ФУНКЦИЙ ДЛЯ ГЛОБАЛЬНОГО ДОСТУПА
// ==============================

// Для совместимости с другими модулями
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeMenu,
        addToCart,
        updateCartItemQuantity,
        removeFromCart,
        clearCart
    };
}