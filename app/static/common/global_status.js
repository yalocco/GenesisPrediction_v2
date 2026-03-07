(function(){
  "use strict";

  function safeText(x){
    return (x == null) ? "" : String(x);
  }

  function setText(id, v){
    const el = document.getElementById(id);
    if(el) el.textContent = safeText(v);
  }

  function setRiskClass(id, level){
    const el = document.getElementById(id);
    if(!el) return;

    el.classList.remove(
      "risk-low",
      "risk-medium",
      "risk-high",
      "risk-missing"
    );

    if(level === "LOW") el.classList.add("risk-low");
    else if(level === "MEDIUM") el.classList.add("risk-medium");
    else if(level === "HIGH") el.classList.add("risk-high");
    else el.classList.add("risk-missing");
  }

  async function fetchJson(url){
    const r = await fetch(url, { cache: "no-store" });
    if(!r.ok) throw new Error("HTTP " + r.status);
    return await r.json();
  }

  async function pickFirstJson(urls){
    for(const u of urls){
      try{
        const j = await fetchJson(u);
        return { url: u, data: j };
      }catch(_e){}
    }
    return null;
  }

  function firstNumber(){
    for(let i = 0; i < arguments.length; i++){
      const v = arguments[i];
      if(typeof v === "number" && !Number.isNaN(v)) return v;
      if(typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
    }
    return null;
  }

  function firstString(){
    for(let i = 0; i < arguments.length; i++){
      const v = arguments[i];
      if(typeof v === "string" && v.trim()) return v.trim();
    }
    return "";
  }

  function toLevelFromRisk(v){
    if(v == null) return "—";
    if(v >= 0.72) return "HIGH";
    if(v >= 0.42) return "MEDIUM";
    return "LOW";
  }

  function normalizeRisk(summary, sentiment){
    const summaryRisk = firstNumber(
      summary && summary.risk_score,
      summary && summary.risk,
      summary && summary.riskScore
    );
    if(summaryRisk != null) return summaryRisk;

    const s = sentiment && (sentiment.summary || sentiment.today || sentiment.sentiment_summary || sentiment);
    return firstNumber(
      s && s.risk,
      s && s.risk_score,
      s && s.riskScore
    );
  }

  function normalizeSentimentBalance(sentiment){
    if(!sentiment) return { label: "—", detail: "sentiment missing" };

    const s = sentiment.summary || sentiment.today || sentiment.sentiment_summary || sentiment;

    const pos = firstNumber(s && s.positive_count, s && s.positive, s && s.pos_count);
    const neg = firstNumber(s && s.negative_count, s && s.negative, s && s.neg_count);
    const neu = firstNumber(s && s.neutral_count, s && s.neutral);
    const mix = firstNumber(s && s.mixed_count, s && s.mixed);

    if(pos != null || neg != null || neu != null || mix != null){
      const pairs = [
        ["POS", pos || 0],
        ["NEG", neg || 0],
        ["NEU", neu || 0],
        ["MIX", mix || 0]
      ].sort(function(a, b){ return b[1] - a[1]; });

      const top = pairs[0];
      return {
        label: top[0],
        detail: "pos " + (pos || 0) + " / neg " + (neg || 0) + " / neu " + (neu || 0) + " / mix " + (mix || 0)
      };
    }

    const items = Array.isArray(sentiment.items) ? sentiment.items : [];
    if(items.length){
      const counts = { positive: 0, negative: 0, neutral: 0, mixed: 0, unknown: 0 };
      items.forEach(function(it){
        const label = firstString(it.sentiment_label, it.sentiment, it.label).toLowerCase();
        if(Object.prototype.hasOwnProperty.call(counts, label)) counts[label] += 1;
        else counts.unknown += 1;
      });
      const top = Object.entries(counts).sort(function(a, b){ return b[1] - a[1]; })[0];
      return {
        label: top ? top[0].toUpperCase() : "—",
        detail: "items " + items.length
      };
    }

    return { label: "—", detail: "no sentiment stats" };
  }

  function normalizeArticles(vm, sentiment){
    if(vm){
      const sectionCards = Array.isArray(vm.sections)
        ? vm.sections.reduce(function(n, sec){
            return n + (Array.isArray(sec.cards) ? sec.cards.length : 0);
          }, 0)
        : null;

      const articles = firstNumber(
        vm && vm.meta && vm.meta.items,
        vm && vm.sentiment_summary && vm.sentiment_summary.articles,
        vm && vm.today && vm.today.sentiment_summary && vm.today.sentiment_summary.articles,
        sectionCards
      );

      if(articles != null) return articles;
    }

    if(sentiment && Array.isArray(sentiment.items)) return sentiment.items.length;
    return null;
  }

  function normalizeUpdated(vm, summary, sentiment, health){
    return firstString(
      vm && vm.date,
      vm && vm.as_of,
      summary && summary.date,
      summary && summary.as_of,
      sentiment && sentiment.date,
      sentiment && sentiment.as_of,
      health && health.date,
      health && health.as_of
    ) || "--";
  }

  function normalizeFxRegime(fx){
    if(!fx) return { label: "—", detail: "fx decision missing" };

    const label = firstString(
      fx.regime,
      fx.decision,
      fx.action,
      fx.status,
      fx.recommendation
    ) || "—";

    const detail = firstString(
      fx.reason,
      fx.rationale,
      fx.message,
      fx.note
    ) || "global decision";

    return {
      label: label.toUpperCase(),
      detail: detail
    };
  }

  const DEFAULT_CANDIDATES = {
    viewModel: [
      "/data/digest/view_model_latest.json",
      "/data/world_politics/analysis/view_model_latest.json"
    ],
    health: [
      "/data/digest/health_latest.json",
      "/data/world_politics/analysis/health_latest.json"
    ],
    summary: [
      "/data/digest/daily_summary_latest.json",
      "/data/world_politics/analysis/daily_summary_latest.json"
    ],
    sentiment: [
      "/data/world_politics/analysis/sentiment_latest.json",
      "/data/digest/sentiment_latest.json"
    ],
    fxDecision: [
      "/data/fx/fx_decision_latest.json",
      "/data/fx/fx_decision_latest_jpythb.json"
    ]
  };

  async function loadGlobalStatus(options){
    const cfg = Object.assign({}, DEFAULT_CANDIDATES, options || {});

    const vmRes = await pickFirstJson(cfg.viewModel);
    const healthRes = await pickFirstJson(cfg.health);
    const senRes = await pickFirstJson(cfg.sentiment);
    const sumRes = await pickFirstJson(cfg.summary);
    const fxRes = await pickFirstJson(cfg.fxDecision);

    const vm = vmRes && vmRes.data;
    const health = healthRes && healthRes.data;
    const sentiment = senRes && senRes.data;
    const summary = sumRes && sumRes.data;
    const fxDecision = fxRes && fxRes.data;

    const updated = normalizeUpdated(vm, summary, sentiment, health);
    const riskScore = normalizeRisk(summary, sentiment);
    const riskLevel = toLevelFromRisk(riskScore);
    const sentimentBalance = normalizeSentimentBalance(sentiment);
    const fxRegime = normalizeFxRegime(fxDecision);
    const articles = normalizeArticles(vm, sentiment);

    setText("pillAsOf", "as_of: " + updated);
    setText("pillReady", "Ready");

    setText("gsRisk", riskLevel);
    setRiskClass("gsRisk", riskLevel);
    setText(
      "gsRiskSub",
      riskScore != null
        ? ("risk score " + Number(riskScore).toFixed(2))
        : "daily summary fallback"
    );

    setText("gsSentiment", sentimentBalance.label);
    setText("gsSentimentSub", sentimentBalance.detail);

    setText("gsFx", fxRegime.label);
    setText("gsFxSub", fxRegime.detail);

    setText("gsArticles", articles != null ? String(articles) : "—");
    setText("gsArticlesSub", vmRes ? "digest latest" : "sentiment fallback");

    setText("gsUpdated", updated);
    setText(
      "gsUpdatedSub",
      firstString(
        vmRes && vmRes.url,
        sumRes && sumRes.url,
        senRes && senRes.url,
        healthRes && healthRes.url
      ) || "runtime latest"
    );

    return {
      viewModel: vm,
      health: health,
      sentiment: sentiment,
      summary: summary,
      fxDecision: fxDecision,
      meta: {
        updated: updated,
        riskScore: riskScore,
        riskLevel: riskLevel,
        articles: articles
      }
    };
  }

  window.GPGlobalStatus = {
    load: loadGlobalStatus,
    setRiskClass: setRiskClass,
    helpers: {
      firstNumber: firstNumber,
      firstString: firstString,
      normalizeRisk: normalizeRisk,
      normalizeSentimentBalance: normalizeSentimentBalance,
      normalizeArticles: normalizeArticles,
      normalizeUpdated: normalizeUpdated,
      normalizeFxRegime: normalizeFxRegime,
      toLevelFromRisk: toLevelFromRisk
    }
  };
})();