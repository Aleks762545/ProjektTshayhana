// ===============================
// ЭЛЕМЕНТЫ
// ===============================
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const aiSuggestions = document.getElementById("aiSuggestions");

// ===============================
// ОТОБРАЖЕНИЕ СООБЩЕНИЙ
// ===============================
function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = `message message-${role}`;
    div.innerHTML = `
        <div class="message-content">${text}</div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===============================
// ОТПРАВКА ВОПРОСА
// ===============================
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = messageInput.value.trim();
    if (!text) return;

    addMessage("user", text);
    messageInput.value = "";

    await sendToAI(text);
});

// ===============================
// ОТПРАВКА НА БЭКЕНД
// ===============================
async function sendToAI(userMessage) {
    try {
        const response = await fetch("/api/ai/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        });

        const data = await response.json();
        addMessage("ai", (data && data.data && data.data.message) ? data.data.message : (data.reply || 'Ошибка: нет ответа'));

        const suggestions = (data && data.data && data.data.suggestions) ? data.data.suggestions : (data.suggestions || []);
        updateSuggestionsFromObjects(suggestions);

        updateSuggestions(data.suggestions || []);

    } catch (e) {
        addMessage("ai", "Ошибка связи с ИИ.");
        console.error(e);
    }
}

// ===============================
// ОБНОВЛЕНИЕ ПРЕДЛОЖЕНИЙ
// ===============================
function updateSuggestions(suggestions) {
    aiSuggestions.innerHTML = "";

    if (!suggestions.length) return;

    suggestions.forEach(text => {
        const btn = document.createElement("button");
        btn.className = "suggestion-btn";
        btn.textContent = text;

        btn.onclick = () => {
            addMessage("user", text);
            sendToAI(text);
        };

        aiSuggestions.appendChild(btn);
    });
}
