(() => {
  "use strict";

  const DEFAULT_LANG = "en";
  const STORAGE_KEY = "gp_lang";
  const LANG_CHANGED_EVENT = "gp:lang-changed";
  const SUPPORTED_LANGS = ["en", "ja", "th"];
  const TRANSLATIONS = Object.create(null);

  function normalizeLang(lang) {
    const value = String(lang || "").trim().toLowerCase();
    return SUPPORTED_LANGS.includes(value) ? value : DEFAULT_LANG;
  }

  function readStoredLang() {
    try {
      return normalizeLang(window.localStorage.getItem(STORAGE_KEY));
    } catch (_error) {
      return DEFAULT_LANG;
    }
  }

  function getLang() {
    return normalizeLang(window.GP_LANG || readStoredLang() || DEFAULT_LANG);
  }

  function writeStoredLang(lang) {
    try {
      window.localStorage.setItem(STORAGE_KEY, normalizeLang(lang));
    } catch (_error) {
      // ignore storage failure
    }
  }

  function applyDocumentLang(lang) {
    const activeLang = normalizeLang(lang);
    window.GP_LANG = activeLang;
    if (document && document.documentElement) {
      document.documentElement.lang = activeLang;
    }
    return activeLang;
  }

  function emitLangChanged(nextLang, previousLang) {
    const detail = {
      lang: normalizeLang(nextLang),
      previousLang: normalizeLang(previousLang)
    };

    document.dispatchEvent(new CustomEvent(LANG_CHANGED_EVENT, { detail }));
    window.dispatchEvent(new CustomEvent(LANG_CHANGED_EVENT, { detail }));
  }

  function setLang(lang, options = {}) {
    const nextLang = normalizeLang(lang);
    const previousLang = getLang();
    const skipEvent = Boolean(options && options.skipEvent);

    writeStoredLang(nextLang);
    applyDocumentLang(nextLang);

    if (!skipEvent && nextLang !== previousLang) {
      emitLangChanged(nextLang, previousLang);
    }

    return nextLang;
  }

  function safeObject(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : null;
  }

  function mergeTranslations(target, source) {
    const dst = safeObject(target) || {};
    const src = safeObject(source) || {};
    Object.keys(src).forEach((key) => {
      const existing = safeObject(dst[key]);
      const incoming = safeObject(src[key]);
      if (existing && incoming) {
        dst[key] = mergeTranslations({ ...existing }, incoming);
      } else {
        dst[key] = incoming || src[key];
      }
    });
    return dst;
  }

  function registerTranslations(namespace, table) {
    const key = String(namespace || "global").trim() || "global";
    const current = safeObject(TRANSLATIONS[key]) || {};
    TRANSLATIONS[key] = mergeTranslations(current, table);
    return TRANSLATIONS[key];
  }

  function resolveKey(key) {
    const raw = String(key || "").trim();
    if (!raw) {
      return null;
    }

    const dot = raw.indexOf(".");
    if (dot === -1) {
      return {
        namespace: "global",
        token: raw
      };
    }

    return {
      namespace: raw.slice(0, dot),
      token: raw.slice(dot + 1)
    };
  }

  function t(key, fallback = "", lang = null) {
    const resolved = resolveKey(key);
    const activeLang = normalizeLang(lang || getLang());
    const fallbackText = String(fallback || "");

    if (!resolved) {
      return fallbackText || String(key || "");
    }

    const bucket = safeObject(TRANSLATIONS[resolved.namespace]) || {};
    const entry = safeObject(bucket[resolved.token]);

    if (!entry) {
      return fallbackText || resolved.token || String(key || "");
    }

    return (
      entry[activeLang] ||
      entry[DEFAULT_LANG] ||
      entry.ja ||
      entry.th ||
      fallbackText ||
      resolved.token
    );
  }

  function init() {
    applyDocumentLang(readStoredLang());
  }

  init();

  const api = {
    DEFAULT_LANG,
    STORAGE_KEY,
    LANG_CHANGED_EVENT,
    SUPPORTED_LANGS: [...SUPPORTED_LANGS],
    normalizeLang,
    getLang,
    setLang,
    init,
    registerTranslations,
    t
  };

  window.GP_LANG_MANAGER = api;
})();
