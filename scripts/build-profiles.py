#!/usr/bin/env python3
"""Generate the clinician profile pages and the cards on The Doctors from one data set.

    python3 scripts/build-profiles.py          # write the pages
    python3 scripts/build-profiles.py --check  # exit 1 if any page on disk differs from what would be written

Owns: dr-*.html / <slug>.html for every entry in CLINICIANS, and the <li> cards inside each category
panel's <ul> on the-doctors.html. Everything else on the-doctors.html is left alone.

The page shell (head, header, footer) is scripts/profile-shell.html; the tokens it carries are filled
in below. Portraits live in assets/clinicians/ as <id>.jpg, <id>-640.jpg, <id>-320.jpg plus the same
three as .webp, all square; the full size is read from the JPEG itself so srcset descriptors and the
og:image size can never go stale. Before writing, the script refuses to run if a portrait is missing,
if a clinician is absent from sitemap.xml, analytics.js or the view-transition rule in site.css, or if
a category panel on the-doctors.html has no <ul> to put a card in.

Text fields are plain text and are escaped on the way out. Fields marked "html" in the comments are
raw HTML. Adding a clinician: copy an entry, add the six portrait files, add the page to sitemap.xml,
add the clinician to CLINICIANS in analytics.js, add ::view-transition-group(portrait-<id>) to site.css,
then run this script.
"""
import html
import json
import pathlib
import re
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHELL = ROOT / 'scripts' / 'profile-shell.html'
DECK = ROOT / 'the-doctors.html'
SITE = 'https://stef-01.github.io/revamped-adhd.me'
PORTRAITS = 'assets/clinicians'

# The Doctors: which tab panel each category's cards go in. The first clinician in the default panel
# is the one card that loads eagerly; every other card is lazy.
PANELS = {'gp': 'gps', 'psychologist': 'psychologists', 'allied': 'allied-health'}
DEFAULT_PANEL = 'gp'

# ---------------------------------------------------------------- data

GP_FEES = dict(
    heading='What a diagnosis costs',
    figures=[('$299', 'Initial consultation'), ('$199', 'Follow-up consultation')],
    notes=[  # html
        'Both consultations together are the ADHD assessment and diagnosis: $498 in total.',
        'Some people may require an additional 30-minute clinical review where further history, records or medical assessment are needed. If this applies to you, the practice will explain why and discuss the cost before any additional appointment is booked.',
        'No Medicare rebate, nothing to claim back.',
        '<strong>The fee is set and charged by the practice you book with; ADHDme receives no part of it.</strong> It is published here so the cost is settled before you arrive rather than at the front desk.',
    ],
)
GP_BILLING = '$299 initial, $199 follow-up, no Medicare rebate; set and charged by the practice'
HEALTHENGINE_HINT = 'Opens the practice’s booking page on Healthengine, in a new tab.'

WPC = 'https://wellnesspsychologyclinic.com.au/'

