# Onboarding pack: Atlantis Recovery Centre, Bundall (Gold Coast)

STATUS: built from the practice's team page, with the practice's own portraits. Seven profiles
are live in the data: Bart Traynor, Jeff Leech, Michael Rehardt, Sarah Savage, Dr Yuri Lima, Tom
Hissey and Lester Rafanan. Jade Evans (co-owner, business operations) is not a clinician and is not
listed. Heather Cameron and Steven Walker appear on HotDoc but not on the practice's team page, so
they are not listed either.

The portraits are now the practice's own headshots, taken from its media library once the site's
WordPress REST API turned out to answer even though the HTML sits behind a bot interstitial.

Still to come from the practice, per person: whether they offer telehealth
(nobody carries the pill until declared), pronouns if wanted, and any fee they will publish. One
correction was made to the team page text: "injurty" to "injury" in Lester Rafanan's bio.

The sections below are the record of what was verified before the team page arrived.

## The practice, verified

| Field | Value | Source |
|---|---|---|
| Name | Atlantis Recovery Centre (Atlantis RC) | practice site title |
| What it is | Multidisciplinary allied-health centre: psychology, physiotherapy, exercise physiology, hydrotherapy | practice site |
| Address | 1/25 Upton Street, Bundall QLD 4217 | practice contact page, healthdirect |
| Phone | (07) 5610 2312 | practice contact page |
| Email | info@atlantisrc.com.au | practice site |
| Booking | HotDoc: https://www.hotdoc.com.au/medical-centres/bundall-QLD-4217/atlantis-recovery-centre/doctors | HotDoc |
| Funding | Private, DVA, NDIS, private health funds, WorkCover, GP Mental Health Care Plans and chronic condition plans. "Bulk billing is available with conditions, though fees may apply." | practice DVA and NDIS page |
| NDIS | No service agreements; participants are not locked into a contract | practice DVA and NDIS page |
| Access | "Purpose built, all abilities accessible clinic" | practice about page |
| ADHD | "The centre's hybrid model is ideal for ADHD, anxiety, trauma". Psychology "starts with a comprehensive assessment" and blends therapy with movement-based work (REAX lights and treadmill, VR) | practice psychology page |
| Wait | "Committed to servicing new clients quickly with low wait times" | practice site |

Fees: the practice publishes none that could be found. Same rule as GOALS, NCAU and REACH: no
figures until the practice states them; the notes carry the funding routes instead.

## The people, verified

Seven names. Two are first names only, and one role is unknown. Everything in the bio column is a
short public statement the practice or HotDoc made; it is a brief for the draft, not the draft.

| # | Name | Role | HotDoc page | What is public |
|---|---|---|---|---|
| 1 | Bart Traynor | Clinical psychologist, director and co-owner | `/doctors/bart-traynor-1` | AHPRA board-approved clinical supervisor. Member, Australian Association of Psychologists and Association of Applied Sports Psychology. "Particular passion for helping athletes/men's mental health." Also has a Halaxy profile listing Merrimac. |
| 2 | Jeff (surname not found) | Psychologist | not found | Master of Clinical Psychology, University of Queensland; Bachelor of Psychological Science (Honours), Southern Cross University. Background in outdoor education, military service, emergency services and adventure/endurance events. "Trauma-informed care, wellbeing, and performance psychology." Practical, strengths-based. |
| 3 | Michael Young | Provisional psychologist | not found | Griffith University. Announced on the practice's Facebook page as joining "our psych team with Bart & Jeff". |
| 4 | Sarah Savage | Exercise physiologist | `/doctors/sarah-savage` | Griffith University, 2013, Bachelor and Graduate Diploma in Exercise Science. Certifications in Pilates, FRC and hydrotherapy. "Exercise as Medicine." |
| 5 | Heather Cameron | Head physiotherapist | `/doctors/heather-cameron` | Trained in Scotland's NHS. Clinical practice, sports rehabilitation, Pilates and acupuncture. Completing a Master's in Clinical Pain Management. |
| 6 | Yuri Lima | Physiotherapist | not found | Master in Rehabilitation Sciences, pursuing a PhD. Orthopaedic and sports rehabilitation. English and Portuguese. |
| 7 | Steven Walker | Physiotherapist | `/doctors/steven-walker` | Listed on HotDoc. Nothing else found. |

Also named in a client review: "Elena", who "helps with anxiety". Role unknown; not on the roster
until the practice confirms who she is.

HotDoc paths are relative to the booking URL above. HotDoc is an online diary, so the button should
read Book, not Enquire; that needs `hotdoc.com.au` added to `ONLINE_DIARIES` in both
`scripts/build-profiles.py` and `scripts/check-site.py` before the build, or every card will say
Enquire.

## What the practice has to supply before anything builds

Per person, in this order of importance:

1. ~~**A square portrait**~~ Done: the practice's own 1254px headshots, resized to the six files.
2. **Their own bio**, in their words, as on the practice's team page. The `about` paragraphs are
   theirs verbatim; the `description` and `chips` are ours, drawn from it.
3. **Full name and registration** (surname for Jeff; confirm Michael Young's provisional status and
   supervisor; AHPRA registration type for each physiotherapist and the ESSA accreditation for Sarah).
4. **Booking**: their own HotDoc page, or the clinic page if they are not on it (Jeff, Michael, Yuri).
5. **Telehealth**: yes or no, declared, per person. The pill is drawn only from this.
6. **Fees**, if the practice will publish any. Otherwise the profile carries the funding notes only.
7. **Pronouns**, if they want them shown, and **languages** beyond English (Yuri: Portuguese).
8. **Wheelchair access**: the practice says all-abilities accessible; confirm the wording to use.
9. **Disclosure**: any commercial relationship with ADHDme, as on the GP profiles.

