/* Kaymer LLC — shared behaviour.
   Two progressive enhancements only: the mobile menu and the apps filter.
   Every page renders its full content without this file. */
(function () {
  'use strict';

  /* ------------------------------------------------------- mobile menu -- */
  var toggle = document.querySelector('.nav-toggle');
  var menu = document.getElementById('site-menu');

  if (toggle && menu) {
    var open = function () {
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Close menu');
      menu.classList.add('is-open');
      document.body.classList.add('is-menu-open');
    };

    var close = function (restoreFocus) {
      if (toggle.getAttribute('aria-expanded') !== 'true') return;
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open menu');
      menu.classList.remove('is-open');
      document.body.classList.remove('is-menu-open');
      if (restoreFocus) toggle.focus();
    };

    var isOpen = function () {
      return toggle.getAttribute('aria-expanded') === 'true';
    };

    toggle.addEventListener('click', function () {
      if (isOpen()) close(false); else open();
    });

    /* Escape closes and returns focus to the control that opened the menu. */
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && isOpen()) close(true);
    });

    /* Selecting a destination closes the menu. */
    menu.addEventListener('click', function (event) {
      if (event.target.closest('a')) close(false);
    });

    /* A click outside the header closes it. */
    document.addEventListener('click', function (event) {
      if (!isOpen()) return;
      if (event.target.closest('.site-header')) return;
      close(false);
    });

    /* Tabbing past the last menu link wraps back to the toggle, so focus can
       never land on page content hidden behind the open panel. */
    menu.addEventListener('keydown', function (event) {
      if (event.key !== 'Tab' || !isOpen()) return;
      var links = menu.querySelectorAll('a');
      if (!links.length) return;
      var last = links[links.length - 1];
      if (!event.shiftKey && event.target === last) {
        event.preventDefault();
        toggle.focus();
      }
    });

    /* Returning to the desktop breakpoint discards the mobile state. */
    var query = window.matchMedia('(min-width: 861px)');
    var onChange = function (event) { if (event.matches) close(false); };
    if (query.addEventListener) query.addEventListener('change', onChange);
    else if (query.addListener) query.addListener(onChange);
  }

  /* --------------------------------------------------------- app filter -- */
  var filterBar = document.querySelector('.filter-bar');
  var cardList = document.getElementById('app-list');

  if (filterBar && cardList) {
    var status = document.getElementById('filter-status');
    var cards = Array.prototype.slice.call(cardList.querySelectorAll('[data-status]'));
    var buttons = Array.prototype.slice.call(filterBar.querySelectorAll('button[data-filter]'));

    filterBar.hidden = false;

    var apply = function (value) {
      var shown = 0;

      cards.forEach(function (card) {
        var match = value === 'all' || card.getAttribute('data-status') === value;
        card.hidden = !match;
        if (match) shown++;
      });

      buttons.forEach(function (button) {
        button.setAttribute('aria-pressed', String(button.getAttribute('data-filter') === value));
      });

      if (status) {
        status.textContent = shown === 1
          ? 'Showing 1 app.'
          : 'Showing ' + shown + ' apps.';
      }
    };

    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        apply(button.getAttribute('data-filter'));
      });
    });

    apply('all');
  }
}());
