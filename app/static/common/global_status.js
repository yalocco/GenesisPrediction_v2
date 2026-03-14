(() => {
  "use strict";

  const JSON_FETCH_OPTIONS = {
    cache: "no-store",
    headers: {
      "Cache-Control": "no-cache",
      Pragma: "no-cache",
    },
  };

  const GLOBAL_STATUS_PATH = "/data/world_politics/analysis/view_model_latest.json";

  function textValue(value, fallback = "--") {
    if (value === null || value === undefined) return fallback;
    const text = String(value).trim();
    return text ? text : fallback;
  }

  function formatPill(label, value) {
    return `${label}: ${textValue(value)}`;
  }

  function setTextContent(selectors, value) {
    if (value === undefined || value === null) return false;
    let touched = false;

    selectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach((node) => {
        node.textContent = String(value);
        touched = true;
      });
    });

    return touched;
  }

  function setButtonLikeText(prefixes, value) {
    const nodes = Array.from(
      document.querySelectorAll(
        ".pill, .meta-pill, .status-pill, .chip, .badge, button, .nav-pill, .site-pill"
      )
    );

    nodes.forEach((node) => {
      const text = String(node.textContent || "").trim().toLowerCase();
      const matched = prefixes.some((prefix) =>
        text.startsWith(String(prefix).toLowerCase())
      );
      if (matched) {
        node.textContent = value;
      }
    });
  }

  function findStatusCardByLabel(labelText) {
    const normalizedTarget = String(labelText || "").trim().toLowerCase();
    const candidates = Array.from(
      document.querySelectorAll(".status-item, .metric-card, .card, .kpi-card")
    );

    return candidates.find((card) => {
      const labelNode =
        card.querySelector(".status-label, .metric-label, .card-label, .label") ||
        Array.from(card.querySelectorAll("*")).find((el) => {
          const text = String(el.textContent || "").trim().toLowerCase();
          return text === normalizedTarget;
        });

      if (!labelNode) return false;
      const text = String(labelNode.textContent || "").trim().toLowerCase();
      return text === normalizedTarget;
    });
  }

  function setStatusCard(labelText, value, sub) {
    const card = findStatusCardByLabel(labelText);
    if (!card) return;

    const valueNode =
      card.querySelector(".status-value, .metric-value, .value") ||
      Array.from(card.children).find((el) => {
        const cls = String(el.className || "");
        return /value/i.test(cls);
      });

    const subNode =
      card.querySelector(".status-sub, .metric-sub, .sub") ||
      Array.from(card.children).find((el) => {
        const cls = String(el.className || "");
        return /sub/i.test(cls);
      });

    if (valueNode) valueNode.textContent = String(value);
    if (subNode) subNode.textContent = String(sub);
  }

  function normalizeRiskClassName(value) {
    const text = String(value || "").trim().toLowerCase();

    if (text === "low") return "risk-low";
    if (text === "guarded") return "risk-guarded";
    if (text === "elevated") return "risk-elevated";
    if (text === "high") return "risk-high";
    if (text === "critical") return "risk-critical";

    return "";
  }

  function applyRiskClass(rawRiskValue) {
    const className = normalizeRiskClassName(rawRiskValue);

    const nodes = document.querySelectorAll(
      "[data-risk-target], .risk-pill, .global-risk-pill, .status-item, .metric-card"
    );

    nodes.forEach((node) => {
      node.classList.remove(
        "risk-low",
        "risk-guarded",
        "risk-elevated",
        "risk-high",
        "risk-critical"
      );

      if (className) {
        node.classList.add(className);
      }
    });

    document.documentElement.dataset.globalRisk = className.replace(/^risk-/, "");
  }

  async function fetchGlobalStatus() {
    const response = await fetch(GLOBAL_STATUS_PATH, JSON_FETCH_OPTIONS);
    if (!response.ok) {
      throw new Error(`global status fetch failed: ${response.status}`);
    }

    const data = await response.json();
    if (!data || typeof data !== "object") {
      throw new Error("global status payload is not an object");
    }

    return data;
  }

  function buildDisplaySnapshot(payload) {
    return {
      riskValue: textValue(payload.global_risk).toUpperCase(),
      riskSub: textValue(payload.global_risk_sub),

      sentimentValue: textValue(payload.sentiment_balance),
      sentimentSub: textValue(payload.sentiment_balance_sub),

      fxValue: textValue(payload.fx_regime),
      fxSub: textValue(payload.fx_regime_sub),

      articlesValue: textValue(payload.articles),
      articlesSub: textValue(payload.articles_sub),

      updatedValue: textValue(payload.updated ?? payload.as_of),
      updatedSub: textValue(payload.updated_sub ?? payload.sources?.summary ?? "analysis latest"),

      healthValue: textValue(payload.health),
      healthSub: textValue(payload.health_sub),

      asOfValue: textValue(payload.as_of),
    };
  }

  function applyStatusSnapshot(snapshot) {
    setStatusCard("GLOBAL RISK", snapshot.riskValue, snapshot.riskSub);
    setStatusCard("SENTIMENT BALANCE", snapshot.sentimentValue, snapshot.sentimentSub);
    setStatusCard("FX REGIME", snapshot.fxValue, snapshot.fxSub);
    setStatusCard("ARTICLES", snapshot.articlesValue, snapshot.articlesSub);
    setStatusCard("UPDATED", snapshot.updatedValue, snapshot.updatedSub);

    setTextContent(
      [
        "#global-risk-value",
        "#home-global-risk-value",
        "#status-global-risk-value",
        "[data-bind='global-risk-value']",
      ],
      snapshot.riskValue
    );
    setTextContent(
      [
        "#global-risk-sub",
        "#home-global-risk-sub",
        "#status-global-risk-sub",
        "[data-bind='global-risk-sub']",
      ],
      snapshot.riskSub
    );

    setTextContent(
      [
        "#sentiment-balance-value",
        "#home-sentiment-balance-value",
        "[data-bind='sentiment-balance-value']",
      ],
      snapshot.sentimentValue
    );
    setTextContent(
      [
        "#sentiment-balance-sub",
        "#home-sentiment-balance-sub",
        "[data-bind='sentiment-balance-sub']",
      ],
      snapshot.sentimentSub
    );

    setTextContent(
      [
        "#fx-regime-value",
        "#home-fx-regime-value",
        "[data-bind='fx-regime-value']",
      ],
      snapshot.fxValue
    );
    setTextContent(
      [
        "#fx-regime-sub",
        "#home-fx-regime-sub",
        "[data-bind='fx-regime-sub']",
      ],
      snapshot.fxSub
    );

    setTextContent(
      [
        "#articles-value",
        "#home-articles-value",
        "[data-bind='articles-value']",
      ],
      snapshot.articlesValue
    );
    setTextContent(
      [
        "#articles-sub",
        "#home-articles-sub",
        "[data-bind='articles-sub']",
      ],
      snapshot.articlesSub
    );

    setTextContent(
      [
        "#updated-value",
        "#home-updated-value",
        "[data-bind='updated-value']",
      ],
      snapshot.updatedValue
    );
    setTextContent(
      [
        "#updated-sub",
        "#home-updated-sub",
        "[data-bind='updated-sub']",
      ],
      snapshot.updatedSub
    );

    setTextContent(
      [
        "#global-status-as-of",
        "#header-as-of",
        "[data-bind='global-status-as-of']",
      ],
      formatPill("as_of", snapshot.asOfValue)
    );

    setTextContent(
      [
        "#global-status-health",
        "#header-health",
        "[data-bind='global-status-health']",
      ],
      formatPill("Health", snapshot.healthValue)
    );

    setButtonLikeText(["as_of:", "as_of"], formatPill("as_of", snapshot.asOfValue));
    setButtonLikeText(["health:", "health"], formatPill("Health", snapshot.healthValue));

    applyRiskClass(snapshot.riskValue);

    document.documentElement.dataset.globalHealth = snapshot.healthValue.toLowerCase();
    document.documentElement.dataset.globalReady = "ready";
    document.documentElement.dataset.globalStatusPath = GLOBAL_STATUS_PATH;
  }

  function applyLoadError(error) {
    const message = error instanceof Error ? error.message : String(error || "load error");

    setTextContent(
      [
        "#updated-sub",
        "#home-updated-sub",
        "[data-bind='updated-sub']",
      ],
      message
    );

    document.documentElement.dataset.globalReady = "error";
    document.documentElement.dataset.globalStatusPath = GLOBAL_STATUS_PATH;
  }

  async function refreshGlobalStatus() {
    const payload = await fetchGlobalStatus();
    const snapshot = buildDisplaySnapshot(payload);
    applyStatusSnapshot(snapshot);
    return { payload, snapshot };
  }

  window.GenesisGlobalStatus = {
    refresh: refreshGlobalStatus,
    path: GLOBAL_STATUS_PATH,
  };

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      () => {
        refreshGlobalStatus().catch(applyLoadError);
      },
      { once: true }
    );
  } else {
    refreshGlobalStatus().catch(applyLoadError);
  }
})();