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
   Swiping the strip changes category; the arrows, the counter and the keyboard all follow the same state. */
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
  function nearest(box, items) {
    var mid = box.scrollLeft + box.clientWidth / 2, best = 0, gap = Infinity;
    items.forEach(function (el, i) { var d = Math.abs(el.offsetLeft + el.offsetWidth / 2 - mid); if (d < gap) { gap = d; best = i; } });
    return best;
  }
  function selected() { for (var i = 0; i < tabs.length; i++) if (tabs[i].getAttribute('aria-selected') === 'true') return i; return 0; }
  function key(i) { return tabs[i].id.replace(/^tab-btn-/, ''); }

  // the strip, with an arrow either side
  var wrap = document.createElement('div'); wrap.className = 'deck-tabs-wrap';
  strip.parentNode.insertBefore(wrap, strip);
  var tPrev = arrow('prev', 'Previous kind of clinician'), tNext = arrow('next', 'Next kind of clinician');
  wrap.appendChild(tPrev); wrap.appendChild(strip); wrap.appendChild(tNext);
  function tabArrows() { var i = selected(); tPrev.disabled = i === 0; tNext.disabled = i === tabs.length - 1; }
  tPrev.addEventListener('click', function () { var i = selected(); if (i > 0) window.switchCategory(key(i - 1)); });
  tNext.addEventListener('click', function () { var i = selected(); if (i < tabs.length - 1) window.switchCategory(key(i + 1)); });

  // swiping the strip picks the category that settles in the middle
  var quietUntil = 0, stripTimer;
  strip.addEventListener('scroll', function () {
    clearTimeout(stripTimer);
    stripTimer = setTimeout(function () {
      if (Date.now() < quietUntil) return;
      var i = nearest(strip, tabs);
      if (i !== selected()) window.switchCategory(key(i));
      else centre(tabs[i], strip, behave);
    }, 140);
  }, { passive: true });

  // a fresh order on every visit, so no one is always first. People with an online diary stay ahead of those you
  // enquire with (the site check holds the page to that); each group is shuffled on its own.
  function shuffle(a) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  [].slice.call(document.querySelectorAll('[role="tabpanel"] > .deck-track')).forEach(function (track) {
    var cards = [].slice.call(track.children);
    var books = function (li) { var b = li.querySelector('.btn-press'); return b && /^Book/.test((b.getAttribute('aria-label') || b.textContent).trim()); };
    shuffle(cards.filter(books)).concat(shuffle(cards.filter(function (li) { return !books(li); })))
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
    var at = 0;
    function mark(i) {
      at = i;
      cards.forEach(function (c, j) { c.classList.toggle('is-current', j === i); dots.children[j].classList.toggle('is-on', j === i); });
      count.textContent = cards.length ? (i + 1) + ' of ' + cards.length : '';
      cPrev.hidden = i === 0 || cards.length < 2; cNext.hidden = i >= cards.length - 1;
      ctrl.hidden = cards.length < 2;
    }
    // the first time a row of cards comes into view on a phone, it slides a little to show there is more
    var nudged = false;
    function nudge() {
      if (nudged || cards.length < 2 || !phone.matches || still.matches || panel.classList.contains('hidden')) return;
      nudged = true;
      track.classList.add('is-nudging');
      setTimeout(function () { track.classList.remove('is-nudging'); }, 1400);
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es, io) {
        es.forEach(function (e) { if (e.isIntersecting) { nudge(); if (nudged) io.disconnect(); } });
      }, { threshold: 0.6 }).observe(track);
    }
    function go(i, how) { i = Math.max(0, Math.min(cards.length - 1, i)); if (cards[i]) { centre(cards[i], track, how || behave); mark(i); } }
    // light each card by how near the centre it is, every frame the track moves
    function light() {
      var mid = track.scrollLeft + track.clientWidth / 2;
      cards.forEach(function (c) {
        var d = Math.abs(c.offsetLeft + c.offsetWidth / 2 - mid) / (c.offsetWidth || 1);
        c.style.setProperty('--lit', Math.max(0, 1 - d * 1.6).toFixed(3));
      });
      var i = nearest(track, cards); if (i !== at) mark(i);
    }
    var queued = false;
    track.addEventListener('scroll', function () {
      if (queued) return; queued = true;
      requestAnimationFrame(function () { queued = false; light(); });
    }, { passive: true });
    cPrev.addEventListener('click', function () { go(at - 1); });
    cNext.addEventListener('click', function () { go(at + 1); });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); go(at + 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); go(at - 1); }
    });
    decks[panel.id] = { go: go, now: function () { return at; }, cards: cards, light: light, nudge: nudge };
    mark(0); light();
  });

  window.deckSync = function (cat) {
    var i = tabs.findIndex ? tabs.findIndex(function (t) { return key(tabs.indexOf(t)) === cat; }) : -1;
    if (i < 0) return;
    quietUntil = Date.now() + 700;
    centre(tabs[i], strip, behave);
    tabArrows();
    var d = decks['panel-' + cat];
    if (d) requestAnimationFrame(function () { d.go(d.now(), 'auto'); d.light(); setTimeout(d.nudge, 450); });
  };
  window.deckShow = function (li) {
    var panel = li.closest('[role="tabpanel"]'), d = panel && decks[panel.id];
    if (d) requestAnimationFrame(function () { d.go(d.cards.indexOf(li), 'auto'); d.light(); });
  };
  window.addEventListener('resize', function () {
    var i = selected(); centre(tabs[i], strip, 'auto');
    var d = decks['panel-' + key(i)]; if (d) { d.go(d.now(), 'auto'); d.light(); }
  });
  tabArrows();
  requestAnimationFrame(function () { centre(tabs[selected()], strip, 'auto'); });
})();
