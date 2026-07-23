// StayFlow - motor compartilhado de traducao (i18n).
// Usado tanto pela landing page (index.html) quanto pelo Dashboard -
// cada pagina traz seu PROPRIO dicionario de traducoes (arquivo
// separado), esse arquivo so tem a logica generica de aplicar/trocar
// idioma, pra nao duplicar a mesma engine em 2 lugares.

(function () {
  const SUPPORTED_LANGS = ["pt", "en", "es", "fr", "de"];
  const STORAGE_KEY = "stayflow_lang";

  function getInitialLang() {
    const urlLang = new URLSearchParams(window.location.search).get("lang");
    if (SUPPORTED_LANGS.includes(urlLang)) return urlLang;

    const saved = localStorage.getItem(STORAGE_KEY);
    if (SUPPORTED_LANGS.includes(saved)) return saved;

    const browser = (navigator.language || navigator.userLanguage || "en").toLowerCase();
    if (browser.startsWith("pt")) return "pt";
    if (browser.startsWith("es")) return "es";
    if (browser.startsWith("fr")) return "fr";
    if (browser.startsWith("de")) return "de";
    return "en";
  }

  function persistLang(lang) {
    localStorage.setItem(STORAGE_KEY, lang);
  }

  // Aplica um dicionario {chave: texto} de UM idioma em todos os
  // elementos [data-i18n]/[data-i18n-html] da pagina atual. Retorna o
  // idioma realmente aplicado (cai pra "en" se o pedido nao for suportado
  // ou o dicionario nao tiver esse idioma).
  function applyTranslations(translations, lang) {
    const safeLang = SUPPORTED_LANGS.includes(lang) ? lang : "en";
    const dict = (translations && translations[safeLang]) || (translations && translations.en) || {};

    document.documentElement.lang = safeLang;
    persistLang(safeLang);

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key] !== undefined) el.textContent = dict[key];
    });

    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      const key = el.getAttribute("data-i18n-html");
      if (dict[key] !== undefined) el.innerHTML = dict[key];
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (dict[key] !== undefined) el.setAttribute("placeholder", dict[key]);
    });

    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      if (dict[key] !== undefined) el.setAttribute("title", dict[key]);
    });

    document.querySelectorAll("[data-route]").forEach((link) => {
      const base = link.getAttribute("data-route");
      if (base) link.setAttribute("href", `${base}?lang=${safeLang}`);
    });

    document.querySelectorAll("[data-lang-current]").forEach((el) => {
      el.textContent = safeLang.toUpperCase();
    });

    document.querySelectorAll("[data-lang]").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-lang") === safeLang);
    });

    document.dispatchEvent(new CustomEvent("stayflow:language-changed", { detail: { lang: safeLang } }));

    return safeLang;
  }

  // Helper pra strings montadas em JS (innerHTML dinamico, alert/confirm/
  // prompt) em vez de atributo HTML - t(dict, lang, chave, fallback_pt).
  function t(translations, lang, key, fallback) {
    const safeLang = SUPPORTED_LANGS.includes(lang) ? lang : "en";
    const dict = (translations && translations[safeLang]) || {};
    if (dict[key] !== undefined) return dict[key];
    const ptDict = (translations && translations.pt) || {};
    if (ptDict[key] !== undefined) return ptDict[key];
    return fallback !== undefined ? fallback : key;
  }

  function currentLang() {
    return document.documentElement.lang || getInitialLang();
  }

  // Liga o dropdown de idioma generico: um botao "gatilho" que abre/fecha
  // um container com botoes [data-lang="xx"] dentro - mesmo padrao visual
  // ja usado pelo seletor de hostel.
  function wireLanguageSwitcher(triggerId, dropdownId, translations, onChange) {
    const trigger = document.getElementById(triggerId);
    const dropdown = document.getElementById(dropdownId);
    if (!trigger || !dropdown) return;

    // Segue o mesmo padrao ja usado pelo dropdown de hostel
    // (toggleHostelSelector): visibilidade via style.display inline,
    // nao via classe CSS - nao existe regra .open no app.css.
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
    });

    dropdown.querySelectorAll("[data-lang]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const lang = btn.getAttribute("data-lang");
        const applied = applyTranslations(translations, lang);
        dropdown.style.display = "none";
        if (typeof onChange === "function") onChange(applied);
      });
    });

    document.addEventListener("click", (event) => {
      if (dropdown.style.display === "none") return;
      if (!dropdown.contains(event.target) && !trigger.contains(event.target)) {
        dropdown.style.display = "none";
      }
    });
  }

  window.StayFlowI18n = {
    SUPPORTED_LANGS,
    getInitialLang,
    persistLang,
    applyTranslations,
    t,
    currentLang,
    wireLanguageSwitcher,
  };
})();
