// Сбрасываем корзину только если была полная перезагрузка страницы
if (performance.navigation.type === performance.navigation.TYPE_RELOAD) {
    console.log("Полная перезагрузка страницы — корзина очищена");
    localStorage.removeItem('tea_house_cart');
}
