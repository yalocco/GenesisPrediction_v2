(function () {
  "use strict";

  const GLOBAL_STATUS_URL = "/analysis/global_status_latest.json";
  const i18n = window.GP_I18N || window.GenesisI18n || null;
  const manager = window.GP_LANG_MANAGER || null;
  const LANG_CHANGED_EVENT =
    (i18n && i18n.events && i18n.events.langChanged) ||
    (manager && manager.LANG_CHANGED_EVENT) ||
    "gp:lang-changed";

  const UI_TEXT = {
    en: {
      "gs.label.date": "Date",
      "gs.label.system": "System",
      "gs.label.analysis": "Analysis",
      "gs.label.prediction": "Prediction",
      "gs.label.health": "Health",
      "gs.label.fx_base": "FX Base",
      "gs.label.fx_signal": "FX Signal",
      "gs.label.trend": "Trend",
      "gs.label.articles": "Articles",
      "gs.label.highlights": "Highlights",
      "gs.label.risk": "Risk",
      "gs.label.positive": "Positive",
      "gs.label.negative": "Negative",
      "gs.label.regime": "Regime",
      "gs.label.signal": "Signal",
      "gs.label.confidence": "Confidence",
      "gs.label.snapshots": "Snapshots",
      "gs.label.drift": "Drift",
      "gs.label.review": "Review",
      "gs.sub.analysis_latest": "analysis latest",
      "gs.state.ready": "Ready",
      "gs.state.blocked": "Blocked",
      "gs.prefix.health": "Health",
      "gs.prefix.fx": "FX",
      "gs.prefix.as_of": "as_of"
    },
    ja: {
      "gs.label.date": "日付",
      "gs.label.system": "システム",
      "gs.label.analysis": "分析",
      "gs.label.prediction": "予測",
      "gs.label.health": "健全性",
      "gs.label.fx_base": "FX基準",
      "gs.label.fx_signal": "FXシグナル",
      "gs.label.trend": "トレンド",
      "gs.label.articles": "記事数",
      "gs.label.highlights": "ハイライト",
      "gs.label.risk": "リスク",
      "gs.label.positive": "ポジティブ",
      "gs.label.negative": "ネガティブ",
      "gs.label.regime": "レジーム",
      "gs.label.signal": "シグナル",
      "gs.label.confidence": "信頼度",
      "gs.label.snapshots": "スナップショット",
      "gs.label.drift": "変化",
      "gs.label.review": "レビュー",
      "gs.sub.analysis_latest": "analysis latest",
      "gs.state.ready": "準備完了",
      "gs.state.blocked": "停止",
      "gs.prefix.health": "健全性",
      "gs.prefix.fx": "FX",
      "gs.prefix.as_of": "as_of"
    },
    th: {
      "gs.label.date": "วันที่",
      "gs.label.system": "ระบบ",
      "gs.label.analysis": "การวิเคราะห์",
      "gs.label.prediction": "การคาดการณ์",
      "gs.label.health": "สุขภาพข้อมูล",
      "gs.label.fx_base": "ฐาน FX",
      "gs.label.fx_signal": "สัญญาณ FX",
      "gs.label.trend": "แนวโน้ม",
      "gs.label.articles": "บทความ",
      "gs.label.highlights": "ไฮไลต์",
      "gs.label.risk": "ความเสี่ยง",
      "gs.label.positive": "เชิงบวก",
      "gs.label.negative": "เชิงลบ",
      "gs.label.regime": "ระบอบ",
      "gs.label.signal": "สัญญาณ",
      "gs.label.confidence": "ความเชื่อมั่น",
      "gs.label.snapshots": "สแนปช็อต",
      "gs.label.drift": "การเปลี่ยนแปลง",
      "gs.label.review": "การทบทวน",
      "gs.sub.analysis_latest": "analysis latest",
      "gs.state.ready": "พร้อม",
      "gs.state.blocked": "ถูกบล็อก",
      "gs.prefix.health": "สุขภาพข้อมูล",
      "gs.prefix.fx": "FX",
      "gs.prefix.as_of": "as_of"
    }
  };

  const DEFAULT_STATUS = {
    as_of: "--",
    updated: "--",
    global_risk: "--",
    global_risk_sub: "",
    sentiment_balance: "--",
    sentiment_balance_sub: "",
    fx_regime: "--",
    fx_regime_sub: "",
    articles: "--",
    articles_sub: "",
    health: "--",
    health_sub: ""
  };

  let latestStatus = { ...DEFAULT_STATUS };
  let hasFetched = false;
  let headerRetryCount = 0;
  let headerRetryTimer = null;

  function text(value, fallback = "--") {
    if (value === null || value === undefined) return fallback;
    const s = String(value).trim();
    return s ? s : fallback;
  }

  function upper(value, fallback = "--") {
    const s = text(value, fallback);
    return s === fallback ? fallback : s.toUpperCase();
  }

  function getLang() {
    if (i18n && typeof i18n.getLang === "function") {
      return i18n.getLang();
    }
    if (manager && typeof manager.getLang === "function") {
      return manager.getLang();
    }
    return String(window.GP_LANG || "en").trim().toLowerCase() || "en";
  }

  function tr(key) {
    if (i18n && typeof i18n.translate === "function") {
      return i18n.translate(UI_TEXT, key, getLang());
    }
    const lang = getLang();
    return (UI_TEXT[lang] && UI_TEXT[lang][key]) || UI_TEXT.en[key] || key;
  }

  function normalizeStatusClass(value) {
    const v = upper(value);

    if (
      v === "SAFE" ||
      v === "OK" ||
      v === "POS" ||
      v === "LOW" ||
      v === "READY" ||
      v === "STABLE"
    ) {
      return "safe";
    }

    if (
      v === "CAUTION" ||
      v === "WARN" ||
      v === "WARNING" ||
      v === "MIX" ||
      v === "GUARDED" ||
      v === "ELEVATED" ||
      v === "DEGRADED" ||
      v === "WATCH"
    ) {
      return "caution";
    }

    if (
      v === "DANGER" ||
      v === "NG" ||
      v === "NEG" ||
      v === "HIGH" ||
      v === "CRITICAL" ||
      v === "OFF" ||
      v === "BLOCKED" ||
      v === "ALERT"
    ) {
      return "danger";
    }

    return "neutral";
  }

  function addStatusClass(node, value) {
    if (!node) return;
    node.classList.remove("status-safe", "status-caution", "status-danger", "status-neutral");
    node.classList.add("status-" + normalizeStatusClass(value));
  }

  function setFirstText(selectors, value) {
    for (const selector of selectors) {
      const node = document.querySelector(selector);
      if (node) node.textContent = value;
    }
  }

  function setFirstClass(selectors, value) {
    for (const selector of selectors) {
      const node = document.querySelector(selector);
      if (node) addStatusClass(node, value);
    }
  }

  function getHeaderSelectors() {
    return {
      ready: [
        "#pillReady",
        "#headerReady",
        "[data-role='header-ready']",
        "[data-header-ready]",
        ".js-header-ready",
        ".gp-header-ready"
      ],
      health: [
        "#pillHealth",
        "#headerHealth",
        "[data-role='header-health']",
        "[data-header-health]",
        ".js-header-health",
        ".gp-header-health"
      ],
      fx: [
        "#pillFx",
        "#headerFx",
        "[data-role='header-fx']",
        "[data-header-fx]",
        ".js-header-fx",
        ".gp-header-fx",
        "#pillStatus",
        "#headerStatus",
        "[data-role='header-status']",
        "[data-header-status]",
        ".js-header-status",
        ".gp-header-status"
      ],
      asof: [
        "#pillAsOf",
        "#headerAsOf",
        "[data-role='header-asof']",
        "[data-header-asof]",
        ".js-header-asof",
        ".gp-header-asof"
      ]
    };
  }

  function hasHeaderNodes() {
    const s = getHeaderSelectors();
    return (
      s.ready.some((x) => document.querySelector(x)) ||
      s.health.some((x) => document.querySelector(x)) ||
      s.fx.some((x) => document.querySelector(x)) ||
      s.asof.some((x) => document.querySelector(x))
    );
  }

  function deriveHeaderReadyText(status) {
    const health = upper(status.health);
    return health === "NG" ? tr("gs.state.blocked") : tr("gs.state.ready");
  }

  function deriveHeaderReadyClassValue(status) {
    return upper(status.health) === "NG" ? "BLOCKED" : "READY";
  }

  function deriveHeaderFx(status) {
    const fx = upper(status.fx_regime);
    if (fx === "--") return `${tr("gs.prefix.fx")}: --`;
    return `${tr("gs.prefix.fx")}: ${fx}`;
  }

  function buildCardsForPage(pageType, status) {
    const asOf = text(status.as_of || status.updated);
    const analysisLatest = tr("gs.sub.analysis_latest");

    if (pageType === "overlay") {
      return [
        { label: tr("gs.label.date"), value: asOf, sub: analysisLatest, statusValue: "" },
        { label: tr("gs.label.fx_base"), value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: tr("gs.label.fx_signal"), value: upper(status.fx_regime), sub: text(status.fx_regime_sub, ""), statusValue: status.fx_regime },
        { label: tr("gs.label.trend"), value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: tr("gs.label.health"), value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "digest") {
      return [
        { label: tr("gs.label.date"), value: asOf, sub: analysisLatest, statusValue: "" },
        { label: tr("gs.label.articles"), value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: tr("gs.label.highlights"), value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: tr("gs.label.risk"), value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: tr("gs.label.health"), value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "sentiment") {
      return [
        { label: tr("gs.label.date"), value: asOf, sub: analysisLatest, statusValue: "" },
        { label: tr("gs.label.articles"), value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: tr("gs.label.positive"), value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: tr("gs.label.negative"), value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: tr("gs.label.health"), value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "prediction") {
      return [
        { label: tr("gs.label.date"), value: asOf, sub: analysisLatest, statusValue: "" },
        { label: tr("gs.label.regime"), value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: tr("gs.label.signal"), value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: tr("gs.label.confidence"), value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: tr("gs.label.health"), value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "history") {
      return [
        { label: tr("gs.label.date"), value: asOf, sub: analysisLatest, statusValue: "" },
        { label: tr("gs.label.snapshots"), value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: tr("gs.label.drift"), value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: tr("gs.label.review"), value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: tr("gs.label.health"), value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    return [
      { label: tr("gs.label.date"), value: asOf, sub: analysisLatest, statusValue: "" },
      { label: tr("gs.label.system"), value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
      { label: tr("gs.label.analysis"), value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
      { label: tr("gs.label.prediction"), value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
      { label: tr("gs.label.health"), value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
    ];
  }

  function createCard(card) {
    const article = document.createElement("article");
    article.className = "status-item";
    addStatusClass(article, card.statusValue);

    const labelEl = document.createElement("div");
    labelEl.className = "status-label";
    labelEl.textContent = text(card.label);

    const valueEl = document.createElement("div");
    valueEl.className = "status-value";
    valueEl.textContent = text(card.value);

    const subEl = document.createElement("div");
    subEl.className = "status-sub";
    subEl.textContent = text(card.sub, "");

    article.appendChild(labelEl);
    article.appendChild(valueEl);
    article.appendChild(subEl);

    return article;
  }

  function renderCardRoots(status) {
    const roots = Array.from(document.querySelectorAll("[data-global-status]"));

    roots.forEach((root) => {
      const pageType = text(root.dataset.page, "home").toLowerCase();
      const cards = buildCardsForPage(pageType, status);

      root.innerHTML = "";

      const grid = document.createElement("section");
      grid.className = "global-status";

      cards.forEach((card) => {
        grid.appendChild(createCard(card));
      });

      root.appendChild(grid);
    });
  }

  function renderHeader(status) {
    const selectors = getHeaderSelectors();

    const readyText = deriveHeaderReadyText(status);
    const readyClassValue = deriveHeaderReadyClassValue(status);
    const healthText = `${tr("gs.prefix.health")}: ${upper(status.health)}`;
    const fxText = deriveHeaderFx(status);
    const asOfText = `${tr("gs.prefix.as_of")}: ${text(status.as_of || status.updated)}`;

    setFirstText(selectors.ready, readyText);
    setFirstText(selectors.health, healthText);
    setFirstText(selectors.fx, fxText);
    setFirstText(selectors.asof, asOfText);

    setFirstClass(selectors.ready, readyClassValue);
    setFirstClass(selectors.health, status.health);
    setFirstClass(selectors.fx, status.fx_regime);
    setFirstClass(selectors.asof, "");
  }

  function renderLegacyFields(status) {
    setFirstText(["#globalRiskValue", "[data-role='global-risk-value']"], upper(status.global_risk));
    setFirstText(["#globalRiskSub", "[data-role='global-risk-sub']"], text(status.global_risk_sub, ""));
    setFirstText(["#sentimentBalanceValue", "[data-role='sentiment-balance-value']"], upper(status.sentiment_balance));
    setFirstText(["#sentimentBalanceSub", "[data-role='sentiment-balance-sub']"], text(status.sentiment_balance_sub, ""));
    setFirstText(["#fxRegimeValue", "[data-role='fx-regime-value']"], upper(status.fx_regime));
    setFirstText(["#fxRegimeSub", "[data-role='fx-regime-sub']"], text(status.fx_regime_sub, ""));
    setFirstText(["#healthValue", "[data-role='health-value']"], upper(status.health));
    setFirstText(["#healthSub", "[data-role='health-sub']"], text(status.health_sub, ""));
    setFirstText(["#globalStatusAsOf", "[data-role='global-status-asof']"], text(status.as_of || status.updated));
  }

  function renderAll(status) {
    renderCardRoots(status);
    renderHeader(status);
    renderLegacyFields(status);
  }

  async function fetchGlobalStatus() {
    const response = await fetch(GLOBAL_STATUS_URL + "?t=" + Date.now(), {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error("Failed to fetch global status: " + response.status);
    }

    const data = await response.json();
    if (!data || typeof data !== "object") {
      throw new Error("Invalid global status payload");
    }

    return { ...DEFAULT_STATUS, ...data };
  }

  function startHeaderRetry() {
    if (headerRetryTimer !== null) return;

    headerRetryCount = 0;

    headerRetryTimer = window.setInterval(() => {
      headerRetryCount += 1;

      if (hasHeaderNodes()) {
        renderHeader(latestStatus);
        window.clearInterval(headerRetryTimer);
        headerRetryTimer = null;
        return;
      }

      if (headerRetryCount >= 20) {
        window.clearInterval(headerRetryTimer);
        headerRetryTimer = null;
      }
    }, 250);
  }

  async function initGlobalStatus() {
    startHeaderRetry();

    if (!hasFetched) {
      hasFetched = true;
      try {
        latestStatus = await fetchGlobalStatus();
      } catch (error) {
        console.error("[global_status] fetch failed", error);
        latestStatus = { ...DEFAULT_STATUS };
      }
    }

    renderAll(latestStatus);
  }

  window.GenesisGlobalStatus = {
    init: initGlobalStatus,
    rerender: function () {
      renderAll(latestStatus);
    }
  };

  window.GPGlobalStatus = window.GenesisGlobalStatus;

  document.addEventListener("DOMContentLoaded", initGlobalStatus, { once: true });
  document.addEventListener("layout:mounted", function () {
    renderAll(latestStatus);
  });
  document.addEventListener(LANG_CHANGED_EVENT, function () {
    renderAll(latestStatus);
  });
  window.addEventListener("load", function () {
    renderAll(latestStatus);
  });
})();
