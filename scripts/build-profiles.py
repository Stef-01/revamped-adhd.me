#!/usr/bin/env python3
"""Generate the clinician profile pages and the cards on The Network from one data set.

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
LANDING = ROOT / 'index.html'
SITE = 'https://www.adhdme.au'
PORTRAITS = 'assets/clinicians'

# The Network: which tab panel each category's cards go in. The first clinician in the default panel
# is the one card that loads eagerly; every other card is lazy.
PANELS = {'gp': 'gps', 'psychologist': 'psychologists', 'allied': 'allied-health',
          'exercise-physiology': 'exercise-physiology', 'coach': 'coaches'}
DEFAULT_PANEL = 'gp'

# ---------------------------------------------------------------- data

GP_FEES = dict(
    heading='What a diagnosis costs',
    figures=[('$299', 'Initial consultation'), ('$199', 'Follow-up consultation')],
    notes=[  # html
        'The two consultations make up the ADHD assessment and diagnosis, $498 in total.',
        'Some people need an extra 30-minute review. The practice explains why, and the cost, before booking it.',
        'There is no Medicare rebate for either consultation.',
        '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
    ],
)
GP_BILLING = '$299 initial, $199 follow-up, no Medicare rebate; set and charged by the practice'
HEALTHENGINE_HINT = 'Opens Healthengine in a new tab.'

WPC = 'https://wellnesspsychologyclinic.com.au/'

# Neurotherapy Clinics Australia, five clinics; Lara Schulz practises at the Jindabyne one.
NCAU = 'https://www.ncau.com.au/'

# Neutral Minds Psychology, Ashgrove in Brisbane. Jess Katsamatsas is its psychologist and its director.
NMP = 'https://www.neutralmindspsychology.com.au/'
NMP_BOOK = 'https://clientportal.zandahealth.com/clientportal/neutralmindspsychology/appointment-booking'

# GOALS Psychology, Fortitude Valley. One clinic, eight clinicians, so the shared facts sit here once.
GOALS = 'https://www.goalspsychology.com/'
GOALS_BOOK = 'https://www.halaxy.com/book/goals-psychology/location/726621'
GOALS_BOOK_HINT = 'Opens Halaxy in a new tab.'
GOALS_PLACE = 'Brisbane & telehealth'
GOALS_LINKS = [
    ('instagram', '@goals.psychology', 'https://www.instagram.com/goals.psychology/'),
    ('website', 'goalspsychology.com', GOALS),
]
GOALS_REACH = 'Clinic appointments in Fortitude Valley, and telehealth Australia-wide'
GOALS_REACH_VISITS = ('Clinic appointments in Fortitude Valley, telehealth Australia-wide, and home, school and '
                      'community visits across Brisbane')
GOALS_APPOINTMENTS = '50-minute sessions; times set with the clinic'
# From the clinic's own "How to find us": first floor of the Central Brunswick Complex, Suite 14A2.
GOALS_ACCESS = 'Yes: level access from the same-level car park, with free one-hour client parking in the centre'
GOALS_DISCLOSURE = 'GOALS Psychology is an independent practice.'
GOALS_WORKS_FOR = dict(url=GOALS, telephone='0451 674 121', locality='Fortitude Valley', state='QLD')


# Medicare rebates for a session of at least 50 minutes under a Mental Health Treatment Plan. These are the
# government's figures, not any clinic's fee: MBS items 80110 (registered psychologist) and 80010 (clinical
# psychologist), schedule fee updated 1 July 2026, read from the two pages below on 2026-09-21. They are
# indexed each July; when they move, change them here and in how-it-works.html (check-site.py compares the two).
MBS_REBATE_REGISTERED = '$101.55'
MBS_REBATE_CLINICAL = '$149.05'
MBS_SOURCE = 'https://www9.health.gov.au/mbs/fullDisplay.cfm?type=item&q=80110&qt=item'


def goals_fees(rebate_note):
    """GOALS publishes no session fee, so this block carries no figures: see the note in `figures`.

    Inventing a number for a real clinic would be worse than publishing none, and the free 15-minute
    call is the clinic's own published way to ask before committing to a session.

    Checked again 2026-09-19 against the clinic's Halaxy page, so nobody has to repeat it: on a fresh
    load the price column is blank for "Appointment Request (50 minutes)" and for the 90-minute OT
    group session, and picking a named practitioner (tried Kate Row and Flynn Simonis) narrows the
    list to "New Client Free 15minute Call" at A$0.00. A$0.00 is the only figure anywhere on the page.
    Nothing on goalspsychology.com carries one either. If the clinic ever publishes a schedule, put
    the numbers in `figures` and the notes here can shrink.
    """
    return dict(
        heading='What a session costs',
        figures=[],  # deliberately empty: the clinic has not published a fee, so there is no figure to show
        notes=[
            'GOALS Psychology quotes its fee when you book. New clients can book a free 15-minute call to ask '
            'about cost first.',
            rebate_note,
            '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
        ],
    )


GOALS_FEES = goals_fees(
    'With a GP’s Mental Health Treatment Plan and referral, <a class="font-semibold text-[#1a1c1c] underline '
    'decoration-[#f1bc31] decoration-2 underline-offset-4" target="_blank" rel="noopener noreferrer" href="' + MBS_SOURCE
    + '">Medicare</a> pays ' + MBS_REBATE_REGISTERED + ' a session with a psychologist, or ' + MBS_REBATE_CLINICAL
    + ' with a clinical psychologist, for up to 10 sessions a year.')
GOALS_FEES_PROVISIONAL = goals_fees(
    'Provisional psychologist sessions have no Medicare rebate. The NDIS and some private health extras may cover '
    'them.')
GOALS_FEES_OT = goals_fees(
    'A Mental Health Treatment Plan doesn’t cover OT. The NDIS, private health extras or a GP’s chronic disease '
    'management plan often do.')

# REACH ADHD Coaching and Consultancy, Perth. One practice, six coaches, so the shared facts sit here once.
# Coaching is not a registered health profession, which is why the disclosure says so and why worksFor is a
# ProfessionalService rather than the MedicalBusiness the clinics get.
REACH = 'https://www.reachadhd.com.au/'
REACH_BOOK = REACH + 'contact/'
REACH_BOOK_HINT = 'Opens the practice’s website in a new tab.'
REACH_PLACE = 'Perth & online'
REACH_LINKS = [
    ('instagram', '@reach_adhd_coaching', 'https://www.instagram.com/reach_adhd_coaching/'),
    ('website', 'reachadhd.com.au', REACH),
]
REACH_REACH = 'Coaching online, and in person in Perth'
REACH_APPOINTMENTS = 'An initial consultation, then sessions weekly or fortnightly'
REACH_BILLING = 'Set and quoted by the practice; JobAccess funding may cover it'
REACH_DISCLOSURE = ('REACH ADHD Coaching and Consultancy is an independent practice. ADHD coaching is not a registered health '
                    'profession. Coaches do not assess, diagnose or provide therapy.')
REACH_WORKS_FOR = dict(type='ProfessionalService', url=REACH, telephone='(08) 6361 3506', locality='Perth', state='WA')
REACH_JOBACCESS = REACH + 'unlocking-support-how-adhd-coaching-can-be-funded-through-jobaccess/'

# Lawson ADHD Solutions, Sutherland in Sydney's south. Alex Lawson is its coach and its founder.
LAS = 'https://lawsonadhdsolutions.com.au/'

# Riverview Counselling, Glenbrook in the Blue Mountains. Trisha Harris is its clinical counsellor.
RVC = 'https://riverviewcounselling.com.au/'
RVC_BOOK = 'https://www.halaxy.com/book/riverview-counselling/location/671701'

# Another practice that publishes no price list, so no figures: same rule as GOALS and NCAU above. What it does
# publish, and what almost nobody looking at a coach knows, is that the work can be government-funded — so the
# notes carry that, with REACH's own figure and their guide to claiming it.
REACH_FEES = dict(
    heading='What coaching costs',
    figures=[],
    notes=[
        'REACH quotes its fee when you enquire.',
        'If you work at least eight hours a week, the Employment Assistance Fund can pay for coaching: '
        '<strong>around $1,770.44 a year</strong>, REACH says. Apply through <a ' + 'class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" '
        'target="_blank" rel="noopener noreferrer" href="https://www.jobaccess.gov.au/">JobAccess</a>; REACH’s <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] '
        'decoration-2 underline-offset-4" target="_blank" rel="noopener noreferrer" href="'
        + REACH_JOBACCESS + '">guide</a> has the steps.',
        'Self-managed and plan-managed NDIS participants can claim. For children, REACH says the NDIS is usually '
        'the only funding route.',
        '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
    ],
)


def reach_details():
    return [
        ('Reach', REACH_REACH),
        ('Appointments', REACH_APPOINTMENTS),
        ('Billing', REACH_BILLING),
        ('Wheelchair access', 'Not declared'),
    ]

# Atlantis Recovery Centre, Bundall: the first practice with rooms on the Gold Coast. It publishes no fee
# for any discipline, so the figures are empty and the notes carry the funding routes it names instead.
# Nobody there has declared telehealth, so nobody carries the pill. The portraits are illustrations until
# the practice supplies photographs (scripts/build-placeholder-portraits.py).
ARC = 'https://atlantisrc.com.au/'
ARC_BOOK = 'https://www.hotdoc.com.au/medical-centres/bundall-QLD-4217/atlantis-recovery-centre/doctors'
ARC_BOOK_HINT = 'Opens HotDoc in a new tab.'
ARC_PLACE = 'Bundall, Gold Coast'
ARC_LINKS = [('website', 'atlantisrc.com.au', ARC)]
ARC_REACH = 'Clinic appointments in Bundall, on the Gold Coast'
ARC_APPOINTMENTS = 'Times set with the practice; booked online through HotDoc'
ARC_BILLING = 'Quoted by the practice; DVA, NDIS, private health, WorkCover and Medicare plans accepted'
ARC_ACCESS = 'Yes: the practice describes the clinic as purpose-built and all-abilities accessible'
ARC_DISCLOSURE = 'Atlantis Recovery Centre is an independent practice.'
ARC_WORKS_FOR = dict(url=ARC, telephone='(07) 5610 2312', locality='Bundall', state='QLD')
ARC_SCHEMA = dict(same_as=[ARC + 'team/'], works_for=ARC_WORKS_FOR, area='Gold Coast, QLD, Australia', area_type='Place')
ARC_FEES = dict(
    heading='What a session costs',
    figures=[],
    notes=[
        'The practice quotes its fee when you book.',
        'It works with DVA, the NDIS, private health funds, WorkCover and GP care plans, and says bulk billing is '
        'available with conditions.',
        'NDIS participants don’t have to sign a service agreement.',
        '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
    ],
)


def arc_details():
    return [
        ('Reach', ARC_REACH),
        ('Appointments', ARC_APPOINTMENTS),
        ('Billing', ARC_BILLING),
        ('Wheelchair access', ARC_ACCESS),
    ]


CLINICIANS = [
    dict(
        slug='dr-anubhav-saxena', id='anubhav-saxena', category='gp',
        name='Dr Anubhav Saxena', short='Dr Saxena', role='GP', pronouns='he/him',
        practice='Beecroft Family & Skin Cancer Clinic', place='Beecroft & Double Bay', descriptor=None,
        description='ADHD assessment with a documented physical baseline, looked at alongside sleep, heart and metabolic health.',
        chips=['Baseline physical screening', 'Integrative care', 'Phone consultations'],
        telehealth=True,
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
        disclosure='Dr Saxena owns Beecroft Family & Skin Cancer Clinic. The clinic is ADHDme’s first clinic partner and has a commercial relationship with ADHDme.',
        schema=dict(type='Physician', areas=['Beecroft', 'Double Bay'], state='NSW'),
    ),
    dict(
        slug='dr-anu-saxena', id='anu-saxena', category='gp',
        name='Dr Anu Saxena', short='Dr Anu Saxena', role='GP', pronouns='she/her',
        practice='Bay Health Clinic', place='Double Bay & Hornsby', descriptor=None,
        description='A GP with an honours degree in psychology and clinical interests in ADHD, mental health and women’s health.',
        chips=['Mental health focus', 'Women’s health', 'Hindi & Urdu'],
        telehealth=True,
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
            ('Reach', 'Practice appointments in Double Bay and Hornsby, and telehealth'),
            ('Appointments', 'Appointment lengths set with the practice'),
            ('Billing', GP_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Dr Anu Saxena has a declared interest in ADHDme, the company that runs this listing.',
        schema=dict(type='Physician', areas=['Double Bay', 'Hornsby'], state='NSW'),
    ),
    dict(
        slug='paula-garrido', id='paula-garrido', category='psychologist',
        name='Paula Garrido', short='Paula Garrido', role='Clinical Psychologist', pronouns='she/her',
        practice='Wellness Psychology Clinic', place='Telehealth Australia-wide', descriptor='Clinical psychologist',
        description='Clinical psychologist certified in ADHD and autism care, seeing clients by video anywhere in Australia.',
        chips=['Neuroaffirming', 'Trauma-informed', 'ADHD & autism certified'],
        telehealth=True,
        book_href=WPC + 'appointment-page/', book_hint='Opens the practice’s website in a new tab.',
        links=[  # (kind, label, href): shown as pills under the booking button and in the Details "Online" row
            ('instagram', '@wellnesspsychologyclinic.au', 'https://www.instagram.com/wellnesspsychologyclinic.au/'),
            ('website', 'wellnesspsychologyclinic.com.au', WPC),
        ],
        fees=dict(
            heading='What a session costs',
            figures=[('$253', 'Per session'), ('$149', 'Medicare rebate')],
            notes=[
                'With the rebate, a session is $104 out of pocket.',
                'The rebate needs a Mental Health Treatment Plan and referral from your GP.',
                'Sessions run for 60 minutes, by secure video.',
                '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
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
        disclosure='Paula works through Wellness Psychology Clinic. The clinic also lists Dr Anu Saxena, who has a declared interest in ADHDme.',
        schema=dict(
            type='Person',
            credentials=['Master of Clinical Psychology', 'ADHD-Certified Clinical Services Provider (ADHD-CCSP)', 'Certified Autism Spectrum Disorder Clinical Specialist (ASDCS)'],
            same_as=['https://www.instagram.com/wellnesspsychologyclinic.au/', WPC + 'doctor/clinpsych-paula-garrido/'],
            works_for=dict(url=WPC, telephone='1800 31 31 39', locality='Sydney', state='NSW'),
            area='Australia',
        ),
    ),
    dict(
        slug='kate-row', id='kate-row', category='psychologist',
        name='Kate Row', short='Kate Row', role='Psychologist and Clinic Director', pronouns='she/her',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Psychologist & clinic director',
        description='Works with toddlers through to adults using CBT, ACT and MI, and supports families with the NDIS.',
        chips=['Toddlers to adults', 'NDIS journeys', 'CBT, ACT & MI'],
        telehealth=True,
        book_href=GOALS_BOOK, book_hint=GOALS_BOOK_HINT,
        links=GOALS_LINKS,
        fees=GOALS_FEES,
        qualifications='Psychologist, BSc(Psych) BA PostGradDip(Psych)',
        languages=[],
        experience=[
            'Psychologist and clinic director, GOALS Psychology, Fortitude Valley',
            'Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT) and Motivational Interviewing (MI)',
            'Solution-focused brief therapy, communication and social skills building',
            'Supporting individuals and families through their NDIS journey',
            'Career counselling and post-schooling decision making',
            'Bachelor of Science (Psychology) and Bachelor of Arts',
            'Postgraduate Diploma in Psychology',
        ],
        about=[
            'Kate works with toddlers, children, teenagers, and adults. The main therapeutic modalities she utilises include Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT), Motivational Interviewing (MI), solution-focused brief therapy, communication, and social skills building for growing client’s toolkits of practical coping strategies.',
            'Kate enjoys working with clients to identify their goals and work towards achieving them to improve overall well-being and live their most fulfilling lives possible. She has a life-long passion for working with clients with diffabilities/disabilities and supporting individuals and families through their NDIS journey to thrive. Kate is mum to three children.',
        ],
        details=[
            ('Reach', GOALS_REACH),
            ('Appointments', GOALS_APPOINTMENTS),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Science (Psychology)', 'Bachelor of Arts', 'Postgraduate Diploma in Psychology'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='ellie-putland', id='ellie-putland', category='psychologist',
        name='Ellie Putland', short='Ellie Putland', role='Psychologist', pronouns='she/her',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Psychologist',
        description='Trauma-informed therapy for children, teens and adults, with a particular interest in young people.',
        chips=['Trauma-informed', 'Young people', 'CBT, ACT & DBT'],
        telehealth=True,
        book_href=GOALS_BOOK, book_hint=GOALS_BOOK_HINT,
        links=GOALS_LINKS,
        fees=GOALS_FEES,
        qualifications='Psychologist, BPsychSc(Hons I)',
        languages=[],
        experience=[
            'Psychologist, GOALS Psychology, Fortitude Valley',
            'Trauma-informed care framework, working collaboratively with families',
            'Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT), Dialectical Behaviour Therapy (DBT) and Motivational Interviewing',
            'Experienced in administering an array of assessments',
            'Liaison with clients’ wider support teams',
            'Bachelor of Psychological Science with First Class Honours, Griffith University',
            'Associate Member of the Australian Psychological Society',
        ],
        about=[
            'Ellie works with children, teenagers and adults. She works with clients from a trauma-informed care framework and works collaboratively with families on psychoeducation towards their goals. Ellie utilises Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT), Dialectical Behaviour Therapy (DBT) and Motivational Interviewing.',
            'Ellie is experienced in administering an array of assessments, incorporating relevant resources into sessions and liaising with clients’ wider support teams wherever helpful towards client goals. By supporting clients to develop and refine their psychological and coping skills, Ellie has a particular passion for supporting young people who would like to reduce their stressors.',
            'With a Bachelor of Psychological Science from Griffith University with 1st class Honours, Ellie is also an Associate Member of the Australian Psychological Society.',
        ],
        details=[
            ('Reach', GOALS_REACH),
            ('Appointments', GOALS_APPOINTMENTS),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychological Science (First Class Honours), Griffith University',
                         'Associate Member, Australian Psychological Society'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='lachlan-avent', id='lachlan-avent', category='psychologist',
        name='Lachlan Avent', short='Lachlan Avent', role='Psychologist', pronouns='he/him',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Psychologist',
        description='Therapy, parenting support, and autism and ADHD assessment for children, teenagers and adults.',
        chips=['Autism & ADHD assessment', 'Children to adults', 'Triple P practitioner'],
        telehealth=True,
        book_href=GOALS_BOOK, book_hint=GOALS_BOOK_HINT,
        links=GOALS_LINKS,
        fees=GOALS_FEES,
        qualifications='Psychologist, BPsychSc(Hons)',
        languages=[],
        experience=[
            'Psychologist, GOALS Psychology, Fortitude Valley',
            'Autism assessment and ADHD assessment appointments',
            'Assessment administration including the WISC, WIAT, WAIS, ADOS and MIGDAS',
            'Cognitive Behavioural Therapy (CBT), Dialectical Behavioural Therapy (DBT), Acceptance and Commitment Therapy (ACT), Motivational Interviewing (MI) and Emotion Focussed Therapy (EFT)',
            'Certified Triple P Stepping Stones Parenting Program Practitioner',
            'Bachelor of Psychological Science with Honours, University of Queensland',
        ],
        about=[
            'Lachlan works with children, teenagers and adults and is passionate about providing a safe space for clients to express themselves, achieve their potential and meet the challenges that life presents. He is experienced working with clients who have autism, ADHD, OCD, specific learning disorders, depression, intellectual disability, are experiencing anxiety, phobias, depression, issues with self-esteem / confidence, stress / burn out, anger, bullying, interpersonal difficulties, and provides parenting support.',
            'Lachlan utilises Cognitive Behavioural Therapy (CBT), Dialectical Behavioural Therapy (DBT), Acceptance and Commitment Therapy (ACT), Motivational Interviewing (MI) and Emotion Focussed Therapy (EFT) to support clients to create meaningful change and build skills to live a life that fulfils them. Lachlan is experienced in administering assessments including the WISC, WIAT, WAIS, ADOS, MIGDAS and offers appointments for autism assessment and ADHD assessment. Lachlan is also a certified Triple P Stepping Stones Parenting Program Practitioner.',
            'Lachlan holds a Bachelor of Psychological Science with Honours from the University of Queensland.',
        ],
        details=[
            ('Reach', GOALS_REACH),
            ('Appointments', GOALS_APPOINTMENTS),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychological Science (Honours), University of Queensland',
                         'Certified Triple P Stepping Stones Parenting Program Practitioner'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='samantha-courtney', id='samantha-courtney', category='psychologist',
        name='Samantha Courtney', short='Samantha Courtney', role='Psychologist', pronouns='she/her',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Psychologist',
        description='A credentialed eating disorder clinician who also sees teens and adults for perinatal mental health.',
        chips=['Eating disorders', 'Perinatal & fertility', 'CEDC-MH credentialed'],
        telehealth=True,
        book_href=GOALS_BOOK, book_hint=GOALS_BOOK_HINT,
        links=GOALS_LINKS,
        fees=GOALS_FEES,
        qualifications='Psychologist, BPsychSc BSocSc(Psych)(Hons I) CEDC-MH',
        languages=[],
        experience=[
            'Psychologist, GOALS Psychology, Fortitude Valley',
            'Credentialed Eating Disorder Clinician (CEDC-MH)',
            'Eating disorder treatment with mums, new parents, athletes, and clients with co-occurring health conditions',
            'Perinatal mental health, fertility, and functional neurological disorder (FND)',
            'Trauma-informed care framework and a strengths-based lens',
            'Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT) and Dialectical Behaviour Therapy (DBT)',
            'Liaison with dieticians, GPs and psychiatrists',
            'Bachelor of Psychological Science, University of New England',
            'Bachelor of Social Science in Psychology (First Class Honours), University of the Sunshine Coast',
        ],
        about=[
            'Samantha works with teenagers and adults. She has experience working with clients who are experiencing difficulties with eating disorders, perinatal mental health, fertility, functional neurological disorder (FND), anxiety, depression, postnatal anxiety and depression, trauma and PTSD, and life stressors, including major life transitions such as parenthood, injuries, retiring and personal losses.',
            'Samantha is a Credentialed Eating Disorder Clinician (CEDC-MH) and her experience includes supporting clients who are mums, new parents, athletes, and clients from diverse life experiences with co-occurring health conditions to navigate eating disorder treatment. She is able to liaise with clients’ wider support teams such as dieticians, GPs and psychiatrists wherever helpful towards client goals.',
            'Samantha works from a trauma-informed care framework and a strengths-based lens to provide a calm, inclusive, and supportive environment for her clients to engage in individualised interventions. She utilises therapy modalities including Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT) and Dialectical Behaviour Therapy (DBT).',
            'Sam holds a Bachelor of Psychological Science from the University of New England, and a Bachelor of Social Science in Psychology (1st Class Honours) from the University of the Sunshine Coast.',
        ],
        details=[
            ('Reach', GOALS_REACH),
            ('Appointments', GOALS_APPOINTMENTS),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Credentialed Eating Disorder Clinician (CEDC-MH)',
                         'Bachelor of Psychological Science, University of New England',
                         'Bachelor of Social Science in Psychology (First Class Honours), University of the Sunshine Coast'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='lauren-poulos', id='lauren-poulos', category='psychologist',
        name='Lauren Poulos', short='Lauren Poulos', role='Psychologist', pronouns='she/her',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Psychologist',
        description='Early intervention and Parent-Child Interaction Therapy for young children, and therapy for teens and adults.',
        chips=['Toddlers & children', 'PCIT & early intervention', 'Psychometric assessment'],
        telehealth=True,
        book_href=GOALS_BOOK, book_hint=GOALS_BOOK_HINT,
        links=GOALS_LINKS,
        fees=GOALS_FEES,
        qualifications='Psychologist, BPsychSc(Hons) MProfPsych',
        languages=[],
        experience=[
            'Psychologist, GOALS Psychology, Fortitude Valley',
            'Early intervention with children, in clinic and at home',
            'Parent-Child Interaction Therapy (PCIT)',
            'Programs for managing disruptive behaviours in children to strengthen family dynamics',
            'Cognitive Behavioural Therapy (CBT), Motivational Interviewing (MI), skills building and coping strategies',
            'Psychometric assessment',
            'Communication methods including Proloquo2Go, PECS and ALD',
            'Bachelor of Psychological Sciences with Honours, University of Queensland',
            'Master of Professional Psychology, Bond University',
        ],
        about=[
            'Lauren works with toddlers, children, teens and adults. She is experienced working with clients who are experiencing anxiety, depression, emotional regulation, neurodivergence, autism, ADHD, intellectual disability, self esteem/ confidence, trauma, friendships & socialising, and offers parenting support among other presenting concerns.',
            'Lauren thoroughly enjoys facilitating a safe and collaborative space where clients can explore their goals and work toward meaningful change. She is experienced with Cognitive Behavioural Therapy (CBT), Motivational Interviewing (MI), skills building and coping strategies, Parent-Child Interaction Therapy (PCIT) and facilitating programs relating to managing disruptive behaviours in children to strengthen family dynamics. Lauren also has experience working with children in an early intervention context both in-clinic and at-home settings.',
            'Lauren holds a Bachelor of Psychological Sciences with Honours from the University of Queensland and a Master of Professional Psychology from Bond University.',
        ],
        details=[
            ('Reach', GOALS_REACH_VISITS),
            ('Appointments', GOALS_APPOINTMENTS),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychological Sciences (Honours), University of Queensland',
                         'Master of Professional Psychology, Bond University'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='alice-bui', id='alice-bui', category='psychologist',
        name='Alice Bui', short='Alice Bui', role='Provisional Psychologist', pronouns='she/her',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Provisional psychologist',
        description='Trauma-informed therapy, with a special interest in refugee, newly arrived and culturally diverse clients.',
        chips=['Trauma-informed', 'CALD & refugee clients', 'CBT, ACT, DBT & narrative'],
        telehealth=True,
        book_href=GOALS_BOOK, book_hint=GOALS_BOOK_HINT,
        links=GOALS_LINKS,
        fees=GOALS_FEES_PROVISIONAL,
        qualifications='Provisional psychologist, BPsych BPsychSc(Hons), Master of Clinical Psychology in progress',
        languages=[],
        experience=[
            'Provisional psychologist, GOALS Psychology, Fortitude Valley',
            'Evidence-based practice for clients who have experienced trauma',
            'Work with refugee and newly arrived clients, and clients from culturally and linguistically diverse (CALD) backgrounds',
            'Displacement, cultural transition and complex trauma',
            'Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT), Dialectical Behaviour Therapy (DBT) and Narrative Therapy',
            'Bachelor of Psychology, Macquarie University',
            'Bachelor of Psychological Science (Honours)',
            'Master of Clinical Psychology, currently completing',
        ],
        about=[
            'Alice works with children, teens and adults. She is experienced working with clients regarding trauma, PTSD, anxiety, depression, adjustment difficulties, autism, ADHD, intellectual disability, neurodivergence, emotional dysregulation, behavioural challenges, among other presenting concerns. Her therapy style is trauma-informed and emphasises a safe collaborative space.',
            'Alice has special clinical interests in evidence-based practice for clients who have experienced trauma. She is particularly passionate about working with clients who are refugees and newly arrived backgrounds and thoroughly enjoys supporting clients from culturally and linguistically diverse (CALD) backgrounds who have experienced displacement, cultural transition and complex trauma with cultural sensitivity to tailor interventions to their unique lived experiences. Alice is experienced with Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT), Dialectical Behaviour Therapy (DBT) and Narrative Therapy.',
            'Alice holds a Bachelor of Psychology from Macquarie University, Bachelor of Psychological Science (Honours) and is currently completing a Master of Clinical Psychology.',
        ],
        details=[
            ('Reach', GOALS_REACH),
            ('Appointments', GOALS_APPOINTMENTS),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychology, Macquarie University',
                         'Bachelor of Psychological Science (Honours)'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='meera-lakhani', id='meera-lakhani', category='psychologist',
        name='Meera Lakhani', short='Meera Lakhani', role='Educational and Developmental Psychologist', pronouns='she/her',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Educational & developmental psychologist',
        description='Educational and developmental psychologist focused on autism, ADHD and cognitive assessment.',
        chips=['Autism & ADHD assessment', 'Cognitive assessment', 'Young adults & families'],
        telehealth=True,
        # Meera is not one of the practitioners bookable on the clinic's Halaxy page, so this goes to the clinic instead.
        book_href=GOALS + 'contact',
        book_hint='Opens the practice’s website in a new tab.',
        links=GOALS_LINKS,
        fees=GOALS_FEES,
        qualifications='Educational and developmental psychologist, BPsychSc MPsych(Ed&Dev)',
        languages=[],
        experience=[
            'Educational and developmental psychologist, GOALS Psychology, Fortitude Valley',
            'Neurodivergence assessment: autism assessment, ADHD assessment and cognitive assessment',
            'Assessment tools including the WISC, WAIS, WIAT and MIGDAS',
            'Educational and developmental assessments',
            'Circle of Security (COS), Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT) and attachment theory',
            'Previously a psychologist in a school, and at the Queensland Children’s Hospital Child Development Service',
            'Bachelor of Psychological Science, University of Queensland',
            'Master of Psychology (Educational & Developmental), Queensland University of Technology',
        ],
        about=[
            'Meera works with children, teenagers and adults. She enjoys working with clients to understand their goals then create a plan to achieve their goals. Meera is passionate about helping clients to identify their unique areas of strengths and difficulties and collaborate with relevant stakeholders to maximise positive outcomes in their lives.',
            'Meera’s current focus is on neurodivergence assessments — autism assessment, ADHD assessment and cognitive assessment. She utilises assessment tools including WISC, WAIS, WIAT, MIGDAS and others as required to support clients with discovering an enhanced understanding of their unique neurotype. Meera is especially passionate about working with young adults and their families, in a way that aligns with their values and beliefs, to be the best version of themselves. She thrives on supporting clients to lean into vulnerability, learn new skills and navigate life’s challenges.',
            'Meera holds a Bachelor of Psychological Science from The University of Queensland and a Master of Psychology - Educational & Developmental from Queensland University of Technology. She has previously worked as a Psychologist in a school and at the Queensland Children’s Hospital Child Development Service.',
        ],
        details=[
            ('Reach', GOALS_REACH),
            ('Appointments', 'Arranged by enquiry with the clinic'),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychological Science, University of Queensland',
                         'Master of Psychology (Educational & Developmental), Queensland University of Technology'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    # First in Allied health on purpose: counselling is the allied service people with ADHD reach for
    # most, so she leads the panel. The deck sorts online diaries ahead of enquiry forms and keeps this
    # file's order within each half, so her position here is what puts her at the top.
    dict(
        slug='trisha-harris', id='trisha-harris', category='allied',
        name='Trisha Harris', short='Trisha', role='Clinical Counsellor', pronouns='she/her',
        practice='Riverview Counselling', place='Glenbrook & telehealth',
        descriptor='Clinical counsellor',
        description='A counsellor with ADHD herself, seeing teens, adults, couples and NDIS participants in Glenbrook.',
        chips=['Teens, adults & couples', 'NDIS participants', 'Lived experience'],
        telehealth=True,
        book_href=RVC_BOOK, book_hint='Opens Halaxy in a new tab.',
        links=[
            ('instagram', '@riverviewcounselling_', 'https://www.instagram.com/riverviewcounselling_/'),
            ('website', 'riverviewcounselling.com.au', RVC),
        ],
        fees=dict(
            heading='What a session costs',
            figures=[('$180', 'Individual, 60 minutes'), ('$220', 'Couples & family')],
            notes=[
                'Ninety minutes is $270, or $330 for couples and families. Weekends and after 5pm add $25.',
                'NDIS participants are $156.16 per 60 minutes.',
                'Counselling has no Medicare rebate, so you don’t need a GP plan or referral.',
                '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
            ],
        ),
        qualifications='Clinical counsellor, PACFA Registered Clinical (27633), PGDipCouns',
        languages=[],
        experience=[
            'Clinical counsellor, Riverview Counselling, Glenbrook',
            'PACFA Registered Clinical counsellor, registration 27633',
            'Over two decades working in mental health and counselling',
            'Individuals, couples, families and teenagers, including NDIS participants',
            'Attachment-based, CBT, compassion-focused, family systems, Internal Family Systems, person-centred, psychodynamic and solution-focused brief therapy',
            'Registered career counsellor',
            'Post Graduate Diploma of Counselling, 2014',
            'Post Graduate Certificate in Education (Career Development), Australian Catholic University, 2011',
            'Bachelor of Social Science (Criminology), Western Sydney University, 2003',
        ],
        about=[
            'Hi, I’m Trisha, a Clinical Counsellor, mum of 4 (3 who have diagnosis\'), I have ADHD and run a business, so I absolutely understand how busy, stressful and chaotic life can get!',
            'I work with individuals, couples and teens, including NDIS participants.',
            'I understand the need for support, to be heard, to have undivided attention that is just for YOU. I can help you handle the \'right now\' with a safe space for you to plan for your future and reach your goals.',
            'Supporting you, every step of the way.',
        ],
        details=[
            ('Reach', 'Face-to-face sessions in Glenbrook in the Blue Mountains, and by phone and video'),
            ('Appointments', '60 and 90-minute sessions, weekdays 10am to 4pm; the practice has a waiting list for late afternoons'),
            ('Billing', '$180 per 60 minutes for an individual, $220 for couples and families; set and charged by the practice'),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Riverview Counselling is an independent practice. Counsellors are registered with PACFA, not AHPRA.',
        schema=dict(
            type='Person',
            credentials=['PACFA Registered Clinical counsellor (27633)', 'Post Graduate Diploma of Counselling',
                         'Post Graduate Certificate in Education (Career Development), Australian Catholic University',
                         'Bachelor of Social Science (Criminology), Western Sydney University'],
            same_as=[RVC, 'https://www.instagram.com/riverviewcounselling_/',
                     'https://www.linkedin.com/in/trisha-harris',
                     'https://www.psychologytoday.com/au/counselling/trisha-harris-riverview-counselling-glenbrook-nsw/880222'],
            works_for=dict(url=RVC, telephone='(02) 4703 5077', locality='Glenbrook', state='NSW'),
            area='Australia',
        ),
    ),
    dict(
        slug='flynn-simonis', id='flynn-simonis', category='allied',
        name='Flynn Simonis', short='Flynn Simonis', role='Occupational Therapist', pronouns='he/him',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Occupational therapist',
        description='Paediatric occupational therapy led by the child’s own interests, in clinic, at home or at school.',
        chips=['Paediatric OT', 'Home & school visits', 'FCA report writing'],
        telehealth=True,
        book_href=GOALS_BOOK, book_hint=GOALS_BOOK_HINT,
        links=GOALS_LINKS,
        fees=GOALS_FEES_OT,
        qualifications='Occupational therapist',
        languages=[],
        experience=[
            'Occupational therapist, GOALS Psychology, Fortitude Valley',
            'Paediatric occupational therapy, including play therapy and parent training',
            'Functional Capacity Assessments (FCAs) and report writing',
            'Group programs including LEGO, Minecraft and Ninja Warrior-style social and movement programs',
            'Outdoor adventure and nature camps building independence, resilience and confidence',
            'Sensory profiles, emotional regulation needs and functional challenges',
            'Family-centred practice with caregivers, schools and multidisciplinary teams',
            'In-clinic, home visit, kindergarten and school visit appointments',
        ],
        about=[
            'Flynn works with toddlers, children, teenagers and young adults. He is experienced working with clients who have experienced developmental trauma, neurodivergence, autism, Attention-Deficit Hyperactivity Disorder (ADHD), school refusal / school can’t, developmental delay, non-verbal communication profiles, Generalised Anxiety Disorder (GAD), emotional regulation, parenting support, intellectual disability, Oppositional Defiant Disorder (ODD), Rett Syndrome, and Muscular Dystrophy and many other presentations. Flynn enjoys supporting children with varying communication styles, sensory profiles, emotional regulation needs, and functional challenges.',
            'Flynn is particularly passionate about paediatric occupational therapy including play therapy and parent training. He facilitates sessions that are guided by his client’s interests, recognising that children engage and learn best when therapy is meaningful and motivating towards skill development for participation in everyday life. Flynn emphasises a foundation of communication with families, schools and multidisciplinary teams, to create a safe, supportive, creative and fun therapy environment. He values family-centred practice in working with caregivers to ensure that recommended strategies are practical, achievable and able to be easily implemented into daily routines. Flynn offers in-clinic, home visits, kindergarten and school visit appointments where appropriate towards his clients’ goals.',
            'Flynn is also experienced with Functional Capacity Assessments (FCAs) and report writing, and facilitating group programs including LEGO, Minecraft and Ninja Warrior-style social and movement programs, outdoor adventure and nature camps, all supporting goals including social skills, teamwork, and motor development, building independence, resilience, and confidence in children and young people.',
        ],
        details=[
            ('Reach', GOALS_REACH_VISITS),
            ('Appointments', 'Clinic, home, kindergarten and school visits; times set with the clinic'),
            ('Billing', 'Set and charged by the clinic; quoted when you book'),
            ('Wheelchair access', GOALS_ACCESS),
        ],
        disclosure=GOALS_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Registered occupational therapist'],
            same_as=[GOALS + 'our-team', 'https://www.instagram.com/goals.psychology/'],
            works_for=GOALS_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='lara-schulz', id='lara-schulz', category='allied',
        name='Lara Schulz', short='Lara Schulz', role='Neurotherapy Practitioner and Director', pronouns='she/her',
        practice='Neurotherapy Clinics Australia', place='Jindabyne & Snowy Mountains',
        descriptor='Neurotherapy practitioner & director',
        description='QEEG brain mapping and neurotherapy in Jindabyne, with a consultation on the findings before training starts.',
        chips=['QEEG brain mapping', 'ERP assessment', 'Neurostimulation'],
        # Neurotherapy needs the equipment and the client in the same room, and the practice offers no
        # remote option, so the marker stays off.
        telehealth=False,
        book_href=NCAU + 'contact-us/',
        book_hint='Opens the practice’s website in a new tab.',
        links=[
            ('instagram', '@neurotherapy_clinics_australia', 'https://www.instagram.com/neurotherapy_clinics_australia/'),
            ('website', 'ncau.com.au', NCAU),
        ],
        fees=dict(
            heading='What it costs',
            # Another clinic with no published price list: same rule as GOALS above, so no figures.
            figures=[],
            notes=[
                'The clinic quotes fees for each person when you get in touch. Payment plans can be arranged.',
                'The quote covers a two-hour first appointment with QEEG brain scans and a results consultation. '
                'Training sessions then run 30 minutes each.',
                '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
            ],
        ),
        qualifications='Neurotherapy practitioner, GradDipPsych MBusMgt',
        languages=[],
        experience=[
            'Director and principal neurotherapy practitioner, Neurotherapy Clinics Australia',
            'Alpine Neurotherapy Clinic, Jindabyne, established after relocating from Perth',
            'Neurotherapy training in Santa Barbara, California, with Dr Nicholas Dogris, founder of Neurofield Neurotherapy, and Dr Tiffany Thompson',
            'EEG and QEEG assessment, and ERP assessment and analysis',
            'Neurostimulation including tACS, tDCS, tAPNS and pEMF',
            'Graduate Diploma in Psychology, University of New South Wales',
            'Master of Business Management, Charles Sturt University',
            'Presented her practice results at the Neurofield International Conference, Santa Barbara, September 2022',
            'Speaks at conferences internationally and domestically, and to clinician groups on mental health awareness in regional areas',
        ],
        about=[
            'Lara Schulz established her first Neurotherapy practice in Perth in 2019 after completing her neurotherapy training in Santa Barbara, California with expert neuroscientist and founder of Neurofield Neurotherapy, Dr Nicholas Dogris and Dr Tiffany Thompson. Since relocating to Jindabyne in Alpine NSW, she has established Alpine Neurotherapy.',
            'Lara has a Graduate Diploma in Psychology from the University of NSW and will be continuing with her Post Graduate Psychology study after a well deserved break from study between degrees. She has studied in the USA learning how to read EEG and QEEG assessment as well as ERP assessment and analysis; and a diverse range of neurostimulation techniques including tACS, tDCS, tAPNS and pEMF.',
            'In September 2022 Lara was invited to present the results of her neurotherapy practice at the Neurofield International Conference in Santa Barbara USA. Lara has appeared on Sky News being interviewed by Erin Molan along with Dr Dogris in the hope of bringing awareness to Australia about this state of the art therapy for all Australians.',
            'As well as speaking at conferences both internationally and domestically Lara regularly is invited to speak to groups for Mental Health information awareness for clinicians in regional areas discussing case studies and Neurostimulation.',
            'Lara came to this work as a client, for her own learning difficulties, and changed careers after her own child needed neurofeedback. Having completed a Masters of Business Management at Charles Sturt University, she enrolled in the Graduate Diploma in Psychology through the University of New South Wales to extend her knowledge of psychological functioning, which she describes as integral to her neurotherapy practice. She says she has always felt passionately about wanting to help and reassure anyone with learning difficulties, ADHD or any other disability that they are no different from anyone else: “We just think differently and that is something to nurture and be proud of”.',
        ],
        details=[
            ('Reach', 'Clinic appointments in Jindabyne, serving the Snowy Mountains, Cooma and the Snowy Monaro region'),
            ('Appointments', 'A two-hour first appointment, then a 30-minute consultation on the findings; training sessions run 30 minutes'),
            ('Billing', 'Set and quoted by the practice for each person; payment plans can be arranged'),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Neurotherapy Clinics Australia is an independent practice.',
        schema=dict(
            type='Person',
            credentials=['Graduate Diploma in Psychology, University of New South Wales',
                         'Master of Business Management, Charles Sturt University',
                         'Neurofield neurotherapy training, Santa Barbara, California'],
            same_as=[NCAU + 'about/', 'https://www.instagram.com/neurotherapy_clinics_australia/'],
            works_for=dict(url=NCAU, telephone='+61 418 216 077', locality='Jindabyne', state='NSW'),
            # She sees people in one town, so the country-wide default would overstate it.
            area='Snowy Mountains, NSW, Australia', area_type='Place',
        ),
    ),
    dict(
        slug='fiona-alexander', id='fiona-alexander', category='coach',
        name='Fiona Alexander', short='Fiona Alexander', role='ADHD Coach',
        # REACH's coaches write their own bios in the first person and none of them states a pronoun,
        # so the field is left empty rather than guessed; meta_line drops it.
        pronouns='',
        practice='REACH ADHD Coaching and Consultancy', place=REACH_PLACE,
        descriptor='ADHD coach',
        description='An ADHD coach with 25 years of teaching, helping students and families understand how their brain works.',
        chips=['Executive functioning', 'Students & families', 'Able & gifted learners'],
        telehealth=True,
        book_href=REACH_BOOK, book_hint=REACH_BOOK_HINT,
        links=REACH_LINKS,
        fees=REACH_FEES,
        qualifications='ADHD coach, BA(Primary Ed) BEd AACC ACC',
        languages=[],
        experience=[
            'Co-founder, REACH ADHD Coaching and Consultancy, Perth',
            '25 years teaching in local and international schools',
            'ADHD coach training at the ADHD Coaching Academy (ADDCA), New York',
            'Associate Certified Coach (ACC), International Coaching Federation',
            'Bachelor of Arts (Primary School Education)',
            'Bachelor of Education',
            'Teaching and Learning for Able/Gifted Children',
        ],
        about=[
            'Throughout my 25 years in education, I’ve had the privilege of teaching children from all walks of life, each with their own strengths and unique ways of thinking. It didn’t take long for me to recognise that every student learns differently and that diversity in learning is something to be celebrated. This realisation inspired me to specialise in ADHD education, where I could focus on supporting neurodivergent students and their families.',
            'My teaching journey has taken me across both local and international schools, and in every classroom, I’ve learned just as much as my students. Understanding how your brain works is the first step in overcoming challenges, and it’s incredibly rewarding to help students and families discover that. My coaching approach is about guiding individuals through this journey of self-discovery, helping them embrace who they are, and confidently navigating the learning process.',
            'I’m passionate about helping clients thrive in their own way. Together, we can make learning an empowering experience that brings out the best in you.',
        ],
        details=reach_details(),
        disclosure=REACH_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Arts (Primary School Education)', 'Bachelor of Education',
                         'AACC ADHD Coach, ADHD Coaching Academy (ADDCA)',
                         'Associate Certified Coach (ACC), International Coaching Federation'],
            same_as=[REACH + 'meet-the-coaches/', 'https://www.instagram.com/reach_adhd_coaching/'],
            works_for=REACH_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='debbie-hirte', id='debbie-hirte', category='coach',
        name='Debbie Hirte', short='Debbie Hirte', role='ADHD Coach', pronouns='',
        practice='REACH ADHD Coaching and Consultancy', place=REACH_PLACE,
        descriptor='ADHD coach',
        description='ADHD coach and former Gifted and Talented Specialist with nearly 30 years in independent schools.',
        chips=['Executive functioning', 'Children & teens', 'Gifted & talented'],
        telehealth=True,
        book_href=REACH_BOOK, book_hint=REACH_BOOK_HINT,
        links=REACH_LINKS,
        fees=REACH_FEES,
        qualifications='ADHD coach, BA(Early Childhood Ed) AACC ACC',
        languages=[],
        experience=[
            'Co-founder, REACH ADHD Coaching and Consultancy, Perth',
            'Nearly 30 years in independent schools as classroom teacher, specialist and Gifted and Talented Specialist',
            'Mentoring educators, and co-designing Individual Education Plans with families and schools',
            'ADHD coach training at the ADHD Coaching Academy (ADDCA), New York',
            'Associate Certified Coach (ACC), International Coaching Federation',
            'Bachelor of Arts (Early Childhood Education)',
        ],
        about=[
            'With nearly three decades in Independent schools, my commitment to supporting neurodivergent students and their families has been a driving force throughout my career. I’ve had the opportunity to work as a classroom teacher, specialist, and later, as a Gifted and Talented Specialist, advocating for students and helping them succeed both academically and socially.',
            'Over the years, I’ve developed a deep understanding of the unique challenges neurodivergent individuals face. My role has allowed me to mentor educators, collaborate with families, and support students through tailored strategies designed to meet their needs. Working closely with this incredible community has only strengthened my passion for helping individuals embrace their unique brain wiring.',
            'Through ADHD coaching, my goal is to help students and families see that differences in learning are something to be embraced, not feared. I’m here to provide the tools and strategies that enable growth and success, helping every individual step into their best self with confidence.',
        ],
        details=reach_details(),
        disclosure=REACH_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Arts (Early Childhood Education)', 'Gifted and Talented Specialist',
                         'AACC ADHD Coach, ADHD Coaching Academy (ADDCA)',
                         'Associate Certified Coach (ACC), International Coaching Federation'],
            same_as=[REACH + 'meet-the-coaches/', 'https://www.instagram.com/reach_adhd_coaching/'],
            works_for=REACH_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='romney-taylor', id='romney-taylor', category='coach',
        name='Romney Taylor', short='Romney Taylor', role='ADHD Consultant Coach', pronouns='',
        practice='REACH ADHD Coaching and Consultancy', place=REACH_PLACE,
        descriptor='ADHD consultant coach',
        description='ADHD coach with 23 years of work with students, building strategies for school, home and relationships.',
        chips=['Executive functioning', 'Students', 'Advocacy & inclusion'],
        telehealth=True,
        book_href=REACH_BOOK, book_hint=REACH_BOOK_HINT,
        links=REACH_LINKS,
        fees=REACH_FEES,
        qualifications='ADHD coach, BSc GradDipEd AACC ACC',
        languages=[],
        experience=[
            'Consultant coach, REACH ADHD Coaching and Consultancy, Perth',
            '23 years working with students across local and interstate schools',
            'ADHD coach training at the ADHD Coaching Academy (ADDCA), New York',
            'Associate Certified Coach (ACC), International Coaching Federation',
            'Bachelor of Science',
            'Graduate Diploma in Education',
            'Mini-COGE, gifted and talented education',
        ],
        about=[
            'For the past 23 years, I’ve worked with students across diverse local and interstate schools, and one of the most important things I’ve learned is that no two minds work the same. Recognising this truth inspired me to pursue specialist training as an ADHD coach, allowing me to focus on supporting neurodivergent individuals in a way that celebrates their strengths and addresses their unique challenges.',
            'As a consultant coach to REACH ADHD it provides me the opportunity to create a safe and inclusive space where neurodiverse students can feel heard and understood. It’s incredibly rewarding to help them develop strategies that fit their individual needs, whether that’s in the classroom, in relationships, or at home. My passion for advocacy drives me to promote awareness and acceptance for all neurodiverse individuals, building a culture of inclusivity in every environment I work in.',
            'Watching my clients grow and achieve goals they once thought were out of reach is the most fulfilling part of my work. Together, we’ll work towards success in a way that is meaningful to you.',
        ],
        details=reach_details(),
        disclosure=REACH_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Science', 'Graduate Diploma in Education',
                         'AACC ADHD Coach, ADHD Coaching Academy (ADDCA)',
                         'Associate Certified Coach (ACC), International Coaching Federation'],
            same_as=[REACH + 'meet-the-coaches/', 'https://www.instagram.com/reach_adhd_coaching/'],
            works_for=REACH_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='erin-lysle', id='erin-lysle', category='coach',
        name='Erin Lysle', short='Erin Lysle', role='ADHD Consultant Coach', pronouns='',
        practice='REACH ADHD Coaching and Consultancy', place=REACH_PLACE,
        descriptor='ADHD consultant coach',
        description='ADHD coach with over 34 years of teaching, working on executive functioning, confidence and social skills.',
        chips=['Executive functioning', 'Self-confidence', 'Social skills'],
        telehealth=True,
        book_href=REACH_BOOK, book_hint=REACH_BOOK_HINT,
        links=REACH_LINKS,
        fees=REACH_FEES,
        qualifications='ADHD coach, BA BEd AACC',
        languages=[],
        experience=[
            'Consultant coach, REACH ADHD Coaching and Consultancy, Perth',
            'Over 34 years teaching across a wide range of educational settings',
            'ADHD coach training at the ADHD Coaching Academy (ADDCA), New York',
            'Bachelor of Arts',
            'Bachelor of Education',
        ],
        about=[
            'With over 34 years of teaching experience, I’ve had the privilege of working across a wide range of educational settings. Over time, I’ve come to understand just how varied and complex ADHD can be for each individual, and this insight has shaped my approach as an ADHD coach. I bring together my expertise in education with a deep understanding of ADHD, crafting strategies that truly connect with each client.',
            'As a consulting coach to REACH ADHD, my priority is meeting each person where they are. I believe in creating a supportive, positive environment where clients feel encouraged to explore new strategies and tackle challenges head-on. Whether we’re focusing on building self-confidence, improving executive functioning, or enhancing social skills, my coaching is centred around empathy, patience, and understanding.',
            'My role is to help clients not only manage ADHD traits but to help them grow in a way that aligns with their personal goals and values. I celebrate every milestone with my clients, big or small, and I’m dedicated to equipping them with tools that lead to long-lasting success.',
        ],
        details=reach_details(),
        disclosure=REACH_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Arts', 'Bachelor of Education',
                         'AACC ADHD Coach, ADHD Coaching Academy (ADDCA)'],
            same_as=[REACH + 'meet-the-coaches/', 'https://www.instagram.com/reach_adhd_coaching/'],
            works_for=REACH_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='donna-italiano', id='donna-italiano', category='coach',
        name='Donna Italiano', short='Donna Italiano', role='ADHD Consultant Coach',
        pronouns='she/her',  # the only one of the six whose bio states it
        practice='REACH ADHD Coaching and Consultancy', place=REACH_PLACE,
        descriptor='ADHD consultant coach',
        description='ADHD coach and secondary teacher working with young people on executive functioning and emotional regulation.',
        chips=['Executive functioning', 'Emotional regulation', 'Neurodivergent-affirming'],
        telehealth=True,
        book_href=REACH_BOOK, book_hint=REACH_BOOK_HINT,
        links=REACH_LINKS,
        fees=REACH_FEES,
        qualifications='ADHD coach, BA BEd AACC',
        languages=[],
        experience=[
            'Consultant coach, REACH ADHD Coaching and Consultancy, Perth',
            'Over two decades across Australian and international school communities',
            'Secondary education: ATAR Economics and Business Management, Special Needs Support, Commerce and Sport',
            'Middle-management leadership, and roles in professional services, governance and community sport',
            'ADHD coach training at the ADHD Coaching Academy (ADDCA), New York',
            'Bachelor of Arts',
            'Bachelor of Education',
        ],
        about=[
            'With over two decades of experience across Australian and international school communities, Donna Italiano is an ADHD coach, consultant, and educator with a deep understanding of how learning, wellbeing, and performance intersect. Her background spans secondary education, ATAR Economics and Business Management, Special Needs Support, Commerce, and Sport, giving her a whole-person perspective on education that integrates neuroscience, emotional safety, and compassion.',
            'Throughout her career, Donna has taught and mentored thousands of students, led middle-management teams, supported both high-performing and neurodivergent learners, and contributed beyond the classroom through roles in professional services, governance, and community sport. These diverse experiences have shaped her belief that connection is foundational to learning, and that understanding how the brain works is key to unlocking confidence, regulation, and growth.',
            'As a consultant coach with REACH ADHD, Donna focuses on ADHD, executive functioning, emotional regulation, and neurodivergent-affirming practice. She is passionate about creating safe, inclusive spaces where students and families feel seen, understood, and supported. Donna works alongside young people to help them understand their unique brain wiring, build practical strategies, and move toward their goals with clarity, confidence, and self-belief.',
        ],
        details=reach_details(),
        disclosure=REACH_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Arts', 'Bachelor of Education',
                         'AACC ADHD Coach, ADHD Coaching Academy (ADDCA)'],
            same_as=[REACH + 'meet-the-coaches/', 'https://www.instagram.com/reach_adhd_coaching/'],
            works_for=REACH_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='kate-dallimore', id='kate-dallimore', category='coach',
        name='Kate Dallimore', short='Kate Dallimore', role='ADHD Consultant Coach', pronouns='',
        practice='REACH ADHD Coaching and Consultancy', place=REACH_PLACE,
        descriptor='ADHD consultant coach',
        description='ADHD coach with a background in physiotherapy and teaching, using a trauma-informed approach.',
        chips=['Trauma-informed', 'Executive functioning', 'Neurodiversity-affirming'],
        telehealth=True,
        book_href=REACH_BOOK, book_hint=REACH_BOOK_HINT,
        links=REACH_LINKS,
        fees=REACH_FEES,
        qualifications='ADHD coach, BSc(Physio Hons) PGDipPhysio MTeach AACC ACC',
        languages=[],
        experience=[
            'Consultant coach, REACH ADHD Coaching and Consultancy, Perth',
            'Over 30 years across healthcare, secondary and tertiary education, mentoring and leadership',
            'Supporting people through ongoing stress, anxiety, overwhelm and complex life experiences',
            'ADHD coach training at the ADHD Coaching Academy (ADDCA), New York',
            'Associate Certified Coach (ACC)',
            'Bachelor of Science (Physiotherapy) with Honours',
            'Postgraduate Diploma in Respiratory Physiotherapy',
            'Master of Teaching (Secondary)',
        ],
        about=[
            'I bring over 30 years of experience across healthcare, secondary and tertiary education, mentoring, leadership and community involvement to my work as an ADHD Consultant Coach. Across my career, I have been drawn to supporting people who have not always felt understood, helping them feel safe enough to recognise their strengths, trust themselves and take the next step. My work with students, families, clients and professionals has always centred on creating calm, supportive spaces where people feel heard, respected and able to build confidence and belief in themselves.',
            'As an ADHD Consultant Coach with REACH ADHD, I bring a warm, neurodiversity-affirming and trauma-informed approach to supporting individuals with ADHD and executive functioning challenges. My experience supporting people navigating ongoing stress, anxiety, overwhelm and complex life experiences has shaped the way I coach, with a strong focus on safety, trust, empathy and respect.',
            'I believe meaningful growth begins with connection and a genuine sense of belonging. My coaching is collaborative and strengths-based, helping clients better understand their unique brain wiring, recognise what is already working, develop practical strategies and move toward their goals with greater clarity, confidence and self-trust.',
        ],
        details=reach_details(),
        disclosure=REACH_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Science (Physiotherapy) with Honours',
                         'Postgraduate Diploma in Respiratory Physiotherapy', 'Master of Teaching (Secondary)',
                         'AACC ADHD Coach, ADHD Coaching Academy (ADDCA)', 'Associate Certified Coach (ACC)'],
            same_as=[REACH + 'meet-the-coaches/', 'https://www.instagram.com/reach_adhd_coaching/'],
            works_for=REACH_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='jessica-katsamatsas', id='jessica-katsamatsas', category='psychologist',
        name='Jessica Katsamatsas', short='Jess', role='Psychologist and Director',
        pronouns='',  # not declared anywhere on the practice's site
        practice='Neutral Minds Psychology', place='Brisbane & telehealth',
        descriptor='Psychologist & director',
        description='Psychologist working mainly with young neurodivergent adults on anxiety, burnout and self-esteem.',
        chips=['Neurodivergent adults', 'Neurodiversity-affirming', 'Trauma-informed'],
        telehealth=True,
        book_href=NMP_BOOK,
        book_hint='Opens Zanda in a new tab.',
        links=[
            ('instagram', '@neutralmindspsychology', 'https://www.instagram.com/neutralmindspsychology/'),
            ('website', 'neutralmindspsychology.com.au', NMP),
        ],
        fees=dict(
            heading='What a session costs',
            # The practice publishes the fee but not the rebate, so only the fee is a figure.
            figures=[('$220', 'Per session')],
            notes=[
                'Medicare rebates apply with a GP’s referral and Mental Health Care Plan. Ask the rebate and the gap '
                'when you book.',
                'Sessions run 50 minutes, for adults 18 and over, in person at Ashgrove or by telehealth anywhere in '
                'Australia.',
                'Self-managed and plan-managed NDIS participants pay the current NDIS fee schedule rate instead.',
                '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
            ],
        ),
        qualifications='Registered psychologist',
        languages=[],
        experience=[
            'Registered psychologist and director, Neutral Minds Psychology, Ashgrove',
            'Individual supportive psychological counselling for adults 18 and over',
            'Cognitive Behavioural Therapy (CBT), Acceptance and Commitment Therapy (ACT) and mindfulness',
            'Attachment-focused, trauma-informed and somatic-informed practice',
            'Anxiety, burnout, low self-esteem, relationship difficulties and attachment wounds',
            'Neurodiversity-affirming care for young neurodivergent adults',
            'Psychological integration support for experiences undertaken outside formal therapeutic settings',
            'NDIS participants who are self-managed and plan-managed',
        ],
        about=[
            'Hi, I’m Jess, a psychologist who believes therapy should feel like a space where you can take a breath, put the mask down, and be a little more human.',
            'I work primarily with young neurodivergent adults who may be navigating anxiety, burnout, low self-esteem, relationship difficulties, attachment wounds, or the lingering impact of past experiences. Many of the people I work with have spent a long time trying to understand why everyday life can feel harder than it seems to for everyone else. They may be used to overthinking, people-pleasing, masking, holding everything together, or feeling like they’re constantly trying to keep up.',
            'As someone passionate about neurodiversity-affirming care, I also understand that healing and growth don’t have to mean becoming “less neurodivergent” or learning to fit yourself into someone else’s idea of what life should look like. Sometimes, therapy is about understanding yourself more deeply, letting go of strategies that no longer serve you, and creating a life that actually works for you.',
            'My work draws on evidence-based approaches including CBT, ACT and mindfulness, alongside attachment-focused, trauma-informed and somatic-informed perspectives. I have a particular interest in the ways our early relationships and experiences can shape how we see ourselves, connect with others and cope with the world around us.',
            'My approach to therapy is warm, collaborative and down-to-earth. I’m not here to tell you how you should feel or hand you a list of strategies and send you on your way. Instead, we’ll work together to better understand your experiences, patterns, relationships and nervous system, while finding practical ways to make life feel more manageable.',
            'You don’t need to have the right words. You don’t need to know exactly what you want to work on. You just need a place to start. We can figure out the rest together.',
        ],
        details=[
            ('Reach', 'In-person appointments in Ashgrove, Brisbane, and telehealth Australia-wide'),
            ('Appointments', '50-minute sessions for adults 18 and over; booked online through the practice’s portal'),
            ('Billing', '$220 per session, Medicare rebate with a referral and Mental Health Care Plan; set and charged by the practice'),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Neutral Minds Psychology is an independent practice.',
        schema=dict(
            type='Person',
            credentials=['Registered psychologist'],
            same_as=[NMP + 'about', 'https://www.instagram.com/neutralmindspsychology/'],
            works_for=dict(url=NMP, telephone='0494 642 583', locality='Ashgrove', state='QLD'),
            area='Australia',
        ),
    ),
    dict(
        slug='bart-traynor', id='bart-traynor', category='psychologist',
        name='Bart Traynor', short='Bart', role='Clinical Psychologist and Director', pronouns='',  # not declared on the practice's site
        practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Clinical psychologist & director',
        description='Clinical psychologist and director who works with career and performance pressure and major life changes.',
        chips=['Performance & career', 'Life transitions', 'Clinical supervisor'],
        exercise=True,
        telehealth=False,
        book_href=ARC_BOOK + '/bart-traynor-1', book_hint=ARC_BOOK_HINT,
        links=ARC_LINKS,
        fees=ARC_FEES,
        qualifications='Clinical psychologist',
        languages=[],
        experience=[
            'Clinical psychologist, director and co-owner, Atlantis Recovery Centre, Bundall',
            'AHPRA board-approved clinical supervisor',
            'Complex challenges, career and performance pressures, and major life transitions',
            'Supervision and professional development for clinicians',
            'Member, Australian Association of Psychologists',
            'Member, Association of Applied Sports Psychology',
        ],
        about=[
            'Bart is a passionate, straight-talking Clinical Psychologist who believes mental health support should help people function better in everyday life—not just feel better in the therapy room. He works with clients facing complex challenges, career and performance pressures, and major life transitions, while also supporting clinicians through supervision and professional development.',
            'As Director of Atlantis Recovery Centre, Bart leads an integrated approach that brings together psychology, movement, physical rehabilitation, and performance. His warm, practical style helps people build resilience, improve both mental and physical fitness, and create meaningful, lasting change.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['Clinical psychologist', 'AHPRA board-approved clinical supervisor'], **ARC_SCHEMA),
    ),
    dict(
        slug='jeff-leech', id='jeff-leech', category='psychologist',
        name='Jeff Leech', short='Jeff', role='Clinical Psychologist', pronouns='',  # not declared on the practice's site
        practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Clinical psychologist',
        description='Clinical psychologist using schema therapy and ACT for trauma, anxiety, depression and performance.',
        chips=['Trauma', 'Anxiety & depression', 'Schema therapy & ACT'],
        exercise=True,
        telehealth=False,
        book_href=ARC_BOOK, book_hint=ARC_BOOK_HINT,
        links=ARC_LINKS,
        fees=ARC_FEES,
        qualifications='Clinical psychologist, MClinPsych BPsychSc(Hons)',
        languages=[],
        experience=[
            'Clinical psychologist, Atlantis Recovery Centre, Bundall',
            'Schema Therapy, Acceptance and Commitment Therapy (ACT) and Activity-Based Psychotherapy',
            'Trauma, anxiety, depression and performance',
            'Advanced training in Psychedelic-Assisted Therapy, in progress',
            'Master of Clinical Psychology, University of Queensland',
            'Bachelor of Psychological Science (Honours), Southern Cross University',
            'Background in outdoor education, military service, emergency services and adventure and endurance events',
        ],
        about=[
            'Jeff is passionate about helping people overcome life’s most complex challenges. Whether you’re recovering from trauma, managing anxiety or depression, or striving to perform at your best, Jeff provides personalised, evidence-based care using Schema Therapy, ACT, and Activity-Based Psychotherapy. He is also completing advanced training in Psychedelic-Assisted Therapy, combining proven approaches with emerging treatments to help clients achieve lasting change.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['Master of Clinical Psychology, University of Queensland', 'Bachelor of Psychological Science (Honours), Southern Cross University'], **ARC_SCHEMA),
    ),
    dict(
        slug='michael-rehardt', id='michael-rehardt', category='psychologist',
        name='Michael Rehardt', short='Michael', role='Provisional Psychologist', pronouns='',  # not declared on the practice's site
        practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Provisional psychologist',
        description='Provisional psychologist on the final placement of his Master of Clinical Psychology at Griffith University.',
        chips=['Final placement', 'Master of Clinical Psychology', 'Aboriginal artist'],
        exercise=True,
        telehealth=False,
        book_href=ARC_BOOK, book_hint=ARC_BOOK_HINT,
        links=ARC_LINKS,
        fees=ARC_FEES,
        qualifications='Provisional psychologist',
        languages=[],
        experience=[
            'Provisional psychologist on a final externship placement, Atlantis Recovery Centre, Bundall',
            'Master of Clinical Psychology, Griffith University, in progress',
            'Building clinical experience across a range of presentations',
            'Aboriginal artist and former competitive sprinter',
        ],
        about=[
            'Michael is completing his final externship placement at Atlantis Recovery Centre as part of his Master of Clinical Psychology at Griffith University. He brings a thoughtful, creative and practical approach to his work and is continuing to build his clinical experience across a range of presentations. Outside psychology, Michael is also an Aboriginal artist and former competitive sprinter, bringing creativity, discipline and a unique perspective to the Atlantis team.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['Provisional psychologist', 'Master of Clinical Psychology, Griffith University (in progress)'], **ARC_SCHEMA),
    ),
    dict(
        slug='sarah-savage', id='sarah-savage', category='exercise-physiology',
        name='Sarah Savage', short='Sarah', role='Senior Exercise Physiologist', pronouns='',  # not declared on the practice's site
        practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Senior exercise physiologist',
        description='Senior exercise physiologist using Pilates and hydrotherapy, with an interest in older adults.',
        chips=['Exercise as Medicine', 'Pilates & hydrotherapy', 'Older adults'],
        exercise=True,
        telehealth=False,
        book_href=ARC_BOOK + '/sarah-savage', book_hint=ARC_BOOK_HINT,
        links=ARC_LINKS,
        fees=ARC_FEES,
        qualifications='Exercise physiologist, BExSc GradDipExSc',
        languages=[],
        experience=[
            'Senior exercise physiologist, Atlantis Recovery Centre, Bundall',
            'Pilates, Functional Range Conditioning and hydrotherapy',
            'Particular interest in supporting older adults',
            'Bachelor and Graduate Diploma in Exercise Science, Griffith University',
        ],
        about=[
            '‘Exercise as Medicine’ … Sarah lives and breathes her mantra. Sarah is passionate about helping people move with confidence, build strength, and enjoy a better quality of life. She has a particular interest in supporting older adults and brings warmth, intelligence, and genuine care to every session.',
            'Sarah combines her Exercise Physiology expertise with Pilates, Functional Range Conditioning, and hydrotherapy to create safe, personalised programs that make exercise feel achievable, empowering, and enjoyable.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['Bachelor of Exercise Science, Griffith University', 'Graduate Diploma in Exercise Science, Griffith University'], **ARC_SCHEMA),
    ),
    dict(
        slug='yuri-lima', id='yuri-lima', category='allied',
        name='Dr Yuri Lima', short='Yuri', role='Physiotherapist', pronouns='',  # not declared on the practice's site
        practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Physiotherapist',
        description='Physiotherapist in orthopaedic and sports rehabilitation, with a PhD on ACL injuries in athletes.',
        chips=['Sports rehabilitation', 'Orthopaedic rehab', 'PhD, ACL injuries'],
        exercise=True,
        telehealth=False,
        book_href=ARC_BOOK, book_hint=ARC_BOOK_HINT,
        links=ARC_LINKS,
        fees=ARC_FEES,
        qualifications='Physiotherapist, PhD, Master in Rehabilitation Sciences',
        languages=['English', 'Portuguese'],
        experience=[
            'Physiotherapist, Atlantis Recovery Centre, Bundall',
            'Orthopaedic and sports rehabilitation',
            'PhD investigating ACL injuries in athletes',
            'Master in Rehabilitation Sciences',
        ],
        about=[
            'With a lifelong passion for movement and sports, Yuri’s approach combines clinical expertise in orthopaedic and sports rehabilitation and patient-centred care to help clients return to their optimal level of function and performance. He believes in empowering individuals through education and active involvement in their recovery process. He is also committed to advancing the field of physiotherapy by holding a Master in Rehabilitation Sciences and a PhD where he investigated ACL injuries in Athletes.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['PhD', 'Master in Rehabilitation Sciences'], **ARC_SCHEMA),
    ),
    dict(
        slug='tom-hissey', id='tom-hissey', category='allied',
        name='Tom Hissey', short='Tom', role='Senior Physiotherapist', pronouns='',  # not declared on the practice's site
        practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Senior physiotherapist',
        description='Musculoskeletal and occupational rehabilitation physiotherapist, and an Australian Army veteran.',
        chips=['Musculoskeletal physio', 'Return to function', 'Army veteran'],
        exercise=True,
        telehealth=False,
        book_href=ARC_BOOK, book_hint=ARC_BOOK_HINT,
        links=ARC_LINKS,
        fees=ARC_FEES,
        qualifications='Physiotherapist',
        languages=[],
        experience=[
            'Senior physiotherapist, Atlantis Recovery Centre, Bundall',
            'Occupational rehabilitation and musculoskeletal physiotherapy',
            'Overseas work supporting UK military personnel',
            'High-performance setting in Glasgow: runners, HYROX athletes and footballers',
            'Australian Army veteran',
        ],
        about=[
            'Tom is an incredibly welcoming Australian Army veteran with experience in both occupational rehabilitation and musculoskeletal physiotherapy, including overseas work supporting UK military personnel. He specialises in helping people return to full function, from young athletes to older clients, drawing on experience in a high-performance setting in Glasgow working with runners, HYROX athletes, and footballers.',
            'Having gone through back surgery and rehab himself, Tom understands what recovery really takes. He combines clinical expertise with genuine care, helping clients rebuild strength and confidence as part of Atlantis’s whole person approach to movement and wellbeing.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['Physiotherapist'], **ARC_SCHEMA),
    ),
    dict(
        slug='lester-rafanan', id='lester-rafanan', category='allied',
        name='Lester Rafanan', short='Lester', role='Physiotherapist', pronouns='',  # not declared on the practice's site
        practice='Atlantis Recovery Centre', place=ARC_PLACE, descriptor='Physiotherapist',
        description='Physiotherapist for recovery from injury or surgery, chronic pain, return to sport and NDIS supports.',
        chips=['Doctor of Physiotherapy', 'Strength & conditioning', 'NDIS supports'],
        exercise=True,
        telehealth=False,
        book_href=ARC_BOOK, book_hint=ARC_BOOK_HINT,
        links=ARC_LINKS,
        fees=ARC_FEES,
        qualifications='Physiotherapist, Doctor of Physiotherapy, Bond University',
        languages=[],
        experience=[
            'Physiotherapist, Atlantis Recovery Centre, Bundall',
            'Doctor of Physiotherapy, Bond University',
            'Background in personal training, strength and conditioning, and competitive sport',
            'Injury and surgery recovery, chronic pain, return to sport and NDIS supports',
        ],
        about=[
            'Lester Rafanan graduated with a Doctor of Physiotherapy from Bond University and has a background in personal training, strength and conditioning, and competitive sport, giving Lester a strong understanding of movement, performance, and injury prevention.',
            'He takes an evidence-based, personalised approach to physiotherapy, whether you’re recovering from an injury or surgery, managing chronic pain, returning to sport, accessing NDIS supports, or simply wanting to stay active. Every treatment plan is tailored to your goals so you can move with confidence.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['Doctor of Physiotherapy, Bond University'], **ARC_SCHEMA),
    ),
    dict(
        slug='alex-lawson', id='alex-lawson', category='coach',
        name='Alex Lawson', short='Alex', role='ADHD Coach and Mentor', pronouns='he/him',
        practice='Lawson ADHD Solutions', place='Sutherland Shire & online',
        descriptor='ADHD coach & mentor',
        description='ADHD coach, teacher and former lawyer with ADHD, working with adults, students and parents.',
        chips=['Adults, students & parents', 'Executive function', 'Lived experience'],
        telehealth=True,
        book_href=LAS + 'book-here',
        book_hint='Opens the practice’s website in a new tab.',
        links=[
            ('instagram', '@lawsonadhdsolutions', 'https://www.instagram.com/lawsonadhdsolutions/'),
            ('website', 'lawsonadhdsolutions.com.au', LAS),
        ],
        fees=dict(
            heading='What coaching costs',
            figures=[('$85', 'Per 55-minute session')],
            notes=[
                'The rate is the same in person or online. A post-session plan costs an extra $15.',
                'A free 20-minute discovery call comes first.',
                # His FAQ's structured data still carries an older $65 online rate; his pricing page and his booking
                # page both say $85, so $85 is what is shown. Worth a word to him either way.
                'Coaching has no Medicare rebate, and the practice lists no NDIS or private health arrangement.',
                '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
            ],
        ),
        qualifications='ADHD coach, MTeach(Sec) LLB',
        languages=[],
        experience=[
            'ADHD coach and mentor, Lawson ADHD Solutions, Sutherland',
            'Almost a decade of high school teaching and school leadership, as Head Teacher and Year Advisor',
            'Master of Teaching (Secondary) with Distinction, University of Wollongong',
            'Bachelor of Laws (LLB), and a previous career in law',
            'PESI ADHD Coaching Course',
            'Mentored by ADHD coach Mark Brandtman',
            'More than 50 families, adults and students supported through one-to-one coaching in six months',
            'Proficient High School Teacher Accreditation',
            'Listed in the ADHD Support Australia directory',
        ],
        about=[
            'I’m Alex. I’m an ADHD coach, high school teacher and former lawyer, and I know what it’s like to work in high-pressure environments and navigate the demands of a busy brain.',
            'I’ve been living with ADHD for over 30 years, and today I support adults, students, parents and families who are trying to make sense of ADHD in everyday life. Over that time, I’ve learned what it feels like to want to start something and just not be able to. To work hard, care deeply, and still feel like it doesn’t show the way it should.',
            'For the past decade, I’ve also had the privilege of supporting people with ADHD professionally. As a high school teacher, ADHD coach, educational leader, and through my previous career in law, I’ve helped students, parents, educators, and professionals better understand ADHD, navigate its challenges, and build practical strategies that are useful in real life.',
            'Long before I became an ADHD coach, I noticed something else happening around me. I was the person people came to when they didn’t understand ADHD. Students who felt like they were failing but weren’t. Parents who were exhausted and trying everything they could. Partners who didn’t know how to support someone they loved. Teachers and colleagues trying to make sense of behaviour that didn’t fit the system. And in every conversation, the goal was the same: to help people feel less blamed, less confused, and more understood.',
            'Today, I combine lived experience with years of professional practice to help people with ADHD make life more manageable, understand what is getting in the way, and find practical ways forward. That’s why Lawson ADHD Solutions exists.',
            'There’s no single planner, app, or system that works for every ADHD brain. My role is to understand how your ADHD shows up in your life specifically, then help you build strategies that actually fit. The goal is simple: you leave each session feeling understood, more confident, and knowing exactly what to do next.',
        ],
        details=[
            ('Reach', 'In-person sessions at Sutherland in the Sutherland Shire, and online by Zoom'),
            ('Appointments', '55-minute sessions, most often weekly or fortnightly to start, moving to monthly as things settle'),
            ('Billing', '$85 per session, the same in person or online; set and charged by the practice'),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Lawson ADHD Solutions is an independent practice. ADHD coaching is not a registered health profession. Coaches do not '
                   'assess, diagnose or provide therapy.',
        schema=dict(
            type='Person',
            credentials=['Master of Teaching (Secondary), University of Wollongong', 'Bachelor of Laws (LLB)',
                         'PESI ADHD Coaching Course', 'Proficient High School Teacher Accreditation'],
            same_as=[LAS + 'about-me', 'https://www.instagram.com/lawsonadhdsolutions/',
                     'https://www.linkedin.com/in/adhdcoachalex'],
            works_for=dict(type='ProfessionalService', url=LAS, telephone='', locality='Sutherland', state='NSW'),
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


TITLE_ROOM = 60 - len(' · ADHDme')   # search results cut titles at about 60 characters


def og_title(c):
    """Name, role and place when they fit in a search result's title, and name and role when they do not. The role is
    the sentence-case descriptor. A name and role that still run over stay whole: a search result then trims the
    brand suffix, which is better than cutting a word of the role."""
    role = c['descriptor'] or c['role']
    for t in (f"{c['name']}, {role}, {c['place']}", f"{c['name']}, {role}"):
        if len(t) <= TITLE_ROOM:
            return t
    return f"{c['name']}, {role}"


def meta_description(c):
    """The one-line summary, then who and where, for the search snippet (Google shows about 155 characters).

    The summary alone runs 60 to 110 characters, short enough that search engines replace it with text of
    their own choosing; the role, practice and place are what someone searching actually matches on.
    """
    role = (c['descriptor'] or c['role'])
    role = role[0].upper() + role[1:]
    place = c['place'][0].lower() + c['place'][1:] if c['place'].startswith('Telehealth') else c['place']
    with_role = [f" {role} at {c['practice']}, {place}.", f" {role} at {c['practice']}.", f" {role}, {place}."]
    without = [f" {c['practice']}, {place}.", f" {c['practice']}."]
    # A summary that already names the profession (coach, psychologist, GP) does not need it again.
    named = role.lower().split(' & ')[0].split()[-1] in c['description'].lower()
    for tail in (without + with_role) if named else (with_role + without):
        if len(c['description']) + len(tail) <= 158:
            return c['description'] + tail
    return c['description']


def others(c, n=3):
    """Three clinicians for 'Also in the network': the same practice first, then the same discipline, then roster order."""
    rest = [o for o in CLINICIANS if o is not c]
    ranked = sorted(rest, key=lambda o: (o['practice'] != c['practice'], o['category'] != c['category']))
    return ranked[:n]


# ---------------------------------------------------------------- fragments

PORTRAIT_BOX = 'aspect-square overflow-hidden rounded-2xl bg-[#f6f4ee] shadow-[inset_0_0_0_1px_#e8e6df]'
CHIP = '<span class="px-3.5 py-1.5 rounded-full text-sm font-semibold text-[#1a1c1c] bg-[#f6f4ee] border border-[#e8e6df]">{}</span>'
# One marker, same wording and same first position everywhere, so "can I be seen remotely?" is answered
# by scanning the deck rather than opening each profile. Warm tint sets it apart from the interest chips
# without competing with the yellow booking button.
TELEHEALTH_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-semibold '
                   'text-[#1e547a] bg-[#dcedfa] border border-[#b9d6ee]">'
                   '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                   'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                   '<rect x="2" y="6" width="13" height="12" rx="2.5"/><path d="M15 10.5 22 7v10l-7-3.5z"/></svg>'
                   'Telehealth</span>')


# The second fixed marker. Some practices treat movement as the treatment rather than an extra, and a
# reader scanning the deck cannot tell that from an interest chip. Same shape and position rule as the
# telehealth pill: one wording, one icon, always ahead of the interest chips. Set it from `exercise`.
EXERCISE_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-semibold '
                 'text-[#3c5c3a] bg-[#e4f0e1] border border-[#bcd8b6]">'
                 '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                 '<path d="M6.5 6.5v11M3.5 9v5M17.5 6.5v11M20.5 9v5M6.5 12h11"/></svg>'
                 'Exercise-based</span>')


def chip_row(c):
    """The clinician's interest chips, behind the markers they carry: telehealth, then exercise."""
    markers = (TELEHEALTH_PILL if c['telehealth'] else '') + (EXERCISE_PILL if c.get('exercise') else '')
    return markers + ''.join(CHIP.format(esc(x)) for x in c['chips'])
