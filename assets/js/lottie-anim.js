/*
 * Decorative Lottie animations (Truck Load Calculator page, Findry page hero).
 *
 * Markup:
 *   <div data-lottie-anim data-player=".../lottie_light.min.js" data-src=".../anim.json" aria-hidden="true">
 *     <img src=".../still.svg" alt="">            static frame, shown without JS / with reduced motion
 *     <div data-lottie-stage></div>               the player renders here
 *   </div>
 *
 * - The self-hosted player and each animation JSON are only fetched when that
 *   animation is about to scroll into view, and never when the visitor prefers
 *   reduced motion. Nothing here blocks page load or the calculators.
 * - The container gets .is-playing once the animation is showing.
 * - Animations pause while offscreen or while the tab is hidden.
 */
(function () {
  'use strict';
  var boxes = document.querySelectorAll('[data-lottie-anim]');
  if (!boxes.length || !('IntersectionObserver' in window)) return;

  var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var items = [];
  var player = null;          // 'loading' | 'ready' | null
  var waiting = [];

  function motionOK() { return !(reduce && reduce.matches); }

  function withPlayer(src, cb) {
    if (player === 'ready') { cb(); return; }
    waiting.push(cb);
    if (player === 'loading') return;
    player = 'loading';
    var s = document.createElement('script');
    s.src = src;
    s.async = true;
    s.onload = function () {
      player = window.lottie ? 'ready' : null;
      var queue = waiting; waiting = [];
      if (player) queue.forEach(function (fn) { fn(); });
    };
    s.onerror = function () { player = null; waiting = []; };
    document.head.appendChild(s);
  }

  function sync(item) {
    if (!item.anim) return;
    if (item.visible && motionOK() && !document.hidden) {
      item.box.classList.add('is-playing');
      item.anim.play();
    } else {
      item.anim.pause();
      if (!motionOK()) item.box.classList.remove('is-playing');
    }
  }

  function start(item) {
    if (item.anim || item.loading || !motionOK()) return;
    item.loading = true;
    withPlayer(item.box.getAttribute('data-player'), function () {
      item.anim = window.lottie.loadAnimation({
        container: item.box.querySelector('[data-lottie-stage]'),
        renderer: 'svg',
        loop: true,
        autoplay: false,
        path: item.box.getAttribute('data-src'),
        rendererSettings: { preserveAspectRatio: 'xMidYMid meet', progressiveLoad: true }
      });
      item.anim.addEventListener('DOMLoaded', function () { sync(item); });
    });
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      for (var i = 0; i < items.length; i++) {
        if (items[i].box === entry.target) {
          items[i].visible = entry.isIntersecting;
          if (entry.isIntersecting) start(items[i]);
          sync(items[i]);
        }
      }
    });
  }, { rootMargin: '200px 0px' });

  Array.prototype.forEach.call(boxes, function (box) {
    var item = { box: box, anim: null, loading: false, visible: false };
    items.push(item);
    io.observe(box);
  });

  function syncAll() { items.forEach(sync); }
  document.addEventListener('visibilitychange', syncAll);
  if (reduce) {
    var onChange = function () {
      items.forEach(function (item) { if (motionOK() && item.visible) start(item); });
      syncAll();
    };
    if (reduce.addEventListener) reduce.addEventListener('change', onChange);
    else if (reduce.addListener) reduce.addListener(onChange);
  }
})();
