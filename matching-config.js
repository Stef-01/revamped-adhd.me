// ADHDme — matching pilot configuration.
//
// Like analytics-config.js, this file stays unminified and outside the bundle so the pilot can be switched
// on the live site without a rebuild. Everything defaults to OFF: with this file as committed, no visitor
// sees a matching call-to-action, the request page explains the pilot is not open, and nothing is sent
// anywhere. matching.js reads it; MATCHING-PILOT.md says what each value needs before it can change.
window.ADHDME_MATCHING = {
  // Shows the "Request matching help" cards on the home page, the Network and the no-results state, and
  // lets the request page render its form. Off: every call-to-action stays hidden.
  pilotEnabled: false,

  // Lets the form send. Off while the pilot is at capacity: the page explains that, the button is disabled,
  // and browsing stays available. Off also while there is nowhere approved to send to (see below).
  intakeOpen: false,

  // Where a request is POSTed as JSON. Empty: live submission is disabled whatever intakeOpen says. Must be a
  // same-site endpoint that validates server-side, rate-limits, stores the request where only staff can
  // read it, and never writes the answers into logs or email. None exists in this repository today.
  requestEndpoint: '',

  // The collection notice shown above the consent checkbox is a DRAFT until a founder approves its wording.
  // Approving it means setting this to true and giving the approved text a version label, which is sent
  // with each request so the record says which notice the person agreed to.
  collectionNoticeApproved: false,
  approvedCollectionNoticeVersion: '',

  // Optional approved sentences. Empty strings show nothing: the page never promises a turnaround or a
  // price that nobody signed off.
  approvedResponseTimeText: '',
  approvedPilotPriceText: '',

  // The retention and deletion rule for stored requests, written as a sentence for the collection notice
  // (for example "Requests are deleted 90 days after they are closed."). Empty: the notice says it is
  // not yet set, and intake stays closed.
  retentionPolicyText: '',

  // A label for the call-to-action and form copy in use, carried on the pilot's analytics events so a
  // wording change can be told apart from a behaviour change. Never contains anything a visitor typed.
  copyVersion: 'pilot-2026-10-a'
};
