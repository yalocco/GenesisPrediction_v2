(() => {
  "use strict";


  const LANG_MANAGER = window.GP_LANG_MANAGER || null;
  const LANG_CHANGED_EVENT =
    LANG_MANAGER && LANG_MANAGER.LANG_CHANGED_EVENT ? LANG_MANAGER.LANG_CHANGED_EVENT : "gp:lang-changed";
  const I18N = window.GP_I18N || null;

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
      "ready": "Ready",
      "error": "Error",
      "ok": "OK",
      "missing": "missing",
      "source": "source",
      "date": "date",
      "total": "total",
      "items": "items",
      "articles": "articles",
      "count": "count",
      "positive": "positive",
      "negative": "negative",
      "neutral": "neutral",
      "mixed": "mixed",
      "as_of": "as_of",
      "world_view_missing": "world_view_model_latest.json not available.",
      "health_missing": "health_latest.json not available.",
      "sentiment_missing": "sentiment_latest.json not available.",
      "summary_missing": "daily_summary_latest.json not available.",
      "miss": "MISS",
      "untitled": "untitled"
    },
    ja: {
      "home.title": "ホーム",
      "home.subtitle": "GenesisPrediction は世界の出来事を観測し、トレンド・シグナル・シナリオを将来予測へ接続する分析システムです。この Home 画面は現在の世界状態を示すシステムの出発点です。",
      "home.global_status_title": "グローバルステータス",
      "home.global_risk_label": "グローバルリスク",
      "home.sentiment_balance_label": "センチメントバランス",
      "home.fx_regime_label": "FXレジーム",
      "home.articles_label": "記事数",
      "home.updated_label": "更新日",
      "home.kpi_events": "イベント数",
      "home.kpi_health_ok": "正常数",
      "home.kpi_sentiment_items": "センチメント件数",
      "home.kpi_summary": "サマリー",
      "home.events_today_title": "本日のイベント",
      "home.data_health_title": "データ健全性",
      "home.sentiment_title": "センチメント",
      "home.daily_summary_title": "デイリーサマリー",
      "home.open_json": "JSONを開く",
      "ready": "準備完了",
      "error": "エラー",
      "ok": "OK",
      "missing": "未取得",
      "source": "ソース",
      "date": "日付",
      "total": "合計",
      "items": "件数",
      "articles": "記事数",
      "count": "件数",
      "positive": "ポジティブ",
      "negative": "ネガティブ",
      "neutral": "ニュートラル",
      "mixed": "混合",
      "as_of": "時点",
      "world_view_missing": "world_view_model_latest.json を取得できません。",
      "health_missing": "health_latest.json を取得できません。",
      "sentiment_missing": "sentiment_latest.json を取得できません。",
      "summary_missing": "daily_summary_latest.json を取得できません。",
      "miss": "未取得",
      "untitled": "無題"
    },
    th: {
      "home.title": "หน้าแรก",
      "home.subtitle": "GenesisPrediction คือระบบวิเคราะห์ที่สังเกตเหตุการณ์ทั่วโลกและเชื่อมโยงแนวโน้ม สัญญาณ และฉากทัศน์ไปสู่การคาดการณ์ล่วงหน้า หน้าหลักนี้แสดงสถานะปัจจุบันของโลกซึ่งเป็นจุดเริ่มต้นของระบบ",
      "home.global_status_title": "สถานะรวม",
      "home.global_risk_label": "ความเสี่ยงโลก",
      "home.sentiment_balance_label": "สมดุลเซนติเมนต์",
      "home.fx_regime_label": "ระบอบ FX",
      "home.articles_label": "บทความ",
      "home.updated_label": "อัปเดต",
      "home.kpi_events": "เหตุการณ์",
      "home.kpi_health_ok": "สถานะปกติ",
      "home.kpi_sentiment_items": "รายการเซนติเมนต์",
      "home.kpi_summary": "สรุป",
      "home.events_today_title": "เหตุการณ์วันนี้",
      "home.data_health_title": "สุขภาพข้อมูล",
      "home.sentiment_title": "เซนติเมนต์",
      "home.daily_summary_title": "สรุปรายวัน",
      "home.open_json": "เปิด JSON",
      "ready": "พร้อม",
      "error": "ผิดพลาด",
      "ok": "OK",
      "missing": "ไม่มีข้อมูล",
      "source": "แหล่งที่มา",
      "date": "วันที่",
      "total": "รวม",
      "items": "จำนวนรายการ",
      "articles": "บทความ",
      "count": "จำนวน",
      "positive": "บวก",
      "negative": "ลบ",
      "neutral": "เป็นกลาง",
      "mixed": "ผสม",
      "as_of": "ณ วันที่",
      "world_view_missing": "ไม่พบ world_view_model_latest.json",
      "health_missing": "ไม่พบ health_latest.json",
      "sentiment_missing": "ไม่พบ sentiment_latest.json",
      "summary_missing": "ไม่พบ daily_summary_latest.json",
      "miss": "ไม่มีข้อมูล",
      "untitled": "ไม่มีชื่อ"
    }
  };

  function getLang() {
    if (LANG_MANAGER && typeof LANG_MANAGER.getLang === "function") {
      return LANG_MANAGER.getLang();
    }
    return "en";
  }

  function t(key, fallback = "") {
    const lang = getLang();
    const table = HOME_TEXT[lang] || HOME_TEXT.en;
    return table[key] || HOME_TEXT.en[key] || fallback || key;
  }

  function applyHomeStaticI18n() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key || !String(key).startsWith("home.")) return;
      el.textContent = t(key, el.textContent || key);
    });
  }

  function safeText(x) {
    return x == null ? "" : String(x);
  }

  function setText(id, v) {
    const el = document.getElementById(id);
    if (el) el.textContent = safeText(v);
  }

  function setHref(id, v) {
    const el = document.getElementById(id);
    if (el) el.href = v || "#";
  }

  function firstNumber(...values) {
    for (const v of values) {
      if (typeof v === "number" && !Number.isNaN(v)) return v;
      if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
    }
    return null;
  }

  function firstString(...values) {
    for (const v of values) {
      if (typeof v === "string" && v.trim()) return v.trim();
    }
    return "";
  }

  function shortDate(value) {
    if (!value) return "--";
    return String(value).slice(0, 10);
  }

  function pickLocalizedText(value, fallback = "") {
    if (I18N && typeof I18N.pickI18n === "function") {
      const picked = I18N.pickI18n(value, fallback, getLang());
      if (picked) return picked;
    }
    return firstString(value, fallback);
  }

  function pickLocalizedList(value) {
    if (I18N && typeof I18N.pickI18nList === "function") {
      const picked = I18N.pickI18nList(value, getLang());
      if (Array.isArray(picked) && picked.length) {
        return picked.map((item) => safeText(item)).filter(Boolean);
      }
    }
    if (Array.isArray(value)) {
      return value.map((item) => safeText(item)).filter(Boolean);
    }
    return [];
  }

  function pickLocalizedField(obj, key, fallback = "") {
    if (I18N && typeof I18N.pickText === "function" && obj && typeof obj === "object") {
      const picked = I18N.pickText(obj, key, getLang());
      if (picked) return picked;
    }
    return firstString(obj && obj[key], fallback);
  }


  function renderKV(obj) {
    const lines = [];
    Object.entries(obj || {}).forEach(([k, v]) => {
      if (v == null) return;
      if (typeof v === "object") return;
      let key = k.replace(/_/g, " ");
      key = key.charAt(0).toUpperCase() + key.slice(1);
      lines.push(`${key}: ${String(v)}`);
    });
    return lines.join("\n");
  }

  function latestCheckDate(checks) {
    if (!Array.isArray(checks)) return "";
    let best = "";
    for (const check of checks) {
      const cand = firstString(check && check.updated_at, check && check.date, "");
      if (cand && (!best || cand > best)) best = cand;
    }
    return best;
  }

  function renderHealth(h) {
    if (!h) return "—";
    const sum = h.summary || {};
    const date = shortDate(
      firstString(
        h.date,
        h.generated_at,
        h.as_of,
        latestCheckDate(h.checks),
        ""
      )
    );
    const total = firstNumber(sum.total, h.total, Array.isArray(h.checks) ? h.checks.length : null);
    const ok = firstNumber(sum.ok, h.ok_count, h.OK);
    const warn = firstNumber(sum.warn, h.warn_count, h.WARN);
    const ng = firstNumber(sum.ng, h.ng_count, h.NG);
    const parts = [];
    if (date && date !== "--") parts.push(`${t("date", "date")}: ${date}`);
    if (total != null) parts.push(`${t("total", "total")}: ${total}`);
    if (ok != null) parts.push(`OK: ${ok}`);
    if (warn != null) parts.push(`WARN: ${warn}`);
    if (ng != null) parts.push(`NG: ${ng}`);
    return parts.join("\n");
  }

  function renderSentiment(s) {
    if (!s) return "—";
    const date = s.date || s.as_of || "";
    const labels = s.labels || s.counts || {};
    const today = s.today || {};
    const parts = [];
    if (date) parts.push(`${t("date", "date")}: ${date}`);
    if (today.articles != null) parts.push(`${t("items", "items")}: ${today.articles}`);
    if (labels.positive != null) parts.push(`${t("positive", "positive")}: ${labels.positive}`);
    if (labels.negative != null) parts.push(`${t("negative", "negative")}: ${labels.negative}`);
    if (labels.neutral != null) parts.push(`${t("neutral", "neutral")}: ${labels.neutral}`);
    if (labels.mixed != null) parts.push(`${t("mixed", "mixed")}: ${labels.mixed}`);
    return parts.join("\n");
  }

  function renderSummary(sum) {
    if (!sum) return "—";
    const text = firstString(
      pickLocalizedField(sum, "summary"),
      pickLocalizedField(sum, "text_summary"),
      pickLocalizedField(sum, "daily_summary"),
      pickLocalizedField(sum, "yesterday_summary_text"),
      pickLocalizedField(sum, "text"),
      sum.events_today ? pickLocalizedField(sum.events_today, "summary") : ""
    );

    if (text) {
      return text
        .replace(/\n+/g, "\n")
        .split("\n")
        .slice(0, 6)
        .join("\n");
    }

    return renderKV(sum);
  }

  function renderWorldView(vm) {
    if (!vm) return "—";
    const section = Array.isArray(vm.sections) && vm.sections.length ? vm.sections[0] : null;
    const cards = section && Array.isArray(section.cards) ? section.cards : [];
    const today = vm.today || {};
    const lines = [];

    if (vm.date) lines.push(`${t("date", "date")}: ${vm.date}`);
    if (today.articles != null) lines.push(`${t("articles", "articles")}: ${today.articles}`);
    if (today.count != null) lines.push(`${t("count", "count")}: ${today.count}`);

    if (cards.length) {
      lines.push("");
      cards.slice(0, 6).forEach((card, idx) => {
        const title = firstString(
          pickLocalizedField(card, "title"),
          pickLocalizedField(card, "headline"),
          t("untitled", "untitled")
        );
        lines.push(`${idx + 1}. ${title}`);
      });
    }

    if (!lines.length) return renderKV(vm);
    return lines.join("\n");
  }

  async function fetchJson(url) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return { ok: true, data: await res.json(), url };
    } catch (err) {
      return { ok: false, data: null, url, error: String(err) };
    }
  }

  async function main() {
    try {
      const results = await Promise.all([
        fetchJson("/analysis/global_status_latest.json"),
        fetchJson("/analysis/world_view_model_latest.json"),
        fetchJson("/analysis/health_latest.json"),
        fetchJson("/analysis/sentiment_latest.json"),
        fetchJson("/analysis/daily_summary_latest.json"),
      ]);

      const [gsRes, worldVmRes, healthRes, senRes, sumRes] = results;

      const gs = gsRes.ok ? gsRes.data : null;
      const vm = worldVmRes.ok ? worldVmRes.data : null;
      const health = healthRes.ok ? healthRes.data : null;
      const sentiment = senRes.ok ? senRes.data : null;
      const summary = sumRes.ok ? sumRes.data : null;

      const localAsOf = firstString(
        gs && (gs.updated || gs.as_of),
        summary && (summary.generated_at || summary.as_of || summary.date),
        vm && vm.date,
        health && (health.date || health.as_of || health.generated_at),
        sentiment && (sentiment.date || sentiment.as_of)
      );

      applyHomeStaticI18n();
      setText("pillAsOfLocal", `${t("as_of", "as_of")}: ${shortDate(localAsOf || "--")}`);
      setText("pillReadyLocal", t("ready", "Ready"));

      if (gs) {
        setText("gsRisk", pickLocalizedField(gs, "global_risk", "—") || "—");
        setText("gsRiskSub", pickLocalizedField(gs, "global_risk_sub", "—") || "—");
        setText("gsSentiment", pickLocalizedField(gs, "sentiment_balance", "—") || "—");
        setText("gsSentimentSub", pickLocalizedField(gs, "sentiment_balance_sub", "—") || "—");
        setText("gsFx", pickLocalizedField(gs, "fx_regime", "—") || "—");
        setText("gsFxSub", pickLocalizedField(gs, "fx_regime_sub", "—") || "—");
        setText("gsArticles", pickLocalizedField(gs, "articles", "—") || "—");
        setText("gsArticlesSub", pickLocalizedField(gs, "articles_sub", "—") || "—");
        setText("gsUpdated", shortDate(gs.updated || gs.as_of || "--"));
        setText("gsUpdatedSub", gs.sources && gs.sources.summary ? gs.sources.summary : "—");
      }

      if (vm) {
        setText("evHint", t("ok", "OK"));
        setText("evBody", renderWorldView(vm));
        setText("evSource", `${t("source", "source")}: ${worldVmRes.url}`);
      } else {
        setText("evHint", t("missing", "missing"));
        setText("evBody", t("world_view_missing", "world_view_model_latest.json not available."));
        setText("evSource", `${t("source", "source")}: --`);
      }

      if (health) {
        setText("healthHint", t("ok", "OK"));
        setText("healthBody", renderHealth(health));
        setText("healthSource", `${t("source", "source")}: ${healthRes.url}`);
        setHref("btnOpenHealth", healthRes.url);
      } else {
        setText("healthHint", t("missing", "missing"));
        setText("healthBody", t("health_missing", "health_latest.json not available."));
        setText("healthSource", `${t("source", "source")}: --`);
        setHref("btnOpenHealth", "#");
      }

      if (sentiment) {
        setText("senHint", t("ok", "OK"));
        setText("senBody", renderSentiment(sentiment));
        setText("senSource", `${t("source", "source")}: ${senRes.url}`);
      } else {
        setText("senHint", t("missing", "missing"));
        setText("senBody", t("sentiment_missing", "sentiment_latest.json not available."));
        setText("senSource", `${t("source", "source")}: --`);
      }

      if (summary) {
        setText("sumHint", t("ok", "OK"));
        setText("sumBody", renderSummary(summary));
        setText("sumSource", `${t("source", "source")}: ${sumRes.url}`);
        setHref("btnOpenSummary", sumRes.url);
      } else {
        setText("sumHint", t("missing", "missing"));
        setText("sumBody", t("summary_missing", "daily_summary_latest.json not available."));
        setText("sumSource", `${t("source", "source")}: --`);
        setHref("btnOpenSummary", "#");
      }

      const gsCards = gs && gs.cards ? gs.cards : {};
      const vmToday = vm && vm.today ? vm.today : {};
      const sentimentLabels = sentiment && (sentiment.labels || sentiment.counts || {}) ? (sentiment.labels || sentiment.counts || {}) : {};

      setText(
        "kpiEvents",
        gsCards.events != null
          ? String(gsCards.events)
          : vmToday.articles != null
            ? String(vmToday.articles)
            : vmToday.count != null
              ? String(vmToday.count)
              : "—"
      );

      setText(
        "kpiHealthOk",
        gsCards.health_ok != null
          ? String(gsCards.health_ok)
          : health && health.summary && health.summary.ok != null
            ? String(health.summary.ok)
            : "—"
      );

      const sentimentItems =
        sentiment && sentiment.today && sentiment.today.articles != null
          ? sentiment.today.articles
          : gsCards.sentiment_items != null
            ? gsCards.sentiment_items
            : sentimentLabels.positive != null
              ? sentimentLabels.positive + (sentimentLabels.negative || 0) + (sentimentLabels.neutral || 0) + (sentimentLabels.mixed || 0)
              : null;

      setText("kpiSentimentItems", sentimentItems != null ? String(sentimentItems) : "—");
      setText("kpiSummaryState", gsCards.summary_state != null ? String(gsCards.summary_state) : summary ? t("ok", "OK") : t("miss", "MISS"));
    } catch (e) {
      setText("pillReadyLocal", t("error", "Error"));
      console.warn(e);
    }
  }


  window.addEventListener(LANG_CHANGED_EVENT, () => {
    main();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main, { once: true });
  } else {
    main();
  }
})();
