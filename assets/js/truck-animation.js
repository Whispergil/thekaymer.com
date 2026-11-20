/*
 * Decorative truck-loading animation for the Truck Load Calculator page.
 *
 * - A static SVG frame is in the HTML, so the page looks complete without JS.
 * - The self-hosted Lottie player and animation JSON are only fetched when the
 *   animation is about to scroll into view, and never when the visitor prefers
 *   reduced motion. Nothing here blocks the calculator or page load.
 * - The animation pauses while it is offscreen.
 */
(function () {
  'use strict';
  var box = document.querySelector('[data-truck-anim]');
  if (!box || !('IntersectionObserver' in window)) return;

  var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var stage = box.querySelector('[data-truck-anim-stage]');
  var anim = null;
  var loading = false;
  var visible = false;

  function motionOK() { return !(reduce && reduce.matches); }

  function sync() {
    if (!anim) return;
    if (visible && motionOK() && !document.hidden) {
      box.classList.add('is-playing');
      anim.play();
    } else {
      anim.pause();
      if (!motionOK()) box.classList.remove('is-playing');
    }
  }

  function start() {
    if (anim || loading || !motionOK()) return;
    loading = true;
    var s = document.createElement('script');
    s.src = box.getAttribute('data-player');
    s.async = true;
    s.onload = function () {
      if (!window.lottie) return;
      anim = window.lottie.loadAnimation({
        container: stage,
        renderer: 'svg',
        loop: true,
        autoplay: false,
        path: box.getAttribute('data-src'),
        rendererSettings: { preserveAspectRatio: 'xMidYMid meet', progressiveLoad: true }
      });
      anim.addEventListener('DOMLoaded', sync);
    };
    s.onerror = function () { loading = false; };
    document.head.appendChild(s);
  }

  new IntersectionObserver(function (entries) {
    visible = entries[0].isIntersecting;
    if (visible) start();
    sync();
  }, { rootMargin: '200px 0px' }).observe(box);

  document.addEventListener('visibilitychange', sync);
  if (reduce) {
    var onChange = function () { if (motionOK()) start(); sync(); };
    if (reduce.addEventListener) reduce.addEventListener('change', onChange);
    else if (reduce.addListener) reduce.addListener(onChange);
  }
})();
