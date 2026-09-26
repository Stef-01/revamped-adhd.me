// ADHDme — analytics configuration.
//
// This file stays unminified and outside the bundle on purpose: keys can be set on the live site
// without a rebuild. Every field below is optional. Leave them empty and nothing is sent anywhere —
// events are still validated against the taxonomy in analytics.js and then dropped.
//
// After switching a sink on, update privacy.html's "Cookies and analytics" section and
// measurement.html the same day.
window.ADHDME = {
  // PostHog — the person-level sink. Project API key (starts with "phc_"), from
  // PostHog → Settings → Project → Project API key. Safe to ship in the browser.
  posthogKey: 'phc_nCTxy7xwt9hCTwZradey4xhWqwXraFc63S3TjRnV575d',
  // Where that project lives: https://us.i.posthog.com, https://eu.i.posthog.com, or your own host.
  posthogHost: 'https://us.i.posthog.com',

  // The only hostnames allowed to send. Anywhere else — localhost, a Vercel preview, somebody's
  // fork — validates its events and drops them, exactly as an unconfigured key does.
  //
  // This is not belt and braces, it is a repair. A month of dev browsing on localhost:5173 had
  // put 1,324 events into the production project, a quarter of everything in it, and they landed
  // on the same clinician pages the provider comparison ranks. There is no way to tell them apart
  // afterwards, so the fix has to be that they never arrive.
  productionHosts: ['www.adhdme.au', 'adhdme.au'],
  // Where the library itself is served from. Empty derives it from posthogHost
  // (us.i → us-assets.i, eu.i → eu-assets.i), which is what PostHog Cloud wants.
  posthogAssetHost: '',

  // Every visitor gets a person row, so the Persons list and the dashboard show people rather than
  // just totals. 'identified_only' would only profile people we call identify() on, and this site
  // never does, so that setting would leave the Persons list empty.
  posthogPersonProfiles: 'always',
  // PostHog's own click/pressed-element capture, on top of the declared events. The declared events
  // are what the dashboards are built on; this is the safety net for links nobody thought to name.
  posthogAutocapture: true,
  // Session replay. On, as a decision rather than a default — this is a health-adjacent site and a
  // recording is a much larger thing to hold than a click count. What makes it defensible here:
  // every input is masked before recording (analytics.js), so the newsletter email is never in a
  // recording and there is nothing else on these pages to type into; the practice's booking page
  // is a different origin in another tab and was never recordable; and the opt-out, Global Privacy
  // Control and the measurement.html button stop it with everything else. privacy.html and
  // measurement.html say so in plain words.
  posthogSessionRecording: true,

  // GA4 — the aggregate sink, kept from the earlier setup. A measurement ID (G-XXXXXXX) sends the
  // same declared events, cookieless and without advertising signals.
  gaId: '',

  // true holds every sink until the privacy bar's Agree is pressed, queueing events meanwhile and
  // flushing them on agreement. false treats the bar as the notice it reads as today.
  requireConsent: false,

  // Logs every event and every refusal to the console. ?debug=analytics does the same per visit.
  debug: false
};
