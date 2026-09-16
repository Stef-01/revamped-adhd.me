// ADHDme — privacy notice (ported from the ADHD repo's PrivacyConsent)
// A bar on first arrival, a dialog with the three sentences from the policy, and one value in the
// browser's own storage recording the agreement. Nothing is sent anywhere.
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
    '<p>We use only what is needed to run this site, and nothing you enter is used for advertising.</p>' +
    '<div class="consent-actions">' +
      '<button type="button" class="consent-read" data-consent-read>Privacy policy</button>' +
      '<button type="button" class="consent-agree" data-consent-agree>Agree</button>' +
    '</div>' +
    '<dialog class="consent-dialog" aria-labelledby="consent-title">' +
      '<h2 id="consent-title">How this site handles what you give it</h2>' +
      '<ul>' +
        '<li>Reading these pages tells us nothing about you. There is nothing on them to fill in: the list of GPs and each doctor’s own page are built ahead of time and served the same way to everybody.</li>' +
        '<li>When you follow a booking link to Healthengine, we count that the link was used, not who used it, and from the moment their page opens, Healthengine’s own privacy policy governs what you enter there.</li>' +
        '<li>Your agreement is kept in your browser’s own storage and never leaves your device.</li>' +
      '</ul>' +
      '<p><a href="privacy.html" target="_blank" rel="noopener">Read the full privacy policy</a></p>' +
      '<div class="consent-dialog-actions">' +
        '<button type="button" class="consent-read" data-consent-close>Close</button>' +
        '<button type="button" class="consent-agree" data-consent-agree>I agree</button>' +
      '</div>' +
    '</dialog>';
  document.body.appendChild(bar);

  var dialog = bar.querySelector('dialog');
  var remove = function () { if (bar.parentNode) bar.parentNode.removeChild(bar); };
  var agree = function () {
    try { localStorage.setItem(KEY, '1'); } catch (e) {}
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
