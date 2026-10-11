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
  var STATES = ['NSW', 'QLD', 'VIC', 'WA', 'SA', 'TAS', 'ACT', 'NT'];
  var SERVICES = ['assessment', 'medical', 'psychology', 'allied-or-coaching', 'not-sure'];
  var MODES = ['in-person', 'telehealth', 'either'];
  var BUDGETS = ['', 'not-sure', 'prefer-not-to-say'];     // no price bands: none are approved yet
  var PRIORITIES = ['availability', 'cost', 'location', 'approach', 'not-sure'];
  var MAX_PRIORITIES = 2;
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var NAME = /^[A-Za-zÀ-ɏ' .-]{1,40}$/;
  var LOCALITY = /^[A-Za-z0-9À-ɏ' .-]{2,40}$/;
  var TIMEOUT_MS = 15000;

  // ------------------------------------------------------------ pure: what the configuration allows
  // {enabled, open, reason}: reason names the first thing that keeps intake closed, for the page to explain.
  function decide(cfg) {
    cfg = cfg || {};
    var enabled = cfg.pilotEnabled === true;
    if (!enabled) return { enabled: false, open: false, reason: 'disabled' };
    if (cfg.intakeOpen !== true) return { enabled: true, open: false, reason: 'paused' };
    if (!cfg.requestEndpoint) return { enabled: true, open: false, reason: 'no-endpoint' };
    if (cfg.collectionNoticeApproved !== true || !cfg.approvedCollectionNoticeVersion) {
      return { enabled: true, open: false, reason: 'notice-unapproved' };
    }
    if (!cfg.retentionPolicyText) return { enabled: true, open: false, reason: 'no-retention' };
    return { enabled: true, open: true, reason: '' };
  }

  // ------------------------------------------------------------ pure: validation
  // answers: {scope, service, state, locality, mode, budget, priorities[], firstName, email, consent}
  // Returns {ok, outOfScope, errors: {field: message}} with messages in the site's plain voice.
  function validate(a) {
    a = a || {};
    var errors = {};
    if (a.scope !== 'self-adult') {
      return { ok: false, outOfScope: a.scope === 'other', errors: a.scope ? {} : { scope: 'Choose who the care is for.' } };
    }
    if (SERVICES.indexOf(a.service) === -1) errors.service = 'Choose the kind of care you are looking for.';
    if (STATES.indexOf(a.state) === -1) errors.state = 'Choose your state or territory.';
    if (!LOCALITY.test(String(a.locality || '').trim())) errors.locality = 'Enter your suburb or postcode (letters and numbers only).';
    if (MODES.indexOf(a.mode) === -1) errors.mode = 'Choose in person, telehealth or either.';
    if (BUDGETS.indexOf(a.budget === undefined || a.budget === null ? '' : a.budget) === -1) errors.budget = 'Choose one of the options.';
    var pr = Array.isArray(a.priorities) ? a.priorities : [];
    if (pr.some(function (p) { return PRIORITIES.indexOf(p) === -1; })) errors.priorities = 'Choose from the options listed.';
    else if (pr.length > MAX_PRIORITIES) errors.priorities = 'Choose up to two.';
    if (!NAME.test(String(a.firstName || '').trim())) errors.firstName = 'Enter your first name.';
    if (!EMAIL.test(String(a.email || '').trim())) errors.email = 'Enter an email address we can reply to.';
    if (a.consent !== true) errors.consent = 'Tick the box so we can act on your request.';
    return { ok: !Object.keys(errors).length, outOfScope: false, errors: errors };
  }

  // The request body: only the fields the pilot collects, trimmed, plus the notice version agreed to.
  function payload(a, cfg) {
    return {
      service: a.service, state: a.state, locality: String(a.locality || '').trim(), mode: a.mode,
      budget: a.budget || '', priorities: (a.priorities || []).slice(0, MAX_PRIORITIES),
      first_name: String(a.firstName || '').trim(), email: String(a.email || '').trim(),
      consent: true, collection_notice_version: (cfg && cfg.approvedCollectionNoticeVersion) || '',
      copy_version: (cfg && cfg.copyVersion) || ''
    };
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

  var api = { decide: decide, validate: validate, payload: payload, createSubmitter: createSubmitter,
              PLACEMENTS: PLACEMENTS, MAX_PRIORITIES: MAX_PRIORITIES };
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
      pilotEnabled: true, intakeOpen: preview !== 'paused', requestEndpoint: '/__matching-preview',
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
  var outOfScope = $('[data-matching-out-of-scope]');
  var success = $('[data-matching-success]');
  var failure = $('[data-matching-failure]');
  var summary = $('[data-matching-errors]');
  var submitBtn = $('[data-matching-submit]');
  var submitLabel = submitBtn ? submitBtn.textContent : '';
  var body = $('[data-matching-body]');

  // Optional approved sentences, shown only when configured.
  var rt = $('[data-matching-response-time]');
  if (rt) { if (cfg.approvedResponseTimeText) rt.textContent = cfg.approvedResponseTimeText; else rt.hidden = true; }
  var pt = $('[data-matching-price]');
  if (pt) { if (cfg.approvedPilotPriceText) pt.textContent = cfg.approvedPilotPriceText; else pt.hidden = true; }
  var ret = $('[data-matching-retention]');
  if (ret) ret.textContent = cfg.retentionPolicyText || 'Not yet set: the pilot does not open until it is.';
  var draft = $('[data-matching-notice-draft]');
  if (draft) draft.hidden = cfg.collectionNoticeApproved === true;

  if (!state.enabled) {
    // Pilot off: the page says so and sends nobody anywhere.
    if (notOpen) notOpen.hidden = false;
    if (body) body.hidden = true;
    return;
  }
  if (!state.open) {
    if (state.reason === 'paused' && paused) { paused.hidden = false; }
    else if (notOpen) { notOpen.hidden = false; }
    if (submitBtn) { submitBtn.disabled = true; submitBtn.setAttribute('aria-disabled', 'true'); }
  }

  // Scope gate: the pilot is for adults seeking care for themselves.
  var fields = $('[data-matching-fields]');
  function applyScope() {
    var v = (form.querySelector('input[name="scope"]:checked') || {}).value;
    var other = v === 'other';
    if (outOfScope) outOfScope.hidden = !other;
    if (fields) fields.hidden = v !== 'self-adult';
  }
  Array.prototype.forEach.call(form.querySelectorAll('input[name="scope"]'), function (r) { r.addEventListener('change', applyScope); });
  applyScope();

  // Up to two priorities: once two are ticked, the rest are disabled rather than refused later.
  var priorityBoxes = Array.prototype.slice.call(form.querySelectorAll('input[name="priorities"]'));
  function limitPriorities() {
    var on = priorityBoxes.filter(function (b) { return b.checked; }).length;
    priorityBoxes.forEach(function (b) { b.disabled = !b.checked && on >= MAX_PRIORITIES; });
  }
  priorityBoxes.forEach(function (b) { b.addEventListener('change', limitPriorities); });

  // Form started: the first meaningful interaction, once per attempt.
  var started = false;
  function onFirstInteraction() {
    if (started) return;
    started = true;
    track('matching-form-started', { placement: placementFromReferrer(), copy_version: copyVersion });
  }
  function placementFromReferrer() {
    // Which call-to-action brought the person here, read from the link's own ?from= value (never from
    // anything typed). Unknown or direct arrivals are reported as 'homepage' only when that is the referrer.
    var m = /[?&]from=(homepage|directory|no_results)\b/.exec(location.search);
    return m ? m[1] : 'directory';
  }
  form.addEventListener('input', onFirstInteraction, { once: true });
  form.addEventListener('change', onFirstInteraction, { once: true });

  function read() {
    var val = function (name) { var el = form.querySelector('[name="' + name + '"]:checked, select[name="' + name + '"], input[name="' + name + '"]:not([type=radio]):not([type=checkbox])'); return el ? el.value : ''; };
    return {
      scope: val('scope'), service: val('service'), state: val('state'), locality: val('locality'), mode: val('mode'),
      budget: val('budget'),
      priorities: priorityBoxes.filter(function (b) { return b.checked; }).map(function (b) { return b.value; }),
      firstName: val('first_name'), email: val('email'),
      consent: !!(form.querySelector('input[name="consent"]') || {}).checked
    };
  }

  // Errors: a summary at the top that lists each one as a link, and a message under every field it names.
  var ERROR_IDS = { scope: 'scope', service: 'service', state: 'state', locality: 'locality', mode: 'mode', budget: 'budget',
                    priorities: 'priorities', firstName: 'first_name', email: 'email', consent: 'consent' };
  function showErrors(errors) {
    Object.keys(ERROR_IDS).forEach(function (k) {
      var id = ERROR_IDS[k], msg = $('#' + id + '-error'), group = $('[data-field="' + id + '"]');
      var has = !!errors[k];
      if (msg) { msg.textContent = has ? errors[k] : ''; msg.hidden = !has; }
      if (group) {
        group.classList.toggle('is-invalid', has);
        Array.prototype.forEach.call(group.querySelectorAll('input, select'), function (el) {
          if (has) el.setAttribute('aria-invalid', 'true'); else el.removeAttribute('aria-invalid');
        });
      }
    });
    var keys = Object.keys(errors);
    if (!summary) return;
    if (!keys.length) { summary.hidden = true; summary.innerHTML = ''; return; }
    var list = keys.map(function (k) {
      var id = ERROR_IDS[k];
      return '<li><a href="#' + id + '-field">' + escapeHtml(errors[k]) + '</a></li>';
    }).join('');
    summary.innerHTML = '<h2 class="text-[17px] font-extrabold text-[#1a1c1c]">Please check ' + keys.length + (keys.length === 1 ? ' answer' : ' answers') + '</h2><ul class="mt-2 list-disc pl-5 text-[15px]">' + list + '</ul>';
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

  var previewFetch = function (url, init) {
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
    if (v.outOfScope) { applyScope(); if (outOfScope) outOfScope.focus(); return; }
    showErrors(v.errors);
    if (!v.ok) return;
    setBusy(true);
    submitter(answers).then(function (r) {
      setBusy(false);
      if (r.busy) return;
      if (r.accepted) {
        track('matching-request-submitted', { placement: placementFromReferrer(), copy_version: copyVersion });
        form.reset();                       // the answers are not kept anywhere once the server has them
        if (body) body.hidden = true;
        if (success) { success.hidden = false; var h = success.querySelector('h2'); if (h) h.focus(); }
        try { root.scrollTo({ top: 0, behavior: 'smooth' }); } catch (err) {}
        return;
      }
      if (failure) { failure.hidden = false; failure.focus(); }   // answers stay in the fields for a retry
    });
  });
})(typeof window !== 'undefined' ? window : globalThis);
