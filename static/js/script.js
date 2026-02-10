document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("upload-form");
  const chatForm = document.getElementById("chat-form");
  const chatHistoryDiv = document.getElementById("chat-history");
  const errorMessage = document.getElementById("error-message");
  const loading = document.getElementById("loading");
  const userInput = document.getElementById("user-input");
  
  let sessionId = null;
  let chatEnabled = false;

  // Disable chat button initially
  chatForm.querySelector("button").disabled = true;

  // ========== FILE UPLOAD ==========
  uploadForm.addEventListener("submit", function (e) {
    e.preventDefault();
    errorMessage.textContent = "";
    const file = document.getElementById("file-input").files[0];
    const model = document.getElementById("model-select").value;
    
    if (!file) {
      errorMessage.textContent = "Please select a file.";
      return;
    }
    
    loading.style.display = "block";
    loading.textContent = "Processing document...";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("model", model);

    fetch("/upload", { method: "POST", body: formData })
      .then((res) => res.json())
      .then((data) => {
        loading.style.display = "none";
        
        if (data.error) {
          errorMessage.textContent = "Error: " + data.error;
          chatEnabled = false;
          chatForm.querySelector("button").disabled = true;
          return;
        }
        
        // Success
        sessionId = data.session_id;
        chatHistoryDiv.innerHTML = "";
        errorMessage.textContent = "";
        
        appendBotMessage("✓ Document processed successfully! You can now ask questions.");
        chatEnabled = true;
        chatForm.querySelector("button").disabled = false;
        userInput.focus();
      })
      .catch((error) => {
        loading.style.display = "none";
        errorMessage.textContent = "Upload failed: " + error.message;
        chatEnabled = false;
        chatForm.querySelector("button").disabled = true;
      });
  });

  // ========== CHAT ==========
  chatForm.addEventListener("submit", function (e) {
    e.preventDefault();
    errorMessage.textContent = "";
    
    if (!chatEnabled) {
      errorMessage.textContent = "Please upload a document first.";
      return;
    }
    
    const message = userInput.value.trim();
    if (!message) {
      return;
    }

    // Show user message
    appendUserMessage(message);
    userInput.value = "";
    
    // Show thinking indicator
    const thinkingDiv = appendThinkingIndicator();
    
    // Send query
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 330000); // 5.5 min

    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
      }),
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data) => {
        clearTimeout(timeoutId);
        
        // Remove thinking indicator
        if (thinkingDiv && thinkingDiv.parentNode) {
          thinkingDiv.parentNode.removeChild(thinkingDiv);
        }
        
        if (data.response) {
          appendBotMessage(data.response);
        } else if (data.error) {
          errorMessage.textContent = "Error: " + data.error;
        }
      })
      .catch((err) => {
        clearTimeout(timeoutId);
        
        // Remove thinking indicator
        if (thinkingDiv && thinkingDiv.parentNode) {
          thinkingDiv.parentNode.removeChild(thinkingDiv);
        }
        
        if (err.name === "AbortError") {
          errorMessage.textContent = "Request timed out. Make sure Ollama is running and try again.";
        } else {
          errorMessage.textContent = "Error: " + err.message;
        }
      });
  });

  // ========== UI HELPERS ==========
  function appendUserMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message user";
    msgDiv.textContent = text;
    chatHistoryDiv.appendChild(msgDiv);
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
  }

  function appendBotMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot";
    msgDiv.textContent = text;
    chatHistoryDiv.appendChild(msgDiv);
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
  }

  function appendThinkingIndicator() {
    const thinkingDiv = document.createElement("div");
    thinkingDiv.className = "message bot thinking-indicator";
    thinkingDiv.innerHTML = '<span class="thinking-dots"><span></span><span></span><span></span></span>';
    chatHistoryDiv.appendChild(thinkingDiv);
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    return thinkingDiv;
  }
});
