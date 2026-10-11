// ADHDme — matching pilot configuration.
//
// Like analytics-config.js, this file stays unminified and outside the bundle so the pilot can be switched
// on the live site without a rebuild. matching.js reads it; MATCHING-PILOT.md explains each value.
//
// The pilot is deliberately small: a person leaves an email address, the team sends them a five-minute
// survey, and a founder matches them to clinicians by hand. Nothing is automated.
window.ADHDME_MATCHING = {
  // Shows the "Request matching help" cards on the home page and the Network, and lets the request page
  // render its form. Off: every call-to-action stays hidden and the page says the pilot is not open.
  pilotEnabled: true,

  // Lets the form send. Off while the team is at capacity: the page says so, the button is disabled, and
  // browsing stays available. It is not a waitlist: nothing is stored while it is off.
  intakeOpen: true,

  // Where the request goes. With contactEmail set and requestEndpoint empty, the form opens the person's
  // own mail app with a short message addressed to the team (the same route as the site's Contact link),
  // so nothing is stored by the site at all. A requestEndpoint, once one exists, is POSTed to instead
  // and must validate, rate-limit and store where only staff can read; until then leave it empty.
  contactEmail: 'info@adhdme.au',
  requestEndpoint: '',

  // Needed only for the requestEndpoint route, where the site would hold the request itself: the
  // collection notice shown above the consent box must be approved and versioned, and a retention rule
  // written down. The mail-app route stores nothing here, so it needs neither.
  collectionNoticeApproved: false,
  approvedCollectionNoticeVersion: '',
  retentionPolicyText: '',

  // Optional approved sentences. Empty shows nothing: the page never promises a turnaround nobody signed off.
  approvedResponseTimeText: '',

  // A label for the copy in use, carried on the pilot's analytics events. Never anything a visitor typed.
  copyVersion: 'pilot-2026-10-b'
};
