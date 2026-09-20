// ADHDme — the ADHDme Weekly invitation
//
// A dialog offering the newsletter, shown once, and only to somebody who has already shown they
// are reading rather than passing through. Four rules it holds to:
//   1. Earned, not immediate. It waits for a minute of attention, fifteen clicks, or the foot of a
//      page — whichever comes first. A popup on arrival asks a stranger for their address.
//   2. Asked once. Dismissed is remembered in this browser's own storage, for good.
//   3. Never in the way. It does not appear over the privacy notice, on the policy pages, or to
//      somebody who has already scrolled a signup form into view — they have had the offer.
//   4. Escapable. A native <dialog>, so Escape closes it and focus is handled by the browser.
(function () {
  'use strict';

  var KEY = 'adhdme-weekly-invite';        // 'dismissed' once answered, never asked again
  var CONSENT_KEY = 'adhdme-privacy-ack';  // written by privacy-consent.js
  // The footer form, not the primary one. Its button reads "Join" rather than "Join ADHDme
  // Weekly", which is what fits beside the field once the dialog has taken its padding out of a
  // phone's width — and inside a panel already headed ADHDme Weekly, the longer label only repeats
  // itself. utm_content=popup keeps this placement apart from the footer in beehiiv.
  var FORM = '882d54e5-58fd-458f-b045-38318b963983';
  var SECONDS = 60;                        // of the page actually being looked at
  var CLICKS = 15;

  // Reading a privacy policy is not the moment to be sold a mailing list.
  var QUIET = /(^|\/)(privacy|terms|automated-decisions|measurement|404|academy|academy-login)\.html$/;

  try { if (localStorage.getItem(KEY)) return; } catch (e) {}
  if (QUIET.test(location.pathname)) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var done = false;

  function remember() {
    try { localStorage.setItem(KEY, 'dismissed'); } catch (e) {}
  }
  function track(action, trigger) {
    if (typeof window.adhdmeTrack !== 'function') return;
    window.adhdmeTrack('newsletter-invite', { action: action, trigger: trigger });
  }

  // ------------------------------------------------------------------ the dialog
  function open(trigger) {
    if (done) return;
    done = true;

    var dialog = document.createElement('dialog');
    dialog.className = 'weekly-invite';
    dialog.setAttribute('aria-labelledby', 'weekly-invite-title');
    dialog.innerHTML =
      '<button type="button" class="weekly-invite-close" data-invite-close aria-label="Close">&times;</button>' +
      '<h2 id="weekly-invite-title">ADHDme Weekly</h2>' +
      '<p>Each week, practitioners from our network share the strategies they give their own ' +
        'clients. Free, short, and you can leave whenever you like.</p>' +
      '<div class="bh-embed bh-embed--invite">' +
        '<iframe class="beehiiv-embed" src="https://subscribe-forms.beehiiv.com/' + FORM +
        '?utm_source=adhdme.au&amp;utm_medium=website&amp;utm_campaign=site_embed&amp;utm_content=popup" ' +
        'title="Subscribe to ADHDme Weekly"></iframe>' +
      '</div>' +
      '<p class="weekly-invite-fine">Unsubscribe anytime. See our ' +
        '<a href="privacy.html">Privacy Policy</a>.</p>';
    document.body.appendChild(dialog);

    var close = function () {
      remember();
      track('dismissed', trigger);
      if (dialog.open && typeof dialog.close === 'function') dialog.close();
      if (reduce) { dialog.remove(); return; }
      dialog.classList.add('is-leaving');
      setTimeout(function () { dialog.remove(); }, 180);
    };
    dialog.querySelector('[data-invite-close]').addEventListener('click', close);
    // The backdrop is part of the dialog's own box, so a click outside the panel lands on it.
    dialog.addEventListener('click', function (e) { if (e.target === dialog) close(); });
    // Escape fires 'cancel' before 'close'; remembering here covers both ways out.
    dialog.addEventListener('cancel', function () { remember(); track('dismissed', trigger); });

    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
    track('shown', trigger);
  }

  // ------------------------------------------------------------------ what counts as interest
  // Nothing starts until the privacy notice is out of the way: two dialogs at once is a wall.
  // Read the acknowledgement rather than looking for the bar in the DOM — that would depend on
  // which script ran first, and this one is bundled after it only by convention.
  function waiting() {
    try { return !localStorage.getItem(CONSENT_KEY); } catch (e) { return false; }
  }

  var seconds = 0;
  var clicks = 0;
  var timer = null;

  function fire(trigger) {
    if (done || waiting()) return;
    if (timer) { clearInterval(timer); timer = null; }
    open(trigger);
  }

  // Time, counted only while the page is actually in front of somebody.
  timer = setInterval(function () {
    if (document.visibilityState !== 'visible') return;
    seconds += 1;
    if (seconds >= SECONDS) fire('time');
  }, 1000);

  document.addEventListener('click', function () {
    clicks += 1;
    if (clicks >= CLICKS) fire('clicks');
  }, true);

  // The foot of the page: somebody who has read to the end has read enough to be asked.
  if (window.IntersectionObserver) {
    var foot = document.querySelector('footer');
    if (foot) {
      var footWatch = new IntersectionObserver(function (entries) {
        if (entries.some(function (e) { return e.isIntersecting; })) {
          footWatch.disconnect();
          fire('foot');
        }
      }, { threshold: 0 });
      footWatch.observe(foot);
    }

    // Somebody who has scrolled a signup form into view has already been offered this. Do not
    // interrupt them to offer it again.
    Array.prototype.forEach.call(document.querySelectorAll('.bh-embed'), function (el) {
      var seen = new IntersectionObserver(function (entries) {
        if (!entries.some(function (e) { return e.isIntersecting; })) return;
        seen.disconnect();
        done = true;
        if (timer) { clearInterval(timer); timer = null; }
      }, { threshold: 0.5 });
      seen.observe(el);
    });
  }
})();
