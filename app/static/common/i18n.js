(() => {
  "use strict";
  items: { en: "items", ja: "件数", th: "จำนวน" },
    rendered: { en: "rendered", ja: "表示", th: "แสดงผล" },
    trend_points: { en: "trend points", ja: "トレンド点", th: "จุดแนวโน้ม" }
  },

  const manager = window.GP_LANG_MANAGER || null;
  const DEFAULT_LANG = manager && manager.DEFAULT_LANG ? manager.DEFAULT_LANG : "en";
  const LANG_CHANGED_EVENT =
    manager && manager.LANG_CHANGED_EVENT ? manager.LANG_CHANGED_EVENT : "gp:lang-changed";

  const STATIC_TEXT = {
  sentiment: {
    as_of: { en: "as_of", ja: "時点", th: "ณ วันที่" },
    items: { en: "items", ja: "件数", th: "จำนวน" },
    rendered: { en: "rendered", ja: "表示", th: "แสดงผล" },
    trend_points: { en: "trend points", ja: "トレンド点", th: "จุดแนวโน้ม" }
  },
    en: {
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
      }
    },
    ja: {
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
      }
    },
    th: {
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

    const tr = createTranslator(table);
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
      node.textContent = tr(key, activeLang);
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