BOOK_HREF = 'the-doctors.html#{}'

# A diary you can pick a time in, or a form the practice answers. The button says which, and each
# list on The Network puts the diaries first: the easiest people to reach are the first ones you meet.
ONLINE_DIARIES = ('healthengine.com.au', 'halaxy.com/book', 'hotdoc.com.au')


def books_online(c):
    return any(host in c['book_href'] for host in ONLINE_DIARIES)


def book_verb(c):
    return 'Book' if books_online(c) else 'Enquire'

ARROW_BACK = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M11 18l-6-6 6-6"/></svg>'
ICONS = {
    'instagram': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>',
    'website': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
}
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
    sizes = '(min-width: 1280px) 264px, (min-width: 1024px) 22vw, (min-width: 768px) 30vw, 48vw'
    img_class = 'w-full h-full object-cover object-[center_30%] transition-transform duration-700 group-hover:scale-[1.02]'
    return f'''<li data-reveal id="{c['id']}" class="flex flex-col min-w-0">
  <a class="block group" href="{c['slug']}.html">
    {portrait_span(c, size, 'span', 'block ', sizes, img_attrs, img_class)}
    <span class="block pt-4"><strong class="block text-[22px] font-extrabold tracking-tight text-[#1a1c1c] leading-tight">{esc(c['name'])}</strong><span class="block mt-1 text-[15px] font-semibold text-[#5f5e59]">{esc(subline(c))}</span></span>
  </a>
  <div class="flex flex-wrap gap-2 pt-3">{chip_row(c)}</div>
  <div class="mt-auto pt-4"><a class="btn-press inline-flex items-center gap-2 h-11 px-6 rounded-full bg-[#1a1c1c] text-white text-[15px] font-bold hover:bg-[#2f3130] transition-colors" aria-label="{book_verb(c)} with {esc(c['name'])}" href="{c['slug']}.html">{book_verb(c)} <span class="text-[#f1bc31]" aria-hidden="true">→</span></a></div>
</li>'''


