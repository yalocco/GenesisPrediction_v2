/* app/static/index.js
 * Home page stabilizer
 * - KPI: never flips to "—" due to key mismatch (robust key resolution + fallback chain)
 * - Data Health: always rendered as cards (DOM construction, not raw object dump)
 * - Sentiment preview: never prints [object Object] (safe string + link normalization)
 *
 * NOTE: GUI is read-only. We only fetch /analysis JSON files.
 */

(function () {
  "use strict";

  // ----------------------------
  // DOM helpers
  // ----------------------------
  const $ = (sel) => document.querySelector(sel);

  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  };

  const setText = (id, value) => {
    const node = document.getElementById(id);
    if (!node) return;
    node.textContent = (value === undefined || value === null || value === "") ? "—" : String(value);
  };

  const fmtNum = (x) => {
    if (x === undefined || x === null) return null;
    const n = Number(x);
    if (!Number.isFinite(n)) return null;
    // Keep compact but stable; sentiment metrics are typically 0..1
    if (Math.abs(n) < 10) return n.toFixed(6);
    return String(n);
  };

  const nowISODate = () => {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  };

  // ----------------------------
  // URL/date handling
  // ----------------------------
  const url = new URL(window.location.href);
  const dateParam = (url.searchParams.get("date") || "latest").trim();

  // For navigation prev/next, we only support YYYY-MM-DD. If "latest", we keep it.
  const addDays = (iso, delta) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
    if (!m) return iso;
    const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    d.setDate(d.getDate() + delta);
    const y = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${y}-${mm}-${dd}`;
  };

  const setDateParam = (newDate) => {
    const u = new URL(window.location.href);
    u.searchParams.set("date", newDate);
    window.location.href = u.toString();
  };

  // ----------------------------
  // Fetch helpers (robust, cache-busted)
  // ----------------------------
  async function fetchJson(path) {
    const bust = `cb=${Date.now()}`;
    const sep = path.includes("?") ? "&" : "?";
    const res = await fetch(`${path}${sep}${bust}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${path}`);
    return await res.json();
  }

  async function firstJson(paths) {
    let lastErr = null;
    for (const p of paths) {
      try {
        const j = await fetchJson(p);
        return { path: p, json: j };
      } catch (e) {
        lastErr = e;
      }
    }
    throw lastErr || new Error("all fetch failed");
  }

  // ----------------------------
  // KPI extraction (tolerant)
  // ----------------------------
  function pick(obj, keys) {
    for (const k of keys) {
      if (!obj) continue;
      if (Object.prototype.hasOwnProperty.call(obj, k)) return obj[k];
    }
    return undefined;
  }

  function resolveKpiFromAny(root) {
    // Try common shapes without assuming exact schema.
    // We will look for:
    // - root.kpi.{articles,risk,positive,uncertainty}
    // - root.sentiment.{...}
    // - root.summary.sentiment / root.summary.kpi
    // - root.today / root.latest blocks
    const candidates = [];

    if (root) candidates.push(root);
    if (root && root.summary) candidates.push(root.summary);
    if (root && root.kpi) candidates.push(root.kpi);
    if (root && root.sentiment) candidates.push(root.sentiment);
    if (root && root.summary && root.summary.sentiment) candidates.push(root.summary.sentiment);
    if (root && root.summary && root.summary.kpi) candidates.push(root.summary.kpi);
    if (root && root.latest) candidates.push(root.latest);
    if (root && root.today) candidates.push(root.today);
    if (root && root.latest && root.latest.sentiment) candidates.push(root.latest.sentiment);
    if (root && root.today && root.today.sentiment) candidates.push(root.today.sentiment);

    // Some pipelines store metrics under different key names
    // (pos vs positive, unc vs uncertainty, count vs articles, etc.)
    const out = {
      articles: null,
      risk: null,
      positive: null,
      uncertainty: null,
    };

    for (const c of candidates) {
      if (!c || typeof c !== "object") continue;

      const a = pick(c, ["articles", "article_count", "count", "n", "items"]);
      const r = pick(c, ["risk", "neg", "negative", "downside"]);
      const p = pick(c, ["positive", "pos", "upside"]);
      const u = pick(c, ["uncertainty", "unc", "uncert"]);

      if (out.articles === null || out.articles === undefined) {
        if (Array.isArray(a)) out.articles = a.length;
        else if (a !== undefined) out.articles = a;
      }
      if (out.risk === null || out.risk === undefined) {
        const v = fmtNum(r);
        if (v !== null) out.risk = v;
      }
      if (out.positive === null || out.positive === undefined) {
        const v = fmtNum(p);
        if (v !== null) out.positive = v;
      }
      if (out.uncertainty === null || out.uncertainty === undefined) {
        const v = fmtNum(u);
        if (v !== null) out.uncertainty = v;
      }
    }

    // Normalize articles to integer if possible
    if (out.articles !== null && out.articles !== undefined) {
      const n = Number(out.articles);
      if (Number.isFinite(n)) out.articles = String(Math.trunc(n));
      else out.articles = String(out.articles);
    }

    // Return null if nothing found
    const any =
      (out.articles !== null && out.articles !== undefined) ||
      (out.risk !== null && out.risk !== undefined) ||
      (out.positive !== null && out.positive !== undefined) ||
      (out.uncertainty !== null && out.uncertainty !== undefined);

    return any ? out : null;
  }

  // ----------------------------
  // Data Health rendering
  // ----------------------------
  function normalizeHealth(any) {
    // Accept:
    // - {checks:[{name,status,detail,updated_at,path,exists,bytes}]}
    // - [{...}, {...}]
    // - {something:{...}, ...} -> convert to list
    if (!any) return [];
    if (Array.isArray(any)) return any;

    if (any.checks && Array.isArray(any.checks)) return any.checks;

    if (typeof any === "object") {
      const list = [];
      for (const [k, v] of Object.entries(any)) {
        if (v && typeof v === "object" && !Array.isArray(v)) {
          list.push({ name: k, ...v });
        } else {
          list.push({ name: k, value: v });
        }
      }
      return list;
    }
    return [];
  }

  function healthBadgeClass(status) {
    const s = String(status || "").toLowerCase();
    if (s.includes("ok") || s.includes("pass") || s === "true") return "health-badge ok";
    if (s.includes("warn") || s.includes("maybe")) return "health-badge warn";
    if (s.includes("fail") || s.includes("ng") || s === "false") return "health-badge ng";
    return "health-badge";
  }

  function renderHealth(list, sourceLabel) {
    const grid = $("#healthGrid");
    const hint = $("#healthHint");
    if (!grid) return;

    grid.innerHTML = "";
    const items = normalizeHealth(list);

    if (hint) hint.textContent = sourceLabel ? `Health source: ${sourceLabel}` : "Health source: -";

    if (!items.length) {
      grid.appendChild(el("div", "muted", "Health JSON が見つからない / 空です"));
      return;
    }

    for (const it of items) {
      const card = el("div", "health-card");
      const head = el("div", "health-head");

      const name = it.name || it.key || it.id || it.path || "item";
      const status = it.status ?? it.ok ?? it.state ?? it.exists ?? it.present;
      const badge = el("span", healthBadgeClass(status), (status === undefined ? "-" : String(status)));

      head.appendChild(el("div", "health-name", String(name)));
      head.appendChild(badge);

      const body = el("div", "health-body");

      const detail =
        it.detail ??
        it.message ??
        it.note ??
        it.reason ??
        it.value ??
        it.updated_at ??
        it.mtime ??
        it.timestamp;

      if (detail !== undefined && detail !== null && String(detail).trim() !== "") {
        body.appendChild(el("div", "health-detail", String(detail)));
      }

      const meta = [];
      if (it.path) meta.push(`path=${it.path}`);
      if (it.bytes !== undefined) meta.push(`bytes=${it.bytes}`);
      if (it.size !== undefined) meta.push(`size=${it.size}`);
      if (it.updated_at) meta.push(`updated_at=${it.updated_at}`);
      if (it.date) meta.push(`date=${it.date}`);

      if (meta.length) body.appendChild(el("div", "health-meta", meta.join(" / ")));

      card.appendChild(head);
      card.appendChild(body);
      grid.appendChild(card);
    }
  }

  // ----------------------------
  // Sentiment preview rendering
  // ----------------------------
  function toSafeString(x) {
    if (x === undefined || x === null) return "";
    if (typeof x === "string") return x;
    if (typeof x === "number" || typeof x === "boolean") return String(x);
    // avoid [object Object]
    if (typeof x === "object") {
      // common link object patterns:
      // {title,url,source}
      const t = x.title || x.name || x.text || "";
      const u = x.url || x.href || "";
      const s = x.source || x.site || "";
      const parts = [];
      if (t) parts.push(String(t));
      if (s) parts.push(String(s));
      if (u) parts.push(String(u));
      return parts.join(" | ");
    }
    return String(x);
  }

  function normalizeArticlesFromAny(any) {
    // Accept:
    // - {items:[{title,url,source,...}]}
    // - [{title,url,source}, ...]
    // - {articles:[...]}
    if (!any) return [];
    if (Array.isArray(any)) return any;
    if (any.items && Array.isArray(any.items)) return any.items;
    if (any.articles && Array.isArray(any.articles)) return any.articles;
    if (any.news && Array.isArray(any.news)) return any.news;
    return [];
  }

  function renderSentimentPreview(any, sourceLabel) {
    const ul = $("#sentimentList");
    const hint = $("#sentHint");
    if (!ul) return;

    ul.innerHTML = "";
    if (hint) hint.textContent = sourceLabel ? `Sentiment source: ${sourceLabel}` : "Sentiment source: -";

    const items = normalizeArticlesFromAny(any);
    if (!items.length) {
      ul.appendChild(el("li", "muted", "Sentiment / news JSON が見つからない / 空です"));
      return;
    }

    // show up to 12
    const top = items.slice(0, 12);

    for (const it of top) {
      const li = el("li", "sentiment-item");

      const title = toSafeString(it.title || it.headline || it.name || it.text || "");
      const source = toSafeString(it.source || it.publisher || it.site || "");
      const url = toSafeString(it.url || it.link || it.href || "");

      const row = el("div", "sentiment-row");
      const left = el("div", "sentiment-left");

      if (url) {
        const a = el("a", "sentiment-link", title || url);
        a.href = url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        left.appendChild(a);
      } else {
        left.appendChild(el("div", "sentiment-link", title || "(no title)"));
      }

      if (source) left.appendChild(el("div", "sentiment-src", source));

      // metrics (optional)
      const right = el("div", "sentiment-right");
      const net = fmtNum(it.net ?? it.score ?? it.sentiment ?? it.polarity);
      const risk = fmtNum(it.risk ?? it.neg);
      const pos = fmtNum(it.pos ?? it.positive);
      const unc = fmtNum(it.unc ?? it.uncertainty);

      const chips = [];
      if (net !== null) chips.push(`net=${net}`);
      if (risk !== null) chips.push(`risk=${risk}`);
      if (pos !== null) chips.push(`pos=${pos}`);
      if (unc !== null) chips.push(`unc=${unc}`);

      if (chips.length) right.appendChild(el("div", "sentiment-metrics", chips.join("  ")));

      row.appendChild(left);
      row.appendChild(right);

      li.appendChild(row);
      ul.appendChild(li);
    }
  }

  // ----------------------------
  // Load flow (fallback chain)
  // ----------------------------
  async function loadAll() {
    // Date pill
    const datePill = $("#datePill");
    if (datePill) datePill.textContent = `date: ${dateParam}`;

    // Buttons
    const btnPrev = $("#btnPrev");
    const btnNext = $("#btnNext");
    const btnToday = $("#btnToday");

    if (btnPrev) {
      btnPrev.addEventListener("click", () => {
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateParam)) setDateParam(addDays(dateParam, -1));
        else setDateParam("latest");
      });
    }
    if (btnNext) {
      btnNext.addEventListener("click", () => {
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateParam)) setDateParam(addDays(dateParam, +1));
        else setDateParam("latest");
      });
    }
    if (btnToday) {
      btnToday.addEventListener("click", () => setDateParam(nowISODate()));
    }

    // KPI defaults (do not leave blank)
    setText("kpi_articles", "—");
    setText("kpi_risk", "—");
    setText("kpi_positive", "—");
    setText("kpi_uncertainty", "—");

    const kpiHint = $("#kpiHint");

    // 1) Try daily_summary (dated->latest)
    // 2) If missing, fallback to sentiment_latest.json
    const summaryCandidates = [];
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateParam)) {
      summaryCandidates.push(`/analysis/daily_summary_${dateParam}.json`);
      summaryCandidates.push(`/analysis/daily_summary_${dateParam}.json`); // intentional duplicate safe
    }
    summaryCandidates.push(`/analysis/daily_summary_latest.json`);

    let kpi = null;

    try {
      const { path, json } = await firstJson(summaryCandidates);
      kpi = resolveKpiFromAny(json);
      if (kpiHint) kpiHint.textContent = `KPI source: ${path}`;
    } catch (e) {
      if (kpiHint) kpiHint.textContent = `KPI source: daily_summary not found`;
    }

    if (!kpi) {
      try {
        const { path, json } = await firstJson([`/analysis/sentiment_latest.json`]);
        kpi = resolveKpiFromAny(json);
        if (kpiHint) kpiHint.textContent = `KPI source: ${path}`;
      } catch (e) {
        // keep —
      }
    }

    if (kpi) {
      setText("kpi_articles", kpi.articles ?? "—");
      setText("kpi_risk", kpi.risk ?? "—");
      setText("kpi_positive", kpi.positive ?? "—");
      setText("kpi_uncertainty", kpi.uncertainty ?? "—");
    }

    // Health: try typical names
    try {
      const { path, json } = await firstJson([
        "/analysis/health_latest.json",
        "/analysis/data_health_latest.json",
        "/analysis/data_health.json",
        "/analysis/health.json",
      ]);
      renderHealth(json, path);
    } catch (e) {
      renderHealth([], "not found");
    }

    // Sentiment preview:
    // Prefer dated daily_news if date is YYYY-MM-DD
    // else fallback to daily_news_latest.json then sentiment_latest.json
    const newsCandidates = [];
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateParam)) {
      newsCandidates.push(`/analysis/daily_news_${dateParam}.json`);
    }
    newsCandidates.push(`/analysis/daily_news_latest.json`);
    newsCandidates.push(`/analysis/sentiment_latest.json`);

    try {
      const { path, json } = await firstJson(newsCandidates);
      // If daily_news JSON shape has {items:[...]} or {articles:[...]}, normalize handles it.
      renderSentimentPreview(json, path);
    } catch (e) {
      renderSentimentPreview([], "not found");
    }
  }

  // Run
  window.addEventListener("DOMContentLoaded", () => {
    loadAll().catch((e) => {
      // Fail-safe: never break layout
      console.error(e);
      const kpiHint = $("#kpiHint");
      if (kpiHint) kpiHint.textContent = "KPI source: error (see console)";
      const healthHint = $("#healthHint");
      if (healthHint) healthHint.textContent = "Health source: error (see console)";
      const sentHint = $("#sentHint");
      if (sentHint) sentHint.textContent = "Sentiment source: error (see console)";
    });
  });
})();
