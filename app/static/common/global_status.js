(function(){
  "use strict";

  function safeText(x){
    return (x == null) ? "" : String(x);
  }

  function setText(id, v){
    var el = document.getElementById(id);
    if(el) el.textContent = safeText(v);
  }

  function setRiskClass(id, level){
    var el = document.getElementById(id);
    if(!el) return;

    el.classList.remove("risk-low", "risk-medium", "risk-high", "risk-missing");

    if(level === "LOW") el.classList.add("risk-low");
    else if(level === "MEDIUM") el.classList.add("risk-medium");
    else if(level === "HIGH") el.classList.add("risk-high");
    else el.classList.add("risk-missing");
  }

  async function fetchJson(url){
    var r = await fetch(url, { cache: "no-store" });
    if(!r.ok) throw new Error("HTTP " + r.status);
    return await r.json();
  }

  async function pickFirstOk(urls){
    for(var i = 0; i < urls.length; i++){
      var u = urls[i];
      try{
        var j = await fetchJson(u);
        return { url: u, json: j };
      }catch(_e){}
    }
    return null;
  }

  function firstNumber(){
    for(var i = 0; i < arguments.length; i++){
      var v = arguments[i];
      if(typeof v === "number" && !Number.isNaN(v)) return v;
      if(typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
    }
    return null;
  }

  function firstString(){
    for(var i = 0; i < arguments.length; i++){
      var v = arguments[i];
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
    var summaryRisk = firstNumber(
      summary && summary.risk_score,
      summary && summary.risk,
      summary && summary.riskScore
    );
    if(summaryRisk != null) return summaryRisk;

    var s = sentiment && (sentiment.summary || sentiment.today || sentiment.sentiment_summary || sentiment);
    return firstNumber(
      s && s.risk,
      s && s.risk_score,
      s && s.riskScore
    );
  }

  function normalizeSentimentBalance(sentiment){
    if(!sentiment){
      return { label: "—", detail: "sentiment missing" };
    }

    var s = sentiment.summary || sentiment.today || sentiment.sentiment_summary || sentiment;

    var pos = firstNumber(s && s.positive_count, s && s.positive, s && s.pos_count);
    var neg = firstNumber(s && s.negative_count, s && s.negative, s && s.neg_count);
    var neu = firstNumber(s && s.neutral_count, s && s.neutral);
    var mix = firstNumber(s && s.mixed_count, s && s.mixed);

    if(pos != null || neg != null || neu != null || mix != null){
      var pairs = [
        ["POS", pos || 0],
        ["NEG", neg || 0],
        ["NEU", neu || 0],
        ["MIX", mix || 0]
      ].sort(function(a, b){ return b[1] - a[1]; });

      var top = pairs[0];
      return {
        label: top[0],
        detail: "pos " + (pos || 0) + " / neg " + (neg || 0) + " / neu " + (neu || 0) + " / mix " + (mix || 0)
      };
    }

    var items = Array.isArray(sentiment.items) ? sentiment.items : [];
    if(items.length){
      var counts = { positive: 0, negative: 0, neutral: 0, mixed: 0, unknown: 0 };
      items.forEach(function(it){
        var label = firstString(it.sentiment_label, it.sentiment, it.label).toLowerCase();
        if(Object.prototype.hasOwnProperty.call(counts, label)) counts[label] += 1;
        else counts.unknown += 1;
      });

      var top2 = Object.entries(counts).sort(function(a, b){ return b[1] - a[1]; })[0];
      return {
        label: top2 ? top2[0].toUpperCase() : "—",
        detail: "items " + items.length
      };
    }

    return { label: "—", detail: "no sentiment stats" };
  }

  function normalizeFxRegime(fx){
    if(!fx){
      return { label: "—", detail: "fx decision missing" };
    }

    var reasons = "";
    if(Array.isArray(fx.fx_reasons) && fx.fx_reasons.length){
      reasons = fx.fx_reasons.join(" / ");
    }

    var label = firstString(
      fx.regime,
      fx.decision,
      fx.fx_decision,
      fx.action,
      fx.status,
      fx.recommendation
    ) || "—";

    var detail = firstString(
      fx.reason,
      reasons,
      fx.rationale,
      fx.message,
      fx.note
    ) || "global decision";

    return {
      label: label.toUpperCase(),
      detail: detail
    };
  }

  function normalizeArticles(vm, sentiment){
    if(vm){
      var sectionCards = Array.isArray(vm.sections)
        ? vm.sections.reduce(function(n, sec){
            return n + (Array.isArray(sec.cards) ? sec.cards.length : 0);
          }, 0)
        : null;

      var articles = firstNumber(
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
      summary && summary.date,
      summary && summary.as_of,
      sentiment && sentiment.date,
      sentiment && sentiment.as_of,
      health && health.date,
      health && health.as_of,
      vm && vm.date,
      vm && vm.as_of
    ) || "--";
  }

  async function loadGlobalStatus(opts){
    opts = opts || {};

    var candidates = {
      viewModel: opts.viewModelCandidates || [
        "/data/digest/view_model_latest.json",
        "/data/world_politics/analysis/view_model_latest.json"
      ],
      health: opts.healthCandidates || [
        "/data/world_politics/analysis/health_latest.json",
        "/data/digest/health_latest.json"
      ],
      summary: opts.summaryCandidates || [
        "/data/world_politics/analysis/daily_summary_latest.json",
        "/data/digest/daily_summary_latest.json"
      ],
      sentiment: opts.sentimentCandidates || [
        "/data/world_politics/analysis/sentiment_latest.json",
        "/data/digest/sentiment_latest.json"
      ],
      fxDecision: opts.fxDecisionCandidates || [
        "/data/fx/fx_decision_latest.json"
      ]
    };

    var vmRes = await pickFirstOk(candidates.viewModel);
    var healthRes = await pickFirstOk(candidates.health);
    var senRes = await pickFirstOk(candidates.sentiment);
    var sumRes = await pickFirstOk(candidates.summary);
    var fxRes = await pickFirstOk(candidates.fxDecision);

    var vm = vmRes && vmRes.json;
    var health = healthRes && healthRes.json;
    var sentiment = senRes && senRes.json;
    var summary = sumRes && sumRes.json;
    var fxDecision = fxRes && fxRes.json;

    var updated = normalizeUpdated(vm, summary, sentiment, health);
    var riskScore = normalizeRisk(summary, sentiment);
    var riskLevel = toLevelFromRisk(riskScore);
    var sentimentBalance = normalizeSentimentBalance(sentiment);
    var fxRegime = normalizeFxRegime(fxDecision);
    var articles = normalizeArticles(vm, sentiment);

    setText("pillReady", "Ready");

    setText("gsRisk", riskLevel);
    setRiskClass("gsRisk", riskLevel);
    setText("gsRiskSub", riskScore != null ? ("risk score " + Number(riskScore).toFixed(2)) : "daily summary fallback");

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
        sumRes && sumRes.url,
        senRes && senRes.url,
        healthRes && healthRes.url,
        vmRes && vmRes.url,
        fxRes && fxRes.url
      ) || "runtime latest"
    );

    return {
      vmRes: vmRes,
      healthRes: healthRes,
      senRes: senRes,
      sumRes: sumRes,
      fxRes: fxRes,
      vm: vm,
      health: health,
      sentiment: sentiment,
      summary: summary,
      fxDecision: fxDecision,
      updated: updated,
      riskScore: riskScore,
      riskLevel: riskLevel,
      sentimentBalance: sentimentBalance,
      fxRegime: fxRegime,
      articles: articles
    };
  }

  window.GPGlobalStatus = {
    fetchJson: fetchJson,
    pickFirstOk: pickFirstOk,
    firstNumber: firstNumber,
    firstString: firstString,
    toLevelFromRisk: toLevelFromRisk,
    normalizeRisk: normalizeRisk,
    normalizeSentimentBalance: normalizeSentimentBalance,
    normalizeFxRegime: normalizeFxRegime,
    normalizeArticles: normalizeArticles,
    normalizeUpdated: normalizeUpdated,
    load: loadGlobalStatus,
    setText: setText,
    setRiskClass: setRiskClass
  };
})();