def also_link(c, size):
    return (f'<a class="flex items-center gap-4 group min-w-0" href="{c["slug"]}.html">'
            f'{portrait_span(c, size, "span", "block w-20 shrink-0 ", "96px", "loading=\"lazy\" decoding=\"async\"", "w-full h-full object-cover object-[center_30%]")}'
            f'<span class="min-w-0"><strong class="block text-[19px] leading-[1.25] font-extrabold tracking-tight text-[#1a1c1c]">{esc(c["name"])}</strong>'
            f'<span class="block text-[14px] font-semibold text-[#5f5e59]">{esc(subline(c))}</span></span></a>')


def jsonld(c):
    s = c['schema']
    page = f"{SITE}/{c['slug']}.html"
    image = f"{SITE}/{PORTRAITS}/{c['id']}.jpg"
    if s['type'] == 'Physician':
        d = {'@type': 'Physician', '@id': page + '#physician',
             'name': c['name'], 'url': page, 'jobTitle': c['qualifications'], 'medicalSpecialty': 'PrimaryCare',
             'knowsLanguage': c['languages'], 'image': image,
             'address': {'@type': 'PostalAddress', 'addressLocality': s['areas'][0], 'addressRegion': s['state'], 'addressCountry': 'AU'},
             'areaServed': [{'@type': 'Place', 'name': f"{a}, {s['state']}, Australia"} for a in s['areas']],
             'affiliation': {'@type': 'MedicalOrganization', 'name': c['practice']}}
    elif s['type'] == 'Person':
        w = s['works_for']
        d = {'@type': 'Person', '@id': page + '#person',
             'name': c['name'], 'url': page, 'jobTitle': c['qualifications'], 'image': image,
             'sameAs': s['same_as'],
             'hasCredential': [{'@type': 'EducationalOccupationalCredential', 'name': n} for n in s['credentials']],
             # Not every practice in the network is a health service: coaching is a ProfessionalService.
             'worksFor': {'@type': w.get('type', 'MedicalBusiness'), 'name': c['practice'], 'url': w['url'], 'telephone': w['telephone'],
                          'address': {'@type': 'PostalAddress', 'addressLocality': w['locality'], 'addressRegion': w['state'], 'addressCountry': 'AU'}},
             # A clinician who only sees people in one town gets a Place rather than the whole country.
             'areaServed': {'@type': s.get('area_type', 'Country'), 'name': s['area']}}
    else:
        raise BuildError(f"{c['name']}: unknown schema type {s['type']!r}")
    d['memberOf'] = {'@id': SITE + '/#org'}
    d['potentialAction'] = {'@type': 'ReserveAction', 'target': c['book_href']}
    # The page is a profile of one clinician, reached from The Network; the home page defines #site and #org.
    crumbs = {'@type': 'BreadcrumbList', '@id': page + '#breadcrumb', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'ADHDme', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'The Network', 'item': SITE + '/the-doctors.html'},
        {'@type': 'ListItem', 'position': 3, 'name': c['name'], 'item': page}]}
    profile = {'@type': 'ProfilePage', '@id': page, 'url': page, 'name': og_title(c), 'inLanguage': 'en-AU',
               'isPartOf': {'@id': SITE + '/#site'}, 'mainEntity': {'@id': d['@id']},
               'breadcrumb': {'@id': page + '#breadcrumb'}, 'primaryImageOfPage': {'@type': 'ImageObject', 'url': image}}
    return json.dumps({'@context': 'https://schema.org', '@graph': [d, profile, crumbs]}, ensure_ascii=False)


