(() => {
  "use strict";

  const NAV_ITEMS = [
    { href: "/static/index.html", label: "Home" },
    { href: "/static/overlay.html", label: "Overlay" },
    { href: "/static/sentiment.html", label: "Sentiment" },
    { href: "/static/digest.html", label: "Digest" },
    { href: "/static/prediction.html", label: "Prediction" },
    { href: "/static/prediction_history.html", label: "Prediction History" }
  ];

  function normalizePath(path) {
    return String(path || "")
      .replace(/[?#].*$/, "")
      .replace(/\/+$/, "")
      .toLowerCase();
  }

  function currentPath() {
    try {
      return normalizePath(window.location.pathname || "");
    } catch (_error) {
      return "";
    }
  }

  function isActiveNav(href) {
    return currentPath() === normalizePath(href);
  }

  function buildNavHtml() {
    return NAV_ITEMS.map((item) => {
      const active = isActiveNav(item.href);
      const aria = active ? ' aria-current="page"' : "";
      const cls = `nav-link${active ? " active" : ""}`;
      return `<a class="${cls}" href="${item.href}"${aria}>${item.label}</a>`;
    }).join("");
  }

  function buildHeaderHtml() {
    return `
      <header class="topbar">
        <div class="container">
          <div class="topbar-inner topbar-inner--three">
            <div class="brand" aria-label="GenesisPrediction home">
              <span class="brand-dot" aria-hidden="true"></span>
              <span class="brand-title">GenesisPrediction v2</span>
            </div>

            <nav class="topnav topnav--center" aria-label="Primary navigation">
              ${buildNavHtml()}
            </nav>

            <div class="topbar-status" aria-label="Global status header">
              <span id="pillReady" class="pill">Ready</span>
              <span id="pillHealth" class="pill">Health: --</span>
              <span id="pillAsOf" class="pill">as_of: --</span>
            </div>
          </div>
        </div>
      </header>
    `;
  }

  function buildFooterHtml() {
    const year = new Date().getFullYear();
    return `
      <footer class="footer">
        <div class="container">
          <div>GenesisPrediction v2</div>
          <div class="hint">UI is display only / analysis is SST / © ${year}</div>
        </div>
      </footer>
    `;
  }

  function injectHeader() {
    const root = document.getElementById("site-header");
    if (!root) return;
    root.innerHTML = buildHeaderHtml();
  }

  function injectFooter() {
    const root = document.getElementById("site-footer");
    if (!root) return;
    root.innerHTML = buildFooterHtml();
  }

  async function refreshSharedStatus() {
    try {
      if (window.GenesisGlobalStatus && typeof window.GenesisGlobalStatus.refresh === "function") {
        await window.GenesisGlobalStatus.refresh();
      }
    } catch (_error) {
      // header skeleton remains visible even when status fetch fails
    }
  }

  async function boot() {
    document.documentElement.dataset.layoutReady = "0";

    injectHeader();
    injectFooter();
    await refreshSharedStatus();

    document.documentElement.dataset.layoutReady = "1";
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
