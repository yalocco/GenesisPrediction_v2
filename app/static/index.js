/* app/static/index.js
 * Home page stabilizer + Data Health summary line
 *
 * - KPI: robust key resolution + fallback chain
 * - Data Health: always rendered as cards + top summary line (OK/WARN/NG + thresholds)
 * - Sentiment preview: never prints [object Object] (safe string + link normalization)
 * - Sentiment category jump: Index -> Sentiment (cat + date)
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
  // Sentiment category jump (Index -> Sentiment)
  // ----------------------------
  function openSentimentWithCat(cat) {
    const u = new URL("/static/sentiment.html", window.location.origin);

    // keep the same date context
    if (dateParam) u.searchParams.set("date", dateParam);

    // cat=all は Sentiment 側の default(all) に任せる（URLを綺麗にする）
    if (cat && cat !== "all") u.searchParams.set("cat", cat);

    window.location.href = u.toString();
  }

  function setActiveCatButton(cat) {
    const bar = $("#sentCatBar");
    if (!bar) return;
    const buttons = bar.querySelectorAll("button[data-cat]");
    buttons.forEach((b) => {
      const c = (b.getAttribute("data-cat") || "all").toLowerCase();
      if (c === (cat || "all")) b.classList.add("is-active");
      else b.classList.remove("is-active");
    });
  }

  function wireSentimentCatBar() {
    const bar = $("#sentCatBar");
    if (!bar) return;

    bar.addEventListener("click", (ev) => {
      const btn = ev.target && ev.target.closest ? ev.target.closest("button[data-cat]") : null;
      if (!btn) return;
      const cat = (btn.getAttribute("data-cat") || "all").toLowerCase();

      // UI feedback (念のため)
      setActiveCatButton(cat);

      // jump
      openSentimentWithCat(cat);
    });

    // 初期状態は All をアクティブに見せる
    setActiveCatButton("all");
  }

  // ----------------------------
  // Fetch helpers
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

    const out = { articles: null, risk: null, positive: null, uncertainty: null };

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

    if (out.articles !== null && out.articles !== undefined) {
      const n = Number(out.articles);
      if (Number.isFinite(n)) out.articles = String(Math.trunc(n));
      else out.articles = String(out.articles);
    }

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
    if (!any) return [];
    if (Array.isArray(any)) return any;
    if (any.checks && Array.isArray(any.checks)) return any.checks;
    if (typeof any === "object") {
      const list = [];
      for (const [k, v] of Object.entries(any)) {
        if (v && typeof v === "object" && !Array.isArray(v)) list.push({ name: k, ...v });
        else list.push({ name: k, value: v });
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

  function extractHealthSummary(root, items) {
    // Prefer explicit summary from health json
    const s = root && root.summary ? root.summary : null;
    const t = root && root.thresholds ? root.thresholds : null;

    let ok = null, warn = null, ng = null, total = null;
    if (s && typeof s === "object") {
      ok = (s.ok !== undefined) ? s.ok : ok;
      warn = (s.warn !== undefined) ? s.warn : warn;
      ng = (s.ng !== undefined) ? s.ng : ng;
      total = (s.total !== undefined) ? s.total : total;
    }

    // If missing, compute from items
    if (ok === null || warn === null || ng === null || total === null) {
      let _ok = 0, _warn = 0, _ng = 0;
      for (const it of items) {
        const st = String(it.status ?? it.freshness ?? it.ok ?? it.state ?? "").toUpperCase();
        if (st === "OK") _ok++;
        else if (st === "WARN") _warn++;
        else if (st === "NG" || st === "FAIL") _ng++;
      }
      ok = ok ?? _ok;
      warn = warn ?? _warn;
      ng = ng ?? _ng;
      total = total ?? items.length;
    }

    const okH = t && t.ok_age_hours !== undefined ? t.ok_age_hours : null;
    const warnH = t && t.warn_age_hours !== undefined ? t.warn_age_hours : null;

    return { ok, warn, ng, total, okH, warnH };
  }

  function renderHealth(root, sourceLabel) {
    const grid = $("#healthGrid");
    const hint = $("#healthHint");
    if (!grid) return;

    grid.innerHTML = "";

    const items = normalizeHealth(root);

    // Top summary line
    const summary = extractHealthSummary(root, items);
    const summaryTextParts = [];
    summaryTextParts.push(`Health Summary: OK=${summary.ok}  WARN=${summary.warn}  NG=${summary.ng}  total=${summary.total}`);
    if (summary.okH !== null && summary.warnH !== null) {
      summaryTextParts.push(`(OK<=${summary.okH}h  WARN<=${summary.warnH}h)`);
    }
    const summaryLine = el("div", "muted", summaryTextParts.join("  "));
    summaryLine.style.marginBottom = "10px";
    grid.appendChild(summaryLine);

    if (hint) hint.textContent = sourceLabel ? `Health source: ${sourceLabel}` : "Health source: -";

    if (!items.length) {
      grid.appendChild(el("div", "muted", "Health JSON が見つからない / 空です"));
      return;
    }

    for (const it of items) {
      const card = el("div", "health-card");
      const head = el("div", "health-head");

      const name = it.name || it.key || it.id || it.path || "item";
      const status = it.status ?? it.freshness ?? it.ok ?? it.state ?? it.exists ?? it.present;
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
      if (it.age_hours !== undefined) meta.push(`age_h=${it.age_hours}`);
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
    if (typeof x === "object") {
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

    const top = items.slice(0, 12);

    for (const it of top) {
      const li = el("li", "sentiment-item");

      const title = toSafeString(it.title || it.headline || it.name || it.text || "");
      const source = toSafeString(it.source || it.publisher || it.site || "");
      const linkUrl = toSafeString(it.url || it.link || it.href || "");

      const row = el("div", "sentiment-row");
      const left = el("div", "sentiment-left");

      if (linkUrl) {
        const a = el("a", "sentiment-link", title || linkUrl);
        a.href = linkUrl;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        left.appendChild(a);
      } else {
        left.appendChild(el("div", "sentiment-link", title || "(no title)"));
      }

      if (source) left.appendChild(el("div", "sentiment-src", source));

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
    const datePill = $("#datePill");
    if (datePill) datePill.textContent = `date: ${dateParam}`;

    // wire sentiment category bar (Index -> Sentiment)
    wireSentimentCatBar();

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

    // KPI defaults
    setText("kpi_articles", "—");
    setText("kpi_risk", "—");
    setText("kpi_positive", "—");
    setText("kpi_uncertainty", "—");

    const kpiHint = $("#kpiHint");

    const summaryCandidates = [];
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateParam)) {
      summaryCandidates.push(`/analysis/daily_summary_${dateParam}.json`);
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

    // Health
    try {
      const { path, json } = await firstJson([
        "/analysis/health_latest.json",
        "/analysis/data_health_latest.json",
        "/analysis/data_health.json",
        "/analysis/health.json",
      ]);
      renderHealth(json, path);
    } catch (e) {
      renderHealth({ checks: [], summary: { ok: 0, warn: 0, ng: 0, total: 0 } }, "not found");
    }

    // Sentiment preview
    const newsCandidates = [];
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateParam)) {
      newsCandidates.push(`/analysis/daily_news_${dateParam}.json`);
    }
    newsCandidates.push(`/analysis/daily_news_latest.json`);
    newsCandidates.push(`/analysis/sentiment_latest.json`);

    try {
      const { path, json } = await firstJson(newsCandidates);
      renderSentimentPreview(json, path);
    } catch (e) {
      renderSentimentPreview([], "not found");
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    loadAll().catch((e) => {
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
