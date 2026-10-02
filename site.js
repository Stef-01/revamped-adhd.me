// ADHDme — shared behaviour
(function () {
  'use strict';

  // Fetch a page as soon as someone hovers over or starts to tap a link to it, so it opens at once. Prefetch only:
  // nothing runs until the page is really visited, so analytics never counts a visit that didn't happen.
  if (HTMLScriptElement.supports && HTMLScriptElement.supports('speculationrules')) {
    var rules = document.createElement('script');
    rules.type = 'speculationrules';
    rules.textContent = JSON.stringify({ prefetch: [{ source: 'document', where: { href_matches: '/*' }, eagerness: 'moderate' }] });
    document.head.appendChild(rules);
  }

  // Header shadow on scroll
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Mobile menu
  var toggle = document.querySelector('[data-menu-toggle]');
  var mobileNav = document.getElementById('mobile-nav');
  if (toggle && mobileNav) {
    var setOpen = function (open) {
      toggle.setAttribute('aria-expanded', String(open));
      mobileNav.hidden = !open;
      toggle.querySelector('[data-icon-open]').hidden = open;
      toggle.querySelector('[data-icon-close]').hidden = !open;
    };
    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { setOpen(false); toggle.focus(); }
    });
    window.matchMedia('(min-width: 768px)').addEventListener('change', function (e) { if (e.matches) setOpen(false); });
  }

  // Scroll reveal
  var revealEls = document.querySelectorAll('[data-reveal]');
  if (revealEls.length) {
    if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) { entry.target.classList.add('is-visible'); io.unobserve(entry.target); }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
      revealEls.forEach(function (el) { io.observe(el); });
    } else {
      revealEls.forEach(function (el) { el.classList.add('is-visible'); });
    }
  }

  // Learn page filters
  var filterBtns = document.querySelectorAll('.filter-btn');
  var cards = document.querySelectorAll('.module-card');
  if (filterBtns.length && cards.length) {
    filterBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var f = btn.getAttribute('data-filter');
        filterBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
        cards.forEach(function (card) {
          var cats = (card.getAttribute('data-category') || '').split(' ');
          card.hidden = !(f === 'all' || cats.indexOf(f) !== -1);
        });
        var status = document.getElementById('filter-status');
        if (status) {
          var n = Array.prototype.filter.call(cards, function (c) { return !c.hidden; }).length;
          status.textContent = n + ' module' + (n === 1 ? '' : 's') + ' shown';
        }
      });
    });
  }

  // Our Story: hovering a place on the map brings it forward
  var stage = document.querySelector('.au-stage');
  if (stage) {
    var setHot = function (slug) {
      stage.classList.toggle('is-focusing', !!slug);
      document.querySelectorAll('[data-city-marker]').forEach(function (m) { m.classList.toggle('is-hot', m.getAttribute('data-city-marker') === slug); });
    };
    document.querySelectorAll('[data-city-marker]').forEach(function (m) {
      var slug = m.getAttribute('data-city-marker');
      m.addEventListener('mouseenter', function () { setHot(slug); });
      m.addEventListener('mouseleave', function () { setHot(null); });
    });
  }
})();

/* Our Story journey: the path draws as you scroll past each stretch of it */
(function () {
  var links = document.querySelectorAll('.story-j__link');
  if (!links.length) return;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function draw() {
    var vh = window.innerHeight;
    for (var i = 0; i < links.length; i++) {
      var r = links[i].getBoundingClientRect();
      var p = still ? 1 : Math.min(1, Math.max(0, (vh * 0.85 - r.top) / (r.height + vh * 0.2)));
      links[i].style.setProperty('--draw', (1 - p).toFixed(3));
    }
  }
  var queued = false;
  window.addEventListener('scroll', function () {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; draw(); });
  }, { passive: true });
  window.addEventListener('resize', draw);
  draw();
})();

/* The Network directory. Every card is in the HTML; the script only hides the ones that do not match, keeps the
   choices in the URL, and offers the same filters in a bottom sheet on a phone. No listener touches scrolling. */