SECTION = ('<section class="lg:col-span-12 grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-16 pt-8 border-t border-[#e8e6df]" data-reveal>'
           '<h2 class="lg:col-span-4 text-2xl font-extrabold tracking-tight text-[#1a1c1c]">{}</h2>{}</section>')
DETAIL_ROW = ('<div class="grid grid-cols-1 sm:grid-cols-[10rem_1fr] gap-1 sm:gap-4 py-3 border-b border-[#e8e6df]">'
              '<dt class="text-[15px] font-semibold text-[#5f5e59]">{}</dt><dd class="m-0 text-[17px]">{}</dd></div>')
# About opens with the clinician's first sentence or two, at least READ_MIN words and never more than READ_MAX,
# and the rest of their words sit behind "Read more": a long block of text on first view is hard going with ADHD.
# For the same reason Experience shows its first EXPERIENCE_SHOWN items and folds the rest (a single leftover item
# is shown, not folded).
READ_MIN, READ_MAX = 12, 40
EXPERIENCE_SHOWN = 5
SENTENCE = re.compile(r'(?<=[.!?])\s+(?=[A-Z‘“"(])')
READ_MORE = ('<details class="group"><summary class="inline-flex items-center gap-3 cursor-pointer list-none '
             '[&::-webkit-details-marker]:hidden text-[15px] font-bold text-[#1a1c1c]">{}'
             '<span class="shrink-0 w-8 h-8 rounded-full border border-[#e8e6df] flex items-center justify-center '
             'transition-transform group-open:rotate-45" aria-hidden="true"><svg class="w-4 h-4" viewBox="0 0 24 24" '
             'fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/>'
             '</svg></span></summary>{}</details>')
