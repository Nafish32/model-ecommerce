const BOX_ICON = `
  <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M21 8l-9-5-9 5 9 5 9-5z"></path>
    <path d="M3 8v8l9 5 9-5V8"></path>
    <path d="M12 13v8"></path>
  </svg>`;

const cart = []; // {name, price, qty}

function addToCart(product) {
  const existing = cart.find((i) => i.name === product.name);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ name: product.name, price: product.price, qty: 1 });
  }
  const count = cart.reduce((sum, i) => sum + i.qty, 0);
  const badge = document.getElementById("cart-count");
  badge.textContent = count;
  badge.classList.remove("hidden");
}

async function renderProducts() {
  const res = await fetch("/api/products");
  const products = await res.json();
  const grid = document.getElementById("product-grid");

  for (const p of products) {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <div class="product-thumb">${BOX_ICON}</div>
      <div class="product-info">
        <span class="category">${p.category}</span>
        <h3>${p.name}</h3>
        <p class="desc">${p.description}</p>
        <p class="price">$${p.price.toFixed(2)}</p>
        <button class="btn-add" ${p.in_stock ? "" : "disabled"}>
          ${p.in_stock ? "Add to cart" : "Out of stock"}
        </button>
      </div>`;
    const btn = card.querySelector(".btn-add");
    if (p.in_stock) {
      btn.addEventListener("click", () => addToCart(p));
    }
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
      addMessage("Hi! Ask me about product prices, stock, or orders and refunds.", "bot");
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

function initCart() {
  const cartBtn = document.getElementById("cart-btn");
  const panel = document.getElementById("cart-panel");
  const closeBtn = document.getElementById("cart-close");
  const itemsEl = document.getElementById("cart-items");
  const totalEl = document.getElementById("cart-total");
  const confirmBtn = document.getElementById("cart-confirm");
  const resultEl = document.getElementById("order-result");
  const cancelIdInput = document.getElementById("cancel-order-id");
  const cancelBtn = document.getElementById("cancel-order-btn");

  function renderCart() {
    itemsEl.innerHTML = "";
    if (cart.length === 0) {
      itemsEl.innerHTML = `<p class="cart-empty">Your cart is empty.</p>`;
    }
    let total = 0;
    for (const item of cart) {
      const subtotal = item.price * item.qty;
      total += subtotal;
      const row = document.createElement("div");
      row.className = "cart-row";
      row.innerHTML = `
        <span>${item.name} &times; ${item.qty}</span>
        <span>$${subtotal.toFixed(2)}</span>`;
      itemsEl.appendChild(row);
    }
    totalEl.textContent = `Total: $${total.toFixed(2)}`;
    confirmBtn.disabled = cart.length === 0;
    return total;
  }

  cartBtn.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) renderCart();
  });
  closeBtn.addEventListener("click", () => panel.classList.add("hidden"));

  confirmBtn.addEventListener("click", async () => {
    const total = renderCart();
    if (cart.length === 0) return;
    confirmBtn.disabled = true;
    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: cart, total }),
      });
      const order = await res.json();
      resultEl.textContent = `Order #${order.id} confirmed. Save this number to cancel it later.`;
      resultEl.className = "order-ok";
      cart.length = 0;
      document.getElementById("cart-count").classList.add("hidden");
      renderCart();
    } catch (err) {
      resultEl.textContent = "Could not place order.";
      resultEl.className = "order-error";
    } finally {
      confirmBtn.disabled = cart.length === 0;
    }
  });

  cancelBtn.addEventListener("click", async () => {
    const id = cancelIdInput.value.trim();
    if (!id) return;
    try {
      const res = await fetch(`/api/orders/${id}/cancel`, { method: "POST" });
      if (!res.ok) throw new Error();
      const order = await res.json();
      resultEl.textContent = `Order #${order.id} is now ${order.status}.`;
      resultEl.className = "order-ok";
    } catch (err) {
      resultEl.textContent = `Order #${id} not found.`;
      resultEl.className = "order-error";
    }
  });
}

renderProducts();
loadMetrics();
loadFigures();
initChat();
initCart();
