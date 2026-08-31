/* Kaymer LLC — shared behaviour.
   Two progressive enhancements only: the mobile menu and the apps filter.
   Every page renders its full content without this file. */
(function () {
  'use strict';

  /* ------------------------------------------------------- mobile menu -- */
  var toggle = document.querySelector('.nav-toggle');
  var menu = document.getElementById('site-menu');

  if (toggle && menu) {
    var menuLinks = Array.prototype.slice.call(menu.querySelectorAll('a'));
    var closeTimer = null;
    var closeDelay = 240;
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    var setInteractive = function (interactive) {
      if (interactive) {
        menu.removeAttribute('inert');
        menu.removeAttribute('aria-hidden');
        menuLinks.forEach(function (link) {
          if (!link.hasAttribute('data-menu-tabindex')) return;
          var previous = link.getAttribute('data-menu-tabindex');
          if (previous) link.setAttribute('tabindex', previous);
          else link.removeAttribute('tabindex');
          link.removeAttribute('data-menu-tabindex');
        });
        return;
      }

      menu.setAttribute('inert', '');
      menu.setAttribute('aria-hidden', 'true');
      menuLinks.forEach(function (link) {
        if (!link.hasAttribute('data-menu-tabindex')) {
          link.setAttribute('data-menu-tabindex', link.getAttribute('tabindex') || '');
        }
        link.setAttribute('tabindex', '-1');
      });
    };

    var finishClose = function () {
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      menu.classList.remove('is-closing');
      menu.hidden = true;
    };

    var cancelClose = function () {
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      menu.classList.remove('is-closing');
    };

    menu.hidden = true;
    setInteractive(false);

    var open = function () {
      cancelClose();
      menu.hidden = false;
      setInteractive(true);
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Close menu');
      menu.classList.add('is-open');
      document.body.classList.add('is-menu-open');
    };

    var close = function (restoreFocus, immediate) {
      if (toggle.getAttribute('aria-expanded') !== 'true') {
        if (immediate && menu.classList.contains('is-closing')) finishClose();
        if (restoreFocus) toggle.focus();
        return;
      }

      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open menu');
      menu.classList.remove('is-open');
      document.body.classList.remove('is-menu-open');
      setInteractive(false);
      if (restoreFocus) toggle.focus();

      if (immediate || reducedMotion.matches) {
        finishClose();
        return;
      }

      menu.classList.add('is-closing');
      closeTimer = window.setTimeout(finishClose, closeDelay);
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
      if (!menuLinks.length) return;
      var last = menuLinks[menuLinks.length - 1];
      if (!event.shiftKey && event.target === last) {
        event.preventDefault();
        toggle.focus();
      }
    });

    menu.addEventListener('animationend', function (event) {
      if (event.target === menu && menu.classList.contains('is-closing')) {
        finishClose();
      }
    });

    var onMotionChange = function (event) {
      if (event.matches && menu.classList.contains('is-closing')) finishClose();
    };
    if (reducedMotion.addEventListener) reducedMotion.addEventListener('change', onMotionChange);
    else if (reducedMotion.addListener) reducedMotion.addListener(onMotionChange);

    /* Returning to the desktop breakpoint discards the mobile state. */
    var query = window.matchMedia('(min-width: 861px)');
    var onChange = function (event) { if (event.matches) close(false, true); };
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
