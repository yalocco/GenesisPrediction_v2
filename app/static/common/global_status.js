(function () {
  "use strict";

  const GLOBAL_STATUS_URL = "/analysis/global_status_latest.json";

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

  function deriveHeaderReady(status) {
    const health = upper(status.health);
    if (health === "NG") return "Blocked";
    return "Ready";
  }

  function deriveHeaderFx(status) {
    const fx = upper(status.fx_regime);
    if (fx === "--") return "FX: --";
    return "FX: " + fx;
  }

  function buildCardsForPage(pageType, status) {
    const asOf = text(status.as_of || status.updated);

    if (pageType === "overlay") {
      return [
        { label: "Date", value: asOf, sub: "analysis latest", statusValue: "" },
        { label: "FX Base", value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: "FX Signal", value: upper(status.fx_regime), sub: text(status.fx_regime_sub, ""), statusValue: status.fx_regime },
        { label: "Trend", value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: "Health", value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "digest") {
      return [
        { label: "Date", value: asOf, sub: "analysis latest", statusValue: "" },
        { label: "Articles", value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: "Highlights", value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: "Risk", value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: "Health", value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "sentiment") {
      return [
        { label: "Date", value: asOf, sub: "analysis latest", statusValue: "" },
        { label: "Articles", value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: "Positive", value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: "Negative", value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: "Health", value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "prediction") {
      return [
        { label: "Date", value: asOf, sub: "analysis latest", statusValue: "" },
        { label: "Regime", value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: "Signal", value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: "Confidence", value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: "Health", value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    if (pageType === "history") {
      return [
        { label: "Date", value: asOf, sub: "analysis latest", statusValue: "" },
        { label: "Snapshots", value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
        { label: "Drift", value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
        { label: "Review", value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
        { label: "Health", value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
      ];
    }

    return [
      { label: "Date", value: asOf, sub: "analysis latest", statusValue: "" },
      { label: "System", value: text(status.articles), sub: text(status.articles_sub, ""), statusValue: "" },
      { label: "Analysis", value: upper(status.sentiment_balance), sub: text(status.sentiment_balance_sub, ""), statusValue: status.sentiment_balance },
      { label: "Prediction", value: upper(status.global_risk), sub: text(status.global_risk_sub, ""), statusValue: status.global_risk },
      { label: "Health", value: upper(status.health), sub: text(status.health_sub, ""), statusValue: status.health }
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

    const readyText = deriveHeaderReady(status);
    const healthText = "Health: " + upper(status.health);
    const fxText = deriveHeaderFx(status);
    const asOfText = "as_of: " + text(status.as_of || status.updated);

    setFirstText(selectors.ready, readyText);
    setFirstText(selectors.health, healthText);
    setFirstText(selectors.fx, fxText);
    setFirstText(selectors.asof, asOfText);

    setFirstClass(selectors.ready, readyText);
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
  window.addEventListener("load", function () {
    renderAll(latestStatus);
  });
})();