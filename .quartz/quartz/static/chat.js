document.addEventListener("nav", () => {
  const existing = document.getElementById("kb-chat-widget");
  if (existing) return;

  const widget = document.createElement("div");
  widget.id = "kb-chat-widget";
  widget.innerHTML = `
    <button id="kb-chat-toggle" aria-label="AI 问答">💬</button>
    <div id="kb-chat-panel" class="hidden">
      <div id="kb-chat-header">
        <span>📚 知识库问答</span>
        <button id="kb-chat-close">✕</button>
      </div>
      <div id="kb-chat-messages"></div>
      <div id="kb-chat-input-wrap">
        <input id="kb-chat-input" type="text" placeholder="输入问题..." />
        <button id="kb-chat-send">发送</button>
      </div>
    </div>
  `;
  document.body.appendChild(widget);

  const WORKER_URL = "https://kb-ask.byteninjacyber.workers.dev";

  const toggle = document.getElementById("kb-chat-toggle");
  const panel = document.getElementById("kb-chat-panel");
  const closeBtn = document.getElementById("kb-chat-close");
  const input = document.getElementById("kb-chat-input");
  const sendBtn = document.getElementById("kb-chat-send");
  const messages = document.getElementById("kb-chat-messages");

  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) input.focus();
  });
  closeBtn.addEventListener("click", () => panel.classList.add("hidden"));

  function addMsg(text, role) {
    const div = document.createElement("div");
    div.className = `kb-chat-msg kb-chat-${role}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function ask() {
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    addMsg(q, "user");
    addMsg("思考中...", "loading");

    try {
      const resp = await fetch(WORKER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await resp.json();
      messages.removeChild(messages.lastChild);
      addMsg(data.answer, "bot");
      if (data.sources && data.sources.length) {
        const srcText = "📎 来源: " + data.sources.map((s) => s.title || s).join(", ");
        addMsg(srcText, "source");
      }
    } catch (e) {
      messages.removeChild(messages.lastChild);
      addMsg("连接失败，请检查网络或稍后重试", "bot");
    }
  }

  sendBtn.addEventListener("click", ask);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") ask();
  });
});
