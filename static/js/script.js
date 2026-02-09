document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("upload-form");
  const chatForm = document.getElementById("chat-form");
  const chatHistoryDiv = document.getElementById("chat-history");
  const errorMessage = document.getElementById("error-message");
  const loading = document.getElementById("loading");
  let sessionId = null;
  let chatEnabled = false;
  let chatHistory = [];

  chatForm.querySelector("button").disabled = true;

  // Handle file upload and model selection
  uploadForm.addEventListener("submit", function (e) {
    e.preventDefault();
    errorMessage.textContent = "";
    loading.style.display = "block";
    const formData = new FormData(uploadForm);

    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        loading.style.display = "none";
        if (data.error) {
          errorMessage.textContent = data.error;
          chatEnabled = false;
          chatForm.querySelector("button").disabled = true;
          return;
        }
        sessionId = data.session_id;
        chatHistoryDiv.innerHTML = "";
        chatHistory = [];
        appendMessage("bot", "Document processed. You can now ask questions!");
        chatEnabled = true;
        chatForm.querySelector("button").disabled = false;
      })
      .catch(() => {
        loading.style.display = "none";
        errorMessage.textContent = "Error processing document.";
        chatEnabled = false;
        chatForm.querySelector("button").disabled = true;
      });
  });

  // Handle chat messages
  chatForm.addEventListener("submit", function (e) {
    e.preventDefault();
    errorMessage.textContent = "";
    if (!chatEnabled) {
      errorMessage.textContent = "Please upload a document first.";
      return;
    }
    const userInput = document.getElementById("user-input");
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage("user", message);
    loading.style.display = "block";
    userInput.value = "";

    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
        chat_history: chatHistory,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        loading.style.display = "none";
        if (data.response) {
          appendMessage("bot", data.response);
          chatHistory.push({ user: message, bot: data.response });
        } else if (data.error) {
          errorMessage.textContent = data.error;
        }
      })
      .catch(() => {
        loading.style.display = "none";
        errorMessage.textContent = "Error getting response.";
      });
  });

  function appendMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;
    msgDiv.textContent = text;
    chatHistoryDiv.appendChild(msgDiv);
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
  }
});
