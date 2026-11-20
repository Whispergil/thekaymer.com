/* Kaymer LLC — cookie notice and Google Analytics 4 loader.
   Google's script is never downloaded until the visitor clicks Accept.
   The Measurement ID is set in GA_MEASUREMENT_ID only. */
(function () {
  'use strict';

  var GA_MEASUREMENT_ID = 'G-70J3CD3SYM';
  /* If this constant is ever set back to the placeholder, gtag is not loaded. */
  var GA_PLACEHOLDER_ID = 'G-XXXXXXXXXX';

  var STORAGE_KEY = 'kaymer-consent';
  var gaLoaded = false;

  function hasMeasurementId() {
    return GA_MEASUREMENT_ID !== GA_PLACEHOLDER_ID &&
      /^G-[A-Z0-9]+$/.test(GA_MEASUREMENT_ID);
  }

  function readChoice() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (data && (data.status === 'granted' || data.status === 'denied')) {
        return data;
      }
    } catch (err) {
      /* localStorage can be blocked; treat as no stored choice. */
    }
    return null;
  }

  function saveChoice(status) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        status: status,
        date: new Date().toISOString()
      }));
    } catch (err) {
      /* Ignore quota or access errors; the choice still applies this visit. */
    }
  }

  function deleteGaCookies() {
    var cookies = document.cookie ? document.cookie.split(';') : [];
    var host = window.location.hostname;
    var domains = ['', host, '.' + host];
    var i, j, name, domain, parts;
    for (i = 0; i < cookies.length; i += 1) {
      name = cookies[i].split('=')[0].trim();
      if (name !== '_ga' && name.indexOf('_ga_') !== 0 && name !== '_gid' && name !== '_gat') {
        continue;
      }
      for (j = 0; j < domains.length; j += 1) {
        domain = domains[j] ? '; domain=' + domains[j] : '';
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + domain;
      }
    }
    /* Also clear a typical GA cookie path in case one was set with subpaths. */
    parts = window.location.pathname.split('/');
    while (parts.length > 1) {
      parts.pop();
      var path = parts.join('/') || '/';
      document.cookie = '_ga=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=' + path;
    }
  }

  function loadGoogleAnalytics() {
    if (gaLoaded || !hasMeasurementId()) return;
    gaLoaded = true;

    window.dataLayer = window.dataLayer || [];
    function gtag() { window.dataLayer.push(arguments); }
    window.gtag = gtag;

    gtag('consent', 'default', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: 'denied'
    });
    gtag('consent', 'update', { analytics_storage: 'granted' });
    gtag('js', new Date());
    gtag('config', GA_MEASUREMENT_ID, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false
    });

    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_MEASUREMENT_ID);
    document.head.appendChild(script);
  }

  function hasGlobalPrivacyControl() {
    return navigator.globalPrivacyControl === true;
  }

  function setBannerHeight(banner) {
    var height = banner && !banner.hidden ? banner.offsetHeight : 0;
    document.documentElement.style.setProperty('--cookie-banner-height', height + 'px');
    document.body.classList.toggle('has-cookie-banner', height > 0);
  }

  function hideBanner(banner) {
    banner.hidden = true;
    setBannerHeight(banner);
  }

  function showBanner(banner, moveFocus) {
    banner.hidden = false;
    setBannerHeight(banner);
    if (moveFocus) {
      var title = document.getElementById('cookie-banner-title');
      if (title && typeof title.focus === 'function') {
        title.focus();
      }
    }
  }

  function accept(banner) {
    saveChoice('granted');
    hideBanner(banner);
    loadGoogleAnalytics();
  }

  function decline(banner) {
    saveChoice('denied');
    hideBanner(banner);
    deleteGaCookies();
    if (typeof window.gtag === 'function') {
      window.gtag('consent', 'update', { analytics_storage: 'denied' });
    }
  }

  function buildBanner() {
    var banner = document.createElement('div');
    banner.className = 'cookie-banner';
    banner.id = 'cookie-banner';
    banner.setAttribute('role', 'region');
    banner.setAttribute('aria-labelledby', 'cookie-banner-title');
    banner.hidden = true;
    banner.innerHTML =
      '<div class="shell cookie-banner__inner">' +
        '<div class="cookie-banner__copy">' +
          '<p class="cookie-banner__title" id="cookie-banner-title" tabindex="-1">We\'d like to count visits.</p>' +
          '<p class="cookie-banner__text cookie-banner__text--full">With your OK, we use Google Analytics cookies to see which pages are useful. No ads, and nothing is tracked unless you accept. <a href="/privacy/#s-4-analytics-and-cookies">Privacy Policy</a></p>' +
          '<p class="cookie-banner__text cookie-banner__text--short">We use Google Analytics cookies, only if you accept, to see which pages help. No ads. <a href="/privacy/#s-4-analytics-and-cookies">Privacy</a></p>' +
        '</div>' +
        '<div class="cookie-banner__actions">' +
          '<button type="button" class="btn btn--secondary btn--sm" data-cookie-decline>Decline</button>' +
          '<button type="button" class="btn btn--secondary btn--sm" data-cookie-accept>Accept</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(banner);

    banner.querySelector('[data-cookie-accept]').addEventListener('click', function () {
      accept(banner);
    });
    banner.querySelector('[data-cookie-decline]').addEventListener('click', function () {
      decline(banner);
    });

    window.addEventListener('resize', function () {
      if (!banner.hidden) setBannerHeight(banner);
    });

    return banner;
  }

  function bindCookieSettings(banner) {
    document.addEventListener('click', function (event) {
      var link = event.target.closest('[data-cookie-settings]');
      if (!link) return;
      event.preventDefault();
      showBanner(banner, true);
    });
  }

  function init() {
    var banner = buildBanner();
    bindCookieSettings(banner);

    var choice = readChoice();
    if (choice && choice.status === 'granted') {
      hideBanner(banner);
      loadGoogleAnalytics();
      return;
    }
    if (choice && choice.status === 'denied') {
      hideBanner(banner);
      deleteGaCookies();
      return;
    }
    if (hasGlobalPrivacyControl()) {
      saveChoice('denied');
      hideBanner(banner);
      return;
    }
    showBanner(banner);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
