const PRODUCTS = [
  { name: "Wireless Earbuds", price: 59.99 },
  { name: "Smart Watch", price: 129.99 },
  { name: "Canvas Backpack", price: 45.0 },
  { name: "Running Sneakers", price: 89.99 },
  { name: "Desk Lamp", price: 24.99 },
  { name: "Ceramic Mug", price: 12.99 },
];

const BOX_ICON = `
  <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M21 8l-9-5-9 5 9 5 9-5z"></path>
    <path d="M3 8v8l9 5 9-5V8"></path>
    <path d="M12 13v8"></path>
  </svg>`;

let cartCount = 0;

function renderProducts() {
  const grid = document.getElementById("product-grid");
  for (const p of PRODUCTS) {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <div class="product-thumb">${BOX_ICON}</div>
      <div class="product-info">
        <h3>${p.name}</h3>
        <p class="price">$${p.price.toFixed(2)}</p>
        <button class="btn-add">Add to cart</button>
      </div>`;
    card.querySelector(".btn-add").addEventListener("click", () => {
      cartCount += 1;
      const badge = document.getElementById("cart-count");
      badge.textContent = cartCount;
      badge.classList.remove("hidden");
    });
    grid.appendChild(card);
  }
}

const METRIC_LABELS = {
  intent_accuracy: "Intent Accuracy %",
  intent_macro_f1: "Intent Macro F1",
  rouge1: "ROUGE-1",
  rouge2: "ROUGE-2",
  rougeL: "ROUGE-L",
  bleu: "BLEU",
};

async function loadMetrics() {
  const res = await fetch("/api/metrics");
  const data = await res.json();
  const grid = document.getElementById("metric-cards");

  for (const [key, label] of Object.entries(METRIC_LABELS)) {
    const ft = data.fine_tuned[key];
    const base = data.base[key];
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `
      <div class="label">${label}</div>
      <div class="values">
        <span class="ft">${ft.toFixed(1)}</span>
        <span class="base">base ${base.toFixed(1)}</span>
      </div>`;
    grid.appendChild(card);
  }

  const perplexity = document.createElement("div");
  perplexity.className = "metric-card";
  perplexity.innerHTML = `
    <div class="label">Perplexity (fine-tuned)</div>
    <div class="values"><span class="ft">${data.trainer.perplexity.toFixed(2)}</span></div>`;
  grid.appendChild(perplexity);
}

async function loadFigures() {
  const res = await fetch("/api/figures");
  const files = await res.json();
  const grid = document.getElementById("figure-grid");

  for (const name of files) {
    const fig = document.createElement("figure");
    fig.innerHTML = `
      <img src="/figures/${name}" loading="lazy" alt="${name}">
      <figcaption>${name}</figcaption>`;
    grid.appendChild(fig);
  }
}

function initChat() {
  const toggle = document.getElementById("chat-toggle");
  const panel = document.getElementById("chat-panel");
  const closeBtn = document.getElementById("chat-close");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");

  let greeted = false;
  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!greeted && !panel.classList.contains("hidden")) {
      addMessage("Hi! I can help with orders, refunds, and shipping questions.", "bot");
      greeted = true;
    }
  });
  closeBtn.addEventListener("click", () => panel.classList.add("hidden"));

  function addMessage(text, cls) {
    const el = document.createElement("div");
    el.className = `msg ${cls}`;
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    return el;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    addMessage(text, "user");
    input.value = "";
    input.disabled = true;
    const pending = addMessage("thinking...", "bot pending");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      pending.textContent = data.reply;
      pending.classList.remove("pending");
    } catch (err) {
      pending.textContent = "Error reaching model.";
      pending.classList.remove("pending");
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
}

renderProducts();
loadMetrics();
loadFigures();
initChat();