# Details values that say nothing, so their rows are left out.
UNSAID = ('Not declared', 'Not applicable')


def words(text):
    return len(re.findall(r"[A-Za-z0-9$’'][\w$’'.,%-]*", text))


def about_html(c):
    first, *rest = SENTENCE.split(c['about'][0])
    lead = [first]
    while rest and words(' '.join(lead)) < READ_MIN and words(' '.join(lead + rest[:1])) <= READ_MAX:
        lead.append(rest.pop(0))
    more = ([' '.join(rest)] if rest else []) + list(c['about'][1:])
    para = lambda t: f'<p class="m-0">{esc(t)}</p>'
    return para(' '.join(lead)) + (READ_MORE.format('Read more', '<div class="mt-4 flex flex-col gap-4">'
                                                    + ''.join(para(t) for t in more) + '</div>') if more else '')


def experience_html(c):
    item = lambda x: f'<li class="py-2.5 border-b border-[#e8e6df]">{esc(x)}</li>'
    cut = EXPERIENCE_SHOWN if len(c['experience']) > EXPERIENCE_SHOWN + 1 else len(c['experience'])
    shown, rest = c['experience'][:cut], c['experience'][cut:]
    html_ = '<ul class="list-none p-0 m-0">' + ''.join(item(x) for x in shown) + '</ul>'
    if rest:
        html_ += '<div class="mt-4">' + READ_MORE.format(f'Show {len(rest)} more', '<ul class="list-none p-0 m-0">'
                                                         + ''.join(item(x) for x in rest) + '</ul>') + '</div>'
    return html_


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
    details += [(k, v) for k, v in c['details'] if k != 'Billing' and v not in UNSAID]   # the fee card covers billing
    # A clinic that publishes no fee gets the notes without the figure list, rather than an empty <dl>.
    figures = ''
    if fees['figures']:
        figures = ('\n    <dl class="grid grid-cols-2 gap-6 max-w-md m-0">\n'
                   + '\n'.join(f'      <div><dt class="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#1a1c1c] tabular-nums">{esc(amount)}</dt>'
                               f'<dd class="m-0 mt-1 text-[15px] font-semibold text-[#5f5e59]">{esc(label)}</dd></div>'
                               for amount, label in fees['figures'])
                   + '\n    </dl>')
    return f'''<main id="main" class="w-full bg-[#FAFAF7]">
<script type="application/ld+json">{jsonld(c)}</script>
<div class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pt-6"><a class="inline-flex items-center gap-2 h-11 text-[15px] font-bold text-[#1a1c1c]" href="{BOOK_HREF.format(c['id'])}">{ARROW_BACK}The network</a></div>
<article class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pt-6 pb-16">
<div class="rounded-3xl bg-white border border-[#e8e6df] p-6 sm:p-10 lg:p-14 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-start">
  <div class="lg:col-span-5 arrive" style="--i:0">{portrait_span(c, size, 'div', '', '(min-width: 1280px) 376px, (min-width: 1024px) 30vw, 80vw', 'fetchpriority="high" decoding="async"', 'w-full h-full object-cover object-[center_30%]')}</div>
  <div class="lg:col-span-7 flex flex-col gap-5">
    <h1 class="text-[36px] sm:text-[44px] lg:text-[52px] font-extrabold tracking-tight text-[#1a1c1c] leading-[1.02] arrive" style="--i:1">{esc(c['name'])}</h1>
    <p class="text-[15px] font-semibold text-[#5f5e59] arrive" style="--i:2">{esc(meta_line(c))}</p>
    <p class="text-[19px] sm:text-[22px] font-medium leading-snug text-[#1a1c1c] max-w-[40ch] arrive" style="--i:3" data-declared-by="clinician">{esc(c['description'])}</p>
    <div class="flex flex-wrap gap-2 arrive" style="--i:4">{chip_row(c)}</div>
    <div class="flex flex-col items-start gap-3 pt-2 arrive" style="--i:5">
      <a class="btn-press inline-flex items-center gap-2 h-12 px-7 rounded-full bg-[#f1bc31] text-[#1a1c1c] text-[15px] font-bold hover:bg-[#e2ac24] transition-colors" href="{c['book_href']}" target="_blank" rel="noopener noreferrer">{book_verb(c)} with {esc(c['short'])} <span aria-hidden="true">→</span></a>
      <span class="text-[13px] text-[#5f5e59]">{esc(c['book_hint'])}</span>{pills}
    </div>
  </div>
</div>
<div class="mt-12 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16">
  {SECTION.format('Experience', '<div class="lg:col-span-8 text-[17px]" data-declared-by="clinician">' + experience_html(c) + '</div>')}
  {SECTION.format('About', '<div class="lg:col-span-8 flex flex-col gap-4 text-[17px] leading-relaxed text-[#2b2820] max-w-[62ch]" data-declared-by="clinician">' + about_html(c) + '</div>')}
  {SECTION.format('Details', '<dl class="lg:col-span-8 m-0">' + ''.join(DETAIL_ROW.format(esc(k), v) for k, v in details) + '</dl>')}
</div>
<section class="rounded-3xl bg-white border border-[#e8e6df] p-6 sm:p-10 mt-12 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-16" data-reveal aria-labelledby="fees-title">
  <h2 id="fees-title" class="lg:col-span-4 text-2xl font-extrabold tracking-tight text-[#1a1c1c]">{esc(fees['heading'])}</h2>
  <div class="lg:col-span-8 flex flex-col gap-5">{figures}
{chr(10).join(f'    <p class="text-[17px] text-[#2b2820] max-w-[62ch]">{note}</p>' for note in fees['notes'])}
  </div>
</section>
<p class="mt-8 text-[15px] text-[#5f5e59] max-w-[72ch]">{esc(c['disclosure'])} This profile is written from {esc(c['short'])}’s own description of their work.</p>
</article>

<section class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pb-20" aria-labelledby="also-title">
<h2 id="also-title" class="text-2xl font-extrabold tracking-tight text-[#1a1c1c] mb-5">Also in the network</h2>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-8 items-start">
{chr(10).join(also_link(o, sizes[o['id']]) for o in others(c))}
</div>
<p class="mt-8"><a class="text-[15px] font-semibold text-[#1a1c1c] underline decoration-2 underline-offset-4 hover:text-[#5f5e59] transition-colors" href="the-doctors.html">See the whole network <span aria-hidden="true">→</span></a></p>
</section>
</main>'''


