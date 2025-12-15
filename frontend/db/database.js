// frontend/db/database.js
const API_BASE = (window.__API_BASE__ || '') + '/api';

async function rawRequest(path, method='GET', body=null){
  const url = API_BASE + path;
  const opts = { method, headers: {} };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);

  let json = null;
  try { json = await res.json(); } catch(e){}

  return { ok: res.ok, status: res.status, json };
}

// =============================
// Unified wrapper expected by menu.js
// =============================
async function wrappedRequest(path, method, body) {
    const r = await rawRequest(path, method, body);

    if (!r.ok) {
        return {
            success: false,
            message: r.json?.detail || `HTTP ${r.status}`,
            data: null
        };
    }

    return {
        success: true,
        data: r.json || null
    };
}

// categories
async function getCategories(){
    return wrappedRequest('/categories', 'GET');
}

async function getDishes(params={}) {
    const qs = new URLSearchParams();
    for (const k in params) if (params[k] != null) qs.set(k, params[k]);
    const path = '/dishes' + (qs.toString()? '?' + qs : '');
    return wrappedRequest(path, 'GET');
}

// guests
async function findOrCreateGuest(phone, name=null){
    return wrappedRequest('/guests/find_or_create', 'POST', {phone, name});
}

// orders
async function createOrder(payload){
    return wrappedRequest('/orders', 'POST', payload);
}

// news (главная)
async function getNewsItems(){
    return wrappedRequest('/news', 'GET');
}

// admin tags, ingredients — меню их не использует
async function getTags(){ return wrappedRequest('/tags', 'GET') }
async function getIngredients(){ return wrappedRequest('/ingredients', 'GET') }
// =============================
// NEW FUNCTIONS FOR AI WAITER
// =============================

// Search dishes by query
async function searchDishes(query, category = null) {
    const params = { q: query };
    if (category) params.category = category;
    
    return wrappedRequest('/dishes/search?' + new URLSearchParams(params), 'GET');
}

// Get dish by ID
async function getDishById(id) {
    return wrappedRequest(`/dishes/${id}`, 'GET');
}

// Get dishes by category
async function getDishesByCategory(categoryId) {
    return wrappedRequest(`/categories/${categoryId}/dishes`, 'GET');
}

// Get all dishes with pagination
async function getAllDishes(limit = 20, offset = 0) {
    return wrappedRequest(`/dishes?limit=${limit}&offset=${offset}`, 'GET');
}

// CART FUNCTIONS (shared between pages)
function getCart() {
    const cartJson = localStorage.getItem('teaHouseCart');
    return cartJson ? JSON.parse(cartJson) : [];
}

function saveCart(cart) {
    localStorage.setItem('teaHouseCart', JSON.stringify(cart));
}

function addToCart(dish) {
    const cart = getCart();
    const existingItem = cart.find(item => item.id === dish.id);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: dish.id,
            name: dish.name,
            price: dish.price,
            quantity: 1,
            image: dish.image_url
        });
    }
    
    saveCart(cart);
    updateCartCount();
    return cart;
}

function removeFromCart(dishId) {
    const cart = getCart();
    const filteredCart = cart.filter(item => item.id !== dishId);
    saveCart(filteredCart);
    updateCartCount();
    return filteredCart;
}

function updateCartItemQuantity(dishId, quantity) {
    const cart = getCart();
    const item = cart.find(item => item.id === dishId);
    
    if (item) {
        if (quantity <= 0) {
            return removeFromCart(dishId);
        }
        item.quantity = quantity;
        saveCart(cart);
        updateCartCount();
    }
    
    return cart;
}

function clearCart() {
    localStorage.removeItem('teaHouseCart');
    updateCartCount();
    return [];
}

function getCartTotal() {
    const cart = getCart();
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

function getCartItemCount() {
    const cart = getCart();
    return cart.reduce((count, item) => count + item.quantity, 0);
}

function updateCartCount() {
    const count = getCartItemCount();
    // Update cart count in all pages
    document.querySelectorAll('.cart-count').forEach(element => {
        element.textContent = count;
    });
    
    // Enable/disable checkout button
    const checkoutBtn = document.getElementById('checkoutBtn');
    if (checkoutBtn) {
        checkoutBtn.disabled = count === 0;
    }
}

// =====================
// DEFAULT EXPORT (updated)
// =====================
export default {
    getCategories,
    getDishes,
    findOrCreateGuest,
    createOrder,
    getNewsItems,
    getTags,
    getIngredients,
    
    // New functions for AI waiter
    searchDishes,
    getDishById,
    getDishesByCategory,
    getAllDishes,
    
    // Cart functions
    getCart,
    saveCart,
    addToCart,
    removeFromCart,
    updateCartItemQuantity,
    clearCart,
    getCartTotal,
    getCartItemCount,
    updateCartCount
};

