// ----------------------------
// URL normalization (strong)
// ----------------------------
function normUrl(u) {
  try {
    let s = String(u || "").trim();
    if (!s) return "";
    if (s.startsWith("//")) s = "https:" + s;
    if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(s)) s = "https://" + s;

    const url = new URL(s);
    url.hash = "";

    let host = url.hostname.toLowerCase();
    if (host.startsWith("www.")) host = host.slice(4);

    // NewsBreak share links: query is noisy and breaks join/dedup
    if (host === "newsbreak.com") {
      url.search = "";
    }

    const dropKeys = new Set([
      "fbclid","gclid","dclid","msclkid","igshid","mc_cid","mc_eid",
      "ref","ref_src","ref_url","source","src","spm","cmpid","cid","si","partner",
      "ocid","ito","sc_campaign","sc_channel","sc_content","sc_medium","sc_outcome",
      "ns_source","ns_mchannel","ns_campaign","ns_linkname","share","share_id","trans_data",
      "utm_source","utm_medium","utm_campaign","utm_term","utm_content","utm_id","utm_name"
    ]);

    const kept = [];
    url.searchParams.forEach((v, k) => {
      const kk = String(k).toLowerCase();
      if (kk.startsWith("utm_")) return;
      if (dropKeys.has(kk)) return;
      if (v == null || v === "") return;
      kept.push([k, v]);
    });

    kept.sort((a,b)=> (a[0]===b[0] ? String(a[1]).localeCompare(String(b[1])) : a[0].localeCompare(b[0])));

    url.search = "";
    for (const [k,v] of kept) url.searchParams.append(k,v);

    url.protocol = "https:";
    url.hostname = host;

    if (url.pathname.length > 1 && url.pathname.endsWith("/")) {
      url.pathname = url.pathname.replace(/\/+$/, "");
    }

    return url.toString();
  } catch {
    return String(u || "").trim();
  }
}

function normKey(u) {
  const nu = normUrl(u);
  try {
    const x = new URL(nu);
    // protocol差を無視して join/dedup
    return `${x.hostname}${x.pathname}${x.search}`;
  } catch {
    return nu;
  }
}

function hostLabel(u){
  try{
    const x = new URL(normUrl(u));
    return x.hostname.replace(/^www\./,"");
  }catch{ return ""; }
}

function fmt6(v){
  if (v === null || v === undefined) return "-";
  const n = Number(v);
  if (!Number.isFinite(n)) return "-";
  return n.toFixed(6);
}

