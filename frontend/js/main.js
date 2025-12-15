// ОСНОВНОЙ ФАЙЛ СКРИПТОВ ДЛЯ ГЛАВНОЙ СТРАНИЦЫ

// Данные акций (временно здесь, потом с бэкенда)
const promotionsData = [
    {
        id: 1,
        title: "Живая музыка каждый вечер",
        description: "Наслаждайтесь восточной музыкой и танцами",
        image: "assets/images/promotion1.jpg",
        date: "Ежедневно с 19:00"
    },
    {
        id: 2, 
        title: "Скидка 20% на обеды",
        description: "Специальное предложение на бизнес-ланчи",
        image: "assets/images/promotion2.jpg", 
        date: "До 30 декабря"
    }
];

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('Главная страница Чайханы загружена');
    
    // Загружаем акции
    loadPromotions();
    
    // Анимация для кнопок
    initButtonEffects();
});

// Загрузка и отображение акций
function loadPromotions() {
    const container = document.getElementById('promotionsContainer');
    const section = document.querySelector('.promotions-section');
    
    // Если нет акций - скрываем секцию
    if (!promotionsData || promotionsData.length === 0) {
        section.classList.add('hidden');
        return;
    }
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Добавляем карточки акций
    promotionsData.forEach(promotion => {
        const card = createPromotionCard(promotion);
        container.appendChild(card);
    });
}

// Создание карточки акции
function createPromotionCard(promotion) {
    const card = document.createElement('div');
    card.className = 'promotion-card';
    card.innerHTML = `
        <div class="promotion-image" style="background-image: url('${promotion.image}')"></div>
        <div class="promotion-content">
            <h4>${promotion.title}</h4>
            <p>${promotion.description}</p>
            <div class="promotion-date">${promotion.date}</div>
        </div>
    `;
    return card;
}

// Эффекты для кнопок
function initButtonEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Простые функции для управления акциями (для демонстрации)
window.promotionsManager = {
    addPromotion: function(promotion) {
        promotionsData.push(promotion);
        loadPromotions();
    },
    
    removePromotion: function(id) {
        const index = promotionsData.findIndex(p => p.id === id);
        if (index !== -1) {
            promotionsData.splice(index, 1);
            loadPromotions();
        }
    },
    
    clearAll: function() {
        promotionsData.length = 0;
        loadPromotions();
    }
};