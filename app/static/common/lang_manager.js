(() => {
  "use strict";

  const DEFAULT_LANG = "en";
  const STORAGE_KEY = "gp_lang";
  const LANG_CHANGED_EVENT = "gp:lang-changed";
  const SUPPORTED_LANGS = ["en", "ja", "th"];

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

  function init() {
    applyDocumentLang(readStoredLang());
  }

  init();

  const api = {
    DEFAULT_LANG,
    STORAGE_KEY,
    LANG_CHANGED_EVENT,
    normalizeLang,
    getLang,
    setLang,
    init
  };

  window.GP_LANG_MANAGER = api;
})();