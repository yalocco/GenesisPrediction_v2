(function () {
  "use strict";

  const HEADER_HTML = `
<header class="topbar">
  <div class="container">
    <div class="topbar-inner topbar-inner--three">
      <div class="brand">
        <span class="brand-dot" aria-hidden="true"></span>
        <span class="brand-title">GenesisPrediction v2</span>
      </div>

      <nav class="topnav topnav--center" aria-label="Primary Navigation">
        <a class="pill nav-link" data-page="home" href="/static/index.html">Home</a>
        <a class="pill nav-link" data-page="overlay" href="/static/overlay.html">Overlay</a>
        <a class="pill nav-link" data-page="sentiment" href="/static/sentiment.html">Sentiment</a>
        <a class="pill nav-link" data-page="digest" href="/static/digest.html">Digest</a>
        <a class="pill nav-link" data-page="prediction" href="/static/prediction.html">Prediction</a>
        <a class="pill nav-link" data-page="prediction_history" href="/static/prediction_history.html">Prediction History</a>
      </nav>

      <div class="topbar-status" aria-label="Runtime Status">
        <span id="pillReady" class="pill">Ready</span>
        <span id="pillHealth" class="pill">Health: --</span>
        <span id="pillAsOf" class="pill">as_of: --</span>
      </div>
    </div>
  </div>
</header>
`.trim();

  const FOOTER_HTML = `
<footer class="footer">
  <div class="container">
    GenesisPrediction v2<br>
    UI is read-only / analysis is SST
  </div>
</footer>
`.trim();

  function currentPageKey() {
    const path = (window.location.pathname || "").toLowerCase();

    if (path.endsWith("/overlay.html")) return "overlay";
    if (path.endsWith("/sentiment.html")) return "sentiment";
    if (path.endsWith("/digest.html")) return "digest";
    if (path.endsWith("/prediction.html")) return "prediction";
    if (path.endsWith("/prediction_history.html")) return "prediction_history";
    return "home";
  }

  function ensureLayoutStateFlag() {
    document.documentElement.setAttribute("data-layout-ready", "0");
  }

  function markLayoutReady() {
    window.requestAnimationFrame(function () {
      document.documentElement.setAttribute("data-layout-ready", "1");
    });
  }

  function mountIntoTarget(target, html) {
    if (!target) return;

    if (target.dataset.layoutMounted === "1" && target.innerHTML.trim() === html) {
      return;
    }

    target.innerHTML = html;
    target.dataset.layoutMounted = "1";
  }

  function applyActiveNav(activeKey) {
    const links = document.querySelectorAll(".nav-link[data-page]");

    links.forEach(function (link) {
      const key = (link.getAttribute("data-page") || "").trim();
      const isActive = key === activeKey;

      link.classList.toggle("active", isActive);

      if (isActive) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function mountSharedLayout() {
    const activeKey = currentPageKey();

    const headerTarget = document.getElementById("site-header");
    const footerTarget = document.getElementById("site-footer");

    mountIntoTarget(headerTarget, HEADER_HTML);
    mountIntoTarget(footerTarget, FOOTER_HTML);
    applyActiveNav(activeKey);
  }

  async function fetchJson(url) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) {
        throw new Error("HTTP " + res.status);
      }
      return await res.json();
    } catch (_err) {
      return null;
    }
  }

  function firstString() {
    for (let i = 0; i < arguments.length; i += 1) {
      const value = arguments[i];
      if (typeof value === "string" && value.trim()) {
        return value.trim();
      }
    }
    return "";
  }

  function normalizeHealthStatus(health) {
    if (!health || typeof health !== "object") {
      return "--";
    }

    const raw =
      firstString(
        health.status,
        health.overall,
        health.state,
        health.health
      ) || "--";

    const lower = raw.toLowerCase();

    if (lower === "ok" || lower === "ready" || lower === "healthy") {
      return "OK";
    }

    if (lower === "warn" || lower === "warning") {
      return "WARN";
    }

    if (lower === "error" || lower === "failed" || lower === "critical") {
      return "ERROR";
    }

    return raw;
  }

  function formatAsOf(value) {
    if (!value) return "--";

    const text = String(value).trim();
    if (!text) return "--";

    const m = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) {
      return `${m[1]}-${m[2]}-${m[3]}`;
    }

    const d = new Date(text);
    if (Number.isNaN(d.getTime())) {
      return text;
    }

    const y = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, "0");
    const da = String(d.getDate()).padStart(2, "0");
    return `${y}-${mo}-${da}`;
  }

  function setHealthText(status, asOf) {
    const safeStatus = status || "--";
    const safeAsOf = asOf || "--";

    const pillReady = document.getElementById("pillReady");
    const pillHealth = document.getElementById("pillHealth");
    const pillAsOf = document.getElementById("pillAsOf");
    const legacyHealth = document.getElementById("global-health");

    if (pillReady) {
      pillReady.textContent = "Ready";
    }

    if (pillHealth) {
      pillHealth.textContent = `Health: ${safeStatus}`;
    }

    if (pillAsOf) {
      pillAsOf.textContent = `as_of: ${safeAsOf}`;
    }

    if (legacyHealth) {
      legacyHealth.textContent = `Ready Health: ${safeStatus} as_of: ${safeAsOf}`;
    }
  }

  async function updateGlobalHealth() {
    setHealthText("--", "--");

    const health = await fetchJson("/analysis/health_latest.json");

    if (!health) {
      setHealthText("--", "--");
      return;
    }

    const status = normalizeHealthStatus(health);
    const asOf = formatAsOf(
      firstString(
        health.as_of,
        health.date,
        health.generated_at,
        health.updated_at
      )
    );

    setHealthText(status, asOf);
  }

  async function initLayout() {
    ensureLayoutStateFlag();
    mountSharedLayout();
    markLayoutReady();
    await updateGlobalHealth();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLayout, { once: true });
  } else {
    initLayout();
  }
})();