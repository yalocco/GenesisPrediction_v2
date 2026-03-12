(function () {
  "use strict";

  function currentPageKey() {
    const path = (window.location.pathname || "").toLowerCase();

    if (path.endsWith("/overlay.html")) return "overlay";
    if (path.endsWith("/sentiment.html")) return "sentiment";
    if (path.endsWith("/digest.html")) return "digest";
    if (path.endsWith("/prediction.html")) return "prediction";
    if (path.endsWith("/prediction_history.html")) return "prediction_history";
    return "home";
  }

  function navLink(pageKey, href, label, activeKey) {
    const activeClass = pageKey === activeKey ? " active" : "";
    return `<a href="${href}" class="nav-link${activeClass}" data-page="${pageKey}">${label}</a>`;
  }

  function buildHeader(activeKey) {
    return `
<header class="topbar">
  <div class="container">
    <div class="topbar-inner">
      <div class="brand">GenesisPrediction v2</div>

      <nav>
        ${navLink("home", "/static/index.html", "Home", activeKey)}
        ${navLink("overlay", "/static/overlay.html", "Overlay", activeKey)}
        ${navLink("sentiment", "/static/sentiment.html", "Sentiment", activeKey)}
        ${navLink("digest", "/static/digest.html", "Digest", activeKey)}
        ${navLink("prediction", "/static/prediction.html", "Prediction", activeKey)}
        ${navLink("prediction_history", "/static/prediction_history.html", "Prediction History", activeKey)}
      </nav>

      <div id="global-health" class="health-line">Ready Health: -- as_of: --</div>
    </div>
  </div>
</header>
`;
  }

  function buildFooter() {
    return `
<footer class="footer">
  <div class="container">
    GenesisPrediction v2<br>
    UI is read-only / analysis is SST
  </div>
</footer>
`;
  }

  function mountSharedLayout() {
    const activeKey = currentPageKey();

    const headerTarget = document.getElementById("site-header");
    if (headerTarget) {
      headerTarget.innerHTML = buildHeader(activeKey);
    }

    const footerTarget = document.getElementById("site-footer");
    if (footerTarget) {
      footerTarget.innerHTML = buildFooter();
    }
  }

  async function fetchJson(url) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (_err) {
      return null;
    }
  }

  function firstString() {
    for (let i = 0; i < arguments.length; i += 1) {
      const v = arguments[i];
      if (typeof v === "string" && v.trim()) return v.trim();
    }
    return "";
  }

  function formatAsOf(value) {
    if (!value) return "--";

    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);

    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  async function updateGlobalHealth() {
    const target = document.getElementById("global-health");
    if (!target) return;

    const health =
      await fetchJson("/analysis/health_latest.json") ||
      await fetchJson("/data/digest/health_latest.json");

    if (!health) {
      target.textContent = "Ready Health: -- as_of: --";
      return;
    }

    const status = firstString(
      health.status,
      health.overall,
      health.state,
      health.health
    ) || "--";

    const asOf = formatAsOf(
      firstString(
        health.as_of,
        health.date,
        health.generated_at,
        health.updated_at
      )
    );

    target.textContent = `Ready Health: ${status} as_of: ${asOf}`;
  }

  async function initLayout() {
    mountSharedLayout();
    await updateGlobalHealth();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLayout);
  } else {
    initLayout();
  }
})();