def render_page(c, shell, sizes):
    # rel=expect blocks the first render until the last named portrait on the page is parsed, so the
    # cross-document view transition captures a whole page rather than a half-parsed one.
    last = (others(c) or [c])[-1]
    tokens = {
        'NAME': c['name'], 'SLUG': c['slug'], 'ID': c['id'], 'SITE': SITE, 'EXPECT_ID': last['id'],
        'DESCRIPTION': meta_description(c), 'OG_TITLE': og_title(c), 'PORTRAIT_SIZE': str(sizes[c['id']]),
    }
    page = shell
    for k, v in tokens.items():
        page = page.replace('{{' + k + '}}', esc(v))
    page = page.replace('{{MAIN}}', render_main(c, sizes[c['id']], sizes))
    left = re.findall(r'\{\{[A-Z_]+\}\}', page)
    if left:
        raise BuildError(f'unfilled tokens in shell: {sorted(set(left))}')
    return page


def deck_jsonld():
    """An ItemList of every clinician on The Network, so search engines read the page as a directory."""
    items = [{'@type': 'ListItem', 'position': i, 'url': f"{SITE}/{c['slug']}.html", 'name': c['name']}
             for i, c in enumerate(CLINICIANS, 1)]
    url = f'{SITE}/the-doctors.html'
    graph = [
        {'@type': 'CollectionPage', '@id': url, 'url': url, 'name': 'ADHD clinicians in our network', 'inLanguage': 'en-AU',
         'isPartOf': {'@id': SITE + '/#site'}, 'mainEntity': {'@id': url + '#clinicians'}, 'breadcrumb': {'@id': url + '#breadcrumb'}},
        {'@type': 'ItemList', '@id': url + '#clinicians', 'name': 'ADHDme clinicians', 'url': url,
         'numberOfItems': len(items), 'itemListElement': items},
        {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'ADHDme', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'The Network', 'item': url}]},
    ]
    return '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False) + '</script>'


