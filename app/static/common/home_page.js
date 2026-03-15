(() => {
  "use strict";

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
    if (date && date !== "--") parts.push(`date: ${date}`);
    if (total != null) parts.push(`total: ${total}`);
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
    if (date) parts.push(`date: ${date}`);
    if (today.articles != null) parts.push(`items: ${today.articles}`);
    if (labels.positive != null) parts.push(`positive: ${labels.positive}`);
    if (labels.negative != null) parts.push(`negative: ${labels.negative}`);
    if (labels.neutral != null) parts.push(`neutral: ${labels.neutral}`);
    if (labels.mixed != null) parts.push(`mixed: ${labels.mixed}`);
    return parts.join("\n");
  }

  function renderSummary(sum) {
    if (!sum) return "—";
    const text = firstString(
      sum.summary,
      sum.text_summary,
      sum.daily_summary,
      sum.yesterday_summary_text,
      sum.text,
      sum.events_today && sum.events_today.summary
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

    if (vm.date) lines.push(`date: ${vm.date}`);
    if (today.articles != null) lines.push(`articles: ${today.articles}`);
    if (today.count != null) lines.push(`count: ${today.count}`);

    if (cards.length) {
      lines.push("");
      cards.slice(0, 6).forEach((card, idx) => {
        const title = firstString(card.title, card.headline, "untitled");
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

      setText("pillAsOfLocal", `as_of: ${shortDate(localAsOf || "--")}`);
      setText("pillReadyLocal", "Ready");

      if (gs) {
        setText("gsRisk", gs.global_risk || "—");
        setText("gsRiskSub", gs.global_risk_sub || "—");
        setText("gsSentiment", gs.sentiment_balance || "—");
        setText("gsSentimentSub", gs.sentiment_balance_sub || "—");
        setText("gsFx", gs.fx_regime || "—");
        setText("gsFxSub", gs.fx_regime_sub || "—");
        setText("gsArticles", gs.articles || "—");
        setText("gsArticlesSub", gs.articles_sub || "—");
        setText("gsUpdated", shortDate(gs.updated || gs.as_of || "--"));
        setText("gsUpdatedSub", gs.sources && gs.sources.summary ? gs.sources.summary : "—");
      }

      if (vm) {
        setText("evHint", "OK");
        setText("evBody", renderWorldView(vm));
        setText("evSource", `source: ${worldVmRes.url}`);
      } else {
        setText("evHint", "missing");
        setText("evBody", "world_view_model_latest.json not available.");
        setText("evSource", "source: --");
      }

      if (health) {
        setText("healthHint", "OK");
        setText("healthBody", renderHealth(health));
        setText("healthSource", `source: ${healthRes.url}`);
        setHref("btnOpenHealth", healthRes.url);
      } else {
        setText("healthHint", "missing");
        setText("healthBody", "health_latest.json not available.");
        setText("healthSource", "source: --");
        setHref("btnOpenHealth", "#");
      }

      if (sentiment) {
        setText("senHint", "OK");
        setText("senBody", renderSentiment(sentiment));
        setText("senSource", `source: ${senRes.url}`);
      } else {
        setText("senHint", "missing");
        setText("senBody", "sentiment_latest.json not available.");
        setText("senSource", "source: --");
      }

      if (summary) {
        setText("sumHint", "OK");
        setText("sumBody", renderSummary(summary));
        setText("sumSource", `source: ${sumRes.url}`);
        setHref("btnOpenSummary", sumRes.url);
      } else {
        setText("sumHint", "missing");
        setText("sumBody", "daily_summary_latest.json not available.");
        setText("sumSource", "source: --");
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
      setText("kpiSummaryState", gsCards.summary_state != null ? String(gsCards.summary_state) : summary ? "OK" : "MISS");
    } catch (e) {
      setText("pillReadyLocal", "Error");
      console.warn(e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main, { once: true });
  } else {
    main();
  }
})();
