/**
 * Главная страница - функционал
 * Прокрутка новостей и управление контентом
 */

// ==============================
// НАСТРОЙКИ И КОНФИГУРАЦИЯ
// ==============================

const CONFIG = {
    // Настройки карусели новостей
    CAROUSEL: {
        SCROLL_AMOUNT: 300,    // Количество пикселей для прокрутки
        AUTO_SCROLL_DELAY: 5000 // Автопрокрутка каждые 5 секунд
    }
};

// ==============================
// ПЕРЕМЕННЫЕ И ЭЛЕМЕНТЫ DOM
// ==============================

let currentScrollPosition = 0;
let autoScrollInterval;
let currentCardIndex = 0;

// Элементы DOM
const newsCardsContainer = document.getElementById('newsCards');
const prevButton = document.getElementById('prevBtn');
const nextButton = document.getElementById('nextBtn');
const loginBtn = document.getElementById('loginBtn');
const authModal = document.getElementById('authModal');
const closeModal = document.getElementById('closeModal');
const authForm = document.getElementById('authForm');
const authMessage = document.getElementById('authMessage');

// ==============================
// ФУНКЦИИ ИНИЦИАЛИЗАЦИИ
// ==============================

/**
 * Инициализация главной страницы
 */
function initializeHomePage() {
    loadNewsCards();
    setupEventListeners();
    startAutoScroll();
    createScrollIndicator();
}

/**
 * Загрузка карточек новостей из базы данных
 */
async function loadNewsCards() {
    if (!newsCardsContainer) return;
    
    try {
        // Импортируем database.js
        const dbModule = await import('../db/database.js');
        const db = dbModule.default;
        
        // Получаем данные из базы
        const newsResponse = await db.getNewsItems();
        
        if (newsResponse.success && newsResponse.data && newsResponse.data.length > 0) {
            const newsHTML = newsResponse.data.map(news => `
                <div class="news-card" data-news-id="${news.id}">
                    <h3 class="news-card__title">${news.title}</h3>
                    <p class="news-card__description">${news.description}</p>
                    <span class="news-card__date">${formatDate(news.date)}</span>
                </div>
            `).join('');
            
            newsCardsContainer.innerHTML = newsHTML;
        } else {
            // Если данных нет в БД, показываем заглушку
            newsCardsContainer.innerHTML = '<p class="no-news">Новости скоро появятся</p>';
        }
    } catch (error) {
        console.error('Ошибка загрузки новостей:', error);
        newsCardsContainer.innerHTML = '<p class="no-news">Ошибка загрузки новостей</p>';
    }
}

/**
 * Создание индикатора прокрутки
 */
function createScrollIndicator() {
    if (!newsCardsContainer) return;
    
    const newsSection = document.querySelector('.news-section');
    const existingIndicator = document.querySelector('.news-scroll-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const indicator = document.createElement('div');
    indicator.className = 'news-scroll-indicator';
    
    // Рассчитываем количество точек на основе количества карточек
    const cardCount = Math.ceil(newsCardsContainer.children.length / 4);
    for (let i = 0; i < cardCount; i++) {
        const dot = document.createElement('div');
        dot.className = `scroll-dot ${i === 0 ? 'active' : ''}`;
        dot.addEventListener('click', () => scrollToCard(i));
        indicator.appendChild(dot);
    }
    
    newsSection.appendChild(indicator);
}

/**
 * Настройка обработчиков событий
 */
function setupEventListeners() {
    // Навигация карусели
    if (prevButton) {
        prevButton.addEventListener('click', scrollToPrevious);
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', scrollToNext);
    }
    
    // Остановка автопрокрутки при наведении
    if (newsCardsContainer) {
        newsCardsContainer.addEventListener('mouseenter', stopAutoScroll);
        newsCardsContainer.addEventListener('mouseleave', startAutoScroll);
        newsCardsContainer.addEventListener('scroll', updateScrollIndicator);
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
        if (e.key === 'Escape' && authModal.classList.contains('active')) {
            closeAuthModal();
        }
    });
}

// ==============================
// ФУНКЦИИ РЕГИСТРАЦИИ И АУТЕНТИФИКАЦИИ
// ==============================

/**
 * Открытие модального окна регистрации
 */
function openAuthModal() {
    console.log('Открытие модального окна');
    if (authModal) {
        authModal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Блокируем прокрутку фона
    }
}