def render_deck(deck, sizes):
    """the-doctors.html with each category panel's <ul> refilled from CLINICIANS."""
    ordered = sorted(CLINICIANS, key=lambda c: not books_online(c))  # stable: CLINICIANS order holds within each half
    eager_id = next((c['id'] for c in ordered if c['category'] == DEFAULT_PANEL), None)
    for category, panel in PANELS.items():
        members = [c for c in ordered if c['category'] == category]
        pat = re.compile(r'(<div role="tabpanel" aria-labelledby="tab-btn-' + panel + '" id="panel-' + panel + r'"[^>]*><ul[^>]*>\n)(.*?)(</ul></div>)', re.S)
        found = pat.findall(deck)
        if not members:
            continue
        if len(found) != 1:
            raise BuildError(f'the-doctors.html: panel "{panel}" needs exactly one <div role="tabpanel" id="panel-{panel}"><ul>…</ul></div> to hold '
                             f'{", ".join(c["name"] for c in members)}; found {len(found)}. Replace the "Expected soon" placeholder with '
                             '<div role="tabpanel" aria-labelledby="tab-btn-' + panel + '" id="panel-' + panel + '" class="hidden"><ul class="grid auto-rows-fr grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-10 md:gap-x-8 md:gap-y-12 list-none p-0 m-0">\n</ul></div>')
        cards = '\n'.join(deck_card(c, sizes[c['id']], c['id'] == eager_id) for c in members) + '\n'
        deck = pat.sub(lambda m: m.group(1) + cards + m.group(3), deck, count=1)
    if '<!-- BEGIN:GENERATED deck-ld -->' not in deck:
        deck = deck.replace('</main>', '<!-- BEGIN:GENERATED deck-ld --><!-- END:GENERATED deck-ld -->\n</main>', 1)
    return region(deck, 'deck-ld', deck_jsonld(), 'the-doctors.html')


