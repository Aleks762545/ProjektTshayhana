// cart-reset.js
// Функции для работы с корзиной на всех страницах

import DatabaseAPI from './db/database.js';

// Инициализация корзины при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Обновляем счетчик корзины
    DatabaseAPI.updateCartCount();
    
    // Добавляем обработчики для кнопок корзины, если они есть на странице
    const cartToggle = document.getElementById('cartToggle');
    const cartSidebar = document.getElementById('cartSidebar');
    const cartClose = document.getElementById('cartClose');
    
    if (cartToggle && cartSidebar) {
        cartToggle.addEventListener('click', () => {
            cartSidebar.classList.add('open');
            document.body.classList.add('cart-open');
            renderCart();
        });
    }
    
    if (cartClose && cartSidebar) {
        cartClose.addEventListener('click', () => {
            cartSidebar.classList.remove('open');
            document.body.classList.remove('cart-open');
        });
    }
});

// Функция рендеринга корзины (общая для всех страниц)
function renderCart() {
    const cartItems = document.getElementById('cartItems');
    const emptyCart = document.getElementById('emptyCart');
    const totalAmount = document.getElementById('totalAmount');
    const checkoutBtn = document.getElementById('checkoutBtn');
    
    if (!cartItems || !emptyCart) return;
    
    const cart = DatabaseAPI.getCart();
    cartItems.innerHTML = '';
    
    if (cart.length === 0) {
        if (emptyCart) emptyCart.style.display = 'block';
        if (totalAmount) totalAmount.textContent = '0₽';
        if (checkoutBtn) checkoutBtn.disabled = true;
        return;
    }
    
    if (emptyCart) emptyCart.style.display = 'none';
    
    cart.forEach(item => {
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';
        cartItem.innerHTML = `
            <div class="item-info">
                <div class="item-name">${item.name}</div>
                <div class="item-price">${item.price}₽ × ${item.quantity}</div>
            </div>
            <div class="item-quantity">
                <button class="quantity-btn minus" data-id="${item.id}">-</button>
                <span class="quantity-value">${item.quantity}</span>
                <button class="quantity-btn plus" data-id="${item.id}">+</button>
            </div>
            <button class="remove-btn" data-id="${item.id}">×</button>
        `;
        cartItems.appendChild(cartItem);
    });
    
    if (totalAmount) totalAmount.textContent = `${DatabaseAPI.getCartTotal()}₽`;
    if (checkoutBtn) checkoutBtn.disabled = false;
    
    // Добавляем обработчики событий для элементов корзины
    attachCartItemListeners();
}

// Обработчики для элементов корзины
function attachCartItemListeners() {
    // Plus buttons
    document.querySelectorAll('.quantity-btn.plus').forEach(btn => {
        btn.addEventListener('click', function() {
            const dishId = this.dataset.id;
            const cart = DatabaseAPI.getCart();
            const item = cart.find(item => item.id == dishId);
            if (item) {
                DatabaseAPI.updateCartItemQuantity(dishId, item.quantity + 1);
                renderCart();
                DatabaseAPI.updateCartCount();
            }
        });
    });
    
    // Minus buttons
    document.querySelectorAll('.quantity-btn.minus').forEach(btn => {
        btn.addEventListener('click', function() {
            const dishId = this.dataset.id;
            const cart = DatabaseAPI.getCart();
            const item = cart.find(item => item.id == dishId);
            if (item && item.quantity > 1) {
                DatabaseAPI.updateCartItemQuantity(dishId, item.quantity - 1);
                renderCart();
                DatabaseAPI.updateCartCount();
            }
        });
    });
    
    // Remove buttons
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const dishId = this.dataset.id;
            DatabaseAPI.removeFromCart(dishId);
            renderCart();
            DatabaseAPI.updateCartCount();
        });
    });
}

// Экспортируем функцию для использования на других страницах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderCart, attachCartItemListeners };
}