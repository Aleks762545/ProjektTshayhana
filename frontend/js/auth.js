// СКРИПТ ДЛЯ СТРАНИЦЫ АУТЕНТИФИКАЦИИ

let currentForm = 'register';

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initAuthForms();
    initPhoneMask();
});

// Инициализация форм
function initAuthForms() {
    const showLoginForm = document.getElementById('showLoginForm');
    const showRegisterForm = document.getElementById('showRegisterForm');
    const registrationForm = document.getElementById('registrationForm');
    const loginFormElement = document.getElementById('loginFormElement');
    const continueButton = document.getElementById('continueButton');

    // Переключение между формами
    showLoginForm.addEventListener('click', function(e) {
        e.preventDefault();
        switchToForm('login');
    });

    showRegisterForm.addEventListener('click', function(e) {
        e.preventDefault();
        switchToForm('register');
    });

    // Обработка отправки форм
    registrationForm.addEventListener('submit', handleRegistration);
    loginFormElement.addEventListener('submit', handleLogin);
    
    // Продолжить после успешной регистрации
    continueButton.addEventListener('click', function() {
        window.location.href = '../index.html';
    });
}

// Переключение между формами
function switchToForm(formType) {
    const registerForm = document.getElementById('registerForm');
    const loginForm = document.getElementById('loginForm');
    const successMessage = document.getElementById('successMessage');

    registerForm.style.display = 'none';
    loginForm.style.display = 'none';
    successMessage.style.display = 'none';

    if (formType === 'register') {
        registerForm.style.display = 'block';
        currentForm = 'register';
    } else if (formType === 'login') {
        loginForm.style.display = 'block';
        currentForm = 'login';
    }
}

// Маска для телефона
function initPhoneMask() {
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.startsWith('7') || value.startsWith('8')) {
                value = value.substring(1);
            }
            
            let formattedValue = '+7 (';
            
            if (value.length > 0) {
                formattedValue += value.substring(0, 3);
            }
            if (value.length >= 4) {
                formattedValue += ') ' + value.substring(3, 6);
            }
            if (value.length >= 7) {
                formattedValue += '-' + value.substring(6, 8);
            }
            if (value.length >= 9) {
                formattedValue += '-' + value.substring(8, 10);
            }
            
            e.target.value = formattedValue;
        });
    });
}

// Валидация формы
function validateForm(formData, formType) {
    const errors = {};
    
    // Очищаем предыдущие ошибки
    clearErrors();

    // Валидация имени (только для регистрации)
    if (formType === 'register') {
        if (!formData.name.trim()) {
            errors.name = 'Введите ваше имя';
        } else if (formData.name.trim().length < 2) {
            errors.name = 'Имя должно содержать минимум 2 символа';
        }
    }

    // Валидация телефона
    if (!formData.phone) {
        errors.phone = 'Введите номер телефона';
    } else if (!isValidPhone(formData.phone)) {
        errors.phone = 'Введите корректный номер телефона';
    }

    // Валидация email (только для регистрации, необязательно)
    if (formType === 'register' && formData.email && !isValidEmail(formData.email)) {
        errors.email = 'Введите корректный email адрес';
    }

    // Валидация пароля
    if (!formData.password) {
        errors.password = 'Введите пароль';
    } else if (formData.password.length < 6) {
        errors.password = 'Пароль должен содержать минимум 6 символов';
    }

    // Подтверждение пароля (только для регистрации)
    if (formType === 'register') {
        if (!formData.confirmPassword) {
            errors.confirmPassword = 'Подтвердите пароль';
        } else if (formData.password !== formData.confirmPassword) {
            errors.confirmPassword = 'Пароли не совпадают';
        }

        // Согласие с условиями
        if (!formData.agreeTerms) {
            errors.terms = 'Необходимо согласие с условиями';
        }
    }

    return errors;
}

// Очистка ошибок
function clearErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.textContent = '';
    });
}

// Показать ошибки
function showErrors(errors) {
    for (const [field, message] of Object.entries(errors)) {
        const errorElement = document.getElementById(field + 'Error');
        if (errorElement) {
            errorElement.textContent = message;
        }
    }
}

// Валидация телефона
function isValidPhone(phone) {
    const phoneRegex = /^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$/;
    return phoneRegex.test(phone);
}

// Валидация email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Обработка регистрации
async function handleRegistration(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('regName').value,
        phone: document.getElementById('regPhone').value,
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value,
        confirmPassword: document.getElementById('regConfirmPassword').value,
        agreeTerms: document.getElementById('agreeTerms').checked
    };

    // Валидация
    const errors = validateForm(formData, 'register');
    
    if (Object.keys(errors).length > 0) {
        showErrors(errors);
        return;
    }

    // Показываем загрузку
    const registerButton = document.getElementById('registerButton');
    const btnText = registerButton.querySelector('.btn-text');
    const btnLoading = registerButton.querySelector('.btn-loading');
    
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    registerButton.disabled = true;

    try {
        // Проверяем инициализацию БД
        if (!window.dbManager) {
            throw new Error('База данных не инициализирована');
        }

        await dbManager.init();
        
        // Сохраняем пользователя в БД
        const userData = {
            name: formData.name.trim(),
            phone: formData.phone,
            email: formData.email || null,
            password: formData.password, // В реальном проекте нужно хэшировать!
            createdAt: new Date().toISOString()
        };

        const userId = await dbManager.saveUser(userData);
        
        // Показываем успешное сообщение
        showSuccessMessage();
        
    } catch (error) {
        console.error('Ошибка регистрации:', error);
        alert('Ошибка при регистрации. Пожалуйста, попробуйте позже.');
    } finally {
        // Восстанавливаем кнопку
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        registerButton.disabled = false;
    }
}

// Обработка входа
async function handleLogin(e) {
    e.preventDefault();
    
    const formData = {
        phone: document.getElementById('loginPhone').value,
        password: document.getElementById('loginPassword').value
    };

    // Валидация
    const errors = validateForm(formData, 'login');
    
    if (Object.keys(errors).length > 0) {
        showErrors(errors);
        return;
    }

    // Показываем загрузку
    const loginButton = document.getElementById('loginButton');
    const btnText = loginButton.querySelector('.btn-text');
    const btnLoading = loginButton.querySelector('.btn-loading');
    
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    loginButton.disabled = true;

    try {
        await dbManager.init();
        
        // Аутентификация пользователя
        const user = await dbManager.authenticateUser(formData.phone, formData.password);
        
        if (user) {
            // Сохраняем данные пользователя
            localStorage.setItem('currentUser', JSON.stringify(user));
            alert(`Добро пожаловать, ${user.name}!`);
            window.location.href = '../index.html';
        } else {
            alert('Неверный номер телефона или пароль');
        }
        
    } catch (error) {
        console.error('Ошибка входа:', error);
        alert('Ошибка при входе. Пожалуйста, попробуйте позже.');
    } finally {
        // Восстанавливаем кнопку
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        loginButton.disabled = false;
    }
}

// Показать сообщение об успешной регистрации
function showSuccessMessage() {
    const registerForm = document.getElementById('registerForm');
    const successMessage = document.getElementById('successMessage');
    
    registerForm.style.display = 'none';
    successMessage.style.display = 'block';
}

// Проверка авторизации при загрузке страницы
function checkAuth() {
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
        // Пользователь уже авторизован
        window.location.href = '../index.html';
    }
}

// Вызываем проверку при загрузке
checkAuth();