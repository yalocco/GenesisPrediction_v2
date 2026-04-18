(() => {
  "use strict";

  const manager = window.GP_LANG_MANAGER || null;
  const DEFAULT_LANG = manager && manager.DEFAULT_LANG ? manager.DEFAULT_LANG : "en";
  const LANG_CHANGED_EVENT =
    manager && manager.LANG_CHANGED_EVENT ? manager.LANG_CHANGED_EVENT : "gp:lang-changed";

  const STATIC_TEXT = {
    en: {
      home: {
        eyebrow: "GenesisPrediction",
        hero_title: "Understand Global Risk. Anticipate What Comes Next.",
        hero_subtitle: "Daily global signals, structured into decision-grade insight.",
        hero_meta: "From observation to prediction — no noise, no guesswork.",
        routes_title: "Start here",
        routes_hint: "Choose the next view based on what you need.",
        route_digest_label: "Understand",
        route_digest_title: "Understand the World",
        route_digest_sub: "See what is happening across global events today.",
        route_digest_cta: "View Digest →",
        route_overlay_label: "Detect",
        route_overlay_title: "Detect Key Signals",
        route_overlay_sub: "Identify shifts, risks, and underlying pressures.",
        route_overlay_cta: "View Signals →",
        route_prediction_label: "Decide",
        route_prediction_title: "Make Decisions",
        route_prediction_sub: "See structured scenarios and the most likely outcome.",
        route_prediction_cta: "View Prediction →",
        method_title: "How it works",
        method_hint: "The system moves from observation to decision support in layers.",
        method_flow: "Observation → Trend → Signal → Scenario → Prediction",
        method_sub: "Each layer builds on verified signals — not assumptions.",
        latest_snapshot_title: "Latest Snapshot",
        latest_snapshot_hint: "A compact view of the current system state.",
        global_status_title: "Global Status",
        events_today_title: "Events (today)",
        data_health_title: "Data Health",
        sentiment_title: "Sentiment",
        daily_summary_title: "Daily Summary",
        why_title: "Why this matters",
        why_body_1: "This system is designed for clarity, not speculation.",
        why_body_2: "Every output is traceable, structured, and explainable."
      },

      prediction: {
        hero_title: "Prediction",
        hero_sub: "Decision-grade prediction built from scenario structure, signal interpretation, and runtime context.",
        global_status_title: "Global Status",
        three_layer_title: "Three Layer Structure",
        three_layer_hint: "Signal, scenario, and prediction are shown as separate layers.",
        signal_layer_title: "Signal Layer",
        signal_layer_sub: "Signal explanation and structured watchpoints.",
        scenario_layer_title: "Scenario Layer",
        scenario_layer_sub: "Branch structure and dominant scenario context.",
        prediction_statement_title: "Prediction Statement",
        fx_summary_title: "FX Summary",
        decision_context_title: "Decision Context",
        metric_decision_line: "Decision Line",
        metric_interpretation: "Interpretation",
        metric_runtime_status: "Runtime Status"
      },

      overlay: {
        overlay_title: "Overlay",
        overlay_subtitle:
          "Overlay is a layer that connects global events with market movements. It visualizes how observed developments manifest as FX, economic conditions, and risk. The focus here is not on causes, but on the resulting shape of the market.",
        global_status: "Global Status",
        fx_decision: "FX Decision",
        decision: "Decision",
        image: "Image",
        decision_json: "Decision JSON",
        pair_prefix: "pair",
        source_prefix: "source",
        signals_prefix: "signals",
        controls: "Controls",
        pair: "Pair",
        open_decision_json: "Open decision JSON",
        reason: "Reason",
        fx_overlay: "FX Overlay",
        image_preview: "image preview",
        open_image: "Open image",
        economic_signals: "Economic Signals",
        signals_hint: "world/economy article cards",
        open_source_json: "Open source JSON",
        signals_empty: "Economic signal articles are not available. Check world_view_model_latest.json.",
        note_jpythb: "Overlay for JPYTHB (primary pair)",
        note_usdjpy: "Overlay for USDJPY",
        note_usdthb: "Overlay for USDTHB",
        note_multi: "Overlay for MULTI",
        loading: "loading...",
        ok: "OK",
        missing: "missing",
        miss: "MISS",
        partial: "partial",
        analysis_first: "analysis-first",
        files_missing: "files missing",
        decision_json_not_found: "Decision JSON not found.",
        decision_json_not_available: "Decision JSON not available.",
        decision_json_loaded_no_reason: "Decision JSON loaded, but no reason field was found.",
        untitled: "Untitled",
        summary_not_available: "Summary not available.",
        unknown_source: "Unknown source",
        as_of: "as_of"
      },
      sentiment: {
        as_of: "as_of",
        items: "items",
        rendered: "rendered",
        trend_points: "trend points"
      }
    },

    ja: {
      home: {
        eyebrow: "GenesisPrediction",
        hero_title: "世界を理解し、その先を見通す",
        hero_subtitle: "世界のシグナルを毎日整理し、意思決定レベルの洞察へ",
        hero_meta: "観測から予測へ ― ノイズも推測も排除",
        routes_title: "ここから始める",
        routes_hint: "目的に応じて次の画面を選択してください",
        route_digest_label: "理解",
        route_digest_title: "世界の状況を把握",
        route_digest_sub: "今日の世界で何が起きているかを見る",
        route_digest_cta: "ダイジェストを見る →",
        route_overlay_label: "検知",
        route_overlay_title: "重要シグナルを検知",
        route_overlay_sub: "変化・リスク・圧力を把握",
        route_overlay_cta: "シグナルを見る →",
        route_prediction_label: "判断",
        route_prediction_title: "意思決定する",
        route_prediction_sub: "構造化されたシナリオと最も可能性の高い結果を見る",
        route_prediction_cta: "予測を見る →",
        method_title: "仕組み",
        method_hint: "システムは観測から意思決定まで段階的に進む",
        method_flow: "観測 → トレンド → シグナル → シナリオ → 予測",
        method_sub: "各層は検証されたシグナルに基づく",
        latest_snapshot_title: "最新スナップショット",
        latest_snapshot_hint: "現在の状態をコンパクトに表示",
        global_status_title: "グローバルステータス",
        events_today_title: "本日のイベント",
        data_health_title: "データ状態",
        sentiment_title: "センチメント",
        daily_summary_title: "日次サマリー",
        why_title: "なぜ重要か",
        why_body_1: "このシステムは推測ではなく明確さを重視する",
        why_body_2: "すべての出力は追跡可能で構造化され説明可能"
      },

      prediction: {
        hero_title: "予測",
        hero_sub: "シナリオ構造、シグナル解釈、実行時コンテキストから構成された意思決定レベルの予測。",
        global_status_title: "グローバルステータス",
        three_layer_title: "3層構造",
        three_layer_hint: "シグナル・シナリオ・予測を分けて表示します。",
        signal_layer_title: "シグナル層",
        signal_layer_sub: "シグナル説明と構造化された監視点。",
        scenario_layer_title: "シナリオ層",
        scenario_layer_sub: "分岐構造と優勢シナリオの文脈。",
        prediction_statement_title: "予測ステートメント",
        fx_summary_title: "FXサマリー",
        decision_context_title: "判断コンテキスト",
        metric_decision_line: "判断ライン",
        metric_interpretation: "解釈",
        metric_runtime_status: "実行状態"
      },

      overlay: {
        overlay_title: "オーバーレイ",
        overlay_subtitle:
          "Overlay は世界の出来事と市場の動きを接続するレイヤです。観測された展開が FX・景気・リスクとしてどのような形で現れているかを可視化します。ここで重視するのは原因ではなく、市場に現れた結果のかたちです。",
        global_status: "グローバルステータス",
        fx_decision: "FX 判断",
        decision: "判断",
        image: "画像",
        decision_json: "判断JSON",
        pair_prefix: "ペア",
        source_prefix: "ソース",
        signals_prefix: "シグナル",
        controls: "操作",
        pair: "ペア",
        open_decision_json: "判断JSONを開く",
        reason: "理由",
        fx_overlay: "FX オーバーレイ",
        image_preview: "画像プレビュー",
        open_image: "画像を開く",
        economic_signals: "経済シグナル",
        signals_hint: "world/economy 記事カード",
        open_source_json: "ソースJSONを開く",
        signals_empty: "経済シグナル記事はありません。world_view_model_latest.json を確認してください。",
        note_jpythb: "JPYTHB 用オーバーレイ（主対象ペア）",
        note_usdjpy: "USDJPY 用オーバーレイ",
        note_usdthb: "USDTHB 用オーバーレイ",
        note_multi: "MULTI 用オーバーレイ",
        loading: "読み込み中...",
        ok: "OK",
        missing: "欠落",
        miss: "欠落",
        partial: "一部のみ",
        analysis_first: "analysis優先",
        files_missing: "ファイル不足",
        decision_json_not_found: "判断JSONが見つかりません。",
        decision_json_not_available: "判断JSONはまだ利用できません。",
        decision_json_loaded_no_reason: "判断JSONは読み込めましたが、理由フィールドが見つかりませんでした。",
        untitled: "無題",
        summary_not_available: "要約はありません。",
        unknown_source: "不明なソース",
        as_of: "as_of"
      },
      sentiment: {
        as_of: "時点",
        items: "件数",
        rendered: "表示",
        trend_points: "トレンド点"
      }
    },

    th: {
      home: {
        eyebrow: "GenesisPrediction",
        hero_title: "เข้าใจโลก และคาดการณ์สิ่งที่จะเกิดขึ้น",
        hero_subtitle: "สัญญาณโลกประจำวัน ที่จัดโครงสร้างเป็นข้อมูลเชิงตัดสินใจ",
        hero_meta: "จากการสังเกตสู่การคาดการณ์ — ไม่มีความคลุมเครือ",
        routes_title: "เริ่มต้นที่นี่",
        routes_hint: "เลือกมุมมองถัดไปตามสิ่งที่คุณต้องการ",
        route_digest_label: "เข้าใจ",
        route_digest_title: "เข้าใจสถานการณ์โลก",
        route_digest_sub: "ดูว่าเกิดอะไรขึ้นในโลกวันนี้",
        route_digest_cta: "ดูสรุป →",
        route_overlay_label: "ตรวจจับ",
        route_overlay_title: "ตรวจจับสัญญาณสำคัญ",
        route_overlay_sub: "ระบุการเปลี่ยนแปลงและความเสี่ยง",
        route_overlay_cta: "ดูสัญญาณ →",
        route_prediction_label: "ตัดสินใจ",
        route_prediction_title: "ตัดสินใจ",
        route_prediction_sub: "ดูสถานการณ์และผลลัพธ์ที่เป็นไปได้มากที่สุด",
        route_prediction_cta: "ดูการคาดการณ์ →",
        method_title: "วิธีการทำงาน",
        method_hint: "ระบบทำงานเป็นขั้นตอนจากการสังเกตสู่การตัดสินใจ",
        method_flow: "การสังเกต → แนวโน้ม → สัญญาณ → สถานการณ์ → การคาดการณ์",
        method_sub: "แต่ละขั้นสร้างบนข้อมูลที่ตรวจสอบแล้ว",
        latest_snapshot_title: "ภาพรวมล่าสุด",
        latest_snapshot_hint: "มุมมองสรุปของสถานะปัจจุบัน",
        global_status_title: "สถานะรวม",
        events_today_title: "เหตุการณ์วันนี้",
        data_health_title: "สถานะข้อมูล",
        sentiment_title: "เซนติเมนต์",
        daily_summary_title: "สรุปรายวัน",
        why_title: "ทำไมสิ่งนี้สำคัญ",
        why_body_1: "ระบบนี้เน้นความชัดเจน ไม่ใช่การคาดเดา",
        why_body_2: "ผลลัพธ์ทั้งหมดสามารถตรวจสอบและอธิบายได้"
      },

      prediction: {
        hero_title: "การคาดการณ์",
        hero_sub: "การคาดการณ์ระดับการตัดสินใจที่สร้างจากโครงสร้างสถานการณ์ การตีความสัญญาณ และบริบทขณะรันระบบ",
        global_status_title: "สถานะรวม",
        three_layer_title: "โครงสร้างสามชั้น",
        three_layer_hint: "แสดงสัญญาณ สถานการณ์ และการคาดการณ์แยกเป็นคนละชั้น",
        signal_layer_title: "ชั้นสัญญาณ",
        signal_layer_sub: "คำอธิบายสัญญาณและจุดเฝ้าระวังเชิงโครงสร้าง",
        scenario_layer_title: "ชั้นสถานการณ์",
        scenario_layer_sub: "โครงสร้างการแตกแขนงและบริบทของสถานการณ์หลัก",
        prediction_statement_title: "ข้อความคาดการณ์",
        fx_summary_title: "สรุป FX",
        decision_context_title: "บริบทการตัดสินใจ",
        metric_decision_line: "แนวการตัดสินใจ",
        metric_interpretation: "การตีความ",
        metric_runtime_status: "สถานะการทำงาน"
      },

      overlay: {
        overlay_title: "โอเวอร์เลย์",
        overlay_subtitle:
          "Overlay เป็นเลเยอร์ที่เชื่อมเหตุการณ์โลกกับการเคลื่อนไหวของตลาด โดยแสดงให้เห็นว่าพัฒนาการที่สังเกตได้ปรากฏออกมาเป็น FX ภาวะเศรษฐกิจ และความเสี่ยงอย่างไร จุดเน้นที่นี่ไม่ใช่สาเหตุ แต่เป็นรูปร่างของผลลัพธ์ที่ปรากฏในตลาด",
        global_status: "สถานะรวม",
        fx_decision: "การตัดสินใจ FX",
        decision: "การตัดสินใจ",
        image: "ภาพ",
        decision_json: "Decision JSON",
        pair_prefix: "คู่",
        source_prefix: "แหล่งที่มา",
        signals_prefix: "สัญญาณ",
        controls: "การควบคุม",
        pair: "คู่เงิน",
        open_decision_json: "เปิด Decision JSON",
        reason: "เหตุผล",
        fx_overlay: "FX Overlay",
        image_preview: "ตัวอย่างภาพ",
        open_image: "เปิดภาพ",
        economic_signals: "สัญญาณเศรษฐกิจ",
        signals_hint: "การ์ดบทความ world/economy",
        open_source_json: "เปิด Source JSON",
        signals_empty: "ยังไม่มีบทความสัญญาณเศรษฐกิจ โปรดตรวจสอบ world_view_model_latest.json",
        note_jpythb: "โอเวอร์เลย์สำหรับ JPYTHB (คู่หลัก)",
        note_usdjpy: "โอเวอร์เลย์สำหรับ USDJPY",
        note_usdthb: "โอเวอร์เลย์สำหรับ USDTHB",
        note_multi: "โอเวอร์เลย์สำหรับ MULTI",
        loading: "กำลังโหลด...",
        ok: "OK",
        missing: "ไม่มี",
        miss: "MISS",
        partial: "บางส่วน",
        analysis_first: "ใช้ analysis ก่อน",
        files_missing: "ไฟล์ไม่ครบ",
        decision_json_not_found: "ไม่พบ Decision JSON",
        decision_json_not_available: "Decision JSON ยังไม่พร้อมใช้งาน",
        decision_json_loaded_no_reason: "โหลด Decision JSON ได้แล้ว แต่ไม่พบฟิลด์เหตุผล",
        untitled: "ไม่มีชื่อเรื่อง",
        summary_not_available: "ไม่มีสรุป",
        unknown_source: "ไม่ทราบแหล่งที่มา",
        as_of: "as_of"
      },
      sentiment: {
        as_of: "ณ วันที่",
        items: "จำนวน",
        rendered: "แสดงผล",
        trend_points: "จุดแนวโน้ม"
      }
    }
  };

  function normalizeLang(lang) {
    if (manager && typeof manager.normalizeLang === "function") {
      return manager.normalizeLang(lang);
    }
    const value = String(lang || "").trim().toLowerCase();
    return ["en", "ja", "th"].includes(value) ? value : DEFAULT_LANG;
  }

  function getLang() {
    if (manager && typeof manager.getLang === "function") {
      return manager.getLang();
    }
    return normalizeLang(window.GP_LANG || DEFAULT_LANG);
  }

  function setLang(lang) {
    if (manager && typeof manager.setLang === "function") {
      return manager.setLang(lang);
    }
    const nextLang = normalizeLang(lang);
    window.GP_LANG = nextLang;
    if (document && document.documentElement) {
      document.documentElement.lang = nextLang;
    }
    return nextLang;
  }

  function safeObject(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : null;
  }

  function safeString(value) {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value).trim();
  }

  function safeArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function translate(table, key, lang = null) {
    const activeLang = normalizeLang(lang || getLang());
    const source = safeObject(table) || {};
    const bucket = safeObject(source[activeLang]) || safeObject(source[DEFAULT_LANG]) || {};
    const fallbackBucket = safeObject(source[DEFAULT_LANG]) || {};
    return bucket[key] || fallbackBucket[key] || key;
  }

  function resolveDottedKey(source, key) {
    const parts = String(key || "").split(".").filter(Boolean);
    let node = source;
    for (const part of parts) {
      if (!node || typeof node !== "object" || !(part in node)) {
        return "";
      }
      node = node[part];
    }
    return typeof node === "string" ? node : "";
  }

  function t(key, lang = null, fallback = "") {
    const activeLang = normalizeLang(lang || getLang());
    const preferred = resolveDottedKey(STATIC_TEXT[activeLang] || {}, key);
    if (preferred) return preferred;
    const def = resolveDottedKey(STATIC_TEXT[DEFAULT_LANG] || {}, key);
    if (def) return def;
    return safeString(fallback) || safeString(key);
  }

  function createTranslator(table) {
    return function tr(key, lang = null) {
      return translate(table, key, lang);
    };
  }

  function applyStaticUiText(root, table, options = {}) {
    const targetRoot = root || document;
    if (!targetRoot || typeof targetRoot.querySelectorAll !== "function") {
      return;
    }

    const tr = createTranslator(table || STATIC_TEXT);
    const attr = safeString(options.attribute) || "data-ui-text";
    const activeLang = normalizeLang(options.lang || getLang());

    if (document && document.documentElement) {
      document.documentElement.lang = activeLang;
    }

    targetRoot.querySelectorAll(`[${attr}]`).forEach((node) => {
      const key = node.getAttribute(attr);
      if (!key) {
        return;
      }
      node.textContent = t(key, activeLang, key);
    });
  }

  function pickText(obj, key, lang = null) {
    const target = safeObject(obj);
    if (!target) {
      return "";
    }

    const activeLang = normalizeLang(lang || getLang());
    const i18nKey = `${key}_i18n`;
    const i18n = safeObject(target[i18nKey]);

    if (i18n) {
      const preferred = safeString(i18n[activeLang]);
      if (preferred) return preferred;
      const english = safeString(i18n.en);
      if (english) return english;
      const japanese = safeString(i18n.ja);
      if (japanese) return japanese;
      const thai = safeString(i18n.th);
      if (thai) return thai;
    }

    return safeString(target[key]);
  }

  function pickList(obj, key, lang = null) {
    const target = safeObject(obj);
    if (!target) return [];

    const activeLang = normalizeLang(lang || getLang());
    const i18nKey = `${key}_i18n`;
    const i18n = safeObject(target[i18nKey]);

    if (i18n) {
      const preferred = safeArray(i18n[activeLang]).map((item) => safeString(item)).filter(Boolean);
      if (preferred.length > 0) return preferred;
      const english = safeArray(i18n.en).map((item) => safeString(item)).filter(Boolean);
      if (english.length > 0) return english;
      const japanese = safeArray(i18n.ja).map((item) => safeString(item)).filter(Boolean);
      if (japanese.length > 0) return japanese;
      const thai = safeArray(i18n.th).map((item) => safeString(item)).filter(Boolean);
      if (thai.length > 0) return thai;
    }

    return safeArray(target[key]).map((item) => safeString(item)).filter(Boolean);
  }

  function pickField(value, lang = null) {
    const activeLang = normalizeLang(lang || getLang());

    if (Array.isArray(value)) {
      return value.map((item) => pickField(item, activeLang));
    }

    if (value && typeof value === "object") {
      const asLangMap =
        ("en" in value || "ja" in value || "th" in value) &&
        !Array.isArray(value.en) &&
        !Array.isArray(value.ja) &&
        !Array.isArray(value.th);

      if (asLangMap) {
        const preferred = safeString(value[activeLang]);
        if (preferred) return preferred;
        return safeString(value.en) || safeString(value.ja) || safeString(value.th) || "";
      }
    }

    return value;
  }

  function pickI18n(value, fallback = "", lang = null) {
    const activeLang = normalizeLang(lang || getLang());

    if (value === null || value === undefined) {
      return safeString(fallback);
    }

    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      return safeString(value);
    }

    if (Array.isArray(value)) {
      return value.map((item) => pickI18n(item, "", activeLang)).filter(Boolean).join(" / ");
    }

    if (typeof value === "object") {
      const preferred = safeString(value[activeLang]);
      if (preferred) return preferred;
      const english = safeString(value.en);
      if (english) return english;
      const japanese = safeString(value.ja);
      if (japanese) return japanese;
      const thai = safeString(value.th);
      if (thai) return thai;
    }

    return safeString(fallback);
  }

  function pickI18nList(value, lang = null) {
    const activeLang = normalizeLang(lang || getLang());

    if (!value) return [];

    if (Array.isArray(value)) {
      return value
        .map((item) => {
          if (typeof item === "string") return safeString(item);
          if (Array.isArray(item)) {
            return item.map((nested) => pickI18n(nested, "", activeLang)).filter(Boolean).join(" / ");
          }
          if (item && typeof item === "object") {
            const directText = pickI18n(item, "", activeLang);
            if (directText) return directText;
            return item;
          }
          return "";
        })
        .filter(Boolean);
    }

    if (typeof value === "object") {
      const preferred = safeArray(value[activeLang]);
      if (preferred.length > 0) return preferred;
      const english = safeArray(value.en);
      if (english.length > 0) return english;
      const japanese = safeArray(value.ja);
      if (japanese.length > 0) return japanese;
      const thai = safeArray(value.th);
      if (thai.length > 0) return thai;
    }

    return [];
  }

  const api = {
    defaultLang: DEFAULT_LANG,
    events: {
      langChanged: LANG_CHANGED_EVENT
    },
    STATIC_TEXT,
    normalizeLang,
    getLang,
    setLang,
    translate,
    t,
    createTranslator,
    applyStaticUiText,
    pickText,
    pickList,
    pickField,
    pickI18n,
    pickI18nList,
    safeArray,
    safeObject,
    safeString
  };

  window.GP_I18N = api;
  window.GenesisI18n = api;
})();
