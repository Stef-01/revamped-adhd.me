// ADHDme — analytics configuration.
//
// This file stays unminified and outside the bundle on purpose: keys can be set on the live site
// without a rebuild. Every field below is optional. Leave them empty and nothing is sent anywhere —
// events are still validated against the taxonomy in analytics.js and then dropped.
//
// After switching a sink on, update privacy.html's "Cookies and local storage" section and
// measurement.html's channel list the same day.
window.ADHDME = {
  // PostHog — the person-level sink. Project API key (starts with "phc_"), from
  // PostHog → Settings → Project → Project API key. Safe to ship in the browser.
  posthogKey: '',
  // Where that project lives: https://us.i.posthog.com, https://eu.i.posthog.com, or your own host.
  posthogHost: 'https://us.i.posthog.com',
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
  // Session replay. Off deliberately: this is a health-adjacent site and a recording is a much
  // larger thing to hold than a click count. Turning it on is a decision, not a default.
  posthogSessionRecording: false,

  // GA4 — the aggregate sink, kept from the earlier setup. A measurement ID (G-XXXXXXX) sends the
  // same declared events, cookieless and without advertising signals.
  gaId: '',

  // true holds every sink until the privacy bar's Agree is pressed, queueing events meanwhile and
  // flushing them on agreement. false treats the bar as the notice it reads as today.
  requireConsent: false,

  // Logs every event and every refusal to the console. ?debug=analytics does the same per visit.
  debug: false
};
