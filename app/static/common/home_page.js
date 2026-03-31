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
      "home.ready": "Ready",
      "home.unavailable": "No data",
      "home.source": "source",
      "home.as_of": "as_of",
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
      "home.events_today_title": "今日のイベント",
      "home.data_health_title": "データ健全性",
      "home.sentiment_title": "センチメント",
      "home.daily_summary_title": "デイリーサマリー",
      "home.open_json": "JSON を開く",
      "home.loading": "読み込み中…",
      "home.ready": "準備完了",
      "home.unavailable": "データなし",
      "home.source": "ソース",
      "home.as_of": "as_of",
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
      "home.sentiment_positive": "ポジティブ",
      "home.sentiment_negative": "ネガティブ",
      "home.sentiment_neutral": "ニュートラル",
      "home.sentiment_mixed": "混在",
      "home.sentiment_unknown": "不明"
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
      "home.events_today_title": "เหตุการณ์วันนี้",
      "home.data_health_title": "สุขภาพข้อมูล",
      "home.sentiment_title": "เซนติเมนต์",
      "home.daily_summary_title": "สรุปรายวัน",
      "home.open_json": "เปิด JSON",
      "home.loading": "กำลังโหลด…",
      "home.ready": "พร้อม",
      "home.unavailable": "ไม่มีข้อมูล",
      "home.source": "แหล่งที่มา",
      "home.as_of": "as_of",
      "home.summary_ready": "มี",
      "home.summary_missing": "ไม่มี",
      "home.health_ok_count": "OK",
      "home.health_warn_count": "WARN",
      "home.health_ng_count": "NG",
      "home.health_total_count": "TOTAL",
      "home.events_empty": "ไม่มีไฮไลต์เหตุการณ์",
      "home.sentiment_empty": "ไม่มีรายการเซนติเมนต์",
      "home.summary_empty": "ไม่มีข้อความสรุป",
      "home.risk_sub_fallback": "สรุปรายวัน / เซนติเมนต์",
      "home.sentiment_sub_fallback": "การกระจายบทความ",
      "home.fx_sub_fallback": "การตัดสินใจ / fallback",
      "home.articles_sub_fallback": "digest latest",
      "home.updated_sub_fallback": "เวลารันล่าสุด",
      "home.sentiment_positive": "เชิงบวก",
      "home.sentiment_negative": "เชิงลบ",
      "home.sentiment_neutral": "เป็นกลาง",
      "home.sentiment_mixed": "ผสม",
      "home.sentiment_unknown": "ไม่ทราบ"
    }
  };

  const PATHS = {
    globalStatus: ["/analysis/global_status_latest.json"],
    digestViewModel: ["/data/digest/view_model_latest.json"],
    health: [
      "/data/digest/health_latest.json",
      "/analysis/health_latest.json",
      "/data/world_politics/analysis/health_latest.json"
    ],
    sentiment: [
      "/data/world_politics/analysis/sentiment_latest.json",
      "/analysis/sentiment_latest.json"
    ],
    summary: [
      "/data/world_politics/analysis/daily_summary_latest.json",
      "/analysis/daily_summary_latest.json"
    ]
  };

  const state = {
    globalStatus: null,
    digestViewModel: null,
    health: null,
    sentiment: null,
    summary: null,
    loaded: false
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

  function firstNonEmptyText(values, fallback = "") {
    for (const value of safeArray(values)) {
      const text = safeString(value, "");
      if (text) {
        return text;
      }
    }
    return fallback;
  }

  function pickI18n(value, fallback = "") {
    if (value === null || value === undefined) {
      return fallback;
    }

    if (typeof value === "string") {
      return safeString(value, fallback);
    }

    if (i18n && typeof i18n.pickI18n === "function") {
      const picked = i18n.pickI18n(value, "", getLang());
      if (safeString(picked, "")) {
        return safeString(picked, fallback);
      }
    }

    if (typeof value === "object" && !Array.isArray(value)) {
      const lang = getLang();
      return firstNonEmptyText(
        [value[lang], value.en, value.ja, value.th],
        fallback
      );
    }

    return fallback;
  }

  function pickI18nList(value) {
    if (!Array.isArray(value)) {
      return [];
    }

    return value
      .map((item) => {
        if (typeof item === "string") {
          return safeString(item, "");
        }
        return pickI18n(item, "");
      })
      .filter(Boolean);
  }

  function setText(id, value, fallback = "—") {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = safeString(value, fallback);
    }
  }

  function setBodyText(id, value, fallbackKey = "home.unavailable") {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = safeString(value, tr(fallbackKey));
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

  function setHint(id, mode) {
    const node = document.getElementById(id);
    if (!node) return;

    if (mode === "loading") {
      node.textContent = tr("home.loading");
      return;
    }

    if (mode === "ready") {
      node.textContent = tr("home.ready");
      return;
    }

    node.textContent = tr("home.unavailable");
  }

  function applyStaticText() {
    if (i18n && typeof i18n.applyStaticUiText === "function") {
      i18n.applyStaticUiText(document, HOME_TEXT, {
        attribute: "data-ui-text",
        lang: getLang()
      });
      return;
    }

    document.querySelectorAll("[data-ui-text]").forEach((node) => {
      const key = node.getAttribute("data-ui-text");
      if (key) {
        node.textContent = tr(key);
      }
    });
  }

  async function fetchJsonCandidates(urls) {
    const candidates = safeArray(urls).filter(Boolean);

    for (const url of candidates) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok) {
          continue;
        }
        const json = await response.json();
        return { url, json };
      } catch (_error) {
        // continue
      }
    }

    throw new Error("no-candidate");
  }

  function extractDigestCards(viewModel) {
    const root = safeObject(viewModel);
    if (!root) {
      return [];
    }

    const sections = safeArray(root.sections);
    const fromSections = [];

    sections.forEach((section) => {
      safeArray(section && section.cards).forEach((card) => {
        fromSections.push(card);
      });
    });

    if (fromSections.length > 0) {
      return fromSections;
    }

    return safeArray(root.cards);
  }

  function getDigestArticlesCount() {
    const vm = safeObject(state.digestViewModel) || {};
    const meta = safeObject(vm.meta) || {};
    const cards = extractDigestCards(vm);

    return firstNonEmptyText(
      [
        meta.n_events,
        meta.digest_card_count,
        safeArray(vm.highlights).length || "",
        cards.length || "",
        safeArray(vm.cards).length || ""
      ],
      ""
    );
  }

  function getGlobalRisk() {
    const gs = safeObject(state.globalStatus) || {};
    const summary = safeObject(state.summary) || {};
    const sentiment = safeObject(state.sentiment) || {};
    const today = safeObject(sentiment.today) || {};

    return firstNonEmptyText(
      [
        gs.global_risk,
        summary.uncertainty,
        today.sentiment_label,
        today.sentiment
      ],
      "—"
    );
  }

  function getSentimentBalance() {
    const gs = safeObject(state.globalStatus) || {};
    const sentiment = safeObject(state.sentiment) || {};
    const today = safeObject(sentiment.today) || {};

    return firstNonEmptyText(
      [
        gs.sentiment_balance,
        pickI18n(today.sentiment_label_i18n, ""),
        pickI18n(today.sentiment_i18n, ""),
        today.sentiment_label,
        today.sentiment
      ],
      "—"
    );
  }

  function getFxRegime() {
    const gs = safeObject(state.globalStatus) || {};
    return firstNonEmptyText([gs.fx_regime], "—");
  }

  function getUpdatedStamp() {
    const gs = safeObject(state.globalStatus) || {};
    const vm = safeObject(state.digestViewModel) || {};
    const health = safeObject(state.health) || {};
    const sentiment = safeObject(state.sentiment) || {};
    const summary = safeObject(state.summary) || {};

    return firstNonEmptyText(
      [
        gs.updated,
        vm.generated_at,
        health.generated_at,
        sentiment.generated_at,
        summary.generated_at,
        vm.date,
        summary.date
      ],
      "—"
    );
  }

  function getAsOfStamp() {
    const gs = safeObject(state.globalStatus) || {};
    const vm = safeObject(state.digestViewModel) || {};
    const summary = safeObject(state.summary) || {};
    const sentiment = safeObject(state.sentiment) || {};

    return firstNonEmptyText(
      [
        gs.as_of,
        vm.date,
        summary.date,
        sentiment.date,
        gs.updated
      ],
      "--"
    );
  }

  function getSummaryText() {
    const vm = safeObject(state.digestViewModel) || {};
    const summary = safeObject(state.summary) || {};

    const bulletText = safeArray(summary.bullets)
      .map((item) => `• ${safeString(item, "")}`)
      .filter(Boolean)
      .join("\n");

    const watchText = safeArray(summary.watch)
      .map((item) => `- ${safeString(item, "")}`)
      .filter(Boolean)
      .join("\n");

    const highlights = safeArray(vm.highlights)
      .map((item) => safeString(item, ""))
      .filter(Boolean)
      .join("\n");

    const highlightsI18n = pickI18nList(vm.highlights_i18n).join("\n");

    return firstNonEmptyText(
      [
        pickI18n(vm.summary_i18n, ""),
        safeString(vm.summary, ""),
        safeString(summary.summary, ""),
        safeString(summary.text, ""),
        safeString(summary.headline, ""),
        bulletText,
        watchText,
        highlightsI18n,
        highlights
      ],
      ""
    );
  }

  function getEventLines(limit = 5) {
    const vm = safeObject(state.digestViewModel) || {};
    const cards = extractDigestCards(vm);

    const cardLines = cards
      .slice(0, limit)
      .map((card) => {
        return firstNonEmptyText(
          [
            pickI18n(card && card.title_i18n, ""),
            safeString(card && card.title, ""),
            pickI18n(card && card.summary_i18n, ""),
            safeString(card && card.summary, "")
          ],
          ""
        );
      })
      .filter(Boolean);

    if (cardLines.length > 0) {
      return cardLines;
    }

    const rawHighlights = safeArray(vm.highlights)
      .slice(0, limit)
      .map((item) => safeString(item, ""))
      .filter(Boolean);

    if (rawHighlights.length > 0) {
      return rawHighlights;
    }

    return pickI18nList(vm.highlights_i18n).slice(0, limit).filter(Boolean);
  }

  function getSentimentLines() {
    const sentiment = safeObject(state.sentiment) || {};
    const summary = safeObject(sentiment.summary) || {};
    const today = safeObject(sentiment.today) || {};
    const items = safeArray(sentiment.items);
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

    const todayLine = firstNonEmptyText(
      [
        pickI18n(today.sentiment_label_i18n, ""),
        pickI18n(today.sentiment_i18n, ""),
        today.sentiment_label,
        today.sentiment
      ],
      ""
    );

    if (todayLine) {
      lines.push(todayLine);
    }

    const itemLines = items
      .slice(0, 4)
      .map((item) => {
        return firstNonEmptyText(
          [
            pickI18n(item && item.title_i18n, ""),
            safeString(item && item.title, ""),
            pickI18n(item && item.summary_i18n, ""),
            safeString(item && item.summary, "")
          ],
          ""
        );
      })
      .filter(Boolean);

    if (itemLines.length > 0) {
      lines.push(...itemLines);
    }

    return lines;
  }

  function renderGlobalStatus() {
    const gs = safeObject(state.globalStatus) || {};

    setText("gsRisk", getGlobalRisk());
    setText("gsSentiment", getSentimentBalance());
    setText("gsFx", getFxRegime());
    setText("gsArticles", getDigestArticlesCount() || safeString(gs.articles, "—"));
    setText("gsUpdated", getUpdatedStamp());

    setText("gsRiskSub", safeString(gs.global_risk_sub, tr("home.risk_sub_fallback")), tr("home.risk_sub_fallback"));
    setText("gsSentimentSub", safeString(gs.sentiment_balance_sub, tr("home.sentiment_sub_fallback")), tr("home.sentiment_sub_fallback"));
    setText("gsFxSub", safeString(gs.fx_regime_sub, tr("home.fx_sub_fallback")), tr("home.fx_sub_fallback"));
    setText("gsArticlesSub", safeString(gs.articles_sub, tr("home.articles_sub_fallback")), tr("home.articles_sub_fallback"));
    setText("gsUpdatedSub", safeString(gs.health_sub, tr("home.updated_sub_fallback")), tr("home.updated_sub_fallback"));

    setText("pillAsOfLocal", `${tr("home.as_of")}: ${getAsOfStamp()}`, `${tr("home.as_of")}: --`);
    setText("pillReadyLocal", state.loaded ? tr("home.ready") : tr("home.loading"), tr("home.loading"));
  }

  function renderKpis() {
    const healthSummary = safeObject(state.health && state.health.summary) || safeObject(state.health) || {};
    const sentimentItems = safeArray(state.sentiment && state.sentiment.items);
    const summaryText = getSummaryText();
    const eventLines = getEventLines(5);

    setText("kpiEvents", eventLines.length > 0 ? String(eventLines.length) : "—");
    setText("kpiHealthOk", healthSummary.ok != null ? String(healthSummary.ok) : "—");
    setText("kpiSentimentItems", sentimentItems.length > 0 ? String(sentimentItems.length) : "—");
    setText("kpiSummaryState", summaryText ? tr("home.summary_ready") : tr("home.summary_missing"));
  }

  function renderEvents() {
    const lines = getEventLines(5);

    if (!state.loaded) {
      setHint("evHint", "loading");
      setBodyText("evBody", tr("home.loading"), "home.loading");
      setSource("evSource", "--");
      return;
    }

    setHint("evHint", lines.length > 0 ? "ready" : "empty");
    setBodyText("evBody", lines.length > 0 ? lines.join("\n") : tr("home.events_empty"), "home.events_empty");
    setSource("evSource", state.digestViewModel ? "data/digest/view_model_latest.json" : "--");
  }

  function renderHealth() {
    const healthSummary = safeObject(state.health && state.health.summary) || safeObject(state.health) || {};
    const lines = [];

    if (!state.loaded) {
      setHint("healthHint", "loading");
      setBodyText("healthBody", tr("home.loading"), "home.loading");
      setSource("healthSource", "--");
      return;
    }

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

    setHint("healthHint", lines.length > 0 ? "ready" : "empty");
    setBodyText("healthBody", lines.length > 0 ? lines.join("\n") : tr("home.unavailable"));
    setSource("healthSource", state.health ? "data/digest/health_latest.json" : "--");
  }

  function renderSentiment() {
    const lines = getSentimentLines();

    if (!state.loaded) {
      setHint("senHint", "loading");
      setBodyText("senBody", tr("home.loading"), "home.loading");
      setSource("senSource", "--");
      return;
    }

    setHint("senHint", lines.length > 0 ? "ready" : "empty");
    setBodyText("senBody", lines.length > 0 ? lines.join("\n") : tr("home.sentiment_empty"), "home.sentiment_empty");
    setSource("senSource", state.sentiment ? "data/world_politics/analysis/sentiment_latest.json" : "--");
  }

  function renderSummary() {
    const summaryText = getSummaryText();

    if (!state.loaded) {
      setHint("sumHint", "loading");
      setBodyText("sumBody", tr("home.loading"), "home.loading");
      setSource("sumSource", "--");
      return;
    }

    setHint("sumHint", summaryText ? "ready" : "empty");
    setBodyText("sumBody", summaryText || tr("home.summary_empty"), "home.summary_empty");
    setSource("sumSource", state.summary ? "data/world_politics/analysis/daily_summary_latest.json" : "--");
  }

  function renderAnchors() {
    setHref(
      "btnOpenHealth",
      state.health ? "/data/digest/health_latest.json" : "#"
    );
    setHref(
      "btnOpenSummary",
      state.summary ? "/data/world_politics/analysis/daily_summary_latest.json" : "#"
    );
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
    state.loaded = false;
    renderAll();

    const jobs = [
      fetchJsonCandidates(PATHS.globalStatus)
        .then(({ json }) => {
          state.globalStatus = json;
        })
        .catch(() => {
          state.globalStatus = null;
        }),
      fetchJsonCandidates(PATHS.digestViewModel)
        .then(({ json }) => {
          state.digestViewModel = json;
        })
        .catch(() => {
          state.digestViewModel = null;
        }),
      fetchJsonCandidates(PATHS.health)
        .then(({ json }) => {
          state.health = json;
        })
        .catch(() => {
          state.health = null;
        }),
      fetchJsonCandidates(PATHS.sentiment)
        .then(({ json }) => {
          state.sentiment = json;
        })
        .catch(() => {
          state.sentiment = null;
        }),
      fetchJsonCandidates(PATHS.summary)
        .then(({ json }) => {
          state.summary = json;
        })
        .catch(() => {
          state.summary = null;
        })
    ];

    await Promise.all(jobs);
    state.loaded = true;
    renderAll();
  }

  document.addEventListener(LANG_CHANGED_EVENT, () => {
    renderAll();
  });

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      () => {
        renderAll();
        loadAll();
      },
      { once: true }
    );
  } else {
    renderAll();
    loadAll();
  }
})();