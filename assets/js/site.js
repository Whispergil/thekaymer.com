/* Kaymer LLC — shared behaviour.
   Progressive enhancements: the mobile menu, apps filter, and support email copy.
   Every page renders its full content without this file. */
(function () {
  'use strict';

  /* Copy only the public support address; keep the mail link usable without JS. */
  var copyEmail = document.getElementById('copy-support-email');
  var copyStatus = document.getElementById('copy-email-status');
  if (copyEmail && copyStatus) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      copyEmail.hidden = false;
      copyEmail.addEventListener('click', async function () {
        if (copyEmail.disabled) return;
        copyEmail.disabled = true;
        copyStatus.textContent = '';
        try {
          await navigator.clipboard.writeText('support@thekaymer.com');
          copyStatus.textContent = 'Email address copied: support@thekaymer.com';
        } catch (error) {
          copyStatus.textContent = 'Could not copy automatically. Select and copy support@thekaymer.com, or use the email link.';
        } finally {
          copyEmail.disabled = false;
        }
      });
    } else {
      copyStatus.textContent = 'You can select and copy support@thekaymer.com, or use the email link.';
    }
  }

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
    var query = window.matchMedia('(min-width: 881px)');
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

    /* Two apps do not need a filter. Reveal it once the list is long enough. */
    if (cards.length < 4) return;
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

  /* ------------------------------------------------- scroll and entrance -- */
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  var motionOK = window.matchMedia('(prefers-reduced-motion: no-preference)').matches;
  if (motionOK && 'IntersectionObserver' in window) {
    Array.prototype.forEach.call(document.querySelectorAll('.rise-in'), function (node) {
      var siblings = node.parentElement.querySelectorAll('.rise-in');
      var index = Array.prototype.indexOf.call(siblings, node);
      node.style.setProperty('--d', (index * 60) + 'ms');
      node.classList.add('will-rise');
    });
    var riseObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        riseObserver.unobserve(entry.target);
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -8% 0px' });
    Array.prototype.forEach.call(document.querySelectorAll('.rise-in'), function (node) {
      riseObserver.observe(node);
    });

    Array.prototype.forEach.call(document.querySelectorAll('.rule'), function (rule) {
      rule.classList.add('will-draw');
    });
    var ruleObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var rule = entry.target;
        window.requestAnimationFrame(function () { rule.classList.add('is-drawn'); });
        ruleObserver.unobserve(rule);
      });
    }, { threshold: 0.6 });
    Array.prototype.forEach.call(document.querySelectorAll('.rule'), function (rule) {
      ruleObserver.observe(rule);
    });
  }

  /* ------------------------------------------------------ screenshot rail -- */
  Array.prototype.forEach.call(document.querySelectorAll('.shot-rail-wrap'), function (wrap) {
    var rail = wrap.querySelector('.shot-rail');
    var prev = wrap.querySelector('.shot-prev');
    var next = wrap.querySelector('.shot-next');
    var indexEl = wrap.querySelector('.shot-index');
    if (!rail || !prev || !next) return;
    var frames = Array.prototype.slice.call(rail.querySelectorAll('picture'));

    var nearest = function () {
      var railBox = rail.getBoundingClientRect();
      var railCenter = railBox.left + railBox.width / 2;
      var best = 0;
      var bestVisible = -1;
      frames.forEach(function (frame, i) {
        var box = frame.getBoundingClientRect();
        var visible = Math.min(box.right, railBox.right) - Math.max(box.left, railBox.left);
        if (visible < 0) visible = 0;
        var closer = Math.abs((box.left + box.width / 2) - railCenter);
        var bestBox = frames[best].getBoundingClientRect();
        var bestCloser = Math.abs((bestBox.left + bestBox.width / 2) - railCenter);
        if (visible > bestVisible + 1 || (Math.abs(visible - bestVisible) <= 1 && closer < bestCloser)) {
          bestVisible = visible;
          best = i;
        }
      });
      return best;
    };

    var paint = function () {
      var max = rail.scrollWidth - rail.clientWidth;
      var overflowing = max > 8;
      var index = frames.length ? nearest() : 0;
      rail.classList.toggle('is-overflowing', overflowing);
      rail.classList.toggle('is-at-end', !overflowing || index >= frames.length - 1 || rail.scrollLeft >= max - 8);
      prev.disabled = !overflowing || index <= 0;
      next.disabled = !overflowing || index >= frames.length - 1;
      if (indexEl) indexEl.textContent = String(index + 1);
    };

    var go = function (dir) {
      var i = Math.min(frames.length - 1, Math.max(0, nearest() + dir));
      var frame = frames[i];
      if (!frame) return;
      var frameBox = frame.getBoundingClientRect();
      var railBox = rail.getBoundingClientRect();
      /* Match scroll-snap-align: center. A left-edge target is closer to the
         last snap point on a wide rail, so the browser would skip a slide. */
      var delta = (frameBox.left + frameBox.width / 2) - (railBox.left + railBox.width / 2);
      rail.scrollTo({ left: rail.scrollLeft + delta, behavior: motionOK ? 'smooth' : 'auto' });
    };

    /* Lazy images have no intrinsic size yet when this deferred script runs.
       Remeasure when they decode or the rail's box changes, instead of waiting
       for the user to scroll. */
    var paintQueued = false;
    var schedulePaint = function () {
      if (paintQueued) return;
      paintQueued = true;
      window.requestAnimationFrame(function () {
        paintQueued = false;
        paint();
      });
    };

    frames.forEach(function (frame) {
      var img = frame.querySelector('img');
      if (!img || img.complete) return;
      img.addEventListener('load', schedulePaint);
    });

    if ('ResizeObserver' in window) {
      var observer = new ResizeObserver(schedulePaint);
      observer.observe(rail);
      frames.forEach(function (frame) { observer.observe(frame); });
    }

    prev.addEventListener('click', function () { go(-1); });
    next.addEventListener('click', function () { go(1); });
    rail.addEventListener('scroll', paint, { passive: true });
    rail.addEventListener('keydown', function (event) {
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
      event.preventDefault();
      go(event.key === 'ArrowRight' ? 1 : -1);
    });
    window.addEventListener('resize', schedulePaint);
    schedulePaint();
  });

}());