// ----------------------------
// date helpers
// ----------------------------
function ymd(d){
  const pad=(x)=>String(x).padStart(2,"0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
}
function addDays(ymdStr, delta){
  const [y,m,dd]=ymdStr.split("-").map(Number);
  const dt=new Date(y, m-1, dd);
  dt.setDate(dt.getDate()+delta);
  return ymd(dt);
}
function getQueryDate(){
  const p=new URLSearchParams(location.search);
  const d=p.get("date");
  if (!d) return "";
  if (d === "latest") return "";
  return d;
}
function setQueryDate(d){
  const url=new URL(location.href);
  if (d) url.searchParams.set("date", d);
  else url.searchParams.delete("date");
  history.replaceState({}, "", url.toString());
}

// ----------------------------
// fetch helpers
// ----------------------------
async function jget(path){
  const r=await fetch(path, {cache:"no-store"});
  if (!r.ok) throw new Error(`${r.status} ${r.statusText} @ ${path}`);
  return await r.json();
}

async function getLatestDate(){
  try{
    const j=await jget("/analysis/latest.json");
    if (j && j.date) return j.date;
  }catch{}
  try{
    const j=await jget("/analysis/daily_news_latest.json");
    if (j && j.date) return j.date;
  }catch{}
  return ymd(new Date());
}

function dailyNewsPath(date){
  return date ? `/analysis/daily_news_${date}.json` : `/analysis/daily_news_latest.json`;
}
function sentimentPath(date){
  return date ? `/analysis/sentiment_${date}.json` : `/analysis/sentiment_latest.json`;
}
function digestHtmlPath(date){
  return date ? `/analysis/daily_news_digest_${date}.html` : `/analysis/daily_news_digest_latest.html`;
}

// daily_news / sentiment の配列を雑に救う（将来のschema変更にも耐える）
function safeItems(obj){
  if (!obj) return [];
  if (Array.isArray(obj.items)) return obj.items;
  if (Array.isArray(obj.articles)) return obj.articles;
  if (Array.isArray(obj.data)) return obj.data;
  return [];
}

// ----------------------------
// UI rendering
// ----------------------------
function banner(msg){
  const el = document.getElementById("banner");
  if (!msg) { el.hidden = true; el.textContent = ""; return; }
  el.hidden = false;
  el.textContent = msg;
}

function renderHeadline(sent){
  document.getElementById("riskV").textContent = fmt6(sent?.risk);
  document.getElementById("posV").textContent  = fmt6(sent?.positive);
  document.getElementById("uncV").textContent  = fmt6(sent?.uncertainty);
}

function mkPill(text, cls=""){
  const s=document.createElement("span");
  s.className="pill " + cls;
  s.textContent=text;
  return s;
}

function renderList(rows){
  const list=document.getElementById("list");
  const err=document.getElementById("err");
  list.innerHTML="";
  err.textContent="";

  document.getElementById("countLabel").textContent =
    `${rows.length} articles (deduped)`;

  for (const r of rows){
    const item=document.createElement("div");
    item.className="item";

    const th=document.createElement("div");
    th.className="thumb";
    if (r.image_url){
      const img=document.createElement("img");
      img.src=r.image_url;
      img.alt="";
      img.loading="lazy";
      th.appendChild(img);
    }
    item.appendChild(th);

    const meta=document.createElement("div");
    meta.className="meta";

    const a=document.createElement("a");
    a.className="title";
    a.href=r.url || "#";
    a.target="_blank";
    a.rel="noreferrer";
    a.textContent=r.title || "(no title)";
    meta.appendChild(a);

    const src=document.createElement("div");
    src.className="src";
    src.textContent=r.source || hostLabel(r.url) || "";
    meta.appendChild(src);

    const chips=document.createElement("div");
    chips.className="chips";
    chips.appendChild(mkPill("NEU","m"));
    chips.appendChild(mkPill(hostLabel(r.url) || "-", "m"));

    if (r.sent_found){
      chips.appendChild(mkPill(`net ${fmt6(r.net)}`, "k"));
      chips.appendChild(mkPill(`risk ${fmt6(r.risk_score)}`, "k"));
      chips.appendChild(mkPill(`pos ${fmt6(r.positive_score)}`, "k"));
      chips.appendChild(mkPill(`unc ${fmt6(r.uncertainty_score)}`, "k"));
    } else {
      chips.appendChild(mkPill(`net -`, "k"));
      chips.appendChild(mkPill(`risk -`, "k"));
      chips.appendChild(mkPill(`pos -`, "k"));
      chips.appendChild(mkPill(`unc -`, "k"));
    }

    meta.appendChild(chips);
    item.appendChild(meta);
    list.appendChild(item);
  }
}

function buildJoinedRows(daily, sent){
  const ditems = safeItems(daily);
  const sitems = safeItems(sent);

  // sentiment map (normalized key)
  const smap = new Map();
  for (const it of sitems){
    const k = normKey(it.url || "");
    if (!k) continue;
    if (!smap.has(k)) smap.set(k, it);
  }

  // dedup daily by normalized key
  const seen = new Set();
  const rows = [];

  for (const a of ditems){
    const url0 = a.url || a.link || "";
    const host = hostLabel(url0);
    const k = normKey(url0);
    const fallbackKey = k || `${host}::${String(a.title||"").trim().toLowerCase()}`;

    if (seen.has(fallbackKey)) continue;
    seen.add(fallbackKey);

    const s = smap.get(k);

    rows.push({
      title: a.title || "",
      url: url0,
      source: a.source || a.provider || host,
      image_url: a.image_url || a.image || a.urlToImage || "",
      sent_found: !!s,
      net: s?.net,
      risk_score: s?.risk_score,
      positive_score: s?.positive_score,
      uncertainty_score: s?.uncertainty_score,
    });
  }

  return rows;
}

// ----------------------------
// main loader
// ----------------------------
async function loadAll(){
  const errEl=document.getElementById("err");
  errEl.textContent="";
  banner("");

  let date = getQueryDate();
  if (!date){
    date = await getLatestDate();
    setQueryDate(date);
  }

  // reflect UI
  document.getElementById("dateLabel").textContent = date;
  document.getElementById("dateInput").value = date;
  document.getElementById("digestSub").textContent = date;

  // wire buttons
  document.getElementById("prevBtn").onclick = ()=>{ setQueryDate(addDays(date,-1)); loadAll(); };
  document.getElementById("nextBtn").onclick = ()=>{ setQueryDate(addDays(date, 1)); loadAll(); };
  document.getElementById("todayBtn").onclick = ()=>{ setQueryDate(ymd(new Date())); loadAll(); };
  document.getElementById("latestBtn").onclick = async ()=>{ const d=await getLatestDate(); setQueryDate(d); loadAll(); };

  document.getElementById("dateInput").onchange = (e)=>{
    const v=e.target.value;
    if (v) { setQueryDate(v); loadAll(); }
  };

  document.getElementById("openDigestBtn").onclick = ()=>{
    window.open(digestHtmlPath(date), "_blank", "noreferrer");
  };
  document.getElementById("openDigestHtmlBtn").onclick = ()=>{
    window.open(digestHtmlPath(date), "_blank", "noreferrer");
  };

  // ✅ Daily View 内のボタンも header と同じ “sentiment.html” へ
  document.getElementById("openSentBtn").onclick = ()=>{
    window.open(`/static/sentiment.html?date=${date}`, "_blank", "noreferrer");
  };

  // fetch
  let daily=null, sent=null;

  try{
    daily = await jget(dailyNewsPath(date));
  }catch(e){
    daily = {};
    banner(`daily_news missing for ${date}  (${e.message})`);
  }

  try{
    sent = await jget(sentimentPath(date));
  }catch(e){
    // sentimentが無い日は latest にフォールバック
    try{
      sent = await jget(sentimentPath(""));
      banner((document.getElementById("banner").hidden ? "" : document.getElementById("banner").textContent + " | ") + `sentiment for ${date} missing -> using latest`);
    }catch(e2){
      sent = {};
      banner((document.getElementById("banner").hidden ? "" : document.getElementById("banner").textContent + " | ") + `sentiment missing (${e2.message})`);
    }
  }

  renderHeadline(sent);

  const rows = buildJoinedRows(daily, sent);
  renderList(rows);

  // 0件のときのメッセージ（「表示がなくなった？」対策）
  if (rows.length === 0){
    errEl.textContent = "No articles (daily_news items is empty, or join/dedup removed all).";
  }
}

loadAll();
