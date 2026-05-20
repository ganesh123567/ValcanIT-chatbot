(function () {
  const currentScript = document.currentScript;
  const apiUrl =
    currentScript?.dataset.apiUrl ||
    `${new URL(currentScript?.src || window.location.href).origin}/api/chat`;
  const title = currentScript?.dataset.title || "ValcanIT Assistant";
  const safeTitle = escapeHtml(title);

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, function (character) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[character];
    });
  }

  const root = document.createElement("div");
  root.id = "valcanit-chatbot";
  root.innerHTML = `
    <button class="vc-chat-toggle" type="button" aria-label="Open chat">
      <span>Chat</span>
    </button>
    <section class="vc-chat-panel" aria-label="${safeTitle}" hidden>
      <header class="vc-chat-header">
        <div>
          <strong>${safeTitle}</strong>
          <span>Ask about ValcanIT services</span>
        </div>
        <button class="vc-chat-close" type="button" aria-label="Close chat">&times;</button>
      </header>
      <div class="vc-chat-messages" role="log" aria-live="polite"></div>
      <form class="vc-chat-form">
        <input class="vc-chat-input" name="message" type="text" autocomplete="off" placeholder="Type your question..." maxlength="1500" required />
        <button class="vc-chat-send" type="submit">Send</button>
      </form>
    </section>
  `;

  const style = document.createElement("style");
  style.textContent = `
    #valcanit-chatbot {
      position: fixed;
      right: 20px;
      bottom: 20px;
      z-index: 2147483647;
      font-family: Arial, Helvetica, sans-serif;
      color: #1f2933;
    }
    #valcanit-chatbot * {
      box-sizing: border-box;
    }
    .vc-chat-toggle {
      min-width: 72px;
      min-height: 48px;
      border: 0;
      border-radius: 24px;
      background: #0f5ea8;
      color: #fff;
      font-size: 15px;
      font-weight: 700;
      box-shadow: 0 10px 28px rgba(15, 94, 168, 0.3);
      cursor: pointer;
    }
    .vc-chat-panel {
      width: min(380px, calc(100vw - 32px));
      height: min(560px, calc(100vh - 32px));
      margin-bottom: 12px;
      border: 1px solid #d6dde6;
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
      box-shadow: 0 18px 48px rgba(15, 23, 42, 0.22);
    }
    .vc-chat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      background: #0f5ea8;
      color: #fff;
    }
    .vc-chat-header strong,
    .vc-chat-header span {
      display: block;
      line-height: 1.35;
    }
    .vc-chat-header span {
      margin-top: 2px;
      font-size: 12px;
      opacity: 0.9;
    }
    .vc-chat-close {
      width: 32px;
      height: 32px;
      border: 0;
      border-radius: 16px;
      background: rgba(255,255,255,0.18);
      color: #fff;
      font-size: 24px;
      line-height: 1;
      cursor: pointer;
    }
    .vc-chat-messages {
      height: calc(100% - 124px);
      overflow-y: auto;
      padding: 16px;
      background: #f6f8fb;
    }
    .vc-chat-message {
      max-width: 88%;
      margin-bottom: 12px;
      padding: 10px 12px;
      border-radius: 8px;
      font-size: 14px;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .vc-chat-message.bot {
      background: #fff;
      border: 1px solid #dfe6ee;
    }
    .vc-chat-message.user {
      margin-left: auto;
      background: #0f5ea8;
      color: #fff;
    }
    .vc-chat-form {
      display: flex;
      gap: 8px;
      padding: 12px;
      border-top: 1px solid #dfe6ee;
      background: #fff;
    }
    .vc-chat-input {
      flex: 1;
      min-width: 0;
      height: 42px;
      border: 1px solid #c7d0da;
      border-radius: 6px;
      padding: 0 10px;
      font-size: 14px;
    }
    .vc-chat-send {
      height: 42px;
      border: 0;
      border-radius: 6px;
      padding: 0 14px;
      background: #0f5ea8;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }
    @media (max-width: 480px) {
      #valcanit-chatbot {
        right: 12px;
        bottom: 12px;
      }
      .vc-chat-panel {
        width: calc(100vw - 24px);
        height: calc(100vh - 24px);
      }
    }
  `;

  document.head.appendChild(style);
  document.body.appendChild(root);

  const toggle = root.querySelector(".vc-chat-toggle");
  const panel = root.querySelector(".vc-chat-panel");
  const close = root.querySelector(".vc-chat-close");
  const messages = root.querySelector(".vc-chat-messages");
  const form = root.querySelector(".vc-chat-form");
  const input = root.querySelector(".vc-chat-input");
  let greeted = false;

  function addMessage(text, type) {
    const message = document.createElement("div");
    message.className = `vc-chat-message ${type}`;
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
    return message;
  }

  function openPanel() {
    panel.hidden = false;
    toggle.hidden = true;
    input.focus();
    if (!greeted) {
      addMessage("Hello. Ask me about ValcanIT services, solutions, or contact information.", "bot");
      greeted = true;
    }
  }

  toggle.addEventListener("click", openPanel);
  close.addEventListener("click", function () {
    panel.hidden = true;
    toggle.hidden = false;
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    addMessage(text, "user");
    const pending = addMessage("Thinking...", "bot");

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      if (!response.ok) {
        throw new Error("Chat service unavailable");
      }
      const data = await response.json();
      pending.textContent = data.answer || "I could not generate an answer. Please contact info@valcanit.com.";
    } catch (error) {
      pending.textContent = "The chat service is unavailable right now. Please contact ValcanIT at info@valcanit.com or (469)-306-2882.";
    }
  });
})();
