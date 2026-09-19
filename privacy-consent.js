// ADHDme — privacy notice (ported from the ADHD repo's PrivacyConsent)
// A bar on first arrival, a dialog with the sentences from the policy, and one value in the
// browser's own storage recording the agreement. Agreeing dispatches 'adhdme-privacy-ack' on window,
// which is what analytics.js waits for when analytics-config.js sets requireConsent.
(function () {
  'use strict';
  var KEY = 'adhdme-privacy-ack';
  var EXIT_MS = 180;
  try { if (localStorage.getItem(KEY)) return; } catch (e) {}

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var bar = document.createElement('div');
  bar.className = 'consent-bar';
  bar.setAttribute('role', 'region');
  bar.setAttribute('aria-label', 'Privacy');
  bar.innerHTML =
    '<p>We count visits and which booking links get used, never who used them, and nothing here is used for advertising.</p>' +
    '<div class="consent-actions">' +
      '<button type="button" class="consent-read" data-consent-read>Privacy policy</button>' +
      '<button type="button" class="consent-agree" data-consent-agree>Agree</button>' +
    '</div>' +
    '<dialog class="consent-dialog" aria-labelledby="consent-title">' +
      '<h2 id="consent-title">How this site handles what you give it</h2>' +
      '<ul>' +
        '<li>There is nothing on these pages to fill in. The network list and each clinician’s own page are built ahead of time and served the same way to everybody, so reading them tells us nothing you have typed.</li>' +
        '<li>We count pages opened and booking links followed, against a browser that has no name attached to it. That count says which clinician a link was for, not who followed it, and you can switch it off on the <a href="measurement.html">measurement page</a>.</li>' +
        '<li>When you follow a booking link to Healthengine, Halaxy or a clinic’s own page, we count that the link was used, and from the moment their page opens, that site’s own privacy policy governs what you enter there.</li>' +
        '<li>Your agreement is kept in your browser’s own storage and never leaves your device.</li>' +
      '</ul>' +
      '<p><a href="privacy.html" target="_blank" rel="noopener">Read the full privacy policy</a></p>' +
      '<div class="consent-dialog-actions">' +
        '<button type="button" class="consent-read" data-consent-close>Close</button>' +
        '<button type="button" class="consent-agree" data-consent-agree>I agree</button>' +
      '</div>' +
    '</dialog>';
  document.body.appendChild(bar);
  var setOffset = function () { var h = bar.getBoundingClientRect().height; document.documentElement.style.setProperty('--consent-h', h + 'px'); document.documentElement.classList.add('has-consent'); document.body.classList.add('has-consent'); };
  setOffset(); window.addEventListener('resize', setOffset, { passive: true });

  var dialog = bar.querySelector('dialog');
  var remove = function () { if (bar.parentNode) bar.parentNode.removeChild(bar); document.documentElement.classList.remove('has-consent'); document.body.classList.remove('has-consent'); };
  var agree = function () {
    try { localStorage.setItem(KEY, '1'); } catch (e) {}
    try { window.dispatchEvent(new Event('adhdme-privacy-ack')); } catch (e) {}
    if (dialog.open) dialog.close();
    if (reduce) { remove(); return; }
    bar.classList.add('is-leaving');
    setTimeout(remove, EXIT_MS);
  };
  bar.querySelector('[data-consent-read]').addEventListener('click', function () {
    if (typeof dialog.showModal === 'function') dialog.showModal(); else location.href = 'privacy.html';
  });
  bar.querySelector('[data-consent-close]').addEventListener('click', function () { dialog.close(); });
  bar.querySelectorAll('[data-consent-agree]').forEach(function (b) { b.addEventListener('click', agree); });
})();
