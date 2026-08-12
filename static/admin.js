const $ = (id) => document.getElementById(id);
const SENT_COLORS = { positive: "#16a34a", neutral: "#64748b", negative: "#dc2626" };
const STATUS_COLORS = { placed: "#2563eb", cancelled: "#dc2626", shipped: "#16a34a" };

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (res.status === 401) { showLogin(); throw new Error("unauthorized"); }
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.status === 204 ? null : res.json();
}

// --- auth ---
function showLogin() { $("login").classList.remove("hidden"); $("admin").classList.add("hidden"); }
function showAdmin() { $("login").classList.add("hidden"); $("admin").classList.remove("hidden"); }

async function checkAuth() {
  try { await api("/api/admin/me"); showAdmin(); route(); }
  catch { showLogin(); }
}

$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("login-error").textContent = "";
  try {
    await api("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ email: $("login-email").value, password: $("login-password").value }),
    });
    showAdmin();
    route();
  } catch (err) {
    $("login-error").textContent = err.message;
  }
});

$("logout-btn").addEventListener("click", async () => {
  await api("/api/admin/logout", { method: "POST" });
  showLogin();
});

// --- charts (CSS bars) ---
function barChart(el, data, colors) {
  el.innerHTML = "";
  const max = Math.max(1, ...Object.values(data));
  for (const [label, n] of Object.entries(data)) {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <span class="bar-label">${label}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${(n / max) * 100}%;background:${colors[label] || "#94a3b8"}"></span></span>
      <span class="bar-val">${n}</span>`;
    el.appendChild(row);
  }
}

// --- dashboard ---
async function loadDashboard() {
  const a = await api("/api/admin/analytics");
  $("stat-cards").innerHTML = `
    <div class="stat"><span class="stat-num">${a.orders.count}</span><span class="stat-label">Active orders</span></div>
    <div class="stat"><span class="stat-num">$${a.orders.revenue.toFixed(2)}</span><span class="stat-label">Revenue</span></div>
    <div class="stat"><span class="stat-num">${a.reviews_total}</span><span class="stat-label">Reviews</span></div>`;
  barChart($("status-chart"), a.status, STATUS_COLORS);
  barChart($("sentiment-chart"), a.sentiment, SENT_COLORS);
  await loadOrders();
}

async function loadOrders() {
  const orders = await api("/api/admin/orders");
  const t = $("orders-table");
  t.innerHTML = "<tr><th>ID</th><th>Customer</th><th>Items</th><th>Total</th><th>Status</th><th>Date</th><th></th></tr>";
  for (const o of orders) {
    const tr = document.createElement("tr");
    const items = o.items.map((i) => `${i.name}×${i.qty}`).join(", ");
    tr.innerHTML = `
      <td>#${o.id}</td><td>${o.customer}</td><td>${items}</td><td>$${o.total.toFixed(2)}</td>
      <td>
        <select class="status-sel">
          ${["placed", "shipped", "cancelled"].map((s) => `<option ${s === o.status ? "selected" : ""}>${s}</option>`).join("")}
        </select>
      </td>
      <td>${o.created_at}</td>
      <td><button class="del-btn">Delete</button></td>`;
    tr.querySelector(".status-sel").addEventListener("change", (e) =>
      api(`/api/admin/orders/${o.id}`, { method: "PUT", body: JSON.stringify({ status: e.target.value }) }).then(loadDashboard));
    tr.querySelector(".del-btn").addEventListener("click", () => {
      if (confirm(`Delete order #${o.id}? This cannot be undone.`))
        api(`/api/admin/orders/${o.id}`, { method: "DELETE" }).then(loadDashboard);
    });
    t.appendChild(tr);
  }
}

$("sentiment-card").addEventListener("click", () => { location.hash = "#reviews"; });

// --- reviews (sortable) ---
let reviews = [];
let sortKey = "created_at";
let sortDir = -1;

const COLS = [
  { key: "product", label: "Product" },
  { key: "author", label: "Name" },
  { key: "rating", label: "Rating" },
  { key: "text", label: "Review" },
  { key: "sentiment", label: "Sentiment" },
  { key: "created_at", label: "Date" },
];

async function loadReviews() {
  reviews = await api("/api/admin/reviews");
  renderReviews();
}

function renderReviews() {
  const sorted = [...reviews].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    return (av < bv ? -1 : av > bv ? 1 : 0) * sortDir;
  });
  const t = $("reviews-table");
  const head = COLS.map((c) => {
    const arrow = c.key === sortKey ? (sortDir === 1 ? " ▲" : " ▼") : "";
    return `<th class="sortable" data-key="${c.key}">${c.label}${arrow}</th>`;
  }).join("");
  t.innerHTML = `<tr>${head}</tr>`;
  for (const r of sorted) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.product}</td><td>${r.author}</td><td>${"★".repeat(r.rating)}</td>
      <td class="review-text">${r.text}</td>
      <td><span class="pill pill-${r.sentiment}">${r.sentiment}</span></td>
      <td>${r.created_at}</td>`;
    t.appendChild(tr);
  }
  t.querySelectorAll(".sortable").forEach((th) =>
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (key === sortKey) sortDir *= -1;
      else { sortKey = key; sortDir = 1; }
      renderReviews();
    }));
}

// --- routing ---
function route() {
  const view = location.hash === "#reviews" ? "reviews" : "dashboard";
  $("view-dashboard").classList.toggle("hidden", view !== "dashboard");
  $("view-reviews").classList.toggle("hidden", view !== "reviews");
  document.querySelectorAll(".admin-top nav a").forEach((a) =>
    a.classList.toggle("active", a.dataset.view === view));
  if (view === "dashboard") loadDashboard();
  else loadReviews();
}

window.addEventListener("hashchange", route);
checkAuth();