Plus, once from the practice: confirmation that they want to be listed, and that a physiotherapist
belongs on an ADHD directory at all. The network has no physiotherapy category today; the honest
options are a new "Physiotherapy" tab on The Network, or listing only the psychology and exercise
physiology staff and leaving physiotherapy out.

## What changes on the site when this builds

This is the first practice with rooms on the Gold Coast and the first exercise physiologist, so
several pages that currently say "not yet" have to be updated in the same commit, or the site
contradicts itself:

- `scripts/build-map.py`: Gold Coast moves from planned to live.
- `our-story.html` copy: "Clinicians in Sydney, Brisbane, Perth and the Snowy Mountains today".
- `scripts/build-seo-pages.py`: `adhd-doctor-gold-coast` (whole first screen), `adhd-assessment-queensland`, `adhd-psychologist-brisbane` (mentions), `adhd-exercise-physiologist` ("Where ADHDme stands" section and FAQ), `adhd-treatment-after-diagnosis` (exercise section). The clinician lists select by state and category, so they refill themselves.
- `scripts/build-navigator.py`: Sarah Savage under Health › Sleep and physical health and Work › Stress and burnout; the psychologists under the mood, burnout and assessment aspects, each with the reason quoted from their own profile.
- `the-doctors.html`: exercise physiology under the allied health panel; a new panel only if physiotherapists are listed.
- `analytics.js`: seven entries with `expertise` and `ages`; `exercise-physiology` and `physiotherapy` join the expertise vocabulary.
- `sitemap.xml`, `site.css` view-transition rule, `CLINICIAN-MEDIA-WORKFLOW.md` roster: one line each per person.
- `qa-packs/`: this file gets a returned date and the practice's edits verbatim.

## Draft entry skeleton

One shape for all seven, to be filled from what the practice returns. Fields marked CHECK are
guesses to be corrected, not facts. Nothing in `about` may be written by us.

```python
ARC = 'https://atlantisrc.com.au/'
ARC_BOOK = 'https://www.hotdoc.com.au/medical-centres/bundall-QLD-4217/atlantis-recovery-centre/doctors'
ARC_BOOK_HINT = 'Opens Atlantis Recovery Centre’s booking page on HotDoc, in a new tab.'
ARC_PLACE = 'Bundall, Gold Coast'            # CHECK: add "& telehealth" only if declared
ARC_REACH = 'Clinic appointments in Bundall, on the Gold Coast'
ARC_ACCESS = 'Yes: the practice describes the clinic as all-abilities accessible'   # CHECK wording
ARC_DISCLOSURE = ('Atlantis Recovery Centre is an independent practice: it sets its own fees, availability '
                  'and clinical approach, and ADHDme receives no part of what you pay.')
ARC_WORKS_FOR = dict(url=ARC, telephone='(07) 5610 2312', locality='Bundall', state='QLD')
ARC_FEES = dict(
    heading='What a session costs',
    figures=[],   # the practice publishes no fee; do not fill this with a guess
    notes=[
        'Atlantis Recovery Centre does not publish a fee. It quotes one when you book.',
        'The practice takes private clients and works with DVA, the NDIS, private health funds, WorkCover, '
        'and GP Mental Health Treatment Plans and chronic condition management plans. It says bulk billing '
        'is available with conditions.',
        'NDIS participants are not asked to sign a service agreement.',
        '<strong>The fee is set and charged by the practice you book with; ADHDme receives no part of it.</strong>',
    ],
)

dict(
    slug='bart-traynor', id='bart-traynor', category='psychologist',
    name='Bart Traynor', short='Bart', role='Clinical Psychologist and Director', pronouns='',   # CHECK
    practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Clinical psychologist & director',
    description='',   # ours, one line, from his bio once we have it
    chips=['Men’s mental health', 'Athletes & performance', 'Clinical supervisor'],   # CHECK against his bio
    telehealth=False,   # CHECK: not declared anywhere found
    book_href=ARC_BOOK + '/bart-traynor-1', book_hint=ARC_BOOK_HINT,
    links=[('website', 'atlantisrc.com.au', ARC)],
    fees=ARC_FEES,
    qualifications='Clinical psychologist',   # CHECK: degrees not found
    languages=[],
    experience=[
        'Clinical psychologist, director and co-owner, Atlantis Recovery Centre, Bundall',
        'AHPRA board-approved clinical supervisor',
        'Member, Australian Association of Psychologists',
        'Member, Association of Applied Sports Psychology',
    ],
    about=[],   # his words, from the practice, verbatim; never ours
    details=[('Reach', ARC_REACH), ('Appointments', 'Set with the practice'),   # CHECK
             ('Billing', 'Quoted by the practice; DVA, NDIS, private health, WorkCover and Medicare plans accepted'),
             ('Wheelchair access', ARC_ACCESS)],
    disclosure=ARC_DISCLOSURE,
    schema=dict(type='Person', credentials=['Clinical psychologist'], same_as=[ARC + 'team/'],
                works_for=ARC_WORKS_FOR, area='Gold Coast, QLD, Australia', area_type='Place'),
)
```

Sarah Savage takes `category='allied'` with `descriptor='Exercise physiologist'`; the physiotherapists
take `category='allied'` too unless a physiotherapy panel is added. Jeff, Michael Young and Yuri Lima
take `book_href=ARC_BOOK` (the clinic diary) until a personal HotDoc page is confirmed.

## Sent / returned

Sent:      —
Returned:  2026-09-22, team page text supplied by ADHDme
