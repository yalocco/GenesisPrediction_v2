(() => {
  "use strict";

  const DEFAULT_LANG = "en";
  const LANG_CHANGED_EVENT = "gp:lang-changed";

  const LAYOUT_TEXT = {
    en: {
      nav_home: "Home",
      nav_overlay: "Overlay",
      nav_sentiment: "Sentiment",
      nav_digest: "Digest",
      nav_prediction: "Prediction",
      nav_prediction_history: "Prediction History",
      lang_label: "Lang",
      language_switch: "Language switch",
      brand_home: "GenesisPrediction home",
      primary_navigation: "Primary navigation",
      global_status_header: "Global status header",
      ready: "Ready",
      health: "Health",
      fx: "FX",
      as_of: "as_of",
      footer_hint: "UI is display only / analysis is SST",
      brand_title: "GenesisPrediction v2"
    },
    ja: {
      nav_home: "ホーム",
      nav_overlay: "オーバーレイ",
      nav_sentiment: "センチメント",
      nav_digest: "ダイジェスト",
      nav_prediction: "Prediction",
      nav_prediction_history: "Prediction 履歴",
      lang_label: "言語",
      language_switch: "言語切替",
      brand_home: "GenesisPrediction ホーム",
      primary_navigation: "主要ナビゲーション",
      global_status_header: "グローバルステータスヘッダー",
      ready: "準備完了",
      health: "Health",
      fx: "FX",
      as_of: "as_of",
      footer_hint: "UI は表示専用 / analysis が SST",
      brand_title: "GenesisPrediction v2"
    },
    th: {
      nav_home: "หน้าแรก",
      nav_overlay: "โอเวอร์เลย์",
      nav_sentiment: "เซนติเมนต์",
      nav_digest: "ไดเจสต์",
      nav_prediction: "Prediction",
      nav_prediction_history: "ประวัติ Prediction",
      lang_label: "ภาษา",
      language_switch: "สลับภาษา",
      brand_home: "หน้าแรก GenesisPrediction",
      primary_navigation: "เมนูนำทางหลัก",
      global_status_header: "ส่วนหัวสถานะรวม",
      ready: "พร้อม",
      health: "Health",
      fx: "FX",
      as_of: "as_of",
      footer_hint: "UI มีหน้าที่แสดงผลเท่านั้น / analysis คือ SST",
      brand_title: "GenesisPrediction v2"
    }
  };

  const NAV_ITEMS = [
    { href: "/static/index.html", key: "nav_home" },
    { href: "/static/overlay.html", key: "nav_overlay" },
    { href: "/static/sentiment.html", key: "nav_sentiment" },
    { href: "/static/digest.html", key: "nav_digest" },
    { href: "/static/prediction.html", key: "nav_prediction" },
    { href: "/static/prediction_history.html", key: "nav_prediction_history" }
  ];

  function normalizeLang(lang) {
    const value = String(lang || "").trim().toLowerCase();
    return ["en", "ja", "th"].includes(value) ? value : DEFAULT_LANG;
  }

  function getLang() {
    try {
      return normalizeLang(localStorage.getItem("gp_lang") || window.GP_LANG || DEFAULT_LANG);
    } catch (_error) {
      return normalizeLang(window.GP_LANG || DEFAULT_LANG);
    }
  }

  function initLang() {
    window.GP_LANG = getLang();
  }

  function layoutTr(key, lang = null) {
    const activeLang = normalizeLang(lang || window.GP_LANG || DEFAULT_LANG);
    const table = LAYOUT_TEXT[activeLang] || LAYOUT_TEXT[DEFAULT_LANG];
    return table[key] || LAYOUT_TEXT[DEFAULT_LANG][key] || key;
  }

  async function setLang(lang) {
    const nextLang = normalizeLang(lang);
    const prevLang = normalizeLang(window.GP_LANG || DEFAULT_LANG);

    try {
      localStorage.setItem("gp_lang", nextLang);
    } catch (_error) {
      // ignore storage failure
    }

    window.GP_LANG = nextLang;
    document.documentElement.lang = nextLang;

    rerenderLayout();
    await refreshSharedStatus();

    const detail = { lang: nextLang, previousLang: prevLang };
    document.dispatchEvent(new CustomEvent(LANG_CHANGED_EVENT, { detail }));
    window.dispatchEvent(new CustomEvent(LANG_CHANGED_EVENT, { detail }));
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
      return `<a class="${cls}" href="${item.href}"${aria}>${layoutTr(item.key)}</a>`;
    }).join("");
  }

  function buildLanguageHtml() {
    const lang = window.GP_LANG || DEFAULT_LANG;
    return `
      <label class="lang-switch" for="langSwitch" aria-label="${layoutTr("language_switch")}">
        <span class="lang-switch-label">${layoutTr("lang_label")}</span>
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
            <div class="brand" aria-label="${layoutTr("brand_home")}">
              <span class="brand-dot" aria-hidden="true"></span>
              <span class="brand-title">${layoutTr("brand_title")}</span>
            </div>

            <nav class="topnav topnav--center" aria-label="${layoutTr("primary_navigation")}">
              ${buildNavHtml()}
            </nav>

            <div class="topbar-status" aria-label="${layoutTr("global_status_header")}">
              <span id="pillReady" class="pill">${layoutTr("ready")}</span>
              <span id="pillHealth" class="pill">${layoutTr("health")}: --</span>
              <span id="pillFx" class="pill">${layoutTr("fx")}: --</span>
              <span id="pillAsOf" class="pill">${layoutTr("as_of")}: --</span>
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
          <div>${layoutTr("brand_title")}</div>
          <div class="hint">${layoutTr("footer_hint")} / © ${year}</div>
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

  function rerenderLayout() {
    injectHeader();
    injectFooter();
  }

  function safeObject(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : null;
  }

  function safeString(value) {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value).trim();
  }

  function safeArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function pickText(obj, key, lang = null) {
    const target = safeObject(obj);
    if (!target) {
      return "";
    }

    const activeLang = safeString(lang || window.GP_LANG || DEFAULT_LANG) || DEFAULT_LANG;
    const i18nKey = `${key}_i18n`;
    const i18n = safeObject(target[i18nKey]);

    if (i18n) {
      const preferred = safeString(i18n[activeLang]);
      if (preferred) {
        return preferred;
      }

      const english = safeString(i18n.en);
      if (english) {
        return english;
      }

      const japanese = safeString(i18n.ja);
      if (japanese) {
        return japanese;
      }

      const thai = safeString(i18n.th);
      if (thai) {
        return thai;
      }
    }

    return safeString(target[key]);
  }

  function pickList(obj, key, lang = null) {
    const target = safeObject(obj);
    if (!target) {
      return [];
    }

    const activeLang = safeString(lang || window.GP_LANG || DEFAULT_LANG) || DEFAULT_LANG;
    const i18nKey = `${key}_i18n`;
    const i18n = safeObject(target[i18nKey]);

    if (i18n) {
      const preferred = safeArray(i18n[activeLang]).map((item) => safeString(item)).filter(Boolean);
      if (preferred.length > 0) {
        return preferred;
      }

      const english = safeArray(i18n.en).map((item) => safeString(item)).filter(Boolean);
      if (english.length > 0) {
        return english;
      }

      const japanese = safeArray(i18n.ja).map((item) => safeString(item)).filter(Boolean);
      if (japanese.length > 0) {
        return japanese;
      }

      const thai = safeArray(i18n.th).map((item) => safeString(item)).filter(Boolean);
      if (thai.length > 0) {
        return thai;
      }
    }

    return safeArray(target[key]).map((item) => safeString(item)).filter(Boolean);
  }

  function pickField(value, lang = null) {
    const activeLang = safeString(lang || window.GP_LANG || DEFAULT_LANG) || DEFAULT_LANG;

    if (Array.isArray(value)) {
      return value.map((item) => pickField(item, activeLang));
    }

    if (value && typeof value === "object") {
      const asLangMap =
        ("en" in value || "ja" in value || "th" in value) &&
        !Array.isArray(value.en) &&
        !Array.isArray(value.ja) &&
        !Array.isArray(value.th);

      if (asLangMap) {
        const preferred = safeString(value[activeLang]);
        if (preferred) {
          return preferred;
        }
        return (
          safeString(value.en) ||
          safeString(value.ja) ||
          safeString(value.th) ||
          ""
        );
      }
    }

    return value;
  }

  function exposeI18nHelpers() {
    window.GenesisI18n = {
      getLang,
      setLang,
      pickText,
      pickList,
      pickField,
      tr: layoutTr,
      normalizeLang,
      defaultLang: DEFAULT_LANG,
      events: {
        langChanged: LANG_CHANGED_EVENT
      }
    };
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

  initLang();
  document.documentElement.lang = window.GP_LANG || DEFAULT_LANG;

  async function boot() {
    exposeI18nHelpers();
    document.documentElement.dataset.layoutReady = "0";

    rerenderLayout();

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