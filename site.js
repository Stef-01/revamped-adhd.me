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

/* Network: the category strip and each category's clinicians scroll sideways, one at a time.
   Scrolling is left to the browser's own scroll snapping, which is what makes it smooth on an iPhone; the script
   never moves a row while a finger or trackpad is on it. Tap a category to choose it; the arrows, the counter, the
   dots and the keyboard follow the cards. */
(function () {
  var strip = document.querySelector('.deck-tabs');
  if (!strip || typeof window.switchCategory !== 'function') return;
  var tabs = [].slice.call(strip.querySelectorAll('[role="tab"]'));
  var still = window.matchMedia('(prefers-reduced-motion: reduce)'), phone = window.matchMedia('(max-width: 639px)');
  var behave = still.matches ? 'auto' : 'smooth';
  var ARROW = { prev: '<path d="M15 5l-7 7 7 7"/>', next: '<path d="M9 5l7 7-7 7"/>' };
  function arrow(dir, label) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'deck-arrow'; b.setAttribute('aria-label', label);
    b.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ARROW[dir] + '</svg>';
    return b;
  }
  function centre(el, box, how) { box.scrollTo({ left: el.offsetLeft - (box.clientWidth - el.offsetWidth) / 2, behavior: how }); }
  function selected() { for (var i = 0; i < tabs.length; i++) if (tabs[i].getAttribute('aria-selected') === 'true') return i; return 0; }
  function key(i) { return tabs[i].id.replace(/^tab-btn-/, ''); }

  // the strip, with an arrow either side. It scrolls freely; a category changes only when it is tapped.
  var wrap = document.createElement('div'); wrap.className = 'deck-tabs-wrap';
  strip.parentNode.insertBefore(wrap, strip);
  var tPrev = arrow('prev', 'Previous kind of clinician'), tNext = arrow('next', 'Next kind of clinician');
  wrap.appendChild(tPrev); wrap.appendChild(strip); wrap.appendChild(tNext);
  function tabArrows() { var i = selected(); tPrev.disabled = i === 0; tNext.disabled = i === tabs.length - 1; }
  tPrev.addEventListener('click', function () { var i = selected(); if (i > 0) window.switchCategory(key(i - 1)); });
  tNext.addEventListener('click', function () { var i = selected(); if (i < tabs.length - 1) window.switchCategory(key(i + 1)); });

  // a fresh order on every visit, so no one is always first. People with an online diary come before those you
  // enquire with (the site check holds the page to that); each group is shuffled on its own. Pinned cards (the two
  // most affordable GPs) come before both, in a random order of their own, so either may lead.
  function shuffle(a) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  [].slice.call(document.querySelectorAll('[role="tabpanel"] > .deck-track')).forEach(function (track) {
    var cards = [].slice.call(track.children);
    var pinned = cards.filter(function (li) { return li.hasAttribute('data-pinned'); });
    cards = cards.filter(function (li) { return !li.hasAttribute('data-pinned'); });
    var books = function (li) { var b = li.querySelector('.btn-press'); return b && /^Book/.test((b.getAttribute('aria-label') || b.textContent).trim()); };
    shuffle(pinned).concat(shuffle(cards.filter(books)), shuffle(cards.filter(function (li) { return !books(li); })))
      .forEach(function (li) { track.appendChild(li); });
    // the photo now first in the row should not wait on lazy loading
    var first = track.firstElementChild && track.firstElementChild.querySelector('img');
    if (first) first.loading = 'eager';
  });

  // each category's clinicians
  var decks = {};
  [].slice.call(document.querySelectorAll('[role="tabpanel"] > .deck-track')).forEach(function (track) {
    var panel = track.parentNode, cards = [].slice.call(track.children);
    var label = (document.getElementById(panel.getAttribute('aria-labelledby')) || {}).textContent || 'Clinicians';
    track.setAttribute('tabindex', '0');
    track.setAttribute('aria-label', label + ': use the arrow keys or swipe to see each clinician');
    // the arrows sit on the sides of the card, so they are in view whenever the card is
    var rail = document.createElement('div'); rail.className = 'deck-rail';
    panel.insertBefore(rail, track); rail.appendChild(track);
    var cPrev = arrow('prev', 'Previous clinician'), cNext = arrow('next', 'Next clinician');
    cPrev.classList.add('deck-side', 'deck-side--prev'); cNext.classList.add('deck-side', 'deck-side--next');
    rail.appendChild(cPrev); rail.appendChild(cNext);
    // under the card: a dot for each clinician and a count, so it is plain how many there are
    var ctrl = document.createElement('div'); ctrl.className = 'deck-ctrl';
    var dots = document.createElement('span'); dots.className = 'deck-dots'; dots.setAttribute('aria-hidden', 'true');
    cards.forEach(function () { dots.appendChild(document.createElement('span')); });
    var count = document.createElement('span'); count.className = 'deck-count'; count.setAttribute('aria-live', 'polite');
    ctrl.appendChild(dots); ctrl.appendChild(count);
    panel.appendChild(ctrl);

    // Card positions are measured once, and again only when the layout really changes (a category shown, the
    // window made wider or narrower). Scrolling itself only reads scrollLeft, so a swipe never forces a layout.
    var centres = [], width = 1, lit = [];
    function measure() {
      centres = cards.map(function (c) { return c.offsetLeft + c.offsetWidth / 2; });
      width = (cards[0] && cards[0].offsetWidth) || 1;
    }
    var at = -1;
    function mark(i) {
      if (i === at) return;
      at = i;
      cards.forEach(function (c, j) { c.classList.toggle('is-current', j === i); dots.children[j].classList.toggle('is-on', j === i); });
      count.textContent = cards.length ? (i + 1) + ' of ' + cards.length : '';
      cPrev.hidden = i === 0 || cards.length < 2; cNext.hidden = i >= cards.length - 1;
      ctrl.hidden = cards.length < 2;
    }
    // light each card by how near the centre it is: writes only, and only for the cards whose light changed
    function light() {
      if (!width || !centres.length) return;
      var mid = track.scrollLeft + track.clientWidth / 2, best = 0, gap = Infinity;
      for (var j = 0; j < cards.length; j++) {
        var d = Math.abs(centres[j] - mid);
        if (d < gap) { gap = d; best = j; }
        var v = Math.max(0, 1 - (d / width) * 1.6);
        v = Math.round(v * 50) / 50;
        if (lit[j] !== v) { lit[j] = v; cards[j].style.setProperty('--lit', v); }
      }
      mark(best);
    }
    var queued = false;
    track.addEventListener('scroll', function () {
      if (queued) return; queued = true;
      requestAnimationFrame(function () { queued = false; light(); });
    }, { passive: true });

    // the first time a row of cards comes into view on a phone, it slides a little to show there is more,
    // and stops the moment it is touched
    var nudged = false;
    function stopNudge() { track.classList.remove('is-nudging'); }
    function nudge() {
      if (nudged || cards.length < 2 || !phone.matches || still.matches || panel.classList.contains('hidden') || track.scrollLeft > 4) return;
      nudged = true;
      track.classList.add('is-nudging');
      setTimeout(stopNudge, 1400);
    }
    ['pointerdown', 'touchstart', 'wheel'].forEach(function (t) { track.addEventListener(t, function () { nudged = true; stopNudge(); }, { passive: true }); });
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es, io) {
        es.forEach(function (e) { if (e.isIntersecting) { nudge(); if (nudged) io.disconnect(); } });
      }, { threshold: 0.6 }).observe(track);
    }

    function go(i, how) {
      i = Math.max(0, Math.min(cards.length - 1, i));
      if (!cards[i]) return;
      if (!centres.length) measure();
      track.scrollTo({ left: centres[i] - track.clientWidth / 2, behavior: how || behave });
      mark(i);
    }
    cPrev.addEventListener('click', function () { go(at - 1); });
    cNext.addEventListener('click', function () { go(at + 1); });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); go(at + 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); go(at - 1); }
    });
    function refresh() { measure(); lit = []; light(); }
    decks[panel.id] = { go: go, now: function () { return Math.max(at, 0); }, cards: cards, refresh: refresh, nudge: nudge, panel: panel };
    if (!panel.classList.contains('hidden')) refresh(); else mark(0);
  });

  // Order: Suggested (online diaries first, shuffled), By location (city, then name) or A to Z.
  // The choice is kept for the visit, so coming back from a profile keeps it.
  var suggested = {};
  Object.keys(decks).forEach(function (id) { suggested[id] = decks[id].cards.slice(); });
  function ordered(id, mode) {
    var cards = suggested[id].slice();
    var by = function (f) { return function (a, b) { return f(a).localeCompare(f(b)); }; };
    if (mode === 'name') cards.sort(by(function (li) { return li.getAttribute('data-name') || ''; }));
    if (mode === 'location') cards.sort(function (a, b) {
      var r = (a.getAttribute('data-region') || '').localeCompare(b.getAttribute('data-region') || '');
      return r || (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || '');
    });
    // pinned cards stay in front whichever order is chosen
    var pin = function (li) { return li.hasAttribute('data-pinned'); };
    return cards.filter(pin).concat(cards.filter(function (li) { return !pin(li); }));
  }
  var sortBtns = [].slice.call(document.querySelectorAll('.deck-sort__btn'));
  var SORTABLE = { 'panel-psychologists': true, 'panel-coaches': true };   // the long lists; the rest are a swipe or two
  var sortBox = document.querySelector('.deck-sort');
  function applySort(mode, keep) {
    sortBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-sort') === mode)); });
    Object.keys(decks).forEach(function (id) {
      var d = decks[id], track = d.cards[0] && d.cards[0].parentNode;
      if (!track) return;
      var order = ordered(id, mode);
      order.forEach(function (li) { track.appendChild(li); });
      d.cards.length = 0; order.forEach(function (li) { d.cards.push(li); });
      if (!d.panel.classList.contains('hidden')) { d.refresh(); d.go(keep ? d.now() : 0, 'auto'); }
    });
    try { sessionStorage.setItem('adhdme-order', mode); } catch (e) {}
  }
  // each button is a toggle: press it to order that way, press it again for the suggested order
  sortBtns.forEach(function (b) { b.addEventListener('click', function () { applySort(b.getAttribute('aria-pressed') === 'true' ? 'suggested' : b.getAttribute('data-sort'), false); }); });
  var savedOrder = null;
  try { savedOrder = sessionStorage.getItem('adhdme-order'); } catch (e) {}
  if (savedOrder && savedOrder !== 'suggested') applySort(savedOrder, true);
  if (sortBox) sortBox.hidden = !SORTABLE['panel-' + key(selected())];

  // what this kind of clinician does, in the tab's own colour
  var intro = document.getElementById('deck-intro');
  function showIntro(i) {
    if (!intro) return;
    intro.style.setProperty('--tint', tabs[i].style.getPropertyValue('--tint'));
    intro.firstElementChild.textContent = tabs[i].getAttribute('data-intro') || '';
  }

  window.deckSync = function (cat) {
    var i = -1;
    for (var n = 0; n < tabs.length; n++) if (key(n) === cat) i = n;
    if (i < 0) return;
    centre(tabs[i], strip, behave);
    tabArrows();
    showIntro(i);
    if (sortBox) sortBox.hidden = !SORTABLE['panel-' + cat];
    var d = decks['panel-' + cat];
    if (d) requestAnimationFrame(function () { d.refresh(); d.go(d.now(), 'auto'); setTimeout(d.nudge, 450); });
  };
  window.deckShow = function (li) {
    var panel = li.closest('[role="tabpanel"]'), d = panel && decks[panel.id];
    if (d) requestAnimationFrame(function () { d.refresh(); d.go(d.cards.indexOf(li), 'auto'); });
  };
  // Only a real change of width re-measures. On an iPhone the toolbar showing and hiding fires resize on every
  // vertical scroll, and re-centring then would yank the row out from under the reader.
  var lastW = window.innerWidth, resizeT;
  window.addEventListener('resize', function () {
    if (window.innerWidth === lastW) return;
    lastW = window.innerWidth;
    clearTimeout(resizeT);
    resizeT = setTimeout(function () {
      var i = selected(); centre(tabs[i], strip, 'auto');
      var d = decks['panel-' + key(i)]; if (d) { d.refresh(); d.go(d.now(), 'auto'); }
    }, 150);
  });
  tabArrows();
  showIntro(selected());
  requestAnimationFrame(function () { centre(tabs[selected()], strip, 'auto'); });
})();