CLINICIANS = [
    dict(
        slug='dr-anubhav-saxena', id='anubhav-saxena', category='gp',
        name='Dr Anubhav Saxena', short='Dr Saxena', role='GP', pronouns='he/him',
        practice='Beecroft Family & Skin Cancer Clinic', place='Beecroft & Double Bay', descriptor=None,
        description='A measured assessment with the physical baseline done properly, and ADHD care considered alongside the rest of your health.',
        chips=['Baseline physical screening', 'Integrative care', 'Phone consultations'],
        book_href='https://healthengine.com.au/doctor/nsw/beecroft/dr-anubhav-saxena/p123180', book_hint=HEALTHENGINE_HINT,
        links=[],
        fees=GP_FEES,
        qualifications='General practitioner, MBBS FRACGP MPhil BSc(Adv) DCH',
        languages=['English', 'Hindi', 'Urdu'],
        experience=[
            'Structured adult ADHD assessment',
            'Baseline cardiovascular and metabolic screening',
            'Integrative and preventive care',
            'Chronic disease management',
        ],
        about=[
            'Anubhav trained at the University of Sydney and works in Double Bay and Beecroft. He works from measurement rather than impression, and takes an integrative view: ADHD is looked at alongside sleep, cardiovascular and metabolic health rather than on its own, with a documented baseline before anything starts and review at set intervals rather than only when a problem gets loud enough to prompt a call. He also does aged-care and home visits, and gives a good deal of his spare time to the long-suffering cause of the Parramatta Eels.',
        ],
        details=[  # html values; Qualifications and Languages rows are added by the script
            ('Reach', 'Practice appointments and phone consultations'),
            ('Appointments', 'Long first appointment, scheduled reviews'),
            ('Billing', GP_BILLING),
            ('Wheelchair access', 'Yes'),
        ],
        disclosure='Dr Saxena owns Beecroft Family & Skin Cancer Clinic, which is ADHDme\'s first clinic partner. Disclosed because he appears in a listing run by a company his clinic has a commercial relationship with.',
        schema=dict(type='Physician', areas=['Beecroft', 'Double Bay'], state='NSW'),
    ),
    dict(
        slug='dr-anu-saxena', id='anu-saxena', category='gp',
        name='Dr Anu Saxena', short='Dr Anu Saxena', role='GP', pronouns='she/her',
        practice='Bay Health Clinic', place='Double Bay & Hornsby', descriptor=None,
        description='Brings a mental-health focus to general practice, with psychology training behind it.',
        chips=['Mental health focus', 'Women’s health', 'Hindi & Urdu'],
        book_href='https://healthengine.com.au/doctor/nsw/double-bay/dr-anusha-saxena/p160121', book_hint=HEALTHENGINE_HINT,
        links=[],
        fees=GP_FEES,
        qualifications='General practitioner, MD FRACGP BPsych(Hons) DCH',
        languages=['English', 'Hindi', 'Urdu'],
        experience=[
            'General practice, Bay Health Clinic, Double Bay',
            'Fellow of the Royal Australian College of General Practitioners',
            'Medical degree, Australian National University',
            'Bachelor of Psychology (First Class Honours), University of Sydney',
            'Hospital training across NSW: rotations in cardiology, paediatrics and psychiatry',
            'Sydney Child Health Program, Sydney Children\'s Hospital Network',
            'Diploma of Child Health',
            'Endorsed ADHD prescriber course, completed',
            'Focused Psychological Strategies, training underway',
            'Functional medicine, nutrition, lifestyle medicine and health coaching, further qualifications underway',
        ],
        about=[
            'Anu is an experienced GP at Bay Health Clinic in Double Bay, and a Fellow of the Royal Australian College of General Practitioners. She came to medicine through psychology, a Bachelor of Psychology with First Class Honours at the University of Sydney, then her MD at the Australian National University, with a background in psychiatry and general medicine: hospital training across NSW, including Blacktown and Bathurst, rotations in cardiology, paediatrics and psychiatry, and the Sydney Child Health Program through the Sydney Children\'s Hospital Network; she holds a Diploma of Child Health. Her clinical interests are ADHD, mental health, women\'s health and functional medicine. She has completed an endorsed ADHD prescriber course, is training in Focused Psychological Strategies, and is completing further qualifications in functional medicine, nutrition, lifestyle medicine and health coaching. Of Indian origin and speaking Hindi and Urdu, she values culturally sensitive, holistic and patient-centred care. Outside medicine she enjoys travelling, learning about different cultures, charity and community work, and staying active through sport, cricket and tennis included.',
        ],
        details=[
            ('Reach', 'Practice appointments in Double Bay and Hornsby'),
            ('Appointments', 'Appointment lengths set with the practice'),
            ('Billing', GP_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Dr Anu Saxena has a declared interest in ADHDme. Disclosed because she appears in a listing run by a company she is connected with.',
        schema=dict(type='Physician', areas=['Double Bay', 'Hornsby'], state='NSW'),
    ),
    dict(
        slug='paula-garrido', id='paula-garrido', category='psychologist',
        name='Paula Garrido', short='Paula Garrido', role='Clinical Psychologist', pronouns='she/her',
        practice='Wellness Psychology Clinic', place='Telehealth Australia-wide', descriptor='Clinical psychologist',
        description='Compassionate, neuroaffirming and trauma-informed care for ADHD and other neurodevelopmental differences.',
        chips=['Neuroaffirming', 'Trauma-informed', 'ADHD & autism certified'],
        book_href=WPC + 'appointment-page/', book_hint='Opens the clinic’s appointment request form, in a new tab.',
        links=[  # (kind, label, href): shown as pills under the booking button and in the Details "Online" row
            ('instagram', '@wellnesspsychologyclinic.au', 'https://www.instagram.com/wellnesspsychologyclinic.au/'),
            ('website', 'wellnesspsychologyclinic.com.au', WPC),
        ],
        fees=dict(
            heading='What a session costs',
            figures=[('$253', 'Per session'), ('$149', 'Medicare rebate')],
            notes=[
                'With the rebate, a session is $104 out of pocket.',
                'The rebate needs a Mental Health Treatment Plan and referral from your GP. The clinic can tell you what to bring before you book, and how many rebated sessions a plan covers.',
                'Sessions run for 60 minutes, by secure video.',
                '<strong>The fee is set and charged by the clinic you book with; ADHDme receives no part of it.</strong> It is published here so the cost is settled before you book rather than at the first session.',
            ],
        ),
        qualifications='Clinical psychologist, MClinPsych ADHD-CCSP ASDCS',
        languages=[],
        experience=[
            'Clinical psychologist, Wellness Psychology Clinic, telehealth Australia-wide',
            'Master of Clinical Psychology',
            'ADHD-Certified Clinical Services Provider (ADHD-CCSP)',
            'Certified Autism Spectrum Disorder Clinical Specialist (ASDCS)',
            'Additional training in ADHD, autism, complex trauma and evidence-based psychological therapies',
            'Extensive experience supporting individuals with ADHD and other neurodevelopmental differences',
        ],
        about=[
            'Paula Garrido is a Clinical Psychologist with extensive experience supporting individuals with ADHD and other neurodevelopmental differences. She has a special interest in providing compassionate, neuroaffirming, and trauma-informed psychological care, helping individuals better understand their unique strengths, challenges, and ways of experiencing the world.',
            'With additional training in ADHD, autism, complex trauma, and evidence-based psychological therapies, Paula supports individuals to navigate challenges with emotional regulation, executive functioning, anxiety, self-esteem, relationships, and everyday life. Her warm, collaborative, and non-judgmental approach creates a safe space for clients to explore their experiences, develop practical strategies, build self-understanding, and work towards meaningful and lasting change.',
            'Paula holds a Master of Clinical Psychology and is an ADHD-Certified Clinical Services Provider (ADHD-CCSP) and Certified Autism Spectrum Disorder Clinical Specialist (ASDCS).',
        ],
        details=[
            ('Reach', 'Telehealth, Australia-wide; the clinic is online only'),
            ('Appointments', '60-minute sessions by secure video; times set with the clinic'),
            ('Billing', '$253 per session, $149 Medicare rebate; set and charged by the clinic'),
            ('Wheelchair access', 'Not applicable: telehealth only, no premises to visit'),
        ],
        disclosure='Paula consults through Wellness Psychology Clinic, which also lists Dr Anu Saxena, who has a declared interest in ADHDme.',
        schema=dict(
            type='Person',
            credentials=['Master of Clinical Psychology', 'ADHD-Certified Clinical Services Provider (ADHD-CCSP)', 'Certified Autism Spectrum Disorder Clinical Specialist (ASDCS)'],
            same_as=['https://www.instagram.com/wellnesspsychologyclinic.au/', WPC + 'doctor/clinpsych-paula-garrido/'],
            works_for=dict(url=WPC, telephone='1800 31 31 39', locality='Sydney', state='NSW'),
            area='Australia',
        ),
    ),
]

# ---------------------------------------------------------------- helpers

def esc(text):
    """Plain text to HTML: & ' " < > become entities; curly quotes stay as they are."""
    return html.escape(text, quote=True)


class BuildError(Exception):
    pass


def jpeg_size(path):
    """(width, height) from a JPEG's start-of-frame marker; no image library needed."""
    data = path.read_bytes()
    if data[:2] != b'\xff\xd8':
        raise BuildError(f'{path} is not a JPEG')
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            raise BuildError(f'{path}: malformed JPEG')
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack('>H', data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack('>HH', data[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise BuildError(f'{path}: no frame header found')


def portrait_size(c):
    """Full-size square side in px, after checking all six portrait files exist and are square."""
    base = ROOT / PORTRAITS
    sizes = {}
    for suffix, expected in (('', None), ('-640', 640), ('-320', 320)):
        jpg = base / f"{c['id']}{suffix}.jpg"
        webp = base / f"{c['id']}{suffix}.webp"
        for f in (jpg, webp):
            if not f.exists():
                raise BuildError(f"{c['name']}: portrait file missing: {f.relative_to(ROOT)}")
        w, h = jpeg_size(jpg)
        if w != h:
            raise BuildError(f"{jpg.relative_to(ROOT)} is {w}x{h}; portraits must be square")
        if expected and w != expected:
            raise BuildError(f"{jpg.relative_to(ROOT)} is {w}px wide; expected {expected}")
        sizes[suffix] = w
    if sizes[''] < 640:
        raise BuildError(f"{c['name']}: full portrait is only {sizes['']}px; it must be larger than the 640 candidate")
    return sizes['']


def subline(c):
    """Under the name on the deck card and the 'Also in the network' link."""
    return f"{c['descriptor']} · {c['place']}" if c['descriptor'] else c['place']


def meta_line(c):
    parts = [c['pronouns'], c['descriptor'], c['practice'], c['place']]
    return ' · '.join(p for p in parts if p)


def og_title(c):
    return f"{c['name']}, {c['role']}, {c['place']}"


def others(c):
    return [o for o in CLINICIANS if o is not c]


# ---------------------------------------------------------------- fragments

PORTRAIT_BOX = 'aspect-square overflow-hidden rounded-2xl bg-[#f6f4ee] shadow-[inset_0_0_0_1px_#e8e6df]'
CHIP = '<span class="px-3.5 py-1.5 rounded-full text-sm font-semibold text-[#1a1c1c] bg-[#f6f4ee] border border-[#e8e6df]">{}</span>'
BOOK_HREF = 'the-doctors.html#{}'
ARROW_BACK = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M11 18l-6-6 6-6"/></svg>'
ICONS = {
    'instagram': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>',
    'website': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
}
ONLINE_PREFIX = {'instagram': 'Instagram, ', 'website': ''}
# Icon-only buttons under the booking button; the accessible name says whose account it is.
LINK_ARIA = {'instagram': '{practice} on Instagram, {label}', 'website': '{practice} website, {label}'}


def picture(c, size, sizes, img_attrs, img_class):
    """<picture> with WebP and JPEG candidates at 320, 640 and full size."""
    base = f"{PORTRAITS}/{c['id']}"
    cands = lambda ext: f'{base}-320.{ext} 320w, {base}-640.{ext} 640w, {base}.{ext} {size}w'
    return (f'<picture><source type="image/webp" srcset="{cands("webp")}" sizes="{sizes}">'
            f'<img {img_attrs} width="{size}" height="{size}" alt="Portrait of {esc(c["name"])}" class="{img_class}" '
            f'srcset="{cands("jpg")}" sizes="{sizes}" src="{base}.jpg"></picture>')


def portrait_span(c, size, tag, extra_class, sizes, img_attrs, img_class):
    return (f'<{tag} class="{extra_class}{PORTRAIT_BOX}" id="portrait-{c["id"]}" style="view-transition-name: portrait-{c["id"]}">'
            f'{picture(c, size, sizes, img_attrs, img_class)}</{tag}>')


def deck_card(c, size, eager):
    img_attrs = 'loading="eager" fetchpriority="high" decoding="async"' if eager else 'loading="lazy" decoding="async"'
    sizes = '(min-width: 1024px) 560px, (min-width: 640px) 50vw, 100vw'
    img_class = 'w-full h-full object-cover object-[center_30%] transition-transform duration-700 group-hover:scale-[1.02]'
    return f'''<li data-reveal id="{c['id']}" class="flex flex-col min-w-0">
  <a class="block group" href="{c['slug']}.html">
    {portrait_span(c, size, 'span', 'block ', sizes, img_attrs, img_class)}
    <span class="block pt-4"><strong class="block text-[22px] font-extrabold tracking-tight text-[#1a1c1c] leading-tight">{esc(c['name'])}</strong><span class="block mt-1 text-[15px] font-semibold text-[#5f5e59]">{esc(subline(c))}</span></span>
  </a>
  <div class="flex flex-wrap gap-2 pt-3">{''.join(CHIP.format(esc(x)) for x in c['chips'])}</div>
  <div class="pt-4"><a class="btn-press inline-flex items-center gap-2 h-11 px-6 rounded-full bg-[#1a1c1c] text-white text-[15px] font-bold hover:bg-[#2f3130] transition-colors" aria-label="Book with {esc(c['name'])}" href="{c['slug']}.html">Book <span class="text-[#f1bc31]" aria-hidden="true">→</span></a></div>
</li>'''


def also_link(c, size):
    return (f'<a class="inline-flex items-center gap-5 group" href="{c["slug"]}.html">'
            f'{portrait_span(c, size, "span", "block w-24 ", "96px", "loading=\"lazy\" decoding=\"async\"", "w-full h-full object-cover object-[center_30%]")}'
            f'<span><strong class="block text-[22px] leading-[1.25] font-extrabold tracking-tight text-[#1a1c1c]">{esc(c["name"])}</strong>'
            f'<span class="block text-[15px] font-semibold text-[#5f5e59]">{esc(subline(c))}</span></span></a>')


def jsonld(c):
    s = c['schema']
    page = f"{SITE}/{c['slug']}.html"
    image = f"{SITE}/{PORTRAITS}/{c['id']}.jpg"
    if s['type'] == 'Physician':
        d = {'@context': 'https://schema.org', '@type': 'Physician', '@id': page + '#physician',
             'name': c['name'], 'url': page, 'jobTitle': c['qualifications'], 'medicalSpecialty': 'PrimaryCare',
             'knowsLanguage': c['languages'], 'image': image,
             'address': {'@type': 'PostalAddress', 'addressLocality': s['areas'][0], 'addressRegion': s['state'], 'addressCountry': 'AU'},
             'areaServed': [{'@type': 'Place', 'name': f"{a}, {s['state']}, Australia"} for a in s['areas']],
             'affiliation': {'@type': 'MedicalOrganization', 'name': c['practice']}}
    elif s['type'] == 'Person':
        w = s['works_for']
        d = {'@context': 'https://schema.org', '@type': 'Person', '@id': page + '#person',
             'name': c['name'], 'url': page, 'jobTitle': c['qualifications'], 'image': image,
             'sameAs': s['same_as'],
             'hasCredential': [{'@type': 'EducationalOccupationalCredential', 'name': n} for n in s['credentials']],
             'worksFor': {'@type': 'MedicalBusiness', 'name': c['practice'], 'url': w['url'], 'telephone': w['telephone'],
                          'address': {'@type': 'PostalAddress', 'addressLocality': w['locality'], 'addressRegion': w['state'], 'addressCountry': 'AU'}},
             'areaServed': {'@type': 'Country', 'name': s['area']}}
    else:
        raise BuildError(f"{c['name']}: unknown schema type {s['type']!r}")
    d['memberOf'] = {'@id': SITE + '/#org'}
    d['potentialAction'] = {'@type': 'ReserveAction', 'target': c['book_href']}
    return json.dumps(d, ensure_ascii=False)


SECTION = ('<section class="lg:col-span-12 grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-16 pt-8 border-t border-[#e8e6df]" data-reveal>'
           '<h2 class="lg:col-span-4 text-2xl font-extrabold tracking-tight text-[#1a1c1c]">{}</h2>{}</section>')
DETAIL_ROW = ('<div class="grid grid-cols-1 sm:grid-cols-[10rem_1fr] gap-1 sm:gap-4 py-3 border-b border-[#e8e6df]">'
              '<dt class="text-[15px] font-semibold text-[#5f5e59]">{}</dt><dd class="m-0 text-[17px]">{}</dd></div>')
TEXT_LINK = 'class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" target="_blank" rel="noopener noreferrer"'
ICON_BUTTON = ('class="inline-flex items-center justify-center w-11 h-11 rounded-full text-[#1a1c1c] bg-[#f6f4ee] '
               'border border-[#e8e6df] hover:bg-white transition-colors" target="_blank" rel="noopener noreferrer"')


def render_main(c, size, sizes):
    fees = c['fees']
    pills = ''
    if c['links']:
        pills = ('\n      <div class="flex flex-wrap gap-2 pt-1">'
                 + ''.join(f'<a {ICON_BUTTON} href="{href}" aria-label="{esc(LINK_ARIA[kind].format(practice=c["practice"], label=label))}" title="{esc(label)}">{ICONS[kind]}</a>' for kind, label, href in c['links'])
                 + '</div>')
    details = [('Qualifications', esc(c['qualifications']))]
    if c['languages']:
        details.append(('Languages', esc(', '.join(c['languages']))))
    details += list(c['details'])
    if c['links']:
        details.append(('Online', ' · '.join(f'<a {TEXT_LINK} href="{href}">{esc(ONLINE_PREFIX[kind] + label)}</a>' for kind, label, href in c['links'])))
    return f'''<main id="main" class="w-full bg-[#FAFAF7]">
<script type="application/ld+json">{jsonld(c)}</script>
<div class="max-w-[1140px] mx-auto px-5 md:px-8 pt-6"><a class="inline-flex items-center gap-2 h-11 text-[15px] font-bold text-[#1a1c1c]" href="{BOOK_HREF.format(c['id'])}">{ARROW_BACK}The network</a></div>
<article class="max-w-[1140px] mx-auto px-5 md:px-8 pt-6 pb-16">
<div class="rounded-3xl bg-white border border-[#e8e6df] p-6 sm:p-10 lg:p-14 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-start">
  <div class="lg:col-span-5 arrive" style="--i:0">{portrait_span(c, size, 'div', '', '(min-width: 1024px) 420px, 100vw', 'fetchpriority="high" decoding="async"', 'w-full h-full object-cover object-[center_30%]')}</div>
  <div class="lg:col-span-7 flex flex-col gap-5">
    <h1 class="text-[36px] sm:text-[44px] lg:text-[52px] font-extrabold tracking-tight text-[#1a1c1c] leading-[1.02] arrive" style="--i:1">{esc(c['name'])}</h1>
    <p class="text-[15px] font-semibold text-[#5f5e59] arrive" style="--i:2">{esc(meta_line(c))}</p>
    <p class="text-[20px] sm:text-[22px] font-medium leading-snug text-[#1a1c1c] max-w-[40ch] arrive" style="--i:3" data-declared-by="clinician">{esc(c['description'])}</p>
    <div class="flex flex-wrap gap-2 arrive" style="--i:4">{''.join(CHIP.format(esc(x)) for x in c['chips'])}</div>
    <div class="flex flex-col items-start gap-3 pt-2 arrive" style="--i:5">
      <a class="btn-press inline-flex items-center gap-2 h-13 px-7 py-4 rounded-full bg-[#f1bc31] text-[#1a1c1c] text-[15px] font-bold hover:bg-[#e2ac24] transition-colors" href="{c['book_href']}" target="_blank" rel="noopener noreferrer">Book with {esc(c['short'])} <span aria-hidden="true">→</span></a>
      <span class="text-[13px] text-[#5f5e59]">{esc(c['book_hint'])}</span>{pills}
    </div>
  </div>
</div>
<section class="rounded-3xl bg-white border border-[#e8e6df] p-6 sm:p-10 mt-8 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-16" data-reveal aria-labelledby="fees-title">
  <h2 id="fees-title" class="lg:col-span-4 text-2xl font-extrabold tracking-tight text-[#1a1c1c]">{esc(fees['heading'])}</h2>
  <div class="lg:col-span-8 flex flex-col gap-5">
    <dl class="grid grid-cols-2 gap-6 max-w-md m-0">
{chr(10).join(f'      <div><dt class="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#1a1c1c] tabular-nums">{esc(amount)}</dt><dd class="m-0 mt-1 text-[15px] font-semibold text-[#5f5e59]">{esc(label)}</dd></div>' for amount, label in fees['figures'])}
    </dl>
{chr(10).join(f'    <p class="text-[17px] text-[#2b2820] max-w-[62ch]">{note}</p>' for note in fees['notes'])}
  </div>
</section>
<div class="mt-12 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16">
  {SECTION.format('Experience', '<ul class="lg:col-span-8 list-none p-0 m-0 text-[17px]" data-declared-by="clinician">' + ''.join(f'<li class="py-2.5 border-b border-[#e8e6df]">{esc(x)}</li>' for x in c['experience']) + '</ul>')}
  {SECTION.format('About', '<div class="lg:col-span-8 flex flex-col gap-4 text-[17px] leading-relaxed text-[#2b2820] max-w-[62ch]" data-declared-by="clinician">' + ''.join(f'<p class="m-0">{esc(p)}</p>' for p in c['about']) + '</div>')}
  {SECTION.format('Details', '<dl class="lg:col-span-8 m-0">' + ''.join(DETAIL_ROW.format(esc(k), v) for k, v in details) + '</dl>')}
  <p class="lg:col-span-12 pt-6 text-[15px] text-[#5f5e59] max-w-[72ch]">{esc(c['disclosure'])} Everything above is {esc(c['short'])}’s own declaration; the headings are ours.</p>
</div>
</article>

<section class="max-w-[1140px] mx-auto px-5 md:px-8 pb-20" aria-labelledby="also-title">
<h2 id="also-title" class="text-2xl font-extrabold tracking-tight text-[#1a1c1c] mb-5">Also in the network</h2>
<div class="flex flex-col sm:flex-row flex-wrap gap-8 sm:gap-12">
{chr(10).join(also_link(o, sizes[o['id']]) for o in others(c))}
</div>
</section>
</main>'''


def render_page(c, shell, sizes):
    # rel=expect blocks the first render until the last named portrait on the page is parsed, so the
    # cross-document view transition captures a whole page rather than a half-parsed one.
    last = (others(c) or [c])[-1]
    tokens = {
        'NAME': c['name'], 'SLUG': c['slug'], 'ID': c['id'], 'SITE': SITE, 'EXPECT_ID': last['id'],
        'DESCRIPTION': c['description'], 'OG_TITLE': og_title(c), 'PORTRAIT_SIZE': str(sizes[c['id']]),
    }
    page = shell
    for k, v in tokens.items():
        page = page.replace('{{' + k + '}}', esc(v))
    page = page.replace('{{MAIN}}', render_main(c, sizes[c['id']], sizes))
    left = re.findall(r'\{\{[A-Z_]+\}\}', page)
    if left:
        raise BuildError(f'unfilled tokens in shell: {sorted(set(left))}')
    return page


def render_deck(deck, sizes):
    """the-doctors.html with each category panel's <ul> refilled from CLINICIANS."""
    eager_id = next((c['id'] for c in CLINICIANS if c['category'] == DEFAULT_PANEL), None)
    for category, panel in PANELS.items():
        members = [c for c in CLINICIANS if c['category'] == category]
        pat = re.compile(r'(<div role="tabpanel" aria-labelledby="tab-btn-' + panel + '" id="panel-' + panel + r'"[^>]*><ul[^>]*>\n)(.*?)(</ul></div>)', re.S)
        found = pat.findall(deck)
        if not members:
            continue
        if len(found) != 1:
            raise BuildError(f'the-doctors.html: panel "{panel}" needs exactly one <div role="tabpanel" id="panel-{panel}"><ul>…</ul></div> to hold '
                             f'{", ".join(c["name"] for c in members)}; found {len(found)}. Replace the "Expected soon" placeholder with '
                             '<div role="tabpanel" aria-labelledby="tab-btn-' + panel + '" id="panel-' + panel + '" class="hidden"><ul class="grid grid-cols-1 sm:grid-cols-2 gap-10 md:gap-12 list-none p-0 m-0">\n</ul></div>')
        cards = '\n'.join(deck_card(c, sizes[c['id']], c['id'] == eager_id) for c in members) + '\n'
        deck = pat.sub(lambda m: m.group(1) + cards + m.group(3), deck, count=1)
    return deck


# ---------------------------------------------------------------- checks

def check_data():
    problems = []
    ids = [c['id'] for c in CLINICIANS]
    slugs = [c['slug'] for c in CLINICIANS]
    if len(set(ids)) != len(ids) or len(set(slugs)) != len(slugs):
        problems.append('duplicate id or slug in CLINICIANS')
    required = ['slug', 'id', 'category', 'name', 'short', 'role', 'pronouns', 'practice', 'place', 'descriptor', 'description',
                'chips', 'book_href', 'book_hint', 'links', 'fees', 'qualifications', 'languages', 'experience', 'about', 'details', 'disclosure', 'schema']
    for c in CLINICIANS:
        missing = [k for k in required if k not in c]
        if missing:
            problems.append(f"{c.get('name', c.get('slug'))}: missing fields {missing}")
        if c.get('category') not in PANELS:
            problems.append(f"{c['name']}: category must be one of {sorted(PANELS)}")
        for kind, _, _ in c.get('links', []):
            if kind not in ICONS:
                problems.append(f"{c['name']}: link kind {kind!r} has no icon; use one of {sorted(ICONS)}")
    sitemap = (ROOT / 'sitemap.xml').read_text()
    analytics = (ROOT / 'analytics.js').read_text()
    css = (ROOT / 'site.css').read_text()
    for c in CLINICIANS:
        if f"{SITE}/{c['slug']}.html" not in sitemap:
            problems.append(f"sitemap.xml has no entry for {c['slug']}.html")
        if f"profile: '{c['slug']}.html'" not in analytics:
            problems.append(f"analytics.js CLINICIANS does not declare {c['slug']}.html (profile views and booking clicks would be refused)")
        if f"::view-transition-group(portrait-{c['id']})" not in css:
            problems.append(f"site.css: add ::view-transition-group(portrait-{c['id']}) to the portrait transition rule")
    if problems:
        raise BuildError('\n  '.join(['fix these first:'] + problems))


def build():
    check_data()
    sizes = {c['id']: portrait_size(c) for c in CLINICIANS}
    shell = SHELL.read_text()
    out = {ROOT / f"{c['slug']}.html": render_page(c, shell, sizes) for c in CLINICIANS}
    out[DECK] = render_deck(DECK.read_text(), sizes)
    return out


def main(argv):
    check = '--check' in argv
    try:
        out = build()
    except BuildError as e:
        print(f'build-profiles: {e}', file=sys.stderr)
        return 2
    stale = [p for p, text in out.items() if not p.exists() or p.read_text() != text]
    if check:
        for p in stale:
            print(f'out of date: {p.relative_to(ROOT)}')
        print('profiles are up to date' if not stale else f'{len(stale)} file(s) differ; run python3 scripts/build-profiles.py')
        return 1 if stale else 0
    for p, text in out.items():
        p.write_text(text)
        print(('wrote  ' if p in stale else 'same   ') + str(p.relative_to(ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