(function () {
  var tablist = document.querySelector('.dir-tabs');
  if (!tablist || typeof window.switchCategory !== 'function') return;
  var tabs = [].slice.call(tablist.querySelectorAll('[role="tab"]'));
  var panels = [].slice.call(document.querySelectorAll('[role="tabpanel"]'));
  var specialty = document.getElementById('dir-specialty'), count = document.getElementById('dir-count'), empty = document.getElementById('dir-empty');
  var clear = document.querySelector('.dir-clear'), intro = document.getElementById('dir-intro');
  var orderBox = document.querySelector('.dir-order'), orderSel = document.getElementById('dir-order');
  var modeBoxes = [].slice.call(document.querySelectorAll('.dir-modes input'));
  var gpSel = document.getElementById('dir-gp'), stateSel = document.getElementById('dir-state'), ageSel = document.getElementById('dir-age');
  var gpBox = gpSel && gpSel.closest('.dir-select');
  var EMPTY = function () { return { q: '', modes: [], order: 'suggested', gp: '', st: '', age: '' }; };
  var SORTABLE = { psychologists: true, coaches: true };
  var key = function (t) { return t.id.replace(/^tab-btn-/, ''); };
  function selected() { for (var i = 0; i < tabs.length; i++) if (tabs[i].getAttribute('aria-selected') === 'true') return key(tabs[i]); return key(tabs[0]); }

  // a fresh order on every visit, so no one is always first. People with an online diary come before those you
  // enquire with (the site check holds the page to that); each group is shuffled on its own.
  function shuffle(a) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  var suggested = {};
  panels.forEach(function (panel) {
    var track = panel.querySelector('ul'), cards = [].slice.call(track.children);
    var books = function (li) { var b = li.querySelector('.btn-press'); return b && /^Book/.test((b.getAttribute('aria-label') || b.textContent).trim()); };
    // pinned cards (the two most affordable GPs) come before both, in a random order of their own, so either may lead
    var pin = function (li) { return li.hasAttribute('data-pinned'); };
    var rest = cards.filter(function (li) { return !pin(li); });
    var order = shuffle(cards.filter(pin)).concat(shuffle(rest.filter(books)), shuffle(rest.filter(function (li) { return !books(li); })));
    order.forEach(function (li) { track.appendChild(li); });
    suggested[panel.id] = order;
    var first = order[0] && order[0].querySelector('img'); if (first) first.loading = 'eager';
  });

  // what a card can be searched by: its own name, role, place and tags, read once
  var index = {};
  document.querySelectorAll('.dir-card').forEach(function (li) {
    var parts = [li.getAttribute('data-name'), li.getAttribute('data-region')];
    var head = li.querySelector('a > span:last-child'); if (head) parts.push(head.textContent);
    li.querySelectorAll('div span').forEach(function (s) { parts.push(s.textContent); });
    index[li.id] = parts.join(' ').toLowerCase().replace(/\s+/g, ' ');
  });

  var state = EMPTY();
  function readUrl() {
    var p = new URLSearchParams(location.search);
    state.q = '';   // the search field is gone; the specialty picker took its place
    state.modes = (p.get('mode') || '').split(',').filter(Boolean);
    state.order = p.get('order') || 'suggested';
    state.gp = p.get('gp') || ''; state.st = p.get('state') || ''; state.age = p.get('age') || '';
  }
  function writeUrl(push) {
    var p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.modes.length) p.set('mode', state.modes.join(','));
    if (state.order !== 'suggested') p.set('order', state.order);
    if (state.gp && selected() === 'gps') p.set('gp', state.gp);
    if (state.st) p.set('state', state.st);
    if (state.age) p.set('age', state.age);
    var qs = p.toString(), url = location.pathname + (qs ? '?' + qs : '') + '#panel-' + selected();
    try { (push ? history.pushState : history.replaceState).call(history, null, '', url); } catch (e) {}
    try { sessionStorage.setItem('adhdme-directory', qs ? '?' + qs : ''); } catch (e) {}
  }

  function sortPanel(panel) {
    var track = panel.querySelector('ul'), cards = suggested[panel.id].slice();
    var name = function (li) { return li.getAttribute('data-name') || ''; };
    if (state.order === 'name') cards.sort(function (a, b) { return name(a).localeCompare(name(b)); });
    if (state.order === 'location') cards.sort(function (a, b) { return (a.getAttribute('data-region') || '').localeCompare(b.getAttribute('data-region') || '') || name(a).localeCompare(name(b)); });
    if (!SORTABLE[panel.id.replace(/^panel-/, '')]) cards = suggested[panel.id];
    // pinned cards stay in front whichever order is chosen
    var pinned = function (li) { return li.hasAttribute('data-pinned'); };
    cards = cards.filter(pinned).concat(cards.filter(function (li) { return !pinned(li); }));
    cards.forEach(function (li) { track.appendChild(li); });
  }

  // show the cards that match: one pass, one count
  function apply() {
    var cat = selected(), panel = document.getElementById('panel-' + cat);
    var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean), shown = 0;
    sortPanel(panel);
    [].slice.call(panel.querySelectorAll('.dir-card')).forEach(function (li) {
      var hay = index[li.id] || '', modes = ' ' + (li.getAttribute('data-modes') || '') + ' ';
      var ok = terms.every(function (t) { return hay.indexOf(t) >= 0; }) && state.modes.every(function (m) { return modes.indexOf(' ' + m + ' ') >= 0; })
        && (!state.st || li.getAttribute('data-state') === state.st)
        && (!state.age || (' ' + (li.getAttribute('data-ages') || '') + ' ').indexOf(' ' + state.age + ' ') >= 0)
        && (!state.gp || cat !== 'gps' || li.getAttribute('data-gp') === state.gp);
      li.hidden = !ok; if (ok) shown++;
    });
    count.textContent = shown + (shown === 1 ? ' clinician' : ' clinicians');
    empty.hidden = shown > 0;
    var active = !!(state.q || state.modes.length || state.order !== 'suggested' || state.st || state.age || (state.gp && cat === 'gps'));
    if (gpBox) gpBox.hidden = cat !== 'gps';
    var sheetGp = document.querySelector('[data-sheet-gp]'); if (sheetGp) sheetGp.hidden = cat !== 'gps';
    clear.hidden = !active;
    var fb = document.querySelector('.dir-filter-btn'); if (fb) fb.classList.toggle('is-active', active);
    var sortable = !!SORTABLE[cat];
    orderBox.hidden = !sortable;
    var sheetOrder = document.querySelector('[data-sheet-order]'); if (sheetOrder) sheetOrder.hidden = !sortable;
    var applyBtn = document.querySelector('.dir-sheet__apply'); if (applyBtn) applyBtn.textContent = 'Show ' + shown + (shown === 1 ? ' clinician' : ' clinicians');
    return shown;
  }
  function paint() {
    if (specialty) specialty.value = selected();
    modeBoxes.forEach(function (b) { b.checked = state.modes.indexOf(b.value) >= 0; });
    orderSel.value = state.order;
    if (gpSel) gpSel.value = state.gp; if (stateSel) stateSel.value = state.st; if (ageSel) ageSel.value = state.age;
    var t = tabs.filter(function (x) { return key(x) === selected(); })[0];
    if (intro && t) { intro.style.setProperty('--tint', t.style.getPropertyValue('--tint')); intro.textContent = t.getAttribute('data-intro') || ''; }
    // on a phone the strip scrolls; keep the chosen category in view (the strip only, never the page)
    if (t && tablist.scrollWidth > tablist.clientWidth) tablist.scrollTo({ left: t.offsetLeft - (tablist.clientWidth - t.offsetWidth) / 2, behavior: 'auto' });
  }

  // the page tells us when a category changes (a tab, a deep link, the sheet)
  var syncing = false;
  window.dirSync = function () { paint(); apply(); if (!syncing) writeUrl(true); };
  if (specialty) specialty.addEventListener('change', function () { window.switchCategory(specialty.value); });
  modeBoxes.forEach(function (b) { b.addEventListener('change', function () { state.modes = modeBoxes.filter(function (x) { return x.checked; }).map(function (x) { return x.value; }); apply(); writeUrl(false); }); });
  orderSel.addEventListener('change', function () { state.order = orderSel.value; apply(); writeUrl(false); });
  [[gpSel, 'gp'], [stateSel, 'st'], [ageSel, 'age']].forEach(function (pair) {
    if (pair[0]) pair[0].addEventListener('change', function () { state[pair[1]] = pair[0].value; apply(); writeUrl(false); });
  });
  clear.addEventListener('click', function () { state = EMPTY(); paint(); apply(); writeUrl(false); if (specialty) specialty.focus(); });
  window.addEventListener('popstate', function () {
    readUrl();
    var cat = (location.hash.match(/^#panel-([\w-]+)$/) || [])[1];
    syncing = true;
    if (cat && cat !== selected() && document.getElementById('tab-btn-' + cat)) window.switchCategory(cat); else { paint(); apply(); }
    syncing = false;
  });

  // the phone's sheet: the same choices, large targets, focus back on the button that opened it
  var sheet = document.getElementById('dir-sheet'), fbtn = document.querySelector('.dir-filter-btn');
  if (sheet && fbtn && typeof sheet.showModal === 'function') {
    var sCats = [].slice.call(sheet.querySelectorAll('input[name="sheet-cat"]'));
    var sModes = [].slice.call(sheet.querySelectorAll('input[name="sheet-mode"]'));
    var sOrder = [].slice.call(sheet.querySelectorAll('input[name="sheet-order"]'));
    function fill() {
      sCats.forEach(function (r) { r.checked = r.value === selected(); });
      sModes.forEach(function (c) { c.checked = state.modes.indexOf(c.value) >= 0; });
      sOrder.forEach(function (r) { r.checked = r.value === state.order; });
      [['sheet-gp', state.gp], ['sheet-state', state.st], ['sheet-age', state.age]].forEach(function (g) {
        [].slice.call(sheet.querySelectorAll('input[name="' + g[0] + '"]')).forEach(function (r) { r.checked = r.value === g[1]; });
      });
    }
    fbtn.addEventListener('click', function () { fill(); sheet.showModal(); fbtn.setAttribute('aria-expanded', 'true'); });
    sheet.addEventListener('change', function (e) {
      var t = e.target;
      if (t.name === 'sheet-cat') { window.switchCategory(t.value); }
      else if (t.name === 'sheet-mode') { state.modes = sModes.filter(function (x) { return x.checked; }).map(function (x) { return x.value; }); apply(); writeUrl(false); }
      else if (t.name === 'sheet-order') { state.order = t.value; apply(); writeUrl(false); }
      else if (t.name === 'sheet-gp' || t.name === 'sheet-state' || t.name === 'sheet-age') { state[{ 'sheet-gp': 'gp', 'sheet-state': 'st', 'sheet-age': 'age' }[t.name]] = t.value; paint(); apply(); writeUrl(false); }
    });
    sheet.querySelector('.dir-sheet__clear').addEventListener('click', function () { state = EMPTY(); fill(); paint(); apply(); writeUrl(false); });
    sheet.addEventListener('click', function (e) { if (e.target === sheet) sheet.close(); });   // the backdrop
    sheet.addEventListener('close', function () { fbtn.setAttribute('aria-expanded', 'false'); fbtn.focus(); });
  } else if (fbtn) { fbtn.hidden = true; }

  readUrl();
  var start = (location.hash.match(/^#panel-([\w-]+)$/) || [])[1];
  syncing = true;
  if (start && start !== selected() && document.getElementById('tab-btn-' + start)) window.switchCategory(start); else { paint(); apply(); }
  syncing = false;
  try { sessionStorage.setItem('adhdme-directory', location.search); } catch (e) {}   // what a profile's back link returns to
})();

/* A profile's back link returns to the directory with the search and filters that led there. */
(function () {
  var back = document.querySelector('main a[href^="the-doctors.html#"]'); if (!back) return;
  var saved = ''; try { saved = sessionStorage.getItem('adhdme-directory') || ''; } catch (e) {}
  if (saved) back.setAttribute('href', back.getAttribute('href').replace('the-doctors.html#', 'the-doctors.html' + saved + '#'));
})();
