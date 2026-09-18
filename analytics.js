// ADHDme — analytics and attribution (ported from the ADHD repo's taxonomy, outbound store and /go handoff)
//
// Three rules carried over:
//   1. A closed taxonomy. Every event name and every property value is declared below; anything else
//      is refused and logged as "analytics-refused" instead of becoming a row that looks real.
//   2. Nothing leaves the page unless an analytics ID is configured (analytics-config.js). Until then
//      events are validated and dropped. The UTM tail on booking links works regardless.
//   3. A measurement budget. Sending never delays a click: outbound events go by beacon and the link
//      navigates immediately.
(function () {
  'use strict';

  // Each clinician: the booking link the outbound handler matches, and the profile page that names them.
  var CLINICIANS = {
    'anubhav-saxena': { booking: /dr-anubhav-saxena\/p123180/, profile: 'dr-anubhav-saxena.html' },
    'anu-saxena': { booking: /dr-anusha-saxena\/p160121/, profile: 'dr-anu-saxena.html' },
    'paula-garrido': { booking: /wellnesspsychologyclinic\.com\.au\/appointment-page/, profile: 'paula-garrido.html' },
    // GOALS Psychology: one clinic booking page for the seven bookable clinicians, so the regex cannot
    // tell them apart. clinicianFor() resolves it from the profile page the click came from.
    'kate-row': { booking: /halaxy\.com\/book\/goals-psychology/, profile: 'kate-row.html' },
    'ellie-putland': { booking: /halaxy\.com\/book\/goals-psychology/, profile: 'ellie-putland.html' },
    'lachlan-avent': { booking: /halaxy\.com\/book\/goals-psychology/, profile: 'lachlan-avent.html' },
    'samantha-courtney': { booking: /halaxy\.com\/book\/goals-psychology/, profile: 'samantha-courtney.html' },
    'lauren-poulos': { booking: /halaxy\.com\/book\/goals-psychology/, profile: 'lauren-poulos.html' },
    'alice-bui': { booking: /halaxy\.com\/book\/goals-psychology/, profile: 'alice-bui.html' },
    'meera-lakhani': { booking: /goalspsychology\.com\/contact/, profile: 'meera-lakhani.html' },
    'flynn-simonis': { booking: /halaxy\.com\/book\/goals-psychology/, profile: 'flynn-simonis.html' }
  };
  var CLINICIAN_IDS = Object.keys(CLINICIANS);
  var BOOKING_SURFACES = ['network', 'profile', 'finder', 'examples', 'demo'];
  var LANDING_CONTROLS = ['hero-cta', 'nav-learn', 'nav-cta', 'nav-doctors', 'nav-approach'];

  var EVENTS = {
    'landing-viewed': {},
    'landing-cta': { control: { kind: 'vocabulary', values: LANDING_CONTROLS } },
    'deck-viewed': { clinicians: { kind: 'count' } },
    'profile-viewed': { clinician: { kind: 'vocabulary', values: CLINICIAN_IDS }, surface: { kind: 'vocabulary', values: BOOKING_SURFACES } },
    'booking-outbound': { clinician: { kind: 'vocabulary', values: CLINICIAN_IDS }, surface: { kind: 'vocabulary', values: BOOKING_SURFACES } }
  };

  function findings(name, props) {
    var spec = EVENTS[name];
    if (!spec) return ['"' + name + '" is not an event this product declares'];
    var out = [];
    Object.keys(props).forEach(function (k) { if (!(k in spec)) out.push('"' + name + '" has no property "' + k + '"'); });
    Object.keys(spec).forEach(function (k) {
      var v = props[k];
      if (v === undefined) { out.push('"' + name + '" is missing "' + k + '"'); return; }
      if (spec[k].kind === 'count') { if (typeof v !== 'number' || !isFinite(v)) out.push('"' + name + '"."' + k + '" must be a finite number'); return; }
      if (typeof v !== 'string' || spec[k].values.indexOf(v) === -1) out.push('"' + name + '"."' + k + '" must be one of the declared values, got ' + JSON.stringify(v));
    });
    return out;
  }

  var config = window.ADHDME || {};
  var debug = /[?&]debug=analytics\b/.test(location.search);
  var queue = window.__adhdmeEvents = window.__adhdmeEvents || [];

  // Sink: GA4 only when an ID is configured, with advertising signals off. Otherwise nothing is sent.
  var gaReady = false;
  if (config.gaId) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    var s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(config.gaId);
    document.head.appendChild(s);
    window.gtag('js', new Date());
    window.gtag('config', config.gaId, { allow_google_signals: false, allow_ad_personalization_signals: false, anonymize_ip: true });
    gaReady = true;
  }

  function track(name, props) {
    var f = findings(name, props || {});
    if (f.length) {
      queue.push({ event: 'analytics-refused', name: name, findings: f });
      if (debug) console.warn('analytics-refused', name, f);
      return false;
    }
    queue.push({ event: name, properties: props || {}, at: Date.now() });
    if (debug) console.info('analytics', name, props || {});
    if (gaReady) { try { window.gtag('event', name, Object.assign({ transport_type: 'beacon' }, props || {})); } catch (e) {} }
    return true;
  }
  window.adhdmeTrack = track;

  // Which surface this page is, in the taxonomy's own words.
  var path = location.pathname.replace(/\/index\.html$/, '/');
  var file = path.split('/').pop() || 'index.html';
  function clinicianOfPage(name) {
    for (var k in CLINICIANS) if (CLINICIANS[k].profile === name) return k;
    return null;
  }
  var profileId = clinicianOfPage(file);
  var surface = profileId ? 'profile' : file === 'the-doctors.html' ? 'network' : null;

  // Page events: the funnel's first three steps.
  if (file === 'index.html' || file === '') track('landing-viewed', {});
  if (file === 'the-doctors.html') {
    var seen = {};
    Array.prototype.forEach.call(document.querySelectorAll('a[href]'), function (a) {
      var id = clinicianOfPage(a.getAttribute('href').split(/[?#]/)[0]);
      if (id) seen[id] = true;
    });
    track('deck-viewed', { clinicians: Object.keys(seen).length });
  }
  if (profileId) {
    var src = new URLSearchParams(location.search).get('src');
    var from = BOOKING_SURFACES.indexOf(src) !== -1 ? src : (/the-doctors\.html/.test(document.referrer) ? 'network' : 'profile');
    track('profile-viewed', { clinician: profileId, surface: from });
  }

  // Landing controls: which of five named controls was pressed.
  document.addEventListener('click', function (e) {
    var el = e.target instanceof Element ? e.target.closest('[data-landing-control]') : null;
    if (!el) return;
    track('landing-cta', { control: el.getAttribute('data-landing-control') });
  }, true);

  // Booking handoff: the UTM tail for the practice's own reporting, a local tally, and the last event.
  function clinicianFor(href) {
    // A clinic whose clinicians share one booking page would otherwise always attribute to whichever
    // of them is declared first, so the profile being read wins when its own link is the one clicked.
    if (profileId && CLINICIANS[profileId].booking.test(href)) return profileId;
    for (var k in CLINICIANS) if (CLINICIANS[k].booking.test(href)) return k;
    return null;
  }
  function tallyOutbound(clinician, surf) {
    try {
      var key = 'adhdme-outbound';
      var rows = JSON.parse(localStorage.getItem(key) || '[]');
      rows.push({ clinicianId: clinician, surface: surf, day: new Date().toISOString().slice(0, 10) });
      if (rows.length > 500) rows = rows.slice(-500);
      localStorage.setItem(key, JSON.stringify(rows));
    } catch (e) {}
  }
  document.addEventListener('click', function (e) {
    var a = e.target instanceof Element ? e.target.closest('a[href^="http"]') : null;
    if (!a) return;
    var clinician = clinicianFor(a.href);
    if (!clinician) return;
    var surf = surface || 'network';
    try {
      var u = new URL(a.href);
      u.searchParams.set('utm_source', 'adhd-me');
      u.searchParams.set('utm_medium', 'referral');
      u.searchParams.set('utm_campaign', surf);
      a.href = u.toString();
    } catch (err) {}
    tallyOutbound(clinician, surf);
    track('booking-outbound', { clinician: clinician, surface: surf });
    // No await, no delay: the browser follows the link now; the beacon travels on its own.
  }, true);

  // The measurement page reads this device's tally.
  var tallyEl = document.getElementById('tally');
  if (tallyEl) {
    try {
      var rows = JSON.parse(localStorage.getItem('adhdme-outbound') || '[]');
      if (!rows.length) { tallyEl.textContent = 'No handoffs recorded on this device yet.'; }
      else {
        var by = {};
        rows.forEach(function (r) { by[r.clinicianId] = by[r.clinicianId] || {}; by[r.clinicianId][r.surface] = (by[r.clinicianId][r.surface] || 0) + 1; });
        tallyEl.textContent = Object.keys(by).map(function (c) {
          return c + ': ' + Object.keys(by[c]).map(function (s) { return by[c][s] + ' from ' + s; }).join(', ');
        }).join(' · ');
      }
    } catch (e) { tallyEl.textContent = 'This browser does not allow local storage.'; }
  }
})();
