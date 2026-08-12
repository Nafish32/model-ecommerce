const BOX_ICON = `
  <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M21 8l-9-5-9 5 9 5 9-5z"></path>
    <path d="M3 8v8l9 5 9-5V8"></path>
    <path d="M12 13v8"></path>
  </svg>`;

const cart = []; // {name, price, qty}
let currentUser = null;

function updateBadge() {
  const count = cart.reduce((sum, i) => sum + i.qty, 0);
  const badge = document.getElementById("cart-count");
  badge.textContent = count;
  badge.classList.toggle("hidden", count === 0);
}

// Returns true if the item was added, false if login is required (opens the modal).
function addToCart(product) {
  if (!currentUser) {
    openLogin();
    return false;
  }
  const existing = cart.find((i) => i.name === product.name);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ name: product.name, price: product.price, qty: 1 });
  }
  updateBadge();
  return true;
}

function openLogin() { document.getElementById("login-overlay").classList.remove("hidden"); }
function closeLogin() { document.getElementById("login-overlay").classList.add("hidden"); }

function renderAuth() {
  const btn = document.getElementById("auth-btn");
  const emailEl = document.getElementById("user-email");
  const ordersBtn = document.getElementById("orders-btn");
  if (currentUser) {
    emailEl.textContent = currentUser.email;
    emailEl.classList.remove("hidden");
    ordersBtn.classList.remove("hidden");
    btn.textContent = "Log out";
  } else {
    emailEl.classList.add("hidden");
    ordersBtn.classList.add("hidden");
    btn.textContent = "Log in";
  }
}

async function initAuth() {
  try {
    const res = await fetch("/api/me");
    if (res.ok) currentUser = await res.json();
  } catch (_) { /* not logged in */ }
  renderAuth();

  document.getElementById("auth-btn").addEventListener("click", async () => {
    if (currentUser) {
      await fetch("/api/logout", { method: "POST" });
      currentUser = null;
      document.getElementById("orders-panel").classList.add("hidden");
      renderAuth();
    } else {
      openLogin();
    }
  });
  document.getElementById("login-modal-close").addEventListener("click", closeLogin);
  document.getElementById("login-overlay").addEventListener("click", (e) => {
    if (e.target.id === "login-overlay") closeLogin();
  });
  document.getElementById("storefront-login").addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = document.getElementById("sf-login-error");
    err.textContent = "";
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: document.getElementById("sf-email").value,
          password: document.getElementById("sf-password").value,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Login failed");
      currentUser = await res.json();
      renderAuth();
      closeLogin();
    } catch (e2) {
      err.textContent = e2.message;
    }
  });
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

  let sessionId = null;

  function addMessage(text, cls) {
    const el = document.createElement("div");
    el.className = `msg ${cls}`;
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    return el;
  }

  function addProductCards(products) {
    if (!products || !products.length) return;
    const wrap = document.createElement("div");
    wrap.className = "msg bot chat-products";
    for (const p of products) {
      const card = document.createElement("div");
      card.className = `chat-product${p.in_stock ? " clickable" : " oos"}`;
      card.innerHTML = `
        <span class="name">${p.name}</span>
        <span class="meta">$${p.price.toFixed(2)} · ${p.in_stock ? "Add to cart +" : "out of stock"}</span>`;
      if (p.in_stock) {
        card.addEventListener("click", () => {
          if (addToCart(p)) card.querySelector(".meta").textContent = "Added ✓";
        });
      }
      wrap.appendChild(card);
    }
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
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
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await res.json();
      sessionId = data.session_id;
      pending.textContent = data.reply;
      pending.classList.remove("pending");
      addProductCards(data.products);
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
        <span><button class="cart-remove" aria-label="Remove one">&minus;</button>${item.name} &times; ${item.qty}</span>
        <span>$${subtotal.toFixed(2)}</span>`;
      row.querySelector(".cart-remove").addEventListener("click", () => {
        item.qty -= 1;
        if (item.qty <= 0) cart.splice(cart.indexOf(item), 1);
        renderCart();
        updateBadge();
      });
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
      resultEl.textContent = `Order #${order.id} confirmed.`;
      resultEl.className = "order-ok";
      cart.length = 0;
      updateBadge();
      renderCart();
    } catch (err) {
      resultEl.textContent = "Could not place order.";
      resultEl.className = "order-error";
    } finally {
      confirmBtn.disabled = cart.length === 0;
    }
  });
}

// --- my orders + reviews ---
function initOrders() {
  const btn = document.getElementById("orders-btn");
  const panel = document.getElementById("orders-panel");
  const closeBtn = document.getElementById("orders-close");
  const list = document.getElementById("orders-list");

  const overlay = document.getElementById("review-overlay");
  const form = document.getElementById("review-form");
  const productLabel = document.getElementById("review-product");
  const errEl = document.getElementById("review-error");
  let reviewing = null; // product name being reviewed

  function openReview(product) {
    reviewing = product;
    productLabel.textContent = product;
    errEl.textContent = "";
    form.reset();
    overlay.classList.remove("hidden");
  }
  const closeReview = () => overlay.classList.add("hidden");
  document.getElementById("review-close").addEventListener("click", closeReview);
  overlay.addEventListener("click", (e) => { if (e.target.id === "review-overlay") closeReview(); });

  async function loadOrders() {
    list.innerHTML = `<p class="cart-empty">Loading…</p>`;
    const res = await fetch("/api/orders/mine");
    if (!res.ok) { list.innerHTML = `<p class="cart-empty">Please log in.</p>`; return; }
    const orders = await res.json();
    if (!orders.length) { list.innerHTML = `<p class="cart-empty">No orders yet.</p>`; return; }
    list.innerHTML = "";
    for (const o of orders) {
      const card = document.createElement("div");
      card.className = "order-card";
      const rows = o.items.map((i) => `
        <div class="order-item">
          <span>${i.name} &times; ${i.qty}</span>
          ${o.status === "cancelled" ? "" : `<button class="review-btn" data-product="${i.name}">Review</button>`}
        </div>`).join("");
      card.innerHTML = `
        <div class="order-head">
          <strong>Order #${o.id}</strong>
          <span class="order-status status-${o.status}">${o.status}</span>
        </div>
        <div class="order-meta">${o.created_at} · $${o.total.toFixed(2)}</div>
        ${rows}`;
      list.appendChild(card);
    }
    list.querySelectorAll(".review-btn").forEach((b) =>
      b.addEventListener("click", () => openReview(b.dataset.product)));
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errEl.textContent = "";
    try {
      const res = await fetch("/api/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product: reviewing,
          rating: Number(document.getElementById("review-rating").value),
          text: document.getElementById("review-text").value,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Could not submit review");
      closeReview();
    } catch (e2) {
      errEl.textContent = e2.message;
    }
  });

  btn.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) loadOrders();
  });
  closeBtn.addEventListener("click", () => panel.classList.add("hidden"));
}

initAuth();
initOrders();
renderProducts();
loadMetrics();
loadFigures();
initChat();
initCart();