/**
 * Закрытие модального окна регистрации
 */
function closeAuthModal() {
    if (authModal) {
        authModal.classList.remove('active');
        document.body.style.overflow = ''; // Восстанавливаем прокрутку
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
        const dbModule = await import('../db/database.js');
        const db = dbModule.default;
        
        // Создаем или находим гостя
        const guestResponse = await db.findOrCreateGuest(phone, name);
        
        if (guestResponse.success) {
            showAuthMessage(`Добро пожаловать, ${name}! Регистрация успешна.`, 'success');
            
            // Закрываем модальное окно через 2 секунды
            setTimeout(() => {
                closeAuthModal();
                // Здесь можно добавить логику перенаправления или обновления интерфейса
            }, 2000);
        } else {
            showAuthMessage(guestResponse.message || 'Ошибка регистрации', 'error');
        }
    } catch (error) {
        console.error('Ошибка регистрации:', error);
        showAuthMessage('Произошла ошибка при регистрации', 'error');
    }
}

// ==============================
// ФУНКЦИИ ПРОКРУТКИ КАРУСЕЛИ
// ==============================

/**
 * Прокрутка к определенной карточке
 */
function scrollToCard(cardIndex) {
    if (!newsCardsContainer) return;
    
    const cardWidth = newsCardsContainer.querySelector('.news-card')?.offsetWidth || 0;
    const gap = 25; // соответствует gap в CSS
    const scrollAmount = (cardWidth + gap) * 4 * cardIndex; // Прокрутка на 4 карточки
    
    currentScrollPosition = Math.max(0, Math.min(
        scrollAmount,
        newsCardsContainer.scrollWidth - newsCardsContainer.clientWidth
    ));
    
    newsCardsContainer.scrollTo({
        left: currentScrollPosition,
        behavior: 'smooth'
    });
    
    currentCardIndex = cardIndex;
    updateScrollIndicator();
}

/**
 * Прокрутка к предыдущим карточкам
 */
function scrollToPrevious() {
    const newIndex = Math.max(0, currentCardIndex - 1);
    scrollToCard(newIndex);
}

/**
 * Прокрутка к следующим карточкам
 */
function scrollToNext() {
    const cardCount = Math.ceil(newsCardsContainer.children.length / 4);
    const newIndex = Math.min(cardCount - 1, currentCardIndex + 1);
    scrollToCard(newIndex);
}

/**
 * Обновление индикатора прокрутки
 */
function updateScrollIndicator() {
    const dots = document.querySelectorAll('.scroll-dot');
    const cardWidth = newsCardsContainer.querySelector('.news-card')?.offsetWidth || 0;
    const gap = 25;
    const visibleCards = 4;
    
    if (cardWidth > 0) {
        const scrollPosition = newsCardsContainer.scrollLeft;
        currentCardIndex = Math.round(scrollPosition / ((cardWidth + gap) * visibleCards));
        
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentCardIndex);
        });
    }
}

/**
 * Запуск автоматической прокрутки
 */
function startAutoScroll() {
    stopAutoScroll(); // Очищаем предыдущий интервал
    
    autoScrollInterval = setInterval(() => {
        const cardCount = Math.ceil(newsCardsContainer.children.length / 4);
        
        if (currentCardIndex >= cardCount - 1) {
            // Возврат к началу
            scrollToCard(0);
        } else {
            scrollToNext();
        }
    }, CONFIG.CAROUSEL.AUTO_SCROLL_DELAY);
}

/**
 * Остановка автоматической прокрутки
 */
function stopAutoScroll() {
    if (autoScrollInterval) {
        clearInterval(autoScrollInterval);
        autoScrollInterval = null;
    }
}

// ==============================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ==============================

/**
 * Форматирование даты
 */
function formatDate(dateString) {
    const options = { day: 'numeric', month: 'long', year: 'numeric' };
    return new Date(dateString).toLocaleDateString('ru-RU', options);
}

// ==============================
// ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
// ==============================

document.addEventListener('DOMContentLoaded', initializeHomePage);

// ==============================
// ЭКСПОРТ ФУНКЦИЙ ДЛЯ ДРУГИХ МОДУЛЕЙ
// ==============================

// Для совместимости с другими модулями
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeHomePage,
        scrollToPrevious,
        scrollToNext,
        startAutoScroll,
        stopAutoScroll,
        openAuthModal,
        closeAuthModal
    };
}