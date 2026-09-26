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
