(() => {
  "use strict";

  const DEFAULT_LANG = "en";

  const NAV_ITEMS = [
    { href: "/static/index.html", label: "Home" },
    { href: "/static/overlay.html", label: "Overlay" },
    { href: "/static/sentiment.html", label: "Sentiment" },
    { href: "/static/digest.html", label: "Digest" },
    { href: "/static/prediction.html", label: "Prediction" },
    { href: "/static/prediction_history.html", label: "Prediction History" }
  ];

  function getLang() {
    try {
      return localStorage.getItem("gp_lang") || DEFAULT_LANG;
    } catch (_error) {
      return DEFAULT_LANG;
    }
  }

  function setLang(lang) {
    try {
      localStorage.setItem("gp_lang", lang);
    } catch (_error) {
      // ignore storage failure
    }
    window.GP_LANG = lang;
    window.location.reload();
  }

  function initLang() {
    window.GP_LANG = getLang();
  }

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
    const now = currentPath();
    const normalizedHref = normalizePath(href);

    if (now === normalizedHref) {
      return true;
    }

    if (now === "") {
      return normalizedHref === "/static/index.html";
    }

    return false;
  }

  function buildNavHtml() {
    return NAV_ITEMS.map((item) => {
      const active = isActiveNav(item.href);
      const aria = active ? ' aria-current="page"' : "";
      const cls = `nav-link${active ? " active" : ""}`;
      return `<a class="${cls}" href="${item.href}"${aria}>${item.label}</a>`;
    }).join("");
  }

  function buildLanguageHtml() {
    const lang = window.GP_LANG || DEFAULT_LANG;
    return `
      <label class="lang-switch" for="langSwitch" aria-label="Language switch">
        <span class="lang-switch-label">Lang</span>
        <select id="langSwitch" class="lang-switch-select">
          <option value="en"${lang === "en" ? " selected" : ""}>EN</option>
          <option value="ja"${lang === "ja" ? " selected" : ""}>JA</option>
          <option value="th"${lang === "th" ? " selected" : ""}>TH</option>
        </select>
      </label>
    `;
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
              <span id="pillFx" class="pill">FX: --</span>
              <span id="pillAsOf" class="pill">as_of: --</span>
              ${buildLanguageHtml()}
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
    if (!root) {
      return;
    }
    root.innerHTML = buildHeaderHtml();

    const langSwitch = document.getElementById("langSwitch");
    if (langSwitch) {
      langSwitch.addEventListener("change", (event) => {
        setLang(event.target.value);
      });
    }
  }

  function injectFooter() {
    const root = document.getElementById("site-footer");
    if (!root) {
      return;
    }
    root.innerHTML = buildFooterHtml();
  }

  async function refreshSharedStatus() {
    try {
      if (window.GenesisGlobalStatus) {
        if (typeof window.GenesisGlobalStatus.init === "function") {
          await window.GenesisGlobalStatus.init();
          return;
        }
        if (typeof window.GenesisGlobalStatus.rerender === "function") {
          await window.GenesisGlobalStatus.rerender();
          return;
        }
        if (typeof window.GenesisGlobalStatus.refresh === "function") {
          await window.GenesisGlobalStatus.refresh();
          return;
        }
      }
    } catch (_error) {
      // header skeleton remains visible even when status fetch fails
    }
  }

  async function boot() {
    initLang();
    document.documentElement.dataset.layoutReady = "0";

    injectHeader();
    injectFooter();

    document.dispatchEvent(new CustomEvent("layout:mounted"));

    await refreshSharedStatus();

    document.documentElement.dataset.layoutReady = "1";
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();