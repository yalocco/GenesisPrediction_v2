(() => {
  "use strict";

  const manager = window.GP_LANG_MANAGER || null;
  const DEFAULT_LANG = manager && manager.DEFAULT_LANG ? manager.DEFAULT_LANG : "en";
  const LANG_CHANGED_EVENT =
    manager && manager.LANG_CHANGED_EVENT ? manager.LANG_CHANGED_EVENT : "gp:lang-changed";

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
      if (preferred) {
        return preferred;
      }

      const english = safeString(i18n.en);
      if (english) {
        return english;
      }

      const japanese = safeString(i18n.ja);
      if (japanese) {
        return japanese;
      }

      const thai = safeString(i18n.th);
      if (thai) {
        return thai;
      }
    }

    return safeString(target[key]);
  }

  function pickList(obj, key, lang = null) {
    const target = safeObject(obj);
    if (!target) {
      return [];
    }

    const activeLang = normalizeLang(lang || getLang());
    const i18nKey = `${key}_i18n`;
    const i18n = safeObject(target[i18nKey]);

    if (i18n) {
      const preferred = safeArray(i18n[activeLang]).map((item) => safeString(item)).filter(Boolean);
      if (preferred.length > 0) {
        return preferred;
      }

      const english = safeArray(i18n.en).map((item) => safeString(item)).filter(Boolean);
      if (english.length > 0) {
        return english;
      }

      const japanese = safeArray(i18n.ja).map((item) => safeString(item)).filter(Boolean);
      if (japanese.length > 0) {
        return japanese;
      }

      const thai = safeArray(i18n.th).map((item) => safeString(item)).filter(Boolean);
      if (thai.length > 0) {
        return thai;
      }
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
        if (preferred) {
          return preferred;
        }

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
      if (preferred) {
        return preferred;
      }

      const english = safeString(value.en);
      if (english) {
        return english;
      }

      const japanese = safeString(value.ja);
      if (japanese) {
        return japanese;
      }

      const thai = safeString(value.th);
      if (thai) {
        return thai;
      }
    }

    return safeString(fallback);
  }

  function pickI18nList(value, lang = null) {
    const activeLang = normalizeLang(lang || getLang());

    if (!value) {
      return [];
    }

    if (Array.isArray(value)) {
      return value
        .map((item) => {
          if (typeof item === "string") {
            return safeString(item);
          }
          if (Array.isArray(item)) {
            return item.map((nested) => pickI18n(nested, "", activeLang)).filter(Boolean).join(" / ");
          }
          if (item && typeof item === "object") {
            const directText = pickI18n(item, "", activeLang);
            if (directText) {
              return directText;
            }
            return item;
          }
          return "";
        })
        .filter(Boolean);
    }

    if (typeof value === "object") {
      const preferred = safeArray(value[activeLang]);
      if (preferred.length > 0) {
        return preferred;
      }

      const english = safeArray(value.en);
      if (english.length > 0) {
        return english;
      }

      const japanese = safeArray(value.ja);
      if (japanese.length > 0) {
        return japanese;
      }

      const thai = safeArray(value.th);
      if (thai.length > 0) {
        return thai;
      }
    }

    return [];
  }

  const api = {
    defaultLang: DEFAULT_LANG,
    events: {
      langChanged: LANG_CHANGED_EVENT
    },
    normalizeLang,
    getLang,
    setLang,
    translate,
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