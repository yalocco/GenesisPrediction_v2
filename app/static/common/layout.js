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
    if (!target) return false;

    if (target.dataset.layoutMounted === "1" && target.innerHTML.trim() === html) {
      return false;
    }

    target.innerHTML = html;
    target.dataset.layoutMounted = "1";
    return true;
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

  function setHeaderFallback() {
    const pillReady = document.getElementById("pillReady");
    const pillHealth = document.getElementById("pillHealth");
    const pillAsOf = document.getElementById("pillAsOf");
    const legacyHealth = document.getElementById("global-health");

    if (pillReady) {
      pillReady.textContent = "Ready";
    }
    if (pillHealth) {
      pillHealth.textContent = "Health: --";
    }
    if (pillAsOf) {
      pillAsOf.textContent = "as_of: --";
    }
    if (legacyHealth) {
      legacyHealth.textContent = "Ready Health: -- as_of: --";
    }
  }

  function mountSharedLayout() {
    const activeKey = currentPageKey();

    const headerTarget = document.getElementById("site-header");
    const footerTarget = document.getElementById("site-footer");

    const headerMounted = mountIntoTarget(headerTarget, HEADER_HTML);
    const footerMounted = mountIntoTarget(footerTarget, FOOTER_HTML);

    applyActiveNav(activeKey);
    setHeaderFallback();

    return headerMounted || footerMounted;
  }

  async function refreshSharedStatus() {
    if (typeof window.refreshGlobalStatus === "function") {
      try {
        await window.refreshGlobalStatus();
        return;
      } catch (err) {
        console.error("[layout] refreshGlobalStatus failed:", err);
      }
    }

    setHeaderFallback();
  }

  async function initLayout() {
    ensureLayoutStateFlag();
    mountSharedLayout();
    markLayoutReady();
    await refreshSharedStatus();
  }

  window.GPLayout = {
    init: initLayout,
    remount: async function () {
      mountSharedLayout();
      markLayoutReady();
      await refreshSharedStatus();
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLayout, { once: true });
  } else {
    initLayout();
  }
})();