# ---------------------------------------------------------------- the landing page

# The landing page routes; it does not list, and since it was pared back to a headline and four words it
# states nothing from the data at all. Name a region here (and fill it in render_landing) if it ever does.
LANDING_REGIONS = []


def region(page, name, body, where):
    """Replace the contents of one <!-- BEGIN:GENERATED name --> … <!-- END:GENERATED name --> region."""
    start, end = f'<!-- BEGIN:GENERATED {name} -->', f'<!-- END:GENERATED {name} -->'
    i, j = page.find(start), page.find(end)
    if i < 0 or j < 0 or j < i:
        raise BuildError(f'{where}: no <!-- BEGIN:GENERATED {name} --> … <!-- END:GENERATED {name} --> region to fill')
    if page.find(start, i + 1) >= 0 or page.find(end, j + 1) >= 0:
        raise BuildError(f'{where}: the "{name}" region is marked more than once')
    return page[:i + len(start)] + body + page[j:]


def render_landing(page, sizes):
    """index.html, which currently carries no generated regions."""
    return page


# ---------------------------------------------------------------- checks

def check_data():
    problems = []
    ids = [c['id'] for c in CLINICIANS]
    slugs = [c['slug'] for c in CLINICIANS]
    if len(set(ids)) != len(ids) or len(set(slugs)) != len(slugs):
        problems.append('duplicate id or slug in CLINICIANS')
    required = ['slug', 'id', 'category', 'name', 'short', 'role', 'pronouns', 'practice', 'place', 'descriptor', 'description',
                'chips', 'telehealth', 'book_href', 'book_hint', 'links', 'fees', 'qualifications', 'languages', 'experience', 'about', 'details', 'disclosure', 'schema']
    for c in CLINICIANS:
        missing = [k for k in required if k not in c]
        if missing:
            problems.append(f"{c.get('name', c.get('slug'))}: missing fields {missing}")
        if c.get('category') not in PANELS:
            problems.append(f"{c['name']}: category must be one of {sorted(PANELS)}")
        for kind, _, _ in c.get('links', []):
            if kind not in ICONS:
                problems.append(f"{c['name']}: link kind {kind!r} has no icon; use one of {sorted(ICONS)}")
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    analytics = (ROOT / 'analytics.js').read_text(encoding='utf-8')
    css = (ROOT / 'site.css').read_text(encoding='utf-8')
    for c in CLINICIANS:
        if f"{SITE}/{c['slug']}.html" not in sitemap:
            problems.append(f"sitemap.xml has no entry for {c['slug']}.html")
        if f"profile: '{c['slug']}.html'" not in analytics:
            problems.append(f"analytics.js CLINICIANS does not declare {c['slug']}.html (profile views and booking clicks would be refused)")
        if f"::view-transition-group(portrait-{c['id']})" not in css:
            problems.append(f"site.css: add ::view-transition-group(portrait-{c['id']}) to the portrait transition rule")
    landing = LANDING.read_text(encoding='utf-8')
    for name in LANDING_REGIONS:
        if f'<!-- BEGIN:GENERATED {name} -->' not in landing or f'<!-- END:GENERATED {name} -->' not in landing:
            problems.append(f'index.html has no <!-- BEGIN:GENERATED {name} --> … <!-- END:GENERATED {name} --> region; '
                            'the landing page cannot be filled from the data without it')
    if problems:
        raise BuildError('\n  '.join(['fix these first:'] + problems))


def build():
    check_data()
    sizes = {c['id']: portrait_size(c) for c in CLINICIANS}
    shell = SHELL.read_text(encoding='utf-8')
    out = {ROOT / f"{c['slug']}.html": render_page(c, shell, sizes) for c in CLINICIANS}
    out[DECK] = render_deck(DECK.read_text(encoding='utf-8'), sizes)
    out[LANDING] = render_landing(LANDING.read_text(encoding='utf-8'), sizes)
    return out


def main(argv):
    check = '--check' in argv
    try:
        out = build()
    except BuildError as e:
        print(f'build-profiles: {e}', file=sys.stderr)
        return 2
    stale = [p for p, text in out.items() if not p.exists() or p.read_text(encoding='utf-8') != text]
    if check:
        for p in stale:
            print(f'out of date: {p.relative_to(ROOT)}')
        print('profiles are up to date' if not stale else f'{len(stale)} file(s) differ; run python3 scripts/build-profiles.py')
        return 1 if stale else 0
    for p, text in out.items():
        p.write_text(text, encoding='utf-8', newline='')
        print(('wrote  ' if p in stale else 'same   ') + str(p.relative_to(ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
