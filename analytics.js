// ADHDme — analytics, attribution and person-level reporting
//
// Four rules the site holds to:
//   1. A closed taxonomy. Every event name and every property value is declared below; anything else
//      is refused and logged as "analytics-refused" instead of becoming a row that looks real. The
//      vocabularies for clinician, category, practice and destination are derived from the registry,
//      so a dashboard cannot show a clinician this site does not have.
//   2. Nothing leaves the page unless a sink is configured (analytics-config.js). Until then events
//      are validated and dropped. The UTM tail on booking links works regardless.
//   3. A measurement budget. Sending never delays a click: outbound events go by beacon and the link
//      navigates immediately.
//   4. An opt-out that works. ?analytics=off, a Global Privacy Control signal, or the button on
//      measurement.html stops every sink on this device, for good.
(function () {
  'use strict';

  // ------------------------------------------------------------------ the registry
  // One row per bookable clinician: the booking link the outbound handler matches, the profile page
  // that names them, and the words a dashboard reads back. Keep this in step with CLINICIANS in
  // scripts/build-profiles.py — its --check refuses to build a profile this file does not declare.
  var CLINICIANS = {
    'anubhav-saxena': {
      booking: /dr-anubhav-saxena\/p123180/, profile: 'dr-anubhav-saxena.html',
      name: 'Dr Anubhav Saxena', category: 'gp',
      practice: 'Beecroft Family & Skin Cancer Clinic', destination: 'healthengine',
      expertise: ['assessment', 'physical-health', 'integrative'], ages: ['adults']
    },
    'anu-saxena': {
      booking: /dr-anusha-saxena\/p160121/, profile: 'dr-anu-saxena.html',
      name: 'Dr Anu Saxena', category: 'gp',
      practice: 'Bay Health Clinic', destination: 'healthengine',
      expertise: ['mental-health', 'womens-health'], ages: ['children', 'adults']
    },
    'paula-garrido': {
      booking: /wellnesspsychologyclinic\.com\.au\/appointment-page/, profile: 'paula-garrido.html',
      name: 'Paula Garrido', category: 'psychologist',
      practice: 'Wellness Psychology Clinic', destination: 'clinic-form',
      expertise: ['autism', 'trauma', 'neuroaffirming'], ages: ['adults']
    },
    // GOALS Psychology: one clinic booking page for the seven bookable clinicians, so the regex cannot
    // tell them apart. clinicianFor() resolves it from the profile page the click came from.
    'kate-row': {
      booking: /halaxy\.com\/book\/goals-psychology/, profile: 'kate-row.html',
      name: 'Kate Row', category: 'psychologist',
      practice: 'GOALS Psychology', destination: 'halaxy',
      expertise: ['therapy', 'ndis'], ages: ['children', 'teens', 'adults']
    },
    'ellie-putland': {
      booking: /halaxy\.com\/book\/goals-psychology/, profile: 'ellie-putland.html',
      name: 'Ellie Putland', category: 'psychologist',
      practice: 'GOALS Psychology', destination: 'halaxy',
      expertise: ['therapy', 'trauma'], ages: ['teens', 'adults']
    },
    'lachlan-avent': {
      booking: /halaxy\.com\/book\/goals-psychology/, profile: 'lachlan-avent.html',
      name: 'Lachlan Avent', category: 'psychologist',
      practice: 'GOALS Psychology', destination: 'halaxy',
      expertise: ['assessment', 'autism', 'parenting'], ages: ['children', 'teens', 'adults']
    },
    'samantha-courtney': {
      booking: /halaxy\.com\/book\/goals-psychology/, profile: 'samantha-courtney.html',
      name: 'Samantha Courtney', category: 'psychologist',
      practice: 'GOALS Psychology', destination: 'halaxy',
      expertise: ['eating-disorders', 'perinatal'], ages: ['adults']
    },
    'lauren-poulos': {
      booking: /halaxy\.com\/book\/goals-psychology/, profile: 'lauren-poulos.html',
      name: 'Lauren Poulos', category: 'psychologist',
      practice: 'GOALS Psychology', destination: 'halaxy',
      expertise: ['assessment', 'early-intervention', 'parenting'], ages: ['children']
    },
    'alice-bui': {
      booking: /halaxy\.com\/book\/goals-psychology/, profile: 'alice-bui.html',
      name: 'Alice Bui', category: 'psychologist',
      practice: 'GOALS Psychology', destination: 'halaxy',
      expertise: ['therapy', 'trauma', 'cald'], ages: ['teens', 'adults']
    },
    'meera-lakhani': {
      booking: /goalspsychology\.com\/contact/, profile: 'meera-lakhani.html',
      name: 'Meera Lakhani', category: 'psychologist',
      practice: 'GOALS Psychology', destination: 'clinic-contact',
      expertise: ['assessment', 'autism', 'education'], ages: ['children', 'teens']
    },
    'flynn-simonis': {
      booking: /halaxy\.com\/book\/goals-psychology/, profile: 'flynn-simonis.html',
      name: 'Flynn Simonis', category: 'allied',
      practice: 'GOALS Psychology', destination: 'halaxy',
      expertise: ['occupational-therapy', 'education', 'ndis'], ages: ['children', 'teens']
    },
    'lara-schulz': {
      booking: /ncau\.com\.au\/contact-us/, profile: 'lara-schulz.html',
      name: 'Lara Schulz', category: 'allied',
      practice: 'Neurotherapy Clinics Australia', destination: 'clinic-contact',
      expertise: ['brain-mapping', 'neurotherapy'], ages: ['children', 'teens', 'adults']
    },
    'fiona-alexander': {
      booking: /reachadhd\.com\.au\/contact/, profile: 'fiona-alexander.html',
      name: 'Fiona Alexander', category: 'coach',
      practice: 'REACH ADHD Coaching and Consultancy', destination: 'clinic-contact',
      expertise: ['executive-function', 'education', 'coaching'], ages: ['children', 'teens', 'adults']
    },
    'debbie-hirte': {
      booking: /reachadhd\.com\.au\/contact/, profile: 'debbie-hirte.html',
      name: 'Debbie Hirte', category: 'coach',
      practice: 'REACH ADHD Coaching and Consultancy', destination: 'clinic-contact',
      expertise: ['executive-function', 'education', 'coaching'], ages: ['children', 'teens']
    },
    'romney-taylor': {
      booking: /reachadhd\.com\.au\/contact/, profile: 'romney-taylor.html',
      name: 'Romney Taylor', category: 'coach',
      practice: 'REACH ADHD Coaching and Consultancy', destination: 'clinic-contact',
      expertise: ['executive-function', 'education', 'coaching'], ages: ['children', 'teens']
    },
    'erin-lysle': {
      booking: /reachadhd\.com\.au\/contact/, profile: 'erin-lysle.html',
      name: 'Erin Lysle', category: 'coach',
      practice: 'REACH ADHD Coaching and Consultancy', destination: 'clinic-contact',
      expertise: ['executive-function', 'coaching', 'social-skills'], ages: ['children', 'teens', 'adults']
    },
    'donna-italiano': {
      booking: /reachadhd\.com\.au\/contact/, profile: 'donna-italiano.html',
      name: 'Donna Italiano', category: 'coach',
      practice: 'REACH ADHD Coaching and Consultancy', destination: 'clinic-contact',
      expertise: ['executive-function', 'coaching', 'emotional-regulation'], ages: ['children', 'teens']
    },
    'kate-dallimore': {
      booking: /reachadhd\.com\.au\/contact/, profile: 'kate-dallimore.html',
      name: 'Kate Dallimore', category: 'coach',
      practice: 'REACH ADHD Coaching and Consultancy', destination: 'clinic-contact',
      expertise: ['executive-function', 'coaching', 'trauma'], ages: ['teens', 'adults']
    },
    'jessica-katsamatsas': {
      booking: /zandahealth\.com\/clientportal\/neutralmindspsychology/, profile: 'jessica-katsamatsas.html',
      name: 'Jessica Katsamatsas', category: 'psychologist',
      practice: 'Neutral Minds Psychology', destination: 'zanda',
      expertise: ['therapy', 'neuroaffirming', 'trauma'], ages: ['adults']
    },
    'bart-traynor': {
      booking: /atlantis-recovery-centre\/doctors\/bart-traynor-1/, profile: 'bart-traynor.html',
      name: 'Bart Traynor', category: 'psychologist',
      practice: 'Atlantis Recovery Centre', destination: 'hotdoc',
      expertise: ['therapy', 'performance', 'supervision'], ages: ['adults']
    },
    'jeff-leech': {
      booking: /atlantis-recovery-centre\/doctors/, profile: 'jeff-leech.html',
      name: 'Jeff Leech', category: 'psychologist',
      practice: 'Atlantis Recovery Centre', destination: 'hotdoc',
      expertise: ['therapy', 'trauma', 'performance'], ages: ['adults']
    },
    'michael-rehardt': {
      booking: /atlantis-recovery-centre\/doctors/, profile: 'michael-rehardt.html',
      name: 'Michael Rehardt', category: 'psychologist',
      practice: 'Atlantis Recovery Centre', destination: 'hotdoc',
      expertise: ['therapy'], ages: ['adults']
    },
    'sarah-savage': {
      booking: /atlantis-recovery-centre\/doctors\/sarah-savage/, profile: 'sarah-savage.html',
      name: 'Sarah Savage', category: 'allied',
      practice: 'Atlantis Recovery Centre', destination: 'hotdoc',
      expertise: ['exercise-physiology', 'physical-health'], ages: ['adults']
    },
    'yuri-lima': {
      booking: /atlantis-recovery-centre\/doctors/, profile: 'yuri-lima.html',
      name: 'Dr Yuri Lima', category: 'allied',
      practice: 'Atlantis Recovery Centre', destination: 'hotdoc',
      expertise: ['physiotherapy', 'physical-health'], ages: ['adults']
    },
    'tom-hissey': {
      booking: /atlantis-recovery-centre\/doctors/, profile: 'tom-hissey.html',
      name: 'Tom Hissey', category: 'allied',
      practice: 'Atlantis Recovery Centre', destination: 'hotdoc',
      expertise: ['physiotherapy', 'physical-health'], ages: ['adults']
    },
    'lester-rafanan': {
      booking: /atlantis-recovery-centre\/doctors/, profile: 'lester-rafanan.html',
      name: 'Lester Rafanan', category: 'allied',
      practice: 'Atlantis Recovery Centre', destination: 'hotdoc',
      expertise: ['physiotherapy', 'physical-health', 'ndis'], ages: ['adults']
    }
  };

  function unique(list) {
    var out = [];
    list.forEach(function (v) { if (out.indexOf(v) === -1) out.push(v); });
    return out;
  }
  function column(key) {
    return unique(Object.keys(CLINICIANS).map(function (id) { return CLINICIANS[id][key]; }));
  }

  function columnFlat(key) {
    var out = [];
    Object.keys(CLINICIANS).forEach(function (id) {
      (CLINICIANS[id][key] || []).forEach(function (v) { if (out.indexOf(v) === -1) out.push(v); });
    });
    return out;
  }

  var CLINICIAN_IDS = Object.keys(CLINICIANS);
  var CLINICIAN_NAMES = column('name');
  var CATEGORIES = column('category');        // gp · psychologist · allied · coach
  var PRACTICES = column('practice');
  var DESTINATIONS = column('destination');   // healthengine · halaxy · zanda · clinic-form · clinic-contact
  // Where on the site the click happened, and which link on that page it was. A page may grow a
  // second booking link; mark it with data-booking-link="..." and add the name here.
  var BOOKING_SURFACES = ['network', 'profile', 'finder', 'examples', 'demo'];
  var BOOKING_LINKS = ['profile-cta', 'deck-card', 'other'];
  // What each clinician is sought for, and who they see. Kept here beside the other analytics
  // metadata so a dashboard can ask "what is being looked for", not just "who was looked at" —
  // the answer to that is what says which expertise the network is short of. Derived from the
  // chips and experience in scripts/build-profiles.py; keep the two in step.
  var EXPERTISE = columnFlat('expertise');
  var AGE_BANDS = ['children', 'teens', 'adults'];

  // Where a visit came from, and what it was reading when it came. utm_source names the channel,
  // utm_campaign the theme of the post, utm_content the post itself. The first two are closed
  // vocabularies so a dashboard reads words the team agreed on; the third is a token, because
  // posts are made faster than code is deployed.
  var CHANNELS = ['instagram', 'facebook', 'tiktok', 'linkedin', 'youtube', 'newsletter',
    'search', 'direct', 'referral', 'other'];
  var CONTENT_THEMES = ['adult-adhd', 'women', 'children', 'autism', 'assessment', 'medication',
    'workplace', 'relationships', 'body-doubling', 'late-diagnosis', 'cost-access',
    'clinician-spotlight', 'other'];

  // How far down a clinician's page somebody actually got, by the landmarks every profile carries:
  // the hero they land on, the fee table, the "Also in the network" row, then the foot of the page.
  // The fee table now sits at the foot of the profile rather than under the hero, so 'fees' means
  // "read the whole profile", not "scrolled past the booking button". The rung kept its name so the
  // series does not split; it is worth re-anchoring to the Experience block if a mid-page rung is
  // wanted back, which would be a new vocabulary value.
  // The ADHDme Weekly dialog: what it did, and what earned it. newsletter-invite.js raises these.
  // Whether anybody actually subscribed is beehiiv's to say — the form carries utm_content=popup.
  var INVITE_ACTIONS = ['shown', 'dismissed'];
  var INVITE_TRIGGERS = ['time', 'clicks', 'foot'];
  var READ_DEPTHS = ['hero', 'fees', 'network', 'end'];
  var YES_NO = ['yes', 'no'];
  // The header's four, then the landing page's two doors wherever they appear: the hero card, the
  // pair of panels, and the closing banner.
  var LANDING_CONTROLS = ['nav-learn', 'nav-cta', 'nav-doctors', 'nav-approach',
    'door-diagnosis', 'door-psychology', 'door-allied', 'door-coaches'];
  // Every page that loads this bundle, in the words a dashboard should read back. Anything not
  // listed counts as 'other' rather than being refused, so a new page is never silently uncounted.
  var PAGES = {
    'index.html': 'landing', 'the-doctors.html': 'network', 'how-it-works.html': 'how-it-works',
    'learn.html': 'learn', 'our-story.html': 'our-story', 'measurement.html': 'measurement',
    'privacy.html': 'privacy', 'terms.html': 'terms', 'automated-decisions.html': 'automated-decisions',
    'blog-body-doubling.html': 'blog', 'blog-how-booking-works.html': 'blog',
    'blog-late-diagnosis.html': 'blog', '404.html': 'not-found',
    'care-navigator.html': 'navigator',
    'adhd-services.html': 'service', 'adhd-doctor-gold-coast.html': 'service',
    'adhd-gp-brisbane.html': 'service', 'adhd-assessment-queensland.html': 'service',
    'adhd-assessment-sydney.html': 'service', 'adhd-assessment-online.html': 'service',
    'adhd-treatment-after-diagnosis.html': 'service', 'adhd-exercise-physiologist.html': 'service',
    'adhd-psychologist.html': 'service', 'adhd-psychologist-brisbane.html': 'service',
    'adhd-occupational-therapist.html': 'service', 'adhd-coach.html': 'service'
  };
  var PAGE_NAMES = unique(Object.keys(PAGES).map(function (k) { return PAGES[k]; }).concat(['profile', 'other']));

  // ------------------------------------------------------------------ the taxonomy
  // Three fragments the events share, so a property means the same thing wherever it appears and
  // a new one is added in a single place.
  function spec() {
    var out = {}, args = arguments;
    Array.prototype.forEach.call(args, function (part) {
      Object.keys(part).forEach(function (k) { out[k] = part[k]; });
    });
    return out;
  }
  // Who the clinician is, in the words a dashboard reads back.
  var WHO = {
    clinician: { kind: 'vocabulary', values: CLINICIAN_IDS },
    clinician_name: { kind: 'vocabulary', values: CLINICIAN_NAMES },
    category: { kind: 'vocabulary', values: CATEGORIES }
  };
  // What they are sought for. Lists, because a clinician is several things at once.
  var SOUGHT = {
    expertise: { kind: 'list', values: EXPERTISE },
    ages: { kind: 'list', values: AGE_BANDS }
  };
  // What brought the visit. Carried on every event worth crossing against a content calendar.
  var CAME = {
    channel: { kind: 'vocabulary', values: CHANNELS },
    content_theme: { kind: 'vocabulary', values: CONTENT_THEMES },
    content_post: { kind: 'token' }
  };

  var EVENTS = {
    'page-viewed': spec({ page: { kind: 'vocabulary', values: PAGE_NAMES } }, CAME),
    'landing-viewed': {},
    'landing-cta': {
      control: { kind: 'vocabulary', values: LANDING_CONTROLS }
    },
    'deck-viewed': {
      clinicians: { kind: 'count' }
    },
    'deck-card-opened': spec(WHO, SOUGHT),
    'profile-viewed': spec(WHO, SOUGHT, CAME, {
      practice: { kind: 'vocabulary', values: PRACTICES },
      surface: { kind: 'vocabulary', values: BOOKING_SURFACES }
    }),
    // One summary per profile view, sent when the page goes away: how far it was read, how long it
    // held attention, and whether it ended in a handoff. One event per view, not one per scroll —
    // the question is "who read as far as the fees and still did not book", and that needs a row
    // per reading, not a stream of them.
    'profile-engaged': spec(WHO, SOUGHT, CAME, {
      practice: { kind: 'vocabulary', values: PRACTICES },
      depth: { kind: 'vocabulary', values: READ_DEPTHS },
      dwell: { kind: 'count' },
      acted: { kind: 'vocabulary', values: YES_NO }
    }),
    'newsletter-invite': {
      action: { kind: 'vocabulary', values: INVITE_ACTIONS },
      trigger: { kind: 'vocabulary', values: INVITE_TRIGGERS }
    },
    'booking-outbound': spec(WHO, SOUGHT, CAME, {
      practice: { kind: 'vocabulary', values: PRACTICES },
      destination: { kind: 'vocabulary', values: DESTINATIONS },
      surface: { kind: 'vocabulary', values: BOOKING_SURFACES },
      link: { kind: 'vocabulary', values: BOOKING_LINKS }
    })
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
      // A list: every member must be declared. One clinician is several things at once, and a
      // dashboard should be able to break down by each of them.
      if (spec[k].kind === 'list') {
        if (!Array.isArray(v)) { out.push('"' + name + '"."' + k + '" must be an array'); return; }
        v.forEach(function (item) {
          if (spec[k].values.indexOf(item) === -1) out.push('"' + name + '"."' + k + '" has undeclared member ' + JSON.stringify(item));
        });
        return;
      }
      // A token: not a closed list, because a campaign names a post and posts outrun deploys. Still
      // validated, so what lands is a slug and never free text somebody typed.
      if (spec[k].kind === 'token') {
        if (typeof v !== 'string' || !/^[a-z0-9][a-z0-9-]{0,39}$/.test(v)) out.push('"' + name + '"."' + k + '" must be a short lowercase slug, got ' + JSON.stringify(v));
        return;
      }
      if (typeof v !== 'string' || spec[k].values.indexOf(v) === -1) out.push('"' + name + '"."' + k + '" must be one of the declared values, got ' + JSON.stringify(v));
    });
    return out;
  }

  // ------------------------------------------------------------------ storage that stays here
  var OUTBOUND_KEY = 'adhdme-outbound';     // this device's handoff log, read by measurement.html
  var PROFILES_KEY = 'adhdme-profiles';     // which clinicians this device has looked at
  var VISITOR_KEY = 'adhdme-visitor';       // a random label so a person row is legible, not a name
  var OPTOUT_KEY = 'adhdme-analytics-off';
  var CONSENT_KEY = 'adhdme-privacy-ack';   // written by privacy-consent.js

  function readLocal(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch (e) { return fallback; }
  }
  function writeLocal(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch (e) { return false; }
  }

  // ------------------------------------------------------------------ opt-out
  var config = window.ADHDME || {};
  var params = new URLSearchParams(location.search);
  var debug = config.debug === true || /[?&]debug=analytics\b/.test(location.search);

  if (params.get('analytics') === 'off') { try { localStorage.setItem(OPTOUT_KEY, '1'); } catch (e) {} }
  if (params.get('analytics') === 'on') { try { localStorage.removeItem(OPTOUT_KEY); } catch (e) {} }

  function optedOut() {
    if (navigator.globalPrivacyControl === true) return true;
    try { return localStorage.getItem(OPTOUT_KEY) === '1'; } catch (e) { return false; }
  }

  // ------------------------------------------------------------------ consent
  // requireConsent true holds the sinks until the privacy bar's Agree is pressed. Events raised
  // meanwhile are validated and queued, then sent in order, so the first visit is not lost.
  var needsConsent = config.requireConsent === true;
  function consentGiven() {
    if (!needsConsent) return true;
    try { return localStorage.getItem(CONSENT_KEY) === '1'; } catch (e) { return false; }
  }

  // ------------------------------------------------------------------ this visitor, as a label
  function shortId() {
    var id = readLocal(VISITOR_KEY, null);
    if (typeof id === 'string' && id) return id;
    var bytes = new Uint8Array(4);
    if (window.crypto && window.crypto.getRandomValues) window.crypto.getRandomValues(bytes);
    else for (var i = 0; i < 4; i++) bytes[i] = Math.floor(Math.random() * 256);
    id = Array.prototype.map.call(bytes, function (b) { return ('0' + b.toString(16)).slice(-2); }).join('');
    writeLocal(VISITOR_KEY, id);
    return id;
  }

  // How a clinician is described on an event, in one place so the five call sites cannot drift.
  function who(id) {
    var c = CLINICIANS[id];
    return { clinician: id, clinician_name: c.name, category: c.category,
             expertise: c.expertise, ages: c.ages };
  }

  // ------------------------------------------------------------------ where we are
  var path = location.pathname.replace(/\/index\.html$/, '/');
  var file = path.split('/').pop() || 'index.html';
  if (file === '') file = 'index.html';

  function clinicianOfPage(name) {
    for (var k in CLINICIANS) if (CLINICIANS[k].profile === name) return k;
    return null;
  }
  var profileId = clinicianOfPage(file);
  var pageName = profileId ? 'profile' : (PAGES[file] || 'other');
  var surface = profileId ? 'profile' : file === 'the-doctors.html' ? 'network' : null;

  function referrerHost() {
    try {
      if (!document.referrer) return 'none';
      var h = new URL(document.referrer).hostname;
      return h === location.hostname ? 'this-site' : h;
    } catch (e) { return 'unknown'; }
  }

  // ------------------------------------------------------------------ where this visit came from
  // A visit is one browsing session. Whatever brought it is remembered for the whole of it, so a
  // booking three pages later is still credited to the post that started it rather than to the
  // internal link that happened to be last. Held in sessionStorage, so it ends when the visit does.
  var VISIT_KEY = 'adhdme-visit';
  var SOCIAL = {
    'instagram.com': 'instagram', 'l.instagram.com': 'instagram',
    'facebook.com': 'facebook', 'm.facebook.com': 'facebook', 'l.facebook.com': 'facebook',
    'tiktok.com': 'tiktok', 'linkedin.com': 'linkedin', 'lnkd.in': 'linkedin',
    'youtube.com': 'youtube', 'youtu.be': 'youtube'
  };
  var SEARCH = /(^|\.)(google|bing|duckduckgo|ecosia|yahoo)\./;

  function slug(v) {
    return String(v || '').toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
  }
  function inVocab(v, list, fallback) { return list.indexOf(v) !== -1 ? v : fallback; }

  function channelFromReferrer() {
    var host = referrerHost();
    if (host === 'none') return 'direct';
    if (host === 'this-site' || host === 'unknown') return null;   // keep whatever the visit already had
    var bare = host.replace(/^www\./, '');
    if (SOCIAL[bare]) return SOCIAL[bare];
    if (SEARCH.test(host)) return 'search';
    return 'referral';
  }

  function visit() {
    var held = null;
    try { held = JSON.parse(sessionStorage.getItem(VISIT_KEY) || 'null'); } catch (e) {}
    // An explicit tag always wins: it is the post telling us, rather than us guessing from a host.
    if (params.get('utm_source')) {
      var tagged = {
        channel: inVocab(slug(params.get('utm_source')), CHANNELS, 'other'),
        theme: inVocab(slug(params.get('utm_campaign')), CONTENT_THEMES, 'other'),
        post: slug(params.get('utm_content')) || 'none'
      };
      try { sessionStorage.setItem(VISIT_KEY, JSON.stringify(tagged)); } catch (e) {}
      return tagged;
    }
    if (held && held.channel) return held;
    var derived = { channel: channelFromReferrer() || 'direct', theme: 'other', post: 'none' };
    try { sessionStorage.setItem(VISIT_KEY, JSON.stringify(derived)); } catch (e) {}
    return derived;
  }
  var came = visit();
  // Every event that matters carries it, so "which post produced handoffs" is a breakdown rather
  // than a join.
  function withVisit(props) {
    props.channel = came.channel;
    props.content_theme = came.theme;
    props.content_post = came.post;
    return props;
  }

  // ------------------------------------------------------------------ what a person row says
  // Nothing here names anybody. It is the shape of one device's visit: when it first arrived, what
  // brought it, what it has looked at, and how many booking links it has followed.
  function outboundRows() {
    var rows = readLocal(OUTBOUND_KEY, []);
    return Array.isArray(rows) ? rows : [];
  }
  function profilesSeen() {
    var seen = readLocal(PROFILES_KEY, []);
    return Array.isArray(seen) ? seen : [];
  }
  function personSetOnce() {
    return {
      name: 'Visitor ' + shortId(),
      adhdme_first_seen: new Date().toISOString(),
      adhdme_entry_page: pageName,
      adhdme_entry_referrer: referrerHost(),
      adhdme_entry_utm_source: params.get('utm_source') || 'none',
      adhdme_entry_utm_medium: params.get('utm_medium') || 'none',
      adhdme_entry_utm_campaign: params.get('utm_campaign') || 'none'
    };
  }
  function personSet() {
    var rows = outboundRows();
    var last = rows.length ? rows[rows.length - 1] : null;
    var props = {
      adhdme_last_seen: new Date().toISOString(),
      adhdme_last_page: pageName,
      adhdme_profiles_viewed: profilesSeen().length,
      adhdme_booking_clicks: rows.length,
      adhdme_booked_categories: unique(rows.map(function (r) { return r.category; }).filter(Boolean)),
      adhdme_booked_clinicians: unique(rows.map(function (r) { return r.name; }).filter(Boolean))
    };
    if (last) {
      props.adhdme_last_booking_clinician = last.name || 'unknown';
      props.adhdme_last_booking_category = last.category || 'unknown';
      props.adhdme_last_booking_practice = last.practice || 'unknown';
    }
    return props;
  }

  // ------------------------------------------------------------------ the sinks
  var queue = window.__adhdmeEvents = window.__adhdmeEvents || [];   // always, for the console and tests
  var pending = [];                                                  // held while consent is outstanding
  var posthog = null;                                                // the loaded library
  var posthogQueue = [];                                             // calls raised before it lands
  var gaReady = false;
  var started = false;

  function posthogCall(method, args) {
    if (!config.posthogKey) return;
    if (posthog) { try { posthog[method].apply(posthog, args); } catch (e) {} return; }
    if (posthogQueue.length < 100) posthogQueue.push([method, args]);
  }

  function startPostHog() {
    if (!config.posthogKey) return;
    var host = String(config.posthogHost || 'https://us.i.posthog.com').replace(/\/+$/, '');
    var assets = String(config.posthogAssetHost || '').replace(/\/+$/, '') ||
      host.replace('//us.i.posthog.com', '//us-assets.i.posthog.com')
          .replace('//eu.i.posthog.com', '//eu-assets.i.posthog.com');
    var s = document.createElement('script');
    s.async = true;
    s.src = assets + '/static/array.js';
    s.onload = function () {
      if (!window.posthog || typeof window.posthog.init !== 'function') return;
      window.posthog.init(config.posthogKey, {
        api_host: host,
        // Every visitor becomes a person row, which is what makes the Persons list and the
        // dashboard's people tiles show anybody at all.
        person_profiles: config.posthogPersonProfiles || 'always',
        autocapture: config.posthogAutocapture !== false,
        capture_pageview: true,
        capture_pageleave: true,
        disable_session_recording: config.posthogSessionRecording !== true,
        persistence: 'localStorage+cookie',
        loaded: function (ph) {
          posthog = ph;
          var held = posthogQueue;
          posthogQueue = [];
          held.forEach(function (call) { posthogCall(call[0], call[1]); });
        }
      });
    };
    document.head.appendChild(s);
  }

  function startGA() {
    if (!config.gaId) return;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(config.gaId);
    document.head.appendChild(s);
    window.gtag('js', new Date());
    window.gtag('config', config.gaId, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
      anonymize_ip: true
    });
    gaReady = true;
  }

  function start() {
    if (started || optedOut() || !consentGiven()) return;
    started = true;
    startPostHog();
    startGA();
    // The person row, written once per page so a returning visit updates its own counters.
    posthogCall('setPersonProperties', [personSet(), personSetOnce()]);
    var held = pending;
    pending = [];
    held.forEach(function (row) { send(row.name, row.properties); });
  }

  function send(name, props) {
    posthogCall('capture', [name, props]);
    if (gaReady) {
      try { window.gtag('event', name, Object.assign({ transport_type: 'beacon' }, props)); } catch (e) {}
    }
  }

  function track(name, props) {
    props = props || {};
    var f = findings(name, props);
    if (f.length) {
      queue.push({ event: 'analytics-refused', name: name, findings: f });
      if (debug) console.warn('analytics-refused', name, f);
      return false;
    }
    queue.push({ event: name, properties: props, at: Date.now() });
    if (debug) console.info('analytics', name, props);
    if (optedOut()) return true;
    if (!consentGiven()) { if (pending.length < 50) pending.push({ name: name, properties: props }); return true; }
    start();
    send(name, props);
    return true;
  }
  window.adhdmeTrack = track;

  // privacy-consent.js announces the agreement; the held events go out in the order they happened.
  window.addEventListener('adhdme-privacy-ack', function () { start(); });

  // What measurement.html's controls talk to.
  window.adhdmeAnalytics = {
    status: function () {
      return {
        optedOut: optedOut(),
        globalPrivacyControl: navigator.globalPrivacyControl === true,
        consentRequired: needsConsent,
        consentGiven: consentGiven(),
        posthog: !!config.posthogKey,
        ga: !!config.gaId,
        visitor: shortId()
      };
    },
    optOut: function () {
      try { localStorage.setItem(OPTOUT_KEY, '1'); } catch (e) {}
      pending = [];
      posthogCall('opt_out_capturing', []);
      return true;
    },
    optIn: function () {
      try { localStorage.removeItem(OPTOUT_KEY); } catch (e) {}
      posthogCall('opt_in_capturing', []);
      start();
      return true;
    },
    clearLocalTally: function () {
      try { localStorage.removeItem(OUTBOUND_KEY); localStorage.removeItem(PROFILES_KEY); } catch (e) {}
      return true;
    },
    outbound: outboundRows
  };

  start();

  // ------------------------------------------------------------------ page events
  track('page-viewed', withVisit({ page: pageName }));

  if (file === 'index.html') track('landing-viewed', {});

  if (file === 'the-doctors.html') {
    var seen = {};
    Array.prototype.forEach.call(document.querySelectorAll('a[href]'), function (a) {
      var id = clinicianOfPage(a.getAttribute('href').split(/[?#]/)[0]);
      if (id) seen[id] = true;
    });
    track('deck-viewed', { clinicians: Object.keys(seen).length });
  }

  if (profileId) {
    var c = CLINICIANS[profileId];
    var src = params.get('src');
    var from = BOOKING_SURFACES.indexOf(src) !== -1 ? src : (/the-doctors\.html/.test(document.referrer) ? 'network' : 'profile');
    var seenProfiles = profilesSeen();
    if (seenProfiles.indexOf(profileId) === -1) { seenProfiles.push(profileId); writeLocal(PROFILES_KEY, seenProfiles.slice(-50)); }
    track('profile-viewed', withVisit(spec(who(profileId), {
      practice: c.practice, surface: from
    })));

    // ---------------------------------------------------------------- how the page was read
    // Profile pages put the booking button in the hero, so "did they see the call to action" is
    // true of nearly everybody and worth nothing. What is worth something is how far past it they
    // went: somebody who read all the way to the fee table and left is a different person from
    // somebody who never scrolled, and only one of them is a lost booking.
    //
    // Sent once, when the page goes away, carrying the deepest landmark reached, the seconds the
    // page actually held the screen, and whether the reading ended in a handoff. A booking click
    // runs its own handler before the page hides, so 'acted' is already true by the time this goes.
    // The one reading it cannot give: tabbing away mid-page ends the measurement there.
    var reached = 0;                       // index into READ_DEPTHS
    var acted = false;
    var visibleSince = document.visibilityState === 'visible' ? Date.now() : 0;
    var dwellMs = 0;
    var sent = false;

    var landmarks = [
      { at: 1, el: document.getElementById('fees-title') },
      { at: 2, el: document.getElementById('also-title') },
      { at: 3, el: document.querySelector('footer') }
    ];
    if (window.IntersectionObserver) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          landmarks.forEach(function (m) { if (m.el === e.target && m.at > reached) reached = m.at; });
        });
      }, { threshold: 0 });
      landmarks.forEach(function (m) { if (m.el) io.observe(m.el); });
    }

    var markActed = function () { acted = true; };
    window.addEventListener('adhdme-booking-click', markActed);

    var sendEngagement = function () {
      if (sent) return;
      sent = true;
      if (visibleSince) { dwellMs += Date.now() - visibleSince; visibleSince = 0; }
      track('profile-engaged', withVisit(spec(who(profileId), {
        practice: c.practice, depth: READ_DEPTHS[reached],
        dwell: Math.round(dwellMs / 1000), acted: acted ? 'yes' : 'no'
      })));
    };
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') { visibleSince = visibleSince || Date.now(); return; }
      sendEngagement();
    });
    window.addEventListener('pagehide', sendEngagement);
  }

  // ------------------------------------------------------------------ click events
  // Landing controls: which named door was pressed.
  document.addEventListener('click', function (e) {
    var el = e.target instanceof Element ? e.target.closest('[data-landing-control]') : null;
    if (!el) return;
    track('landing-cta', { control: el.getAttribute('data-landing-control') });
  }, true);

  // The Network: which card was opened, so deck → profile can be read per clinician rather than
  // inferred from the referrer on the other side.
  if (file === 'the-doctors.html') {
    document.addEventListener('click', function (e) {
      var a = e.target instanceof Element ? e.target.closest('a[href]') : null;
      if (!a) return;
      var id = clinicianOfPage((a.getAttribute('href') || '').split(/[?#]/)[0]);
      if (!id) return;
      track('deck-card-opened', who(id));
    }, true);
  }

  // Booking handoff: the UTM tail for the practice's own reporting, a local tally, and the event
  // that carries who, which discipline, which practice and which link.
  function clinicianFor(href) {
    // A clinic whose clinicians share one booking page would otherwise always attribute to whichever
    // of them is declared first, so the profile being read wins when its own link is the one clicked.
    if (profileId && CLINICIANS[profileId].booking.test(href)) return profileId;
    for (var k in CLINICIANS) if (CLINICIANS[k].booking.test(href)) return k;
    return null;
  }
  function linkNameFor(a) {
    var declared = a.getAttribute('data-booking-link');
    if (declared && BOOKING_LINKS.indexOf(declared) !== -1) return declared;
    if (profileId) return 'profile-cta';
    if (file === 'the-doctors.html') return 'deck-card';
    return 'other';
  }
  function tallyOutbound(row) {
    var rows = outboundRows();
    rows.push(row);
    if (rows.length > 500) rows = rows.slice(-500);
    writeLocal(OUTBOUND_KEY, rows);
  }
  document.addEventListener('click', function (e) {
    var a = e.target instanceof Element ? e.target.closest('a[href^="http"]') : null;
    if (!a) return;
    var id = clinicianFor(a.href);
    if (!id) return;
    var person = CLINICIANS[id];
    var surf = surface || 'network';
    var link = linkNameFor(a);
    try {
      var u = new URL(a.href);
      u.searchParams.set('utm_source', 'adhd-me');
      u.searchParams.set('utm_medium', 'referral');
      u.searchParams.set('utm_campaign', surf);
      u.searchParams.set('utm_content', id);
      a.href = u.toString();
    } catch (err) {}
    tallyOutbound({
      clinicianId: id, name: person.name, category: person.category, practice: person.practice,
      destination: person.destination, surface: surf, link: link,
      day: new Date().toISOString().slice(0, 10), at: Date.now()
    });
    track('booking-outbound', withVisit(spec(who(id), {
      practice: person.practice, destination: person.destination, surface: surf, link: link
    })));
    try { window.dispatchEvent(new Event('adhdme-booking-click')); } catch (err2) {}
    // The person row carries the running count, so the Persons list answers "how many booking links
    // has this visitor followed, and for whom" without a query.
    posthogCall('setPersonProperties', [personSet()]);
    // No await, no delay: the browser follows the link now; the beacon travels on its own.
  }, true);

  // ------------------------------------------------------------------ this device's own tally
  // measurement.html reads it back. Everything below is local: it never leaves the browser.
  var CATEGORY_WORDS = { gp: 'GP', psychologist: 'Psychologist', allied: 'Allied health' };

  var tallyEl = document.getElementById('tally');
  if (tallyEl) {
    var rows = outboundRows();
    if (!rows.length) {
      tallyEl.textContent = 'No handoffs recorded on this device yet.';
    } else {
      var by = {};
      rows.forEach(function (r) {
        var key = r.clinicianId || 'unknown';
        by[key] = by[key] || { name: r.name || key, category: r.category, practice: r.practice, total: 0, surfaces: {} };
        by[key].total += 1;
        by[key].surfaces[r.surface] = (by[key].surfaces[r.surface] || 0) + 1;
      });
      var list = document.createElement('ul');
      list.className = 'tally-list';
      Object.keys(by).sort(function (a, b) { return by[b].total - by[a].total; }).forEach(function (key) {
        var r = by[key];
        var li = document.createElement('li');
        var head = document.createElement('strong');
        head.textContent = r.name;
        li.appendChild(head);
        var rest = document.createElement('span');
        var where = Object.keys(r.surfaces).map(function (s) { return r.surfaces[s] + ' from ' + s; }).join(', ');
        rest.textContent = ' — ' + (CATEGORY_WORDS[r.category] || r.category) + ', ' + r.practice +
          ': ' + r.total + (r.total === 1 ? ' handoff' : ' handoffs') + ' (' + where + ')';
        li.appendChild(rest);
        list.appendChild(li);
      });
      tallyEl.textContent = '';
      tallyEl.appendChild(list);
    }
  }

  // The opt-out control and the line that says what is currently on.
  var statusEl = document.getElementById('analytics-status');
  var toggleEl = document.querySelector('[data-analytics-toggle]');
  function paintStatus() {
    if (!statusEl && !toggleEl) return;
    var s = window.adhdmeAnalytics.status();
    if (statusEl) {
      var sinks = [];
      if (s.posthog) sinks.push('PostHog');
      if (s.ga) sinks.push('Google Analytics');
      statusEl.textContent = s.optedOut
        ? (s.globalPrivacyControl
            ? 'Off. Your browser sends a Global Privacy Control signal and this site honours it.'
            : 'Off. This browser is opted out; nothing is counted or sent.')
        : sinks.length
          ? 'On. Counts from this browser go to ' + sinks.join(' and ') + '. You are ' + s.visitor + ' there, and that is the whole of it.'
          : 'On, with nowhere to send. Events are checked against the list above and dropped; no request leaves this page.';
    }
    if (toggleEl) {
      toggleEl.textContent = s.optedOut ? 'Count my visits' : 'Do not count my visits';
      toggleEl.setAttribute('aria-pressed', s.optedOut ? 'true' : 'false');
    }
  }
  if (toggleEl) {
    toggleEl.addEventListener('click', function () {
      if (window.adhdmeAnalytics.status().optedOut) window.adhdmeAnalytics.optIn();
      else window.adhdmeAnalytics.optOut();
      paintStatus();
    });
  }
  paintStatus();
})();
