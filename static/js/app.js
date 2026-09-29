async function api(url, options = {}) {
  const response = await fetch(url, { credentials: "same-origin", ...options });
  const text = await response.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
  if (!response.ok) {
    const message = data.detail || "Something went wrong";
    throw new Error(message);
  }
  return data;
}

function showError(message, elementId = "alert") {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.style.display = "block";
}

function money(value) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value || 0);
}

async function sessionInfo() {
  return api("/api/session-info");
}

async function requireAuth() {
  const info = await sessionInfo();
  if (!info.authenticated) window.location.href = "/login";
  return info;
}

function plannerCard(item) {
  return `
    <article class="reco">
      <div class="reco-head">
        <div>
          <span class="badge">${item.platform}</span>
          <h3>${escapeHtml(item.title)}</h3>
          <p class="muted">${escapeHtml(item.description || "Simulated catalog option.")}</p>
        </div>
        <div class="price">${money(item.price)} × ${item.quantity}</div>
      </div>
      <p><strong>Why:</strong> ${escapeHtml(item.reason)}</p>
      <a class="btn secondary" href="${item.link}" target="_blank" rel="noopener noreferrer">Open platform search</a>
    </article>`;
}

function renderResult(result, targetId = "result") {
  const el = document.getElementById(targetId);
  if (!el) return;
  const breakdown = Object.entries(result.budget_breakdown || {}).map(([key, value]) => `<div><span class="muted">${escapeHtml(key)}</span><br><strong>${money(value)}</strong></div>`).join("");
  el.innerHTML = `
    <div class="card content-card">
      <span class="badge">${result.ai_generated ? "Gemini AI" : "Local fallback"}</span>
      <h2>${escapeHtml(result.title)}</h2>
      <p class="lead">${escapeHtml(result.summary)}</p>
      <div class="stats">
        <div class="stat"><span class="muted">Budget</span><strong>${money(result.budget)}</strong></div>
        <div class="stat"><span class="muted">Estimated total</span><strong>${money(result.estimated_total)}</strong></div>
        <div class="stat"><span class="muted">Remaining</span><strong>${money(result.savings)}</strong></div>
      </div>
      <div class="breakdown">${breakdown}</div>
      <div class="recommendation-list">${(result.recommendations || []).map(plannerCard).join("")}</div>
      <h3>Planning tips</h3>
      <ul>${(result.tips || []).map(t => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
    </div>`;
  el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[ch]));
}

async function logout() {
  try { await api("/api/auth/logout", { method: "POST" }); } finally { window.location.href = "/"; }
}

async function hydrateNav() {
  const info = await sessionInfo();
  const authLinks = document.querySelectorAll("[data-auth-link]");
  authLinks.forEach(el => {
    if (info.authenticated) {
      el.textContent = "Dashboard";
      el.href = "/dashboard";
    }
  });
  const logoutBtn = document.querySelector("[data-logout]");
  if (logoutBtn) logoutBtn.classList.toggle("hidden", !info.authenticated);
  const navName = document.querySelector("[data-user-name]");
  if (navName && info.authenticated) navName.textContent = info.full_name || info.email;
}

document.addEventListener("DOMContentLoaded", hydrateNav);
