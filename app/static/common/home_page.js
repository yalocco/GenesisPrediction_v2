(function () {
  "use strict";

  const i18n = window.GP_I18N || window.GenesisI18n || null;
  const manager = window.GP_LANG_MANAGER || null;
  const LANG_CHANGED_EVENT =
    (i18n && i18n.events && i18n.events.langChanged) ||
    (manager && manager.LANG_CHANGED_EVENT) ||
    "gp:lang-changed";

  const HOME_TEXT = {
    en: {
      "home.title": "Home",
      "home.subtitle": "GenesisPrediction is an analysis system that observes global events and connects trends, signals, and scenarios to forward-looking predictions. This Home screen presents the current state of the world, which serves as the starting point of the system.",
      "home.global_status_title": "Global Status",
      "home.global_risk_label": "Global Risk",
      "home.sentiment_balance_label": "Sentiment Balance",
      "home.fx_regime_label": "FX Regime",
      "home.articles_label": "Articles",
      "home.updated_label": "Updated",
      "home.kpi_events": "Events",
      "home.kpi_health_ok": "Health OK",
      "home.kpi_sentiment_items": "Sentiment Items",
      "home.kpi_summary": "Summary",
      "home.events_today_title": "Events (today)",
      "home.data_health_title": "Data Health",
      "home.sentiment_title": "Sentiment",
      "home.daily_summary_title": "Daily Summary",
      "home.open_json": "Open JSON",
      "home.loading": "loading…",
      "home.source": "source",
      "home.as_of": "as_of",
      "home.ready": "Ready",
      "home.unavailable": "No data",
      "home.summary_ready": "available",
      "home.summary_missing": "missing",
      "home.health_ok_count": "OK",
      "home.health_warn_count": "WARN",
      "home.health_ng_count": "NG",
      "home.health_total_count": "TOTAL",
      "home.events_empty": "No event highlights",
      "home.sentiment_empty": "No sentiment items",
      "home.summary_empty": "No summary text",
      "home.risk_sub_fallback": "daily summary / sentiment",
      "home.sentiment_sub_fallback": "article distribution",
      "home.fx_sub_fallback": "decision / fallback",
      "home.articles_sub_fallback": "digest latest",
      "home.updated_sub_fallback": "latest runtime stamp",
      "home.sentiment_positive": "positive",
      "home.sentiment_negative": "negative",
      "home.sentiment_neutral": "neutral",
      "home.sentiment_mixed": "mixed",
      "home.sentiment_unknown": "unknown"
    },
    ja: {
      "home.title": "ホーム",
      "home.subtitle": "GenesisPrediction は世界の出来事を観測し、トレンド・シグナル・シナリオをつないで将来予測へと統合する分析システムです。この Home 画面は世界の現在地を示す出発点です。",
      "home.global_status_title": "グローバルステータス",
      "home.global_risk_label": "グローバルリスク",
      "home.sentiment_balance_label": "センチメントバランス",
      "home.fx_regime_label": "FX レジーム",
      "home.articles_label": "記事数",
      "home.updated_label": "更新",
      "home.kpi_events": "イベント",
      "home.kpi_health_ok": "Health OK",
      "home.kpi_sentiment_items": "センチメント件数",
      "home.kpi_summary": "サマリー",
      "home.events_today_title": "Events (today)",
      "home.data_health_title": "データ健全性",
      "home.sentiment_title": "センチメント",
      "home.daily_summary_title": "デイリーサマリー",
      "home.open_json": "JSON を開く",
      "home.loading": "読み込み中…",
      "home.source": "source",
      "home.as_of": "as_of",
      "home.ready": "準備完了",
      "home.unavailable": "データなし",
      "home.summary_ready": "あり",
      "home.summary_missing": "なし",
      "home.health_ok_count": "OK",
      "home.health_warn_count": "WARN",
      "home.health_ng_count": "NG",
      "home.health_total_count": "TOTAL",
      "home.events_empty": "イベントハイライトなし",
      "home.sentiment_empty": "センチメント項目なし",
      "home.summary_empty": "サマリーテキストなし",
      "home.risk_sub_fallback": "daily summary / sentiment",
      "home.sentiment_sub_fallback": "article distribution",
      "home.fx_sub_fallback": "decision / fallback",
      "home.articles_sub_fallback": "digest latest",
      "home.updated_sub_fallback": "latest runtime stamp",
      "home.sentiment_positive": "positive",
      "home.sentiment_negative": "negative",
      "home.sentiment_neutral": "neutral",
      "home.sentiment_mixed": "mixed",
      "home.sentiment_unknown": "unknown"
    },
    th: {
      "home.title": "Home",
      "home.subtitle": "GenesisPrediction เป็นระบบวิเคราะห์ที่สังเกตเหตุการณ์ทั่วโลกและเชื่อมโยงแนวโน้ม สัญญาณ และฉากทัศน์ไปสู่การคาดการณ์ล่วงหน้า หน้าจอ Home นี้แสดงสถานะปัจจุบันของโลกซึ่งเป็นจุดเริ่มต้นของระบบ",
      "home.global_status_title": "สถานะรวม",
      "home.global_risk_label": "ความเสี่ยงโลก",
      "home.sentiment_balance_label": "สมดุลเซนติเมนต์",
      "home.fx_regime_label": "ระบอบ FX",
      "home.articles_label": "จำนวนบทความ",
      "home.updated_label": "อัปเดต",
      "home.kpi_events": "เหตุการณ์",
      "home.kpi_health_ok": "Health OK",
      "home.kpi_sentiment_items": "รายการเซนติเมนต์",
      "home.kpi_summary": "สรุป",
      "home.events_today_title": "Events (today)",
      "home.data_health_title": "สุขภาพข้อมูล",
      "home.sentiment_title": "เซนติเมนต์",
      "home.daily_summary_title": "สรุปรายวัน",
      "home.open_json": "เปิด JSON",
      "home.loading": "กำลังโหลด…",
      "home.source": "source",
      "home.as_of": "as_of",
      "home.ready": "พร้อม",
      "home.unavailable": "ไม่มีข้อมูล",
      "home.summary_ready": "มี",
      "home.summary_missing": "ไม่มี",
      "home.health_ok_count": "OK",
      "home.health_warn_count": "WARN",
      "home.health_ng_count": "NG",
      "home.health_total_count": "TOTAL",
      "home.events_empty": "ไม่มีไฮไลต์เหตุการณ์",
      "home.sentiment_empty": "ไม่มีรายการเซนติเมนต์",
      "home.summary_empty": "ไม่มีข้อความสรุป",
      "home.risk_sub_fallback": "daily summary / sentiment",
      "home.sentiment_sub_fallback": "article distribution",
      "home.fx_sub_fallback": "decision / fallback",
      "home.articles_sub_fallback": "digest latest",
      "home.updated_sub_fallback": "latest runtime stamp",
      "home.sentiment_positive": "positive",
      "home.sentiment_negative": "negative",
      "home.sentiment_neutral": "neutral",
      "home.sentiment_mixed": "mixed",
      "home.sentiment_unknown": "unknown"
    }
  };

  const state = {
    globalStatus: null,
    digestViewModel: null,
    health: null,
    sentiment: null,
    summary: null
  };

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
      return i18n.translate(HOME_TEXT, key, getLang());
    }
    const lang = getLang();
    return (HOME_TEXT[lang] && HOME_TEXT[lang][key]) || HOME_TEXT.en[key] || key;
  }

  function pickI18n(value, fallback = "") {
    if (i18n && typeof i18n.pickI18n === "function") {
      return i18n.pickI18n(value, fallback, getLang());
    }
    return fallback;
  }

  function pickI18nList(value) {
    if (i18n && typeof i18n.pickI18nList === "function") {
      return i18n.pickI18nList(value, getLang());
    }
    return [];
  }

  function safeString(value, fallback = "") {
    if (value === null || value === undefined) {
      return fallback;
    }
    const text = String(value).trim();
    return text || fallback;
  }

  function safeArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function safeObject(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : null;
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = safeString(value, "—");
    }
  }

  function setBodyText(id, value) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = safeString(value, tr("home.unavailable"));
    }
  }

  function setHref(id, href) {
    const node = document.getElementById(id);
    if (node) {
      node.href = href || "#";
    }
  }

  function setSource(id, source) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = `${tr("home.source")}: ${safeString(source, "--")}`;
    }
  }

  function setHint(id, ready) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = ready ? tr("home.ready") : tr("home.loading");
    }
  }

  function applyStaticText() {
    if (i18n && typeof i18n.applyStaticUiText === "function") {
      i18n.applyStaticUiText(document, HOME_TEXT, { attribute: "data-ui-text", lang: getLang() });
      return;
    }

    document.querySelectorAll("[data-ui-text]").forEach((node) => {
      const key = node.getAttribute("data-ui-text");
      if (key) {
        node.textContent = tr(key);
      }
    });
  }

  function fetchJsonCandidates(urls) {
    const list = safeArray(urls).filter(Boolean);

    return list.reduce((promise, url) => {
      return promise.catch(async () => {
        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const json = await response.json();
        return { url, json };
      });
    }, Promise.reject(new Error("no-candidate")));
  }

  function extractDigestCards(viewModel) {
    const root = safeObject(viewModel);
    if (!root) {
      return [];
    }

    const sections = safeArray(root.sections);
    const collected = [];

    sections.forEach((section) => {
      safeArray(section && section.cards).forEach((card) => {
        collected.push(card);
      });
    });

    if (collected.length > 0) {
      return collected;
    }

    return safeArray(root.cards);
  }

  function firstNonEmptyText(values, fallback = "") {
    for (const value of safeArray(values)) {
      const text = safeString(value, "");
      if (text) {
        return text;
      }
    }
    return fallback;
  }

  function getSummaryText() {
    const vm = safeObject(state.digestViewModel) || {};
    const summary = safeObject(state.summary) || {};

    return firstNonEmptyText([
      pickI18n(vm.summary_i18n, ""),
      safeString(vm.summary, ""),
      pickI18n(summary.summary_i18n, ""),
      safeString(summary.summary, ""),
      safeString(summary.text, ""),
      safeString(summary.text_summary, ""),
      safeString(summary.daily_summary, ""),
      safeString(summary.yesterday_summary_text, ""),
      safeString(summary.yesterday_summary, "")
    ], "");
  }

  function getEventTitles(limit = 5) {
    const cards = extractDigestCards(state.digestViewModel);
    return cards
      .slice(0, limit)
      .map((card) => {
        return firstNonEmptyText([
          pickI18n(card && card.title_i18n, ""),
          safeString(card && card.title, ""),
          safeString(card && card.headline, "")
        ], "");
      })
      .filter(Boolean);
  }

  function getSentimentLines() {
    const sentiment = safeObject(state.sentiment) || {};
    const summary = safeObject(sentiment.summary) || {};
    const lines = [];
    const countLine = [
      ["positive", summary.positive],
      ["negative", summary.negative],
      ["neutral", summary.neutral],
      ["mixed", summary.mixed],
      ["unknown", summary.unknown]
    ]
      .filter(([, value]) => typeof value === "number")
      .map(([key, value]) => `${tr(`home.sentiment_${key}`)}=${value}`)
      .join(" / ");

    if (countLine) {
      lines.push(countLine);
    }

    const cards = extractDigestCards(state.digestViewModel);
    const cardLines = cards.slice(0, 5).map((card) => {
      return firstNonEmptyText([
        pickI18n(card && card.title_i18n, ""),
        safeString(card && card.title, "")
      ], "");
    }).filter(Boolean);

    if (cardLines.length > 0) {
      lines.push(...cardLines);
      return lines;
    }

    const items = safeArray(sentiment.items);
    items.slice(0, 5).forEach((item) => {
      const row = safeObject(item) || {};
      const label = safeString(row.sentiment, "unknown").toLowerCase();
      const title = firstNonEmptyText([
        pickI18n(row.title_i18n, ""),
        safeString(row.title, "")
      ], "");
      if (title) {
        lines.push(`${tr(`home.sentiment_${label}`)}: ${title}`);
      }
    });

    return lines;
  }

  function renderGlobalStatus() {
    const gs = safeObject(state.globalStatus) || {};

    setText("gsRisk", safeString(gs.global_risk, "—"));
    setText("gsSentiment", safeString(gs.sentiment_balance, "—"));
    setText("gsFx", safeString(gs.fx_regime, "—"));
    setText("gsArticles", safeString(gs.articles, "—"));
    setText("gsUpdated", safeString(gs.updated, "—"));

    setText("gsRiskSub", safeString(gs.global_risk_sub, tr("home.risk_sub_fallback")));
    setText("gsSentimentSub", safeString(gs.sentiment_balance_sub, tr("home.sentiment_sub_fallback")));
    setText("gsFxSub", safeString(gs.fx_regime_sub, tr("home.fx_sub_fallback")));
    setText("gsArticlesSub", safeString(gs.articles_sub, tr("home.articles_sub_fallback")));
    setText("gsUpdatedSub", tr("home.updated_sub_fallback"));

    const asOf = safeString(gs.as_of || gs.updated, "--");
    const ready = safeString(gs.health, "").toUpperCase() === "NG" ? safeString(gs.health, "--") : tr("home.ready");

    setText("pillAsOfLocal", `${tr("home.as_of")}: ${asOf}`);
    setText("pillReadyLocal", ready);
  }

  function renderKpis() {
    const digestCards = extractDigestCards(state.digestViewModel);
    const healthSummary = safeObject(state.health && state.health.summary) || safeObject(state.health) || {};
    const sentimentSummary = safeObject(state.sentiment && state.sentiment.summary) || {};
    const summaryText = getSummaryText();

    setText("kpiEvents", digestCards.length > 0 ? String(digestCards.length) : "—");
    setText("kpiHealthOk", healthSummary.ok != null ? String(healthSummary.ok) : "—");
    setText("kpiSentimentItems", sentimentSummary.mixed != null || sentimentSummary.positive != null || sentimentSummary.negative != null || sentimentSummary.neutral != null || sentimentSummary.unknown != null
      ? String(safeArray(state.sentiment && state.sentiment.items).length || 0)
      : "—");
    setText("kpiSummaryState", summaryText ? tr("home.summary_ready") : tr("home.summary_missing"));
  }

  function renderEvents() {
    const lines = getEventTitles(5);
    setHint("evHint", lines.length > 0);
    setBodyText("evBody", lines.length > 0 ? lines.join("\n") : tr("home.events_empty"));
    setSource("evSource", state.digestViewModel ? "data/digest/view_model_latest.json" : "--");
  }

  function renderHealth() {
    const healthSummary = safeObject(state.health && state.health.summary) || safeObject(state.health) || {};
    const lines = [];

    if (healthSummary.ok != null) {
      lines.push(`${tr("home.health_ok_count")}: ${healthSummary.ok}`);
    }
    if (healthSummary.warn != null) {
      lines.push(`${tr("home.health_warn_count")}: ${healthSummary.warn}`);
    }
    if (healthSummary.ng != null) {
      lines.push(`${tr("home.health_ng_count")}: ${healthSummary.ng}`);
    }
    if (healthSummary.total != null) {
      lines.push(`${tr("home.health_total_count")}: ${healthSummary.total}`);
    }

    setHint("healthHint", lines.length > 0);
    setBodyText("healthBody", lines.length > 0 ? lines.join("\n") : tr("home.unavailable"));
    setSource("healthSource", state.health ? "health_latest.json" : "--");
  }

  function renderSentiment() {
    const lines = getSentimentLines();
    setHint("senHint", lines.length > 0);
    setBodyText("senBody", lines.length > 0 ? lines.join("\n") : tr("home.sentiment_empty"));
    setSource("senSource", state.sentiment ? "data/world_politics/analysis/sentiment_latest.json" : "--");
  }

  function renderSummary() {
    const summaryText = getSummaryText();
    setHint("sumHint", Boolean(summaryText));
    setBodyText("sumBody", summaryText || tr("home.summary_empty"));
    setSource("sumSource", state.summary || state.digestViewModel ? "data/world_politics/analysis/daily_summary_latest.json" : "--");
  }

  function renderAnchors() {
    setHref("btnOpenHealth", state.health ? "/analysis/health_latest.json" : "#");
    setHref("btnOpenSummary", state.summary ? "/data/world_politics/analysis/daily_summary_latest.json" : "#");
  }

  function renderAll() {
    applyStaticText();
    renderGlobalStatus();
    renderKpis();
    renderEvents();
    renderHealth();
    renderSentiment();
    renderSummary();
    renderAnchors();
  }

  async function loadAll() {
    const jobs = [
      fetchJsonCandidates([
        "/analysis/global_status_latest.json"
      ]).then(({ json }) => {
        state.globalStatus = json;
      }).catch(() => {
        state.globalStatus = null;
      }),
      fetchJsonCandidates([
        "/data/digest/view_model_latest.json"
      ]).then(({ json }) => {
        state.digestViewModel = json;
      }).catch(() => {
        state.digestViewModel = null;
      }),
      fetchJsonCandidates([
        "/analysis/health_latest.json",
        "/data/digest/health_latest.json",
        "/data/world_politics/analysis/health_latest.json"
      ]).then(({ json }) => {
        state.health = json;
      }).catch(() => {
        state.health = null;
      }),
      fetchJsonCandidates([
        "/data/world_politics/analysis/sentiment_latest.json",
        "/analysis/sentiment_latest.json"
      ]).then(({ json }) => {
        state.sentiment = json;
      }).catch(() => {
        state.sentiment = null;
      }),
      fetchJsonCandidates([
        "/data/world_politics/analysis/daily_summary_latest.json",
        "/analysis/daily_summary_latest.json"
      ]).then(({ json }) => {
        state.summary = json;
      }).catch(() => {
        state.summary = null;
      })
    ];

    await Promise.all(jobs);
    renderAll();
  }

  document.addEventListener(LANG_CHANGED_EVENT, () => {
    renderAll();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      renderAll();
      loadAll();
    }, { once: true });
  } else {
    renderAll();
    loadAll();
  }
})();