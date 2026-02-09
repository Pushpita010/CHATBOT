document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('upload-form');
    const chatForm = document.getElementById('chat-form');
    const chatHistory = document.getElementById('chat-history');
    let sessionId = null; // For tracking the chat session

    // Handle file upload and model selection
    uploadForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(uploadForm);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            sessionId = data.session_id; // Save session id if provided
            chatHistory.innerHTML = '';
            appendMessage('bot', 'Document processed. You can now ask questions!');
        })
        .catch(() => {
            appendMessage('bot', 'Error processing document.');
        });
    });

    // Handle chat messages
    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const userInput = document.getElementById('user-input');
        const message = userInput.value.trim();
        if (!message) return;

        appendMessage('user', message);
        userInput.value = '';

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(res => res.json())
        .then(data => {
            appendMessage('bot', data.response);
        })
        .catch(() => {
            appendMessage('bot', 'Error getting response.');
        });
    });

    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.textContent = text;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});