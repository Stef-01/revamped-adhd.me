// ADHDme — motion layer (additive to site.js)
// Staggers sibling reveals, settles and drifts the hero photograph, and draws the ink marks.
// Everything stands down under prefers-reduced-motion.
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 1. Stagger: reveals that share a parent arrive 80ms apart, in reading order.
  var seen = new Map();
  document.querySelectorAll('[data-reveal]').forEach(function (el) {
    var parent = el.parentElement;
    if (!parent) return;
    var n = seen.get(parent) || 0;
    el.style.setProperty('--stagger', n);
    seen.set(parent, n + 1);
  });

  // 2. The hero photograph: a slow settle from 1.06 on load, then a drift at a fraction of scroll.
  var firstSection = document.querySelector('main section');
  var hero = firstSection && firstSection.querySelector('.absolute.inset-0 > img.object-cover, .absolute > img.object-cover');
  if (hero && !reduce) {
    hero.classList.add('hero-settle', 'hero-drift');
    hero.style.setProperty('--settle', '1.06');
    var t0 = null;
    var settle = function (ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / 2400);
      var eased = 1 - Math.pow(1 - p, 4);
      hero.style.setProperty('--settle', String(1 + 0.06 * (1 - eased)));
      if (p < 1) requestAnimationFrame(settle);
    };
    var begin = function () { requestAnimationFrame(settle); };
    if (hero.complete && hero.naturalWidth) begin(); else hero.addEventListener('load', begin, { once: true });
    var ticking = false;
    var drift = function () {
      ticking = false;
      var y = Math.min(window.scrollY * 0.18, 140);
      hero.style.setProperty('--drift', y.toFixed(1) + 'px');
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(drift); }
    }, { passive: true });
    drift();
  }

  // 3. Draw: a variable-width ink stroke under any [data-mark] phrase, wiped in once it is on screen.
  var STROKE = '<svg class="mark__stroke" viewBox="0 0 400 26" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="M3 15 C 40 7, 95 17, 150 12 C 215 6, 275 18, 335 10 C 360 7, 382 7, 397 11 C 399 13, 398 16, 394 17 C 378 14, 356 16, 332 19 C 272 26, 212 15, 152 20 C 98 25, 42 15, 5 21 C 1 21, 0 17, 3 15 Z"/></svg>';
  var marks = document.querySelectorAll('[data-mark]');
  if (marks.length) {
    marks.forEach(function (el) { el.classList.add('mark'); el.insertAdjacentHTML('beforeend', STROKE); });
    if (reduce || !('IntersectionObserver' in window)) {
      marks.forEach(function (el) { el.classList.add('is-drawn'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('is-drawn'); io.unobserve(e.target); }
        });
      }, { threshold: 0.6 });
      marks.forEach(function (el) { io.observe(el); });
    }
  }
})();
