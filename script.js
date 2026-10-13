const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const quickPrompts = document.querySelector("#quick-prompts");
const welcomeBlock = document.querySelector("#welcome-block");
const connectionHeading = document.querySelector(".conversation-heading");
const connectionMode = document.querySelector("#connection-mode");
let conversationHistory = [
  {
    role: "assistant",
    content: "Hi, I'm glad you're here. How are you feeling today?",
  },
];
let isSending = false;
let conversationGeneration = 0;

function formatTime() {
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date());
}

function appendMessage(speaker, text, emotion = null) {
  const isUser = speaker === "user";
  const article = document.createElement("article");
  article.className = `message ${isUser ? "user-message" : "assistant-message"}`;

  if (!isUser) {
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none"><path d="M12 19s-7-4-7-9a4 4 0 0 1 7-2.3A4 4 0 0 1 19 10c0 5-7 9-7 9Z" /></svg>';
    article.append(avatar);
  }

  const body = document.createElement("div");
  body.className = "message-body";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  const name = document.createElement("span");
  name.textContent = isUser ? "You" : "SOULMATE";
  const time = document.createElement("time");
  time.dateTime = new Date().toISOString();
  time.textContent = formatTime();
  meta.append(name, time);

  const bubble = document.createElement("div");
  bubble.className = `bubble ${isUser ? "user-bubble" : "assistant-bubble"}`;
  bubble.textContent = text;
  body.append(meta, bubble);

  if (!isUser && emotion && emotion !== "neutral") {
    const emotionNote = document.createElement("p");
    emotionNote.className = "emotion-note";
    emotionNote.textContent = `Picked up on: ${emotion}`;
    body.append(emotionNote);
  }

  article.append(body);
  messages.append(article);
  article.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function submitMessage(message) {
  const text = message.trim();
  if (!text || sendButton.disabled || isSending) return;

  if (welcomeBlock) welcomeBlock.hidden = true;
  quickPrompts.hidden = true;
  appendMessage("user", text);
  input.value = "";
  input.style.height = "auto";

  if (["quit", "exit", "bye"].includes(text.toLowerCase())) {
    appendMessage("assistant", "Goodbye. Take care!");
    input.disabled = true;
    sendButton.disabled = true;
    input.placeholder = "Start a new conversation to keep chatting";
    return;
  }

  isSending = true;
  sendButton.disabled = true;
  const requestGeneration = conversationGeneration;
  appendMessage("assistant", "Thinking...");
  const thinkingMessage = messages.lastElementChild;
  const thinkingBubble = thinkingMessage.querySelector(".bubble");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [...conversationHistory, { role: "user", content: text }],
      }),
    });
    const result = await response.json();
    if (requestGeneration !== conversationGeneration) return;
    if (!response.ok) {
      throw new Error(result.error || `Request failed (${response.status}).`);
    }
    if (typeof result.reply !== "string" || !result.reply.trim()) {
      throw new Error("SOULMATE returned an empty response.");
    }

    thinkingBubble.textContent = result.reply;
    thinkingMessage.querySelector("time").textContent = formatTime();
    if (result.emotion && result.emotion !== "neutral") {
      const emotionNote = document.createElement("p");
      emotionNote.className = "emotion-note";
      emotionNote.textContent = `Picked up on: ${result.emotion}`;
      thinkingMessage.querySelector(".message-body").append(emotionNote);
    }
    conversationHistory.push(
      { role: "user", content: text },
      { role: "assistant", content: result.reply }
    );
    if (conversationHistory.length > 28) {
      conversationHistory = conversationHistory.slice(-28);
    }
  } catch (error) {
    if (requestGeneration !== conversationGeneration) return;
    console.error("SOULMATE chat request failed:", error);
    thinkingBubble.textContent =
      "I couldn't reach SOULMATE's backend. Check that server.py is running, then try again.";
    thinkingMessage.classList.add("assistant-message-error");
    const errorNote = document.createElement("p");
    errorNote.className = "emotion-note";
    errorNote.textContent = error.message;
    thinkingMessage.querySelector(".message-body").append(errorNote);
    connectionMode.textContent = "Connection problem";
    connectionHeading.classList.add("backend-offline");
  } finally {
    if (requestGeneration === conversationGeneration) {
      isSending = false;
      sendButton.disabled = false;
      input.focus();
    }
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitMessage(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submitMessage(input.value);
  }
});

quickPrompts.addEventListener("click", (event) => {
  const prompt = event.target.closest("[data-message]");
  if (prompt) submitMessage(prompt.dataset.message);
});

function startNewConversation() {
  conversationGeneration += 1;
  messages.querySelectorAll(".message").forEach((message) => message.remove());
  if (welcomeBlock) welcomeBlock.hidden = false;
  quickPrompts.hidden = false;
  input.disabled = false;
  sendButton.disabled = false;
  input.placeholder = "Ask SOULMATE...";
  input.value = "";
  input.style.height = "auto";
  isSending = false;
  conversationHistory = [
    {
      role: "assistant",
      content: "Hi, I'm glad you're here. How are you feeling today?",
    },
  ];
  appendMessage("assistant", "Hi, I'm glad you're here. How are you feeling today?");
  input.focus();
}

document.querySelectorAll("#new-chat, #header-new-chat").forEach((button) => {
  button.addEventListener("click", startNewConversation);
});

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    startNewConversation();
  }
});

async function checkBackend() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error(`Backend returned ${response.status}.`);
    const health = await response.json();
    connectionMode.textContent =
      health.mode === "llm" ? `LLM ready · ${health.model}` : "Local mode · no API key";
    connectionHeading.classList.remove("backend-offline");
  } catch (error) {
    console.error("SOULMATE backend health check failed:", error);
    connectionMode.textContent = "Backend offline · run server.py";
    connectionHeading.classList.add("backend-offline");
  }
}

checkBackend();
