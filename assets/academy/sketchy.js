/* Sketchy-method scenes: click or key through a persistent scene one symbol at a time.
   Art lives in <symbol> elements; this file never touches it, so final illustration
   can replace the placeholders without any change here. */
(function () {
  'use strict';
  var KEY = 'adhdme.course.sk-still';
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function put(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  var osReduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var saved = get();
  var still = saved === null ? osReduce : saved === '1';

  var scenes = [].slice.call(document.querySelectorAll('.sk'));
  var apis = scenes.map(function (fig) {
    var syms = [].slice.call(fig.querySelectorAll('.sk__sym')).sort(function (a, b) { return a.getAttribute('data-step') - b.getAttribute('data-step'); });
    var total = syms.length;
    var cap = fig.querySelector('[data-sk-cap]');
    var count = fig.querySelector('[data-sk-count]');
    var next = fig.querySelector('[data-sk-next]');
    var prev = fig.querySelector('[data-sk-prev]');
    var all = fig.querySelector('[data-sk-all]');
    var box = fig.querySelector('[data-sk-motion]');
    var now = 0, revealed = 0;

    function paint() {
      var shown = still ? total : revealed;
      syms.forEach(function (g, i) {
        var n = i + 1;
        g.classList.toggle('is-on', n <= shown);
        g.classList.toggle('is-now', n === now);
        g.setAttribute('tabindex', n <= shown ? '0' : '-1');
        g.setAttribute('aria-hidden', n <= shown ? 'false' : 'true');
      });
      fig.setAttribute('data-still', still ? '1' : '0');
      fig.setAttribute('data-complete', shown >= total ? '1' : '0');
      if (count) count.textContent = now ? 'Symbol ' + now + ' of ' + total : total + ' symbols in this scene';
      if (prev) prev.disabled = now <= 1;
      if (next) { next.disabled = now >= total; next.firstChild.nodeValue = now === 0 ? 'Start the scene ' : 'Next symbol '; }
      if (all) all.hidden = still || revealed >= total;
      if (cap) {
        if (!now) {
          cap.innerHTML = '<b>' + fig.getAttribute('data-world') + '</b><p>' + fig.getAttribute('data-desc') + ' Step through it one symbol at a time, or use the arrow keys.</p>';
        } else {
          var g = syms[now - 1];
          cap.innerHTML = '<b>' + now + '. ' + g.getAttribute('data-title') + '</b><p>' + g.getAttribute('data-recap') + '</p><p class="sk__cues">How it is encoded: ' + g.getAttribute('data-cues') + ' · ' + g.getAttribute('data-lesson') + '</p>';
        }
      }
      if (box) box.checked = still;
    }
    function go(n) { now = Math.max(0, Math.min(total, n)); if (now > revealed) revealed = now; paint(); }

    if (next) next.addEventListener('click', function () { go(now + 1); });
    if (prev) prev.addEventListener('click', function () { go(now - 1); });
    if (all) all.addEventListener('click', function () { revealed = total; if (!now) now = 1; paint(); });
    syms.forEach(function (g, i) {
      function pick() { if (g.classList.contains('is-on')) go(i + 1); }
      g.addEventListener('click', pick);
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); pick(); } });
    });
    fig.addEventListener('keydown', function (ev) {
      if (ev.target.tagName === 'INPUT') return;
      if (ev.key === 'ArrowRight') { ev.preventDefault(); go(now + 1); }
      if (ev.key === 'ArrowLeft') { ev.preventDefault(); go(now - 1); }
    });
    if (box) box.addEventListener('change', function () { still = box.checked; put(still ? '1' : '0'); apis.forEach(function (a) { a.paint(); }); });
    paint();
    return { paint: paint };
  });

  /* symbol explorer: one recap open at a time; hover and focus also reveal via CSS */
  document.querySelectorAll('.skx').forEach(function (grid) {
    var btns = [].slice.call(grid.querySelectorAll('.skx__b'));
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        var open = b.getAttribute('aria-expanded') === 'true';
        btns.forEach(function (o) { o.setAttribute('aria-expanded', 'false'); });
        b.setAttribute('aria-expanded', open ? 'false' : 'true');
      });
    });
  });
})();
