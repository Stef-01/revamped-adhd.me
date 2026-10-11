// ADHDme — matching pilot (client side).
//
// Reads window.ADHDME_MATCHING (matching-config.js). Three jobs:
//   1. On any page: reveal the "Request matching help" calls-to-action when the pilot is enabled, and report
//      that a placement was seen (once per placement per session) or clicked. No answers are involved.
//   2. On matching-help.html: run the request form — scope gate, validation with errors tied to their fields,
//      a loading state, duplicate-submission prevention, a clear failure-and-retry state, and a success
//      screen that appears only after the endpoint accepted the request.
//   3. Keep the answers out of everything that is not the request itself: no localStorage, sessionStorage,
//      URL, analytics property or console line ever carries a form answer or a contact detail.
//
// Analytics go through window.adhdmeTrack (analytics.js), which validates every property against the
// declared vocabulary and refuses anything else, so a form answer cannot reach PostHog by accident.
//
// Local preview, for looking at the flow before anything is approved: on localhost only, ?matchingPreview=1
// forces the pilot on with a mock endpoint that accepts; ?matchingPreview=fail makes it fail (to see the
// retry state); ?matchingPreview=paused shows the at-capacity state. Never honoured on any other host.
//
// The pure parts (validate, decide, createSubmitter) are exported for node:test; see tests/matching.test.js.
(function (root) {
  'use strict';

  var PLACEMENTS = ['homepage', 'directory', 'no_results'];
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var NAME = /^[A-Za-zÀ-ɏ' .-]{1,40}$/;
  var LOCALITY = /^[A-Za-z0-9À-ɏ' .-]{2,40}$/;
  var TIMEOUT_MS = 15000;

  // ------------------------------------------------------------ pure: what the configuration allows
  // {enabled, open, route, reason}: route is 'appointment' (Google Calendar booking page on the team's
  // account, which issues the Meet invite), 'endpoint' (POST to the site's own endpoint), 'mailto' (open the
  // person's mail app addressed to the team) or ''. reason names the first thing keeping intake closed.
  function decide(cfg) {
    cfg = cfg || {};
    if (cfg.pilotEnabled !== true) return { enabled: false, open: false, route: '', reason: 'disabled' };
    var route = cfg.appointmentUrl ? 'appointment' : cfg.requestEndpoint ? 'endpoint' : (cfg.contactEmail ? 'mailto' : '');
    if (!route) return { enabled: true, open: false, route: '', reason: 'no-route' };
    if (cfg.intakeOpen !== true) return { enabled: true, open: false, route: route, reason: 'paused' };
    if (route === 'endpoint') {
      if (cfg.collectionNoticeApproved !== true || !cfg.approvedCollectionNoticeVersion) return { enabled: true, open: false, route: route, reason: 'notice-unapproved' };
      if (!cfg.retentionPolicyText) return { enabled: true, open: false, route: route, reason: 'no-retention' };
    }
    return { enabled: true, open: true, route: route, reason: '' };
  }

  // ------------------------------------------------------------ pure: validation
  // answers: {email, consent}. Returns {ok, errors: {field: message}} in the site's plain voice.
  function validate(a) {
    a = a || {};
    var errors = {};
    if (!EMAIL.test(String(a.email || '').trim())) errors.email = 'Enter an email address we can reply to.';
    if (a.consent !== true) errors.consent = 'Tick the box so we can get in contact.';
    return { ok: !Object.keys(errors).length, errors: errors };
  }

  function payload(a, cfg) {
    return { email: String(a.email || '').trim(), consent: true,
             collection_notice_version: (cfg && cfg.approvedCollectionNoticeVersion) || '',
             copy_version: (cfg && cfg.copyVersion) || '' };
  }

  // The mail-app route: a short, fixed message. The person's address is the sender; it is not written
  // anywhere by the site. Encoded for a mailto: URL.
  function mailtoHref(cfg) {
    var subject = 'Matching help request';
    var body = 'Hi ADHDme team,\n\nI’d like help finding the right clinician. Please get in contact.\n\n(Sent from the matching help page.)';
    return 'mailto:' + cfg.contactEmail + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
  }

  // ------------------------------------------------------------ pure: sending, once at a time
  // createSubmitter(fetchImpl, cfg) → function(answers) → Promise<{accepted:true}|{accepted:false, retry:true}>
  // A second call while one is in flight resolves {accepted:false, busy:true} without sending.
  function createSubmitter(fetchImpl, cfg, timeoutMs) {
    var inFlight = false;
    return function submit(answers) {
      if (inFlight) return Promise.resolve({ accepted: false, busy: true });
      inFlight = true;
      var controller = typeof AbortController === 'function' ? new AbortController() : null;
      var timer = setTimeout(function () { if (controller) controller.abort(); }, timeoutMs || TIMEOUT_MS);
      return Promise.resolve().then(function () {
        return fetchImpl(cfg.requestEndpoint, {
          method: 'POST', credentials: 'same-origin', cache: 'no-store',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify(payload(answers, cfg)),
          signal: controller ? controller.signal : undefined
        });
      }).then(function (res) {
        clearTimeout(timer);
        inFlight = false;
        if (res && res.ok) return { accepted: true };
        return { accepted: false, retry: true, status: res ? res.status : 0 };
      }, function () {
        clearTimeout(timer);
        inFlight = false;
        return { accepted: false, retry: true, status: 0 };
      });
    };
  }

  var api = { decide: decide, validate: validate, payload: payload, mailtoHref: mailtoHref, createSubmitter: createSubmitter, PLACEMENTS: PLACEMENTS };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof document === 'undefined') return;

  // ------------------------------------------------------------ browser: configuration and preview
  var cfg = root.ADHDME_MATCHING || {};
  var preview = (function () {
    var local = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
    var m = local && /[?&]matchingPreview=([a-z0-9]+)/.exec(location.search);
    return m ? m[1] : '';
  })();
  if (preview) {
    cfg = Object.assign({}, cfg, {
      pilotEnabled: true, intakeOpen: preview !== 'paused',
      requestEndpoint: preview === 'mailto' || preview === 'appointment' ? '' : '/__matching-preview',
      appointmentUrl: preview === 'appointment' ? 'about:blank' : '',
      collectionNoticeApproved: true, approvedCollectionNoticeVersion: 'preview',
      retentionPolicyText: cfg.retentionPolicyText || 'Preview only: nothing is stored.'
    });
  }
  var state = decide(cfg);
  var copyVersion = cfg.copyVersion || '';

  function track(name, props) {
    if (typeof root.adhdmeTrack === 'function') root.adhdmeTrack(name, props);
  }

  // ------------------------------------------------------------ browser: calls-to-action
  var seen = {};
  function seenKey(p) { return 'adhdme-matching-seen:' + p; }
  function alreadySeen(p) {       // once per placement per session; the key holds a flag, nothing else
    if (seen[p]) return true;
    try { return sessionStorage.getItem(seenKey(p)) === '1'; } catch (e) { return false; }
  }
  function markSeen(p) { seen[p] = true; try { sessionStorage.setItem(seenKey(p), '1'); } catch (e) {} }

  var ctas = Array.prototype.slice.call(document.querySelectorAll('[data-matching-cta]'));
  if (state.enabled) {
    ctas.forEach(function (el) {
      var placement = el.getAttribute('data-matching-cta');
      if (PLACEMENTS.indexOf(placement) === -1) return;
      el.hidden = false;
      var link = el.matches('a') ? el : el.querySelector('a[href]');
      if (link) link.addEventListener('click', function () { track('matching-cta-clicked', { placement: placement, copy_version: copyVersion }); });
      if (!('IntersectionObserver' in root)) return;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting || alreadySeen(placement)) return;
          // Only count a placement a person could actually see: hidden parents (the no-results state when
          // there are results) never intersect, so no extra check is needed.
          markSeen(placement);
          track('matching-cta-viewed', { placement: placement, copy_version: copyVersion });
          io.unobserve(entry.target);
        });
      }, { threshold: 0.5 });
      io.observe(el);
    });
  }

  // ------------------------------------------------------------ browser: the request page
  var form = document.querySelector('[data-matching-form]');
  if (!form) return;
  var page = form.closest('[data-matching-page]') || document;
  var $ = function (sel, r) { return (r || page).querySelector(sel); };
  var notOpen = $('[data-matching-closed]');
  var paused = $('[data-matching-paused]');
  var success = $('[data-matching-success]');
  var failure = $('[data-matching-failure]');
  var summary = $('[data-matching-errors]');
  var submitBtn = $('[data-matching-submit]');
  var submitLabel = submitBtn ? submitBtn.textContent : '';
  var body = $('[data-matching-body]');
  var emailField = form.querySelector('input[name="email"]');
  var consentBox = form.querySelector('input[name="consent"]');
  function placementFromReferrer() {
    var m = /[?&]from=(homepage|directory|no_results)\b/.exec(location.search);
    return m ? m[1] : 'directory';
  }

  var rt = $('[data-matching-response-time]');
  if (rt) { if (cfg.approvedResponseTimeText) rt.textContent = cfg.approvedResponseTimeText; else rt.hidden = true; }
  // The two routes explain themselves differently: the mail-app route stores nothing on the site.
  Array.prototype.forEach.call(page.querySelectorAll('[data-matching-route]'), function (el) {
    el.hidden = el.getAttribute('data-matching-route') !== state.route;
  });
  var ret = $('[data-matching-retention]');
  if (ret) ret.textContent = cfg.retentionPolicyText || 'Not yet set: this route does not open until it is.';
  var draft = $('[data-matching-notice-draft]');
  if (draft) draft.hidden = state.route !== 'endpoint' || cfg.collectionNoticeApproved === true;

  if (!state.enabled) {
    if (notOpen) notOpen.hidden = false;
    if (body) body.hidden = true;
    return;
  }
  if (!state.open) {
    if (state.reason === 'paused' && paused) paused.hidden = false;
    else if (notOpen) notOpen.hidden = false;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.setAttribute('aria-disabled', 'true'); }
  }

  // The appointment route: Google's own booking page, embedded, with a plain link for anyone whose browser
  // blocks the frame. The booking (and the Meet invite) is Google's to confirm; the page claims nothing.
  var booking = $('[data-matching-booking]');
  if (state.route === 'appointment' && state.open && booking) {
    var frame = booking.querySelector('iframe'), link = booking.querySelector('a[data-matching-booking-link]');
    if (frame) frame.src = cfg.appointmentUrl;
    if (link) {
      link.href = cfg.appointmentUrl;
      link.addEventListener('click', function () { track('matching-form-started', { placement: placementFromReferrer(), copy_version: copyVersion }); });
    }
    booking.hidden = false;
    form.hidden = true;
  }

  var started = false;
  function onFirstInteraction() {
    if (started) return;
    started = true;
    track('matching-form-started', { placement: placementFromReferrer(), copy_version: copyVersion });
  }
  form.addEventListener('input', onFirstInteraction, { once: true });
  form.addEventListener('change', onFirstInteraction, { once: true });

  function read() { return { email: emailField ? emailField.value : '', consent: !!(consentBox && consentBox.checked) }; }

  function showErrors(errors) {
    ['email', 'consent'].forEach(function (id) {
      var msg = $('#' + id + '-error'), group = $('[data-field="' + id + '"]'), has = !!errors[id];
      if (msg) { msg.textContent = has ? errors[id] : ''; msg.hidden = !has; }
      if (group) {
        group.classList.toggle('is-invalid', has);
        Array.prototype.forEach.call(group.querySelectorAll('input'), function (el) {
          if (has) el.setAttribute('aria-invalid', 'true'); else el.removeAttribute('aria-invalid');
        });
      }
    });
    var keys = Object.keys(errors);
    if (!summary) return;
    if (!keys.length) { summary.hidden = true; summary.innerHTML = ''; return; }
    summary.innerHTML = '<p class="text-[16px] font-extrabold text-[#1a1c1c]">Please check:</p><ul class="mt-1 list-disc pl-5 text-[15px]">' +
      keys.map(function (k) { return '<li><a href="#' + k + '-field">' + escapeHtml(errors[k]) + '</a></li>'; }).join('') + '</ul>';
    summary.hidden = false;
    summary.focus();
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  function setBusy(on) {
    if (!submitBtn) return;
    submitBtn.disabled = on || !state.open;
    submitBtn.setAttribute('aria-busy', on ? 'true' : 'false');
    submitBtn.textContent = on ? 'Sending…' : submitLabel;
  }
  function succeed() {
    track('matching-request-submitted', { placement: placementFromReferrer(), copy_version: copyVersion });
    form.reset();                       // the address is not kept anywhere once it has gone
    if (body) body.hidden = true;
    if (success) { success.hidden = false; var h = success.querySelector('h2'); if (h) h.focus(); }
    try { root.scrollTo({ top: 0, behavior: 'smooth' }); } catch (err) {}
  }

  var previewFetch = function () {
    return new Promise(function (resolve) {
      setTimeout(function () { resolve({ ok: preview !== 'fail', status: preview === 'fail' ? 503 : 202 }); }, 600);
    });
  };
  var submitter = createSubmitter(preview ? previewFetch : root.fetch.bind(root), cfg);

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!state.open) return;
    if (failure) failure.hidden = true;
    var answers = read();
    var v = validate(answers);
    showErrors(v.errors);
    if (!v.ok) return;
    if (state.route === 'mailto') {
      // Hands the message to the person's own mail app; the site never sees the address. The success screen
      // follows, since there is nothing further for the page to confirm.
      root.location.href = mailtoHref(cfg);
      succeed();
      return;
    }
    setBusy(true);
    submitter(answers).then(function (r) {
      setBusy(false);
      if (r.busy) return;
      if (r.accepted) { succeed(); return; }
      if (failure) { failure.hidden = false; failure.focus(); }   // the address stays in the field for a retry
    });
  });
})(typeof window !== 'undefined' ? window : globalThis);
