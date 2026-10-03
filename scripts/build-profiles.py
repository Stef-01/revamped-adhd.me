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
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHELL = ROOT / 'scripts' / 'profile-shell.html'
DECK = ROOT / 'the-doctors.html'
SITE = 'https://www.adhdme.au'
PORTRAITS = 'assets/clinicians'
SHARE_CARDS = 'assets/clinicians/og'

# The Network: which tab panel each category's cards go in. The first row of the default panel loads
# eagerly (its first card at high priority); every other card is lazy.
PANELS = {'gp': 'gps', 'psychologist': 'psychologists', 'psychiatrist': 'psychiatrists', 'allied': 'allied-health',
          'coach': 'coaches', 'occupational-therapy': 'occupational-therapy', 'physiotherapy': 'physiotherapy',
          'exercise-physiology': 'exercise-physiology'}
# Pinned to the front of their panel, ahead of everyone else, in an order site.js flips at random on each visit:
# the two Saxenas are the network's most affordable GPs. No other panel has pinned cards.
PINNED = {'anubhav-saxena', 'anu-saxena'}
DEFAULT_PANEL = 'gp'

# ---------------------------------------------------------------- data

GP_FEES = dict(
    heading='What a diagnosis costs',
    figures=[('$299', 'Initial consultation'), ('$199', 'Follow-up consultation')],
    notes=[  # html
        'The two consultations make up the ADHD assessment and diagnosis, $498 in total.',
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
# indexed each July; when they move, change them here. The profiles and the search pages read them from here.
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
    'A Mental Health Treatment Plan usually doesn’t cover OT. The NDIS, private health extras or a GP’s chronic condition '
    'management plan often do.')

# Therapy Co, Benowa on the Gold Coast. One practice, five psychologists and three therapy assistants, so the shared
# facts sit here once. From the practice's own site: no referral needed, Medicare with a Mental Health Treatment Plan,
# in person in Benowa and telehealth Australia-wide. It publishes no fee schedule ("fees vary by clinician and session
# length"), so the fee blocks carry no figures, as with GOALS.
TCO = 'https://thetherapyco.com.au/'
TCO_BOOK = 'https://www.halaxy.com/book/appointment/therapy-co/location/598571'
TCO_BOOK_HINT = 'Opens Halaxy in a new tab.'
TCO_ENQUIRE = TCO + 'contact/'
TCO_ENQUIRE_HINT = 'Opens the Therapy Co enquiry page in a new tab.'
TCO_PLACE = 'Benowa, Gold Coast & telehealth'
TCO_LINKS = [('website', 'thetherapyco.com.au', TCO)]
TCO_REACH = 'In person in Benowa on the Gold Coast, and telehealth Australia-wide'
TCO_REACH_TA = 'In person in Benowa, and at home, at school or in the community'
TCO_APPOINTMENTS = 'Usually 50-minute sessions; times set with the practice'
TCO_BILLING = 'Set and charged by the practice; quoted when you enquire or book'
TCO_DISCLOSURE = 'Therapy Co is an independent practice.'
TCO_WORKS_FOR = dict(url=TCO, telephone='0452 525 783', locality='Benowa', state='QLD')


def tco_fees(rebate_note):
    return dict(
        heading='What a session costs',
        figures=[],  # the practice has not published a fee
        notes=[
            'Therapy Co quotes its fee when you enquire or book. Fees vary by clinician and session length.',
            rebate_note,
            'No referral is needed. NDIS, private health and self-funded clients are welcome.',
            '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
        ],
    )


def _medicare(amount, who):
    return ('With a GP’s Mental Health Treatment Plan and referral, <a class="font-semibold text-[#1a1c1c] underline '
            'decoration-[#f1bc31] decoration-2 underline-offset-4" target="_blank" rel="noopener noreferrer" href="'
            + MBS_SOURCE + '">Medicare</a> pays ' + amount + ' a session with ' + who + ', for up to 10 sessions a year.')


TCO_FEES = tco_fees(_medicare(MBS_REBATE_REGISTERED, 'a psychologist'))
TCO_FEES_CLINICAL = tco_fees(_medicare(MBS_REBATE_CLINICAL, 'a clinical psychologist'))
TCO_FEES_TA = dict(
    heading='What a session costs',
    figures=[],
    notes=[
        'Therapy assistant sessions cost about a third of a psychology session. Therapy Co quotes the fee when you enquire.',
        'There is no Medicare rebate. NDIS plans often fund them as capacity building, for plan-managed and '
        'self-managed participants.',
        'A therapy assistant works under the supervision of your psychologist, who sets the goals.',
        '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
    ],
)

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


# Nurtured Thoughts Psychology, Graceville. One practice, sixteen clinicians across four categories, so the
# shared facts sit here once. Every profile's words come from the clinician's own page on the practice site,
# nurturedthoughtspsychology.com.au/practitioners/<name>, read 2026-10-01. The practice books through its
# contact page rather than an online calendar, so every booking button goes there.
NT = 'https://www.nurturedthoughtspsychology.com.au/'
NT_BOOK = NT + 'contact'
NT_BOOK_HINT = 'Opens Nurtured Thoughts Psychology’s booking enquiry page, in a new tab.'
NT_PLACE = 'Brisbane & telehealth'
NT_LINKS = [
    ('instagram', '@nurturedthoughtspsychology', 'https://www.instagram.com/nurturedthoughtspsychology/'),
    ('website', 'nurturedthoughtspsychology.com.au', NT),
]
NT_REACH = 'Clinic appointments in Graceville, Brisbane, and telehealth'
NT_APPOINTMENTS = 'Clinicians see people Monday to Saturday, with evenings Monday to Wednesday; times set with the practice'
# The practice's own wording: a heritage-listed building with no wheelchair access to the building or bathrooms.
NT_ACCESS = 'No: the practice is in a heritage-listed building without wheelchair access to the building or bathrooms'
NT_DISCLOSURE = ('Nurtured Thoughts Psychology is an independent practice: it sets its own fees, availability and '
                 'clinical approach, and ADHDme receives no part of what you pay.')
NT_WORKS_FOR = dict(url=NT, telephone='(07) 3056 0921', locality='Graceville', state='QLD')
NT_SAME_AS = [NT + 'practitioners', 'https://www.instagram.com/nurturedthoughtspsychology/']
NT_SCHEMA_DR = dict(type='Physician', areas=['Graceville'], state='QLD', works_for=NT_WORKS_FOR)
NT_RESPONSIBLE = '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>'

# Fees as the practice publishes them at nurturedthoughtspsychology.com.au/fees and /adhd-fees (2026-10-01).
NT_FEES_GP = dict(
    heading='What a diagnosis costs',
    figures=[('$1,950', 'Adult ADHD assessment, diagnosis and treatment'), ('~$200', 'Typical Medicare rebate')],
    notes=[
        'One fee for ages 15 and over: assessment, diagnosis, treatment if appropriate, and a report for you and your GP. '
        'The practice confirms your rebate before you book.',
        NT_RESPONSIBLE,
    ],
)
NT_FEES_PSYCHIATRY = dict(
    heading='What a consultation costs',
    figures=[('$900', 'Initial psychiatry consultation'), ('$395–$445', 'Review consultation')],
    notes=[
        'Medicare pays $265 of the first consultation and $85–$135 of a review. The practice confirms the fee when you book.',
        NT_RESPONSIBLE,
    ],
)


def nt_therapy_fees(fee, rebate, gap):
    return dict(
        heading='What a session costs',
        figures=[(fee, 'Per session'), (gap, 'Out of pocket with a plan')],
        notes=[
            f'With a Mental Health Treatment Plan from your GP, Medicare pays {rebate} of each session, for up to 10 '
            'sessions a year.',
            NT_RESPONSIBLE,
        ],
    )


NT_FEES_PSYCHOLOGIST = nt_therapy_fees('$240', '$98.95', '$141.05')
NT_FEES_SOCIAL_WORKER = nt_therapy_fees('$230', '$87.25', '$142.75')
# The fee page lists registered psychologists and social workers only; it carries no clinical psychologist rate,
# so this block shows no figure rather than borrowing the registered rate.
NT_FEES_CLINICAL = dict(
    heading='What a session costs',
    figures=[],
    notes=[
        'The practice quotes this fee when you book. With a Mental Health Treatment Plan, Medicare pays part of it for up '
        'to 10 sessions a year.',
        NT_RESPONSIBLE,
    ],
)

CLINICIANS = [
    dict(
        slug='dr-anubhav-saxena', id='anubhav-saxena', category='gp',
        ages=['adults'],
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
        pathway=[
            ('First consultation', 'A long first appointment, in person or by phone. $299.'),
            ('Follow-up consultation', 'Completes the assessment and diagnosis. $199.'),
            ('After the diagnosis', 'Medication if it’s right for you, then reviews at set intervals. Some people need an extra 30-minute review; the practice explains why and the cost first.'),
        ],
        works_with=[
            'For the thinking and feeling side, a psychologist in the network. With a Mental Health Treatment Plan from a GP, Medicare pays part of up to 10 sessions a year.',
            'For daily life, occupational therapists and coaches turn the plan into routines.',
            'Where the picture is more complex, such as another serious mental illness or a history that makes stimulants risky, a psychiatrist is the right choice. That needs a GP referral. You’ll find psychiatrists in the network too.',
            'Ask at your appointment how your GP shares information with your other clinicians.',
        ],
        about=[
            'Anubhav trained at the University of Sydney and works in Double Bay and Beecroft. He works from measurement rather than impression, and takes an integrative view: ADHD is looked at alongside sleep, cardiovascular and metabolic health rather than on its own, with a documented baseline before anything starts and review at set intervals rather than only when a problem gets loud enough to prompt a call. He also does aged-care and home visits, and gives a good deal of his spare time to the long-suffering cause of the Parramatta Eels.',
        ],
        details=[  # html values; Qualifications and Languages rows are added by the script
            ('Reach', 'Practice appointments and phone consultations'),
            ('Billing', GP_BILLING),
            ('Wheelchair access', 'Yes'),
        ],
        disclosure='Dr Saxena owns Beecroft Family & Skin Cancer Clinic. The clinic is ADHDme’s first clinic partner and has a commercial relationship with ADHDme.',
        schema=dict(type='Physician', areas=['Beecroft', 'Double Bay'], state='NSW'),
    ),
    dict(
        slug='dr-anu-saxena', id='anu-saxena', category='gp',
        ages=['children', 'adults'],
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
        pathway=[
            ('First consultation', 'In person or by telehealth, for children and adults. $299.'),
            ('Follow-up consultation', 'Completes the assessment and diagnosis. $199.'),
            ('After the diagnosis', 'Medication if it’s right for you. Some people need an extra 30-minute review; the practice explains why and the cost first. Ask how ongoing reviews are arranged.'),
        ],
        works_with=[
            'For the thinking and feeling side, a psychologist in the network. With a Mental Health Treatment Plan from a GP, Medicare pays part of up to 10 sessions a year.',
            'For daily life, occupational therapists and coaches turn the plan into routines.',
            'Where the picture is more complex, such as another serious mental illness or a history that makes stimulants risky, a psychiatrist is the right choice. That needs a GP referral. You’ll find psychiatrists in the network too.',
            'Ask at your appointment how your GP shares information with your other clinicians.',
        ],
        about=[
            'Anu is an experienced GP at Bay Health Clinic in Double Bay, and a Fellow of the Royal Australian College of General Practitioners. She came to medicine through psychology, a Bachelor of Psychology with First Class Honours at the University of Sydney, then her MD at the Australian National University, with a background in psychiatry and general medicine: hospital training across NSW, including Blacktown and Bathurst, rotations in cardiology, paediatrics and psychiatry, and the Sydney Child Health Program through the Sydney Children\'s Hospital Network; she holds a Diploma of Child Health. Her clinical interests are ADHD, mental health, women\'s health and functional medicine. She has completed an endorsed ADHD prescriber course, is training in Focused Psychological Strategies, and is completing further qualifications in functional medicine, nutrition, lifestyle medicine and health coaching. Of Indian origin and speaking Hindi and Urdu, she values culturally sensitive, holistic and patient-centred care. Outside medicine she enjoys travelling, learning about different cultures, charity and community work, and staying active through sport, cricket and tennis included.',
        ],
        details=[
            ('Reach', 'Practice appointments in Double Bay and Hornsby, and telehealth'),
            ('Billing', GP_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Dr Anu Saxena has a declared interest in ADHDme, the company that runs this listing.',
        schema=dict(type='Physician', areas=['Double Bay', 'Hornsby'], state='NSW'),
    ),
    # Continuation prescriber: keeps ADHD medication going for people already diagnosed. He will assess in future,
    # not yet, so `assesses=False` keeps him off the assessment search pages until that changes.
    dict(
        slug='dr-yogesh-kalra', id='yogesh-kalra', category='gp', assesses=False, bulk_billed=True,
        ages=['adults'],
        name='Dr Yogesh Kalra', short='Dr Yogesh Kalra', role='GP', pronouns='he/him',
        practice='Dr Yogesh Kalra’s Surgery', place='Bateau Bay, Central Coast', descriptor='Continuation prescriber',
        description='Continues ADHD medication for people already diagnosed. Not offering ADHD assessment or diagnosis yet.',
        chips=['Continues ADHD medication', 'Hindi'],
        telehealth=False,
        book_href='https://healthengine.com.au/doctor/nsw/bateau-bay/dr-yogesh-kalra/p57872', book_hint=HEALTHENGINE_HINT,
        links=[],
        fees=dict(
            heading='What it costs',
            figures=[('$0', 'Bulk billed')],
            notes=[
                'The practice bulk bills all eligible Medicare services for Medicare card holders.',
                'Department of Veterans’ Affairs card holders are welcome.',
                '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
            ],
        ),
        qualifications='General practitioner, FRACGP',
        languages=['English', 'Hindi'],
        experience=[
            'General practice, Dr Yogesh Kalra’s Surgery, Bateau Bay',
            'Fellow of the Royal Australian College of General Practitioners',
            'Diploma in Skin Cancer Surgery',
            'Professional Diploma of Dermoscopy',
        ],
        pathway=[
            ('Already diagnosed', 'For people who already have an ADHD diagnosis and a treatment plan.'),
            ('Book an appointment', 'In person at Bateau Bay, bulk billed.'),
            ('Ongoing prescriptions', 'He keeps your medication going close to home. Ask the practice what to bring.'),
        ],
        works_with=[
            'For the thinking and feeling side, a psychologist in the network. With a Mental Health Treatment Plan from a GP, Medicare pays part of up to 10 sessions a year.',
            'For daily life, occupational therapists and coaches turn the plan into routines.',
            'Where the picture is more complex, such as another serious mental illness or a history that makes stimulants risky, a psychiatrist is the right choice. That needs a GP referral. You’ll find psychiatrists in the network too.',
            'Ask at your appointment how your GP shares information with your other clinicians.',
        ],
        about=[
            'Yogesh is a GP and a Fellow of the Royal Australian College of General Practitioners, practising at his own surgery in Bateau Bay on the Central Coast. For ADHD, he is a continuation prescriber: he keeps your ADHD medication going once you have been diagnosed and have a treatment plan, so you can manage it close to home. He is not offering ADHD assessment or diagnosis yet; that is planned for the future. His other interests are family medicine, women’s health, and skin cancer checks and surgery, with diplomas in skin cancer surgery and dermoscopy. He speaks English and Hindi, and the practice bulk bills all eligible Medicare services.',
        ],
        details=[
            ('Reach', 'Practice appointments in Bateau Bay'),
            ('Appointments', 'Appointment lengths set with the practice'),
            ('Billing', 'Bulk billed for eligible Medicare services; set and charged by the practice'),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='Dr Yogesh Kalra’s Surgery is an independent practice.',
        schema=dict(type='Physician', areas=['Bateau Bay'], state='NSW'),
    ),
    # Dr Allen Macbell, The Local Doctor, Ivanhoe in Melbourne. From thelocaldoctor.com.au/doctors/allen-macbell/ and
    # /services/adhd/ (2026-10-02), with his permission. ADHD appointments are at the Ivanhoe clinic only.
    dict(
        slug='dr-allen-macbell', id='allen-macbell', category='gp',
        ages=['children', 'teens', 'adults'],
        name='Dr Allen Macbell', short='Dr Macbell', role='GP', pronouns='he/him',
        practice='The Local Doctor', place='Ivanhoe, Melbourne', descriptor=None,
        description='ADHD assessment, diagnosis and ongoing care for children aged 10 and over, teens and adults, with the same doctor throughout.',
        chips=['Children 10 and over', 'Autism and ADHD together', 'No referral needed'],
        telehealth=False,
        book_href='https://automedsystems.com.au/ams/clinics/198/the-local-doctor-ivanhoe-3079/doctors', book_hint='Opens AutoMed Systems in a new tab.',
        links=[('website', 'thelocaldoctor.com.au', 'https://thelocaldoctor.com.au/services/adhd/')],
        fees=dict(
            heading='What a diagnosis costs',
            figures=[('$128', 'Initial consultation'), ('$248', 'Comprehensive assessment'), ('$248', 'Diagnostic consultation')],
            notes=[
                'Three appointments, $624 out of pocket in total.',
                'Medicare rebates apply where eligible. An extra review is occasionally needed.',
                '<strong>Fees are set and charged by the practice. ADHDme takes no commission.</strong>',
            ],
        ),
        qualifications='General practitioner, FRACGP',
        languages=[],
        experience=[
            'More than 15 years of ADHD assessment and care',
            'RACGP Victorian GP ADHD Training and Support Program',
            'Member, Australasian ADHD Professionals Association (AADPA)',
            'Teacher, tutor and mentor, University of Melbourne and Monash University',
            'Fellow of the Royal Australian College of General Practitioners',
            'Earlier work in emergency departments and aged care',
        ],
        pathway=[
            ('Initial consultation', '20 minutes to see if a full assessment is right for you. $128.'),
            ('Comprehensive assessment', '40 minutes on your history. $248.'),
            ('Diagnostic consultation', '40 minutes on the findings and your plan. $248.'),
            ('After the diagnosis', 'Medication if it’s right for you, reviewed every 4 to 6 weeks at first.'),
        ],
        works_with=[
            'Allen works with psychologists, psychiatrists, schools and allied health professionals when it helps.',
            'Where specialist input is needed, he may recommend a referral to a paediatrician or psychiatrist.',
            'Already diagnosed by a paediatrician or psychiatrist? He can review that assessment and, where appropriate, continue your care without a new one.',
            'You can keep your regular GP for everything else.',
        ],
        about=[
            'Allen is a GP at The Local Doctor in Ivanhoe, in Melbourne’s north-east, with more than 15 years in ADHD care. He has assessed and managed ADHD in many hundreds of children, teenagers and adults, including people with both autism and ADHD. He sees children aged 10 and over, teens and adults, and does every assessment himself, so you stay with one doctor from the first consultation through diagnosis, treatment and follow-up. His approach is practical and individual, looking at how ADHD affects study, work, relationships and everyday life. He was selected for the RACGP Victorian GP ADHD Training and Support Program, and teaches and mentors medical students and graduates. His other interest is skin cancer medicine.',
        ],
        details=[
            ('Reach', 'Practice appointments in Ivanhoe, Melbourne'),
            ('Appointments', '20 minutes, then two of 40 minutes'),
            ('Billing', '$624 out of pocket across three appointments; set and charged by the practice'),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure='The Local Doctor is an independent practice.',
        schema=dict(type='Physician', areas=['Ivanhoe'], state='VIC'),
    ),
    dict(
        slug='paula-garrido', id='paula-garrido', category='psychologist',
        ages=['adults'],
        name='Paula Garrido', short='Paula Garrido', role='Clinical Psychologist', pronouns='she/her',
        practice='Wellness Psychology Clinic', place='Telehealth Australia-wide', descriptor='Clinical psychologist',
        description='Clinical psychologist certified in ADHD and autism care, seeing clients by video anywhere in Australia.',
        chips=['Neuroaffirming', 'Trauma-informed', 'ADHD & autism certified'],
        telehealth=True,
        in_person=False,   # the clinic is online only
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
        ages=['children', 'teens', 'adults'],
        name='Kate Row', short='Kate Row', role='Psychologist and Clinic Director', pronouns='she/her',
        practice='GOALS Psychology', place=GOALS_PLACE, descriptor='Psychologist & clinic director',
        description='Works with toddlers through to adults using CBT, ACT and MI, and supports families with the NDIS.',
        chips=['Toddlers to adults', 'NDIS participants', 'CBT, ACT & MI'],
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
        ages=['teens', 'adults'],
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
        ages=['children', 'teens', 'adults'],
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
        ages=['adults'],
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
        ages=['children'],
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
        ages=['teens', 'adults'],
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
        ages=['children', 'teens'],
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
            'Meera’s current focus is on neurodivergence assessments: autism assessment, ADHD assessment and cognitive assessment. She utilises assessment tools including WISC, WAIS, WIAT, MIGDAS and others as required to support clients with discovering an enhanced understanding of their unique neurotype. Meera is especially passionate about working with young adults and their families, in a way that aligns with their values and beliefs, to be the best version of themselves. She thrives on supporting clients to lean into vulnerability, learn new skills and navigate life’s challenges.',
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
        ages=['teens', 'adults'],
        name='Trisha Harris', short='Trisha', role='Clinical Counsellor', pronouns='she/her',
        practice='Riverview Counselling', place='Glenbrook & telehealth',
        descriptor='Clinical counsellor',
        description='A counsellor with ADHD herself, seeing teens, adults, couples and NDIS participants in Glenbrook.',
        chips=['Teens, adults & couples', 'NDIS participants'], lived='Has ADHD',
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
        slug='flynn-simonis', id='flynn-simonis', category='occupational-therapy',
        ages=['children', 'teens'],
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
        ages=['children', 'teens', 'adults'],
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
        ages=['children', 'teens', 'adults'],
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
        ages=['children', 'teens'],
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
        ages=['children', 'teens'],
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
        ages=['children', 'teens', 'adults'],
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
        ages=['children', 'teens'],
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
        ages=['teens', 'adults'],
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
        ages=['adults'],
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
    # Therapy Co, Benowa: five psychologists, then three therapy assistants (Allied health).
    dict(
        slug='chantelle-pin', id='chantelle-pin', category='psychologist', lived='Has ADHD',
        ages=['children', 'teens', 'adults'],
        name='Chantelle Pin', short='Chantelle', role='Clinical Psychologist, Founder and Director', pronouns='',
        practice='Therapy Co', place=TCO_PLACE, descriptor='Clinical psychologist & founder',
        description='A clinical psychologist, late-diagnosed with ADHD herself, working with neurodivergent children and adults. Taking on assessments.',
        chips=['Assessments', 'Neurodivergent clients', 'Children to adults'],
        telehealth=True,
        book_href=TCO_BOOK, book_hint=TCO_BOOK_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES_CLINICAL,
        qualifications='Clinical psychologist, MClinPsych PGPsychSci BPsychSci BCrim&CrimJust MAPS',
        languages=[],
        experience=['Clinical psychologist, founder and director, Therapy Co, Benowa', 'Board Approved Supervisor', 'Clinical Registrar Program, completed 2022', 'Master of Clinical Psychology, Griffith University', 'Graduate Diploma of Psychological Science, Bond University', 'Bachelor of Psychological Science, Griffith University', 'Bachelor of Criminology and Criminal Justice, Griffith University'],
        quote='I aim to provide a safe, comfortable space for yourself or your child to tackle the obstacles life throws.',
        about=['I work across the lifespan with neurodiverse clients. I am a late-diagnosed neurodivergent (ADHD) adult, so I bring lived experience together with my training to support my clients.', 'When I am not at Therapy Co, I spend my time with family, my two dachshunds, friends, jigsaw puzzles, Harry Potter and travelling.'],
        details=[
            ('Currently', 'Accepting assessments'),
            ('Reach', TCO_REACH),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Master of Clinical Psychology', 'Graduate Diploma of Psychological Science', 'Bachelor of Psychological Science', 'Bachelor of Criminology and Criminal Justice', 'Board Approved Supervisor'],
            same_as=[TCO + 'team/chantelle-pin/'],
            works_for=TCO_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='sarah-bibo', id='sarah-bibo', category='psychologist',
        ages=['adults'],
        name='Sarah Bibo', short='Sarah', role='Registered Psychologist and Clinical Psychology Registrar', pronouns='',
        practice='Therapy Co', place=TCO_PLACE, descriptor='Psychologist, on maternity leave',
        description='On maternity leave for now. Works with anxiety, low mood, trauma, ADHD, autism, eating and body image.',
        chips=['Neurodivergent clients', 'Eating & body image'],
        telehealth=True,
        book_href=TCO_ENQUIRE, book_hint=TCO_ENQUIRE_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES,
        qualifications='Psychologist, MClinPsych BPsych(Hons)',
        languages=[],
        experience=['Registered psychologist, Therapy Co, Benowa', 'Clinical Registrar Program, in progress', 'Master of Clinical Psychology, 2025', 'Bachelor of Psychology (Honours), research on neural pathways in children with ADHD', 'CBT, DBT, ACT, Compassion-Focused Therapy and Positive Psychology'],
        quote='I am passionate about the transformative potential of psychotherapy in supporting personal growth and healing.',
        about=['I am dedicated to creating a safe, supportive and non-judgmental environment where clients feel empowered to navigate life’s challenges and work towards their goals.', 'I have worked with depression, anxiety, trauma, neurodiversity (autism and ADHD), interpersonal difficulties, disordered eating and body image concerns. My approach is warm, compassionate, person-centred and strengths-based, drawing on CBT, DBT, ACT, Compassion-Focused Therapy and Positive Psychology.', 'Outside work I enjoy gardening, hiking, swimming, travelling, the gym, and time with family and friends.'],
        details=[
            ('Currently', 'On maternity leave; ask the practice when she returns'),
            ('Reach', TCO_REACH),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Master of Clinical Psychology', 'Bachelor of Psychology (Honours)'],
            same_as=[TCO + 'team/sarah-bibo/'],
            works_for=TCO_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='gisele-fortkamp', id='gisele-fortkamp', category='psychologist',
        ages=['children', 'adults'],
        name='Gisele Fortkamp', short='Gisele', role='Senior Psychologist', pronouns='',
        practice='Therapy Co', place=TCO_PLACE, descriptor='Senior psychologist',
        description='Supports children with ADHD or autism and their parents, and women adjusting to a diagnosis. Sessions in English or Portuguese.',
        chips=['Children & parents', 'Women’s wellbeing', 'Portuguese'],
        telehealth=True,
        book_href=TCO_BOOK, book_hint=TCO_BOOK_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES,
        qualifications='Psychologist, BSc(Hons) MAPS',
        languages=['English', 'Portuguese'],
        experience=['Senior psychologist, Therapy Co, Benowa', 'Level 1 Couples Counselling, Gottman Institute, 2026', '5+1 Internship Program, completed 2024', 'Postgraduate Certificate in Psychodrama Psychology, Florianópolis, Brazil', 'Bachelor of Psychology with Honours thesis on learning difficulties in children, Brazil'],
        quote='I am a psychologist committed to supporting children’s development and helping women move toward greater confidence, clarity and more fulfilling relationships.',
        about=['I trained in Brazil and am fully registered in Australia. I provide a warm, supportive space grounded in evidence-based practice, with clear, practical guidance.', 'I work with parents and children on emotional regulation, behaviour, communication and self-esteem, with a special interest in ADHD and autism, using a strengths-based, neurodivergence-affirming approach.', 'I also support women with self-esteem, identity, life transitions, relationships, anxiety and low mood, including women exploring or adjusting to an ADHD or autism diagnosis. I offer sessions in Portuguese and English.'],
        details=[
            ('Currently', 'Taking new clients'),
            ('Reach', TCO_REACH),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychology (Honours)', 'Postgraduate Certificate in Psychodrama Psychology', 'Level 1 Couples Counselling (Gottman Institute)'],
            same_as=[TCO + 'team/gisele-fortkamp/'],
            works_for=TCO_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='lana-hiscock', id='lana-hiscock', category='psychologist',
        ages=['adults'],
        name='Lana Hiscock', short='Lana', role='Psychologist', pronouns='',
        practice='Therapy Co', place=TCO_PLACE, descriptor='Psychologist',
        description='Neurodiversity, relationships, sleep, perinatal mental health and women’s health. Sessions in English or Mandarin.',
        chips=['Perinatal & postnatal', 'Sleep', 'Mandarin & Shanghainese'],
        telehealth=True,
        book_href=TCO_BOOK, book_hint=TCO_BOOK_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES,
        qualifications='Psychologist, MClinPsych BPsych(Hons)',
        languages=['English', 'Mandarin', 'Shanghainese'],
        experience=['Psychologist, Therapy Co, Benowa', 'Master of Clinical Psychology, Bond University, 2026', 'Graduate Diploma of Psychology (Honours), 2023', 'CBT, DBT, ACT and positive psychology'],
        quote='If you’re navigating neurodiversity, relationships, sleep, perinatal and postnatal mental health or women’s health, I offer a supportive and culturally compassionate space shaped by my own diverse background.',
        about=['I integrate lived experience with professional training to support clients in a grounded, holistic way, in a safe and collaborative space where people feel genuinely understood.', 'My approach is warm, compassionate and non-judgmental, drawing on person-centred, strengths-based and evidence-based approaches including CBT, DBT, ACT and positive psychology.', 'In my downtime I get outdoors with a coffee and a good book, travel, do pilates or yoga, and make friends with the local king parrots.'],
        details=[
            ('Currently', 'Taking new clients'),
            ('Reach', TCO_REACH),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Master of Clinical Psychology', 'Graduate Diploma of Psychology (Honours)'],
            same_as=[TCO + 'team/lana-hiscock/'],
            works_for=TCO_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='valeria-urrutia', id='valeria-urrutia', category='psychologist',
        ages=['children', 'teens', 'adults'],
        name='Valeria Urrutia', short='Valeria', role='Registered Psychologist', pronouns='',
        practice='Therapy Co', place=TCO_PLACE, descriptor='Psychologist',
        description='Anxiety, low mood, grief, life changes, neurodiversity and psychological assessments. Sessions in English or Spanish.',
        chips=['Assessments', 'Grief & life changes', 'Spanish'],
        telehealth=True,
        book_href=TCO_BOOK, book_hint=TCO_BOOK_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES,
        qualifications='Psychologist, MClinPsyc BPsychSci(Hons) BA',
        languages=['English', 'Spanish'],
        experience=['Registered psychologist, Therapy Co, Benowa', 'Master of Psychology (Clinical), Bond University, 2026', 'Bachelor of Psychological Science (Honours), Bond University', 'Bachelor of Arts in psychology and music psychology, University of Queensland', 'Inpatient, outpatient and therapeutic community settings'],
        quote='I enjoy taking a curious, collaborative and flexible approach to therapy, and I believe the therapeutic relationship is an important part of creating meaningful change.',
        about=['I aim to create a space where people feel respected, understood and comfortable being themselves. I tailor therapy to each person, drawing on CBT, ACT, DBT and Compassion-Focused Therapy.', 'I work across the lifespan with life transitions, anxiety and depression, grief and loss, neurodiversity, alcohol and other drug concerns, and psychological assessments, which I approach in a client-centred, strengths-based way.', 'I am originally from Peru and can also provide therapy in Spanish. Outside work I enjoy beach days, hiking, tennis, new recipes and a good record.'],
        details=[
            ('Reach', TCO_REACH),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Master of Psychology (Clinical)', 'Bachelor of Psychological Science (Honours)', 'Bachelor of Arts (Psychology)'],
            same_as=[TCO + 'team/valeria-urrutia/'],
            works_for=TCO_WORKS_FOR,
            area='Australia',
        ),
    ),
    dict(
        slug='ebony-young', id='ebony-young', category='allied',
        ages=['children', 'teens', 'adults'],
        name='Ebony Young', short='Ebony', role='Therapy Assistant', pronouns='',
        practice='Therapy Co', place='Benowa, Gold Coast', descriptor='Therapy assistant',
        description='A therapy assistant with a psychology honours degree, practising skills with you between sessions, supervised by your psychologist.',
        chips=['Skills practice', 'Works with your psychologist'],
        telehealth=False,
        book_href=TCO_ENQUIRE, book_hint=TCO_ENQUIRE_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES_TA,
        qualifications='Therapy assistant, BPsych(Hons)',
        languages=[],
        experience=['Therapy assistant, Therapy Co, Benowa, supervised by the practice’s psychologists', 'Bachelor of Psychology (Honours), research on disgust, empathy and moral decision-making'],
        quote='Where people feel safe to learn, experiment and explore, they develop a sense of independence and self-confidence that is so valuable to our wellbeing.',
        about=['My psychology honours degree gave me a good understanding of mental health through psychological theory, assessment and research. I hope to complete a Masters and become a clinical psychologist.', 'In my own time I enjoy my miniature dachshund, friends and family, jigsaw puzzles, reading and true crime podcasts.'],
        details=[
            ('Reach', TCO_REACH_TA),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychology (Honours)'],
            same_as=[TCO + 'team/ebony-young/'],
            works_for=TCO_WORKS_FOR,
            area='Gold Coast',
        ),
    ),
    dict(
        slug='alexandra-wainwright', id='alexandra-wainwright', category='allied',
        ages=['children', 'teens', 'adults'],
        name='Alexandra Wainwright', short='Alexandra', role='Therapy Assistant and Support Worker', pronouns='',
        practice='Therapy Co', place='Benowa, Gold Coast', descriptor='Therapy assistant & support worker',
        description='Studying psychology at Griffith University. Practises skills with you between sessions, supervised by your psychologist.',
        chips=['Skills practice', 'NDIS support work'],
        telehealth=False,
        book_href=TCO_ENQUIRE, book_hint=TCO_ENQUIRE_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES_TA,
        qualifications='Therapy assistant and support worker, BPsychSc (in progress)',
        languages=[],
        experience=['Therapy assistant and support worker, Therapy Co, Benowa, supervised by the practice’s psychologists', 'Bachelor of Psychological Science, Griffith University, in progress'],
        quote='I’m passionate about creating a comfortable, understanding environment where clients feel respected and supported as they work toward their goals.',
        about=['I’m studying a Bachelor of Psychological Science at Griffith University, with a strong interest in developmental psychology, and my studies inform my therapy assistant and support work.', 'In my spare time you will find me with a good book, with friends, or on a sunny beach day with an iced caramel latte.'],
        details=[
            ('Reach', TCO_REACH_TA),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychological Science (in progress)'],
            same_as=[TCO + 'team/alexandra-wainwright/'],
            works_for=TCO_WORKS_FOR,
            area='Gold Coast',
        ),
    ),
    dict(
        slug='eliza-keefe', id='eliza-keefe', category='allied',
        ages=['children', 'teens', 'adults'],
        name='Eliza Keefe', short='Eliza', role='Therapy Assistant and Support Worker', pronouns='she/her',
        practice='Therapy Co', place='Benowa, Gold Coast', descriptor='Therapy assistant & support worker',
        description='Finishing a Master of Clinical Psychology, with an interest in children and teens. Practises life skills with you, supervised by your psychologist.',
        chips=['Children & teens', 'NDIS support work'],
        telehealth=False,
        book_href=TCO_ENQUIRE, book_hint=TCO_ENQUIRE_HINT,
        links=TCO_LINKS,
        fees=TCO_FEES_TA,
        qualifications='Therapy assistant and support worker, BPsychSc(Hons)',
        languages=[],
        experience=['Therapy assistant and support worker, Therapy Co, Benowa, supervised by the practice’s psychologists', 'Master of Clinical Psychology, Griffith University, in progress', 'Bachelor of Psychological Science (Honours), University of New England'],
        quote='Eliza enjoys creating a calm, supportive and engaging environment where you can feel comfortable to learn new skills.',
        about=['She is completing her Master of Clinical Psychology at Griffith University, with a particular interest in child and adolescent mental health, psychological assessment, and supporting children and adults with everyday life skills.', 'Outside work and study you’ll usually find her at the beach, with family and friends, or enjoying a good coffee.'],
        details=[
            ('Reach', TCO_REACH_TA),
            ('Appointments', TCO_APPOINTMENTS),
            ('Billing', TCO_BILLING),
            ('Wheelchair access', 'Not declared'),
        ],
        disclosure=TCO_DISCLOSURE,
        schema=dict(
            type='Person',
            credentials=['Bachelor of Psychological Science (Honours)', 'Master of Clinical Psychology (in progress)'],
            same_as=[TCO + 'team/eliza-keefe/'],
            works_for=TCO_WORKS_FOR,
            area='Gold Coast',
        ),
    ),
    dict(
        slug='bart-traynor', id='bart-traynor', category='psychologist',
        ages=['adults'],
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
            'Bart is a passionate, straight-talking Clinical Psychologist who believes mental health support should help people function better in everyday life, not just feel better in the therapy room. He works with clients facing complex challenges, career and performance pressures, and major life transitions, while also supporting clinicians through supervision and professional development.',
            'As Director of Atlantis Recovery Centre, Bart leads an integrated approach that brings together psychology, movement, physical rehabilitation, and performance. His warm, practical style helps people build resilience, improve both mental and physical fitness, and create meaningful, lasting change.',
        ],
        details=arc_details(),
        disclosure=ARC_DISCLOSURE,
        schema=dict(type='Person', credentials=['Clinical psychologist', 'AHPRA board-approved clinical supervisor'], **ARC_SCHEMA),
    ),
    dict(
        slug='jeff-leech', id='jeff-leech', category='psychologist',
        ages=['adults'],
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
        ages=['adults'],
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
        ages=['adults'],
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
        slug='yuri-lima', id='yuri-lima', category='physiotherapy',
        ages=['adults'],
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
        slug='tom-hissey', id='tom-hissey', category='physiotherapy',
        ages=['adults'],
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
        slug='lester-rafanan', id='lester-rafanan', category='physiotherapy',
        ages=['adults'],
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
        ages=['teens', 'adults'],
        name='Alex Lawson', short='Alex', role='ADHD Coach and Mentor', pronouns='he/him',
        practice='Lawson ADHD Solutions', place='Sutherland Shire & online',
        descriptor='ADHD coach & mentor',
        description='ADHD coach, teacher and former lawyer with ADHD, working with adults, students and parents.',
        chips=['Adults, students & parents', 'Executive functioning'], lived='Has ADHD',
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
    # ---- Nurtured Thoughts Psychology: psychiatrists
    dict(
        slug='dr-jae-cho', id='jae-cho', category='psychiatrist',
        ages=['adults'],
        name='Dr Jae Cho', short='Dr Cho', role='Psychiatrist', pronouns='he/him',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Specialist psychiatrist',
        description='Thorough, compassionate general psychiatry, with calm explanations that make difficult topics feel manageable and clear.',
        chips=['General psychiatry', 'ADHD', 'Trauma-informed'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_PSYCHIATRY,
        qualifications='Specialist psychiatrist, MD FRANZCP',
        languages=[],
        experience=[
            'Specialist psychiatrist, Nurtured Thoughts Psychology, Graceville',
            'Fellow of the Royal Australian and New Zealand College of Psychiatrists',
            'Medical degree, Western Sydney University',
            'Specialist psychiatric training across major Sydney hospitals',
            'Acute inpatient, community mental health, consultation-liaison and outpatient psychiatry',
        ],
        about=[
            'Dr Jae Cho is a specialist psychiatrist who provides thorough, compassionate care across all areas of general psychiatry, with a strong interest in anxiety, depression, insomnia, trauma, ADHD, personality disorder, bipolar disorder, OCD, addiction and other complex mental health conditions. Patients appreciate his calm manner, thoughtful explanations, and ability to make difficult topics feel manageable and clear.',
            'Jae’s approach is evidence-based, trauma-informed, and grounded in the biopsychosocial model. He takes the time to understand each patient’s background, strengths, and goals, and works collaboratively to create a tailored treatment plan. He values close partnership with GPs, psychologists, families, and other clinicians to ensure holistic, coordinated care.',
            'He is a Fellow of the Royal Australian and New Zealand College of Psychiatrists and completed his medical degree at Western Sydney University before undertaking specialist psychiatric training across major hospitals in Sydney. His experience spans acute inpatient care, community mental health, consultation-liaison psychiatry, and outpatient management of complex cases.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$900 initial, $395–$445 review, Medicare rebate applies; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=dict(NT_SCHEMA_DR, specialty='Psychiatric'),
    ),
    dict(
        slug='dr-rajitha-de-silva', id='rajitha-de-silva', category='psychiatrist',
        ages=['adults'],
        name='Dr Rajitha De Silva', short='Dr De Silva', role='Psychiatrist', pronouns='she/her',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Consultant psychiatrist',
        description='Over 16 years caring for adults, with a culturally sensitive approach that begins with feeling heard.',
        chips=['Adults', 'Anxiety & mood', 'Culturally sensitive'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_PSYCHIATRY,
        qualifications='Consultant psychiatrist, FRANZCP MD(Psychiatry), Board Certification in Psychiatry',
        languages=[],
        experience=[
            'Consultant psychiatrist, Nurtured Thoughts Psychology, Graceville',
            'Over 16 years caring for adults, in Sri Lanka and Australia',
            'Fellow of the Royal Australian and New Zealand College of Psychiatrists',
            'MD (Psychiatry) and Board Certification in Psychiatry',
        ],
        about=[
            'Dr Rajitha Marcellin De Silva is a compassionate consultant psychiatrist with over 16 years of experience caring for adults experiencing a wide range of mental health concerns. Having practised in both Sri Lanka and Australia, she brings a thoughtful, culturally sensitive approach to helping people navigate life’s challenges.',
            'She believes that the best care begins with feeling heard. Rajitha takes the time to understand each person’s unique experiences, concerns, and goals, creating a safe, supportive, and non-judgemental environment where patients feel comfortable discussing even the most difficult issues.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$900 initial, $395–$445 review, Medicare rebate applies; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=dict(NT_SCHEMA_DR, specialty='Psychiatric'),
    ),
    # ---- Nurtured Thoughts Psychology: GPs
    dict(
        slug='dr-beth-hansen', id='beth-hansen', category='gp',
        ages=['adults'],
        name='Dr Beth Hansen', short='Dr Hansen', role='GP', pronouns='she/her',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='A gentle, practical and thorough ADHD assessment for adults who have spent years masking, overcompensating or pushing through.',
        chips=['ADHD in women', 'Late-identified ADHD', 'ADHD in parents'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS FRACGP',
        languages=[],
        experience=[
            'General practice with a special interest in mental health, adult ADHD and women’s health',
            'Fellow of the Royal Australian College of General Practitioners',
            'Medical degree, University of Queensland',
            'Urban, rural and remote practice',
        ],
        about=[
            'Dr Beth Hansen is a GP with a special interest in mental health, adult ADHD and women’s health. A UQ graduate and a Fellow of the Royal Australian College of General Practitioners, she brings a gentle, practical and thorough approach to ADHD assessment and care.',
            'Beth is particularly interested in supporting adults who have managed for many years by masking, overcompensating or pushing through, often at the cost of exhaustion, anxiety, self-criticism or burnout. She has a strong interest in how ADHD can present in women, especially when symptoms have been missed, minimised or attributed to other causes.',
            'In her consultations, Beth aims to create a space where patients feel heard, understood and taken seriously. She takes time to explore symptoms in the context of a person’s life, including work, study, relationships, parenting, sleep, emotional regulation and mental health. She has worked across urban, rural and remote settings, which has shaped her interest in accessible and compassionate mental health care.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-bill-liley', id='bill-liley', category='gp',
        ages=['adults'],
        name='Dr Bill Liley', short='Dr Liley', role='GP', pronouns='he/him',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Rural generalist',
        description='More than 40 years of practice and a whole-person approach to how ADHD shapes your day-to-day life.',
        chips=['40+ years in practice', 'Rural & regional', 'Whole-person care'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, FRACGP FACRRM',
        languages=[],
        experience=[
            'Rural generalist GP, more than 40 years of clinical experience',
            'Metropolitan, regional, rural and remote practice in Queensland, New South Wales and Victoria',
            'Private practice, community and public hospital settings',
            'Aboriginal Community Controlled Health Organisations',
        ],
        about=[
            'Dr Bill Liley is an experienced Rural Generalist GP with more than 40 years of clinical experience and a particular interest in supporting people with ADHD.',
            'Throughout his career, Bill has worked across metropolitan, regional, rural and remote communities in Queensland, New South Wales and Victoria, including in private practice, community and public hospital settings, Aboriginal Community Controlled Health Organisations, and rural generalist practice. This breadth has given him extensive experience working with people from diverse backgrounds, including many who experience the effects of ADHD in their everyday lives.',
            'Bill brings a practical, whole-person approach to ADHD care, taking into consideration each patient’s individual circumstances and how ADHD impacts their day-to-day life. Based in regional Queensland, he also appreciates the accessibility that telehealth provides, particularly for people who may otherwise have difficulty accessing ADHD care.',
        ],
        details=[
            ('Reach', 'Telehealth from regional Queensland'),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', 'Not applicable to telehealth'),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-hannah-gray', id='hannah-gray', category='gp',
        ages=['adults'],
        name='Dr Hannah Gray', short='Dr Gray', role='GP', pronouns='she/her',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='Calm, structured and collaborative, explaining each step so you understand the plan and why.',
        chips=['Students & early career', 'Organisation & follow-through', 'New to assessment'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS FRACGP',
        languages=[],
        experience=[
            'General practice with a strong interest in mental health and adult ADHD',
            'Fellow of the Royal Australian College of General Practitioners',
            'Adult ADHD in university students and early-career professionals',
            'Organisation, procrastination and follow-through in study and work',
        ],
        about=[
            'Dr Hannah Gray is a warm and approachable GP with a strong interest in mental health and adult ADHD. She works primarily with adults who are managing study, early career roles or professional responsibilities and are concerned that attention, organisation or follow-through difficulties may be affecting their performance and wellbeing.',
            'In consultations, Hannah is calm, structured and collaborative. She takes pride in explaining her thinking and plans clearly so patients understand each step of the process. Her recommendations emphasise practical strategies and realistic next steps that fit a person’s day-to-day life, and she particularly welcomes patients who are new to mental health or ADHD assessment.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-john-ruberry', id='john-ruberry', category='gp',
        ages=['adults'],
        name='Dr John Ruberry', short='Dr Ruberry', role='GP', pronouns='he/him',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='Thirteen years in community general practice, and passionate about improving access to ADHD care.',
        chips=['13 years in practice', 'Access to ADHD care', 'Mental health'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS',
        languages=[],
        experience=[
            '13 years in community general practice',
            'Five years as owner and principal of his own clinic',
            'Strong interest in mental health and ADHD treatment',
        ],
        about=[
            'Dr John is a General Practitioner with 13 years of experience in community general practice, including five years as the owner and principal of his own busy clinic. Throughout his career, he has developed a strong interest in mental health and has seen firsthand the positive difference effective ADHD treatment can make to a person’s quality of life. He is passionate about improving access to ADHD care and supporting patients through their assessment and treatment journey.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-kay-walls', id='kay-walls', category='gp',
        ages=['adults'],
        name='Dr Kay Walls', short='Dr Walls', role='GP', pronouns='she/her',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='An ADHD assessment that is never just a checklist, and a plan that fits your life.',
        chips=['ADHD in adult women', 'Mothers & postnatal', 'Focused Psychological Strategies'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS BHealthSci FRACGP',
        languages=[],
        experience=[
            'Specialist general practice, with a background in mental health and women’s health',
            'Medical degree, University of Sydney',
            'General practice training, James Cook University; Fellow of the Royal Australian College of General Practitioners',
            'Additional training in Focused Psychological Strategies',
        ],
        about=[
            'Dr Kay Walls is a specialist general practitioner who brings warmth, curiosity, and a deeply holistic lens to everything she does. With a background spanning mental health and women’s health, she has developed a particular focus on ADHD in adult women, a group she feels has historically been under-recognised and underserved.',
            'For Kay, an ADHD assessment is never just a checklist. She is interested in the whole person, including their history, relationships, long-standing patterns, and the strengths that often sit alongside the challenges. She creates space for patients to tell their story fully, and many describe her consultations as the first time they have felt genuinely listened to.',
            'Her interests include supporting mothers and high-functioning women navigating a new ADHD diagnosis, culturally sensitive and person-centred care, and emotional regulation, anxiety and depression, particularly in the postnatal period.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-natalie-cook', id='natalie-cook', category='gp',
        ages=['adults'],
        name='Dr Natalie Cook', short='Dr Cook', role='GP', pronouns='she/her',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='Direct, honest and safety-focused advice, tailored to your work, sleep, family and day-to-day demands.',
        chips=['Complex adult ADHD', 'Evidence-based', 'Central Queensland'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS FRACGP',
        languages=[],
        experience=[
            'General practice in Central Queensland for over 11 years',
            'Russian-born and trained; FRACGP and AMC qualifications in Australia',
            'Assessing and managing adults with ADHD, including complex cases with psychiatrists and other specialists',
        ],
        about=[
            'Dr Natalie Cook is a Russian-born and trained GP who has practised in Central Queensland for over 11 years. She holds FRACGP and AMC qualifications in Australia.',
            'Her approach is direct, honest and safety-focused, providing clear, evidence-based advice while tailoring treatment to each patient’s individual circumstances, preferences and goals, including their work, sleep, family and day-to-day demands. She has extensive experience assessing and managing adults with ADHD, including complex cases requiring collaboration with psychiatrists and other specialists.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-richard-hostiadi', id='richard-hostiadi', category='gp',
        ages=['adults'],
        name='Dr Richard Hostiadi', short='Dr Hostiadi', role='GP', pronouns='he/him',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='Adult ADHD, men’s mental health and lifestyle medicine, with real insight into demanding, high-pressure work.',
        chips=['Men’s mental health', 'ADHD at work', 'Lifestyle medicine'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS FRACGP',
        languages=[],
        experience=[
            'Fellow of the Royal Australian College of General Practitioners',
            'Adult ADHD assessments and ongoing management',
            'Medical Officer, Royal Australian Navy Reserve',
            'Registered Nurse, St Vincent’s Hospital, Sydney',
            'Workers’ compensation, life insurance and disability claims',
        ],
        about=[
            'Dr Richard Hostiadi is a Fellow of the Royal Australian College of General Practitioners with a focus on adult ADHD, men’s mental health and lifestyle medicine. Before studying medicine, he worked as a Registered Nurse at St Vincent’s Hospital in Sydney across a range of clinical areas for several years.',
            'He also worked in workers’ compensation, life insurance and disability claims. Together with his experience as a General Practitioner and Medical Officer in the Royal Australian Navy Reserve, this has given him insight into occupational medicine, workplace health and the challenges faced by professionals, tradespeople and shift workers in physically demanding and high-pressure occupations.',
            'Outside medicine, Richard keeps active and has completed half and full marathons, HYROX events, obstacle course races and the Everest Base Camp trek. He lives with his wife and two young boys, and their dog.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-sally-mcleod', id='sally-mcleod', category='gp',
        ages=['teens', 'adults'],
        name='Dr Sally McLeod', short='Dr McLeod', role='GP', pronouns='she/her',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='Helping adolescents and adults understand how their brain works, with thorough, evidence-based assessment.',
        chips=['Women & girls', 'Late diagnosis', 'Perimenopause'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS FRACGP',
        languages=[],
        experience=[
            'Medical degree, University of Queensland, 2009',
            'Fellow of the Royal Australian College of General Practitioners, 2016',
            'ADHD in women and girls, including late diagnosis in adulthood',
            'Perimenopause and its interaction with ADHD and mental health',
        ],
        about=[
            'Dr Sally McLeod completed her medical degree at the University of Queensland in 2009 before her junior doctor training at the Mater Hospital in South Brisbane, and her Fellowship of the Royal Australian College of General Practitioners in 2016.',
            'Sally has a special interest in ADHD and is passionate about helping adolescents and adults better understand how their brain works. She provides thorough, evidence-based assessments and works collaboratively with patients to develop practical, individualised treatment plans. Her interests include ADHD in women and girls, high-functioning and late-identified ADHD in professionals, perimenopause, and autism, anxiety and depression in the context of neurodivergence.',
            'Outside of medicine, Sally enjoys time with her three sons, reading, music and the outdoors.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    dict(
        slug='dr-shwetha-murthy', id='shwetha-murthy', category='gp',
        ages=['adults'],
        name='Dr Shwetha Murthy', short='Dr Murthy', role='GP', pronouns='she/her',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor=None,
        description='A structured assessment of how ADHD has shown up over time, and what it means for family life.',
        chips=['Parents & carers', 'ADHD in families', 'Men at work'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_GP,
        qualifications='General practitioner, MBBS FRACGP SCHP',
        languages=[],
        experience=[
            'Specialist General Practitioner with a particular interest in adult ADHD and mental health',
            'Medical degree in India; clinical experience in the United Kingdom; in Australia since 2007',
            'Tertiary and regional hospitals in NSW, WA and Queensland: General Medicine, Nephrology, Nuclear Medicine and Radiology',
            'Sydney Child Health Program, University of Sydney',
        ],
        about=[
            'Dr Shwetha Murthy is a Specialist General Practitioner with a particular interest in adult ADHD and mental health. Many of the people she sees are managing busy households, caring for children or relatives, and noticing patterns of attention, organisation or emotional regulation that seem to run through the family. She is especially interested in supporting women who are starting to wonder how their own history, their children’s experiences and ADHD might be connected, and in adult ADHD in men across blue-collar and white-collar work.',
            'In consultations, Shwetha brings a calm, organised style and a strong focus on context: childhood experiences, school reports, family roles, cultural background and current life demands. She maps how symptoms have shown up over time and how they interact with mood, sleep and physical health, explained in clear, practical language.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$1,950 all-inclusive adult ADHD pathway, about $200 Medicare rebate; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=NT_SCHEMA_DR,
    ),
    # ---- Nurtured Thoughts Psychology: psychologists
    dict(
        slug='heather-mcauliffe', id='heather-mcauliffe', category='psychologist',
        ages=['children', 'teens', 'adults'],
        name='Heather McAuliffe', short='Heather McAuliffe', role='Clinical Psychologist', pronouns=None,
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Clinical psychologist',
        description='A neurodivergent clinical psychologist who makes assessment warm and safe, and treats you as the expert on your own experience.',
        chips=['Neurodevelopmental assessment', 'Neurodivergent clinician', 'Collaborative care'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_CLINICAL,
        qualifications='Clinical psychologist',
        languages=[],
        experience=[
            'Clinical psychologist with a particular interest in neurodevelopment',
            'Private and community practice',
            'Detailed assessment and diagnosis, therapeutic intervention and care coordination',
            'Consults with paediatricians, psychiatrists and allied health professionals',
        ],
        about=[
            'Heather is a neurodivergent Clinical Psychologist with a particular interest in neurodevelopment. Her background includes private and community practice, where she has engaged in detailed assessment and diagnosis, therapeutic intervention, and collaborative care coordination.',
            'She strives to ensure that the assessment process provides warmth, safety, and supportive recommendations, valuing the individual as the expert of their own experiences. Her approach is collaborative, and she often consults with paediatricians, psychiatrists, clinical psychologists, and other allied health professionals for a holistic understanding of each person’s needs.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', 'Set and charged by the practice; quoted when you book'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=dict(type='Person', credentials=['Clinical psychologist'], same_as=NT_SAME_AS, works_for=NT_WORKS_FOR, area='Australia'),
    ),
    dict(
        slug='matthew-persello', id='matthew-persello', category='psychologist',
        ages=['teens', 'adults'],
        name='Matthew Persello', short='Matthew Persello', role='Registered Psychologist', pronouns=None,
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Registered psychologist',
        description='Strengths-based, solution-focused therapy for adolescents and adults, with a focus on men’s mental health, neurodiversity and the LGBTQIA+ community.',
        chips=['Teens 13+ & adults', 'Men’s mental health', 'LGBTQIA+'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_PSYCHOLOGIST,
        qualifications='Registered psychologist',
        languages=[],
        experience=[
            'Therapy for adolescents (13+) and adults',
            'Psychology honours, studied in Australia and the United States',
            'Year-long research project on romantic self-sabotage in gender and sexually diverse populations',
            'CBT, ACT, Solution Focused Therapy and Motivational Interviewing',
        ],
        about=[
            'Matthew is a Registered Psychologist specialising in therapy for adolescents (13+ years) and adults, with a strong focus on men’s mental health, neurodiversity and the LGBTQIA+ community. He completed his psychology honours degree through studies in both Australia and the United States, including a year-long research project exploring romantic self-sabotage within gender and sexually diverse populations.',
            'His areas of interest include anxiety, depression and stress, sleep difficulties, neurodiversity including autism and ADHD, gender and sexual identity, self-esteem, emotional regulation and relationship challenges. His approach is strengths-based and solution-focused, drawing on CBT, ACT, Solution Focused Therapy and Motivational Interviewing tailored to each client’s needs.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$240 a session, $98.95 Medicare rebate with a plan; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=dict(type='Person', credentials=['Registered psychologist'], same_as=NT_SAME_AS, works_for=NT_WORKS_FOR, area='Australia'),
    ),
    dict(
        slug='nzubechi-oguoma', id='nzubechi-oguoma', category='psychologist',
        ages=['children', 'teens', 'adults'],
        name='Nzubechi Oguoma', short='Nzubechi Oguoma', role='Registered Psychologist', pronouns=None,
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Registered psychologist',
        description='Working with individuals and families from age 5 and across the lifespan, including neurodevelopmental conditions.',
        chips=['Ages 5+', 'Family therapy', 'Trauma & PTSD'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_PSYCHOLOGIST,
        qualifications='Registered psychologist',
        languages=[],
        experience=[
            'Individuals and families from age 5 and across the lifespan',
            'Mental health conditions and neurodevelopmental disorders',
            'CBT, ACT and Trauma-Informed Practice',
        ],
        about=[
            'Nzubechi is a Registered Psychologist with experience working with individuals and families from age 5 and across the lifespan, presenting with a range of mental health conditions as well as neurodevelopmental disorders.',
            'Areas of interest include anxiety, depression, trauma and post-traumatic stress disorder, family therapy, relationships, self-esteem and self-development, and work-related issues. The primary evidence-based modalities used are Cognitive Behaviour Therapy, Acceptance and Commitment Therapy and Trauma-Informed Practice.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$240 a session, $98.95 Medicare rebate with a plan; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=dict(type='Person', credentials=['Registered psychologist'], same_as=NT_SAME_AS, works_for=NT_WORKS_FOR, area='Australia'),
    ),
    # ---- Nurtured Thoughts Psychology: mental health social workers
    dict(
        slug='canice-curtis', id='canice-curtis', category='allied',
        ages=['teens', 'adults'],
        name='Canice Curtis', short='Canice Curtis', role='Mental Health Social Worker', pronouns='he/him',
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Mental health social worker',
        description='A grounded, integrated and evidence-informed approach for people 15 and over, including complex trauma and ADHD.',
        chips=['Ages 15+', 'Trauma & EMDR', 'Men’s mental health'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_SOCIAL_WORKER,
        qualifications='Mental health social worker, MSW MPaDS BA, AASW member',
        languages=[],
        experience=[
            'Mental health social worker, people aged 15 and over',
            'Nominated by colleagues for the AASW Social Worker of the Year Award',
            'Trauma and EMDR, men’s mental health, and mental health after major life changes or disasters',
        ],
        about=[
            'Canice Curtis is a deeply attuned and compassionate Mental Health Social Worker who considers it a privilege to walk alongside clients as they navigate challenges and work towards meaningful change. His commitment to client care led colleagues to nominate him for the AASW Social Worker of the Year Award.',
            'He supports people aged 15+ experiencing complex trauma, dissociative conditions, addictions, personality disorders, bipolar disorder, ADHD, chronic pain, parenting and relationship difficulties, men’s mental health concerns, grief and loss, anxiety, depression, and the mental health impacts of climate change and natural disasters. With a background spanning international development, child protection and academia, he brings a grounded, integrated, evidence-informed approach tailored to each person.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$230 a session, $87.25 Medicare rebate with a plan; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=dict(type='Person', credentials=['Master of Social Work', 'Master of Peace and Development Studies', 'Bachelor of Arts'],
                    same_as=NT_SAME_AS, works_for=NT_WORKS_FOR, area='Australia'),
    ),
    dict(
        slug='tracey-dale', id='tracey-dale', category='allied',
        ages=['children', 'teens', 'adults'],
        name='Tracey Dale', short='Tracey Dale', role='Accredited Mental Health Social Worker', pronouns=None,
        practice='Nurtured Thoughts Psychology', place=NT_PLACE, descriptor='Mental health social worker',
        description='Warm, empowering and highly personalised therapy, kept straightforward and free from unnecessary jargon.',
        chips=['All ages', 'Burnout & life transitions', 'EMDR'],
        telehealth=True,
        book_href=NT_BOOK, book_hint=NT_BOOK_HINT,
        links=NT_LINKS,
        fees=NT_FEES_SOCIAL_WORKER,
        qualifications='Accredited mental health social worker',
        languages=[],
        experience=[
            'Over 10 years in counselling, therapy and psychotherapy',
            'Counsellor, Queensland University of Technology',
            'Private practice, and clinical operations lead in mental health and crisis support services',
            'CBT, ACT, DBT, EMDR, Narrative Therapy and individual psychotherapy',
        ],
        about=[
            'Tracey is an Accredited Mental Health Social Worker with over 10 years of experience in counselling, therapy and psychotherapy. She works with clients of all ages through major life transitions such as pregnancy and motherhood, and challenges like anxiety, depression, burnout, trauma (including complex PTSD using EMDR), grief, sleep difficulties, disordered eating, and recovery from violence or substance use.',
            'She has provided counselling at QUT, worked in private practice and led clinical operations in busy mental health settings, including crisis support services. Clients often describe her approach as warm, empowering and highly personalised; she draws on CBT, ACT, DBT, EMDR and Narrative Therapy, tailoring each session and keeping things straightforward.',
            'The first session is about getting to know you, your story and what you would like to achieve, and she aims for you to leave each session with practical skills to take into everyday life. Outside therapy she reads, gardens, hikes, and tries her hand at pottery on a throwing wheel.',
        ],
        details=[
            ('Reach', NT_REACH),
            ('Appointments', NT_APPOINTMENTS),
            ('Billing', '$230 a session, $87.25 Medicare rebate with a plan; set and charged by the practice'),
            ('Wheelchair access', NT_ACCESS),
        ],
        disclosure=NT_DISCLOSURE,
        schema=dict(type='Person', credentials=['Accredited Mental Health Social Worker'], same_as=NT_SAME_AS, works_for=NT_WORKS_FOR, area='Australia'),
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


def share_image(c, size):
    """og:image path, width and height: the clinician's 1200x630 share card (scripts/build-og-images.cjs renders it from
    this page) once it exists, else the square portrait, which platforms crop to 1.91:1."""
    card = ROOT / SHARE_CARDS / f"{c['id']}.jpg"
    if not card.exists():
        return f"{PORTRAITS}/{c['id']}.jpg", size, size
    w, h = jpeg_size(card)
    if (w, h) != (1200, 630):
        raise BuildError(f"{card.relative_to(ROOT)} is {w}x{h}; share cards must be 1200x630")
    return f"{SHARE_CARDS}/{c['id']}.jpg", w, h


def subline(c):
    """Under the name on the deck card and the 'Also in the network' link."""
    return f"{c['descriptor']} · {c['place']}" if c['descriptor'] else c['place']


def meta_line(c):
    parts = [c['pronouns'], c['descriptor'], c['practice'], c['place']]
    return ' · '.join(p for p in parts if p)


# Where a clinician is, the way a reader thinks of it first: the city and state, then the suburbs. The city comes
# from the practice's suburb; the three GPs and the telehealth-only psychologist are named here directly.
CITY = {'Fortitude Valley': 'Brisbane, QLD', 'Ashgrove': 'Brisbane, QLD', 'Benowa': 'Gold Coast, QLD', 'Bundall': 'Gold Coast, QLD',
        'Glenbrook': 'Blue Mountains, NSW', 'Jindabyne': 'Snowy Mountains, NSW', 'Sutherland': 'Sydney, NSW', 'Perth': 'Perth, WA',
        'Graceville': 'Brisbane, QLD'}
REGION_BY_ID = {'anubhav-saxena': 'Sydney, NSW', 'anu-saxena': 'Sydney, NSW', 'yogesh-kalra': 'Central Coast, NSW',
                'allen-macbell': 'Melbourne, VIC',
                'paula-garrido': 'Australia-wide via telehealth'}
SUBURBS_BY_ID = {'anubhav-saxena': 'Beecroft & Double Bay', 'anu-saxena': 'Double Bay & Hornsby', 'yogesh-kalra': 'Bateau Bay',
                 'allen-macbell': 'Ivanhoe',
                 'paula-garrido': '', 'alex-lawson': 'Sutherland Shire'}
AGE_LABEL = {'children': 'children', 'teens': 'teens', 'adults': 'adults'}


def city(c):
    return REGION_BY_ID.get(c['id']) or CITY[c['schema']['works_for']['locality']]


def state_of(c):
    """The state the practice is in: NSW, QLD, VIC or WA."""
    return (c['schema'].get('works_for') or {}).get('state') or c['schema'].get('state') or ''


def suburbs(c):
    """The suburb line under the city, empty when it would only repeat the city (Perth, telehealth-only)."""
    if c['id'] in SUBURBS_BY_ID:
        return SUBURBS_BY_ID[c['id']]
    loc = c['schema']['works_for']['locality']
    return '' if city(c).startswith(loc) else loc


def ages_line(c):
    parts = [AGE_LABEL[a] for a in c['ages'] if a in AGE_LABEL]
    if not parts:
        return ''
    text = parts[0] if len(parts) == 1 else ', '.join(parts[:-1]) + ' & ' + parts[-1]
    return 'For ' + text

# There are many psychologists, in many places, so on theirs the place stands out: bold and in ink.
PLACE_BOLD = '<b class="font-extrabold text-[#1a1c1c]">{}</b>'


def place_html(c):
    return PLACE_BOLD.format(esc(c['place'])) if c['category'] == 'psychologist' else esc(c['place'])


def subline_html(c):
    return f"{esc(c['descriptor'])} · {place_html(c)}" if c['descriptor'] else place_html(c)


def meta_line_html(c):
    where = PLACE_BOLD.format(esc(city(c))) + (' · ' + esc(suburbs(c)) if suburbs(c) else '')
    parts = [esc(p) for p in (c['pronouns'], c['descriptor'], c['practice']) if p] + [where]
    return ' · '.join(parts)


TITLE_ROOM = 60 - len(' · ADHDme')   # search results cut titles at about 60 characters


def og_title(c):
    """Name, "ADHD" and role, and place when it fits in a search result's title. The role is the sentence-case
    descriptor. A name and role that still run over stay whole: a search result then trims the brand suffix, which
    is better than cutting a word of the role."""
    role = c['descriptor'] or c['role']
    # "ADHD" leads the role: it is the word people search with ("ADHD GP Brisbane"), and the brand suffix alone
    # does not carry it. It goes before the place does, and the place before the name and bare role.
    adhd = 'ADHD ' + (role[0].lower() + role[1:] if role[1:2].islower() else role)
    with_place, bare = f"{c['name']}, {adhd}, {c['place']}", f"{c['name']}, {adhd}"
    if len(with_place) <= TITLE_ROOM:
        return with_place
    # html-validate refuses a <title> over 70 characters of source (an & counts as &amp;), suffix included; past
    # that the role goes without "ADHD".
    return bare if len(esc(bare)) <= 70 - len(' · ADHDme') else f"{c['name']}, {role}"


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


# Beside it, the same marker for seeing people face to face: most clinicians do both, and a reader should not
# have to open a profile to learn that. Every clinician sees people in person unless `in_person=False`.
IN_PERSON_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-semibold '
                  'text-[#2e5a2b] bg-[#dbe9d3] border border-[#bcd6b1]">'
                  '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                  'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                  '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>'
                  'In person</span>')


# The second fixed marker. Some practices treat movement as the treatment rather than an extra, and a
# reader scanning the deck cannot tell that from an interest chip. Same shape and position rule as the
# telehealth pill: one wording, one icon, always ahead of the interest chips. Set it from `exercise`.
EXERCISE_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-semibold '
                 'text-[#8a3624] bg-[#fbd8cf] border border-[#f0b9a9]">'
                 '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                 '<path d="M6.5 6.5v11M3.5 9v5M17.5 6.5v11M20.5 9v5M6.5 12h11"/></svg>'
                 'Exercise-based</span>')

# Bulk billing, in the gold the site uses for what things cost.
BULK_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-semibold '
             'text-[#7a5a0e] bg-[#fdf3d6] border border-[#ebd8ab]">'
             '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9"/><path d="M14.5 9.6c-.4-.9-1.4-1.4-2.5-1.4-1.4 0-2.5.8-2.5 1.9s1 1.7 2.5 2 2.5.9 2.5 2-1.1 1.9-2.5 1.9c-1.2 0-2.2-.5-2.6-1.4M12 6.6v1.6M12 15.8v1.6"/></svg>'
             'Bulk billed</span>')


# Lived experience, first of all the markers so a reader who wants somebody who gets it from the inside finds
# them by scanning the deck. The wording comes from the clinician's own words, set in `lived`: 'Has ADHD',
# or 'Partner has ADHD' when that is what they say. Never inferred.
LIVED_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-semibold '
              'text-[#4a3d86] bg-[#e7e3f6] border border-[#cdc5ec]">'
              '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
              'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
              '<circle cx="12" cy="8" r="3.5"/><path d="M5 20.5c.8-3.6 3.6-5.5 7-5.5s6.2 1.9 7 5.5"/></svg>'
              '{}</span>')

# What a GP does for ADHD, said plainly and first: assess, diagnose and start treatment, or continue a
# prescription someone else started. Set by `assesses` on the record.
GP_ASSESS_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-bold '
                  'text-white bg-[#1a1c1c] border border-[#1a1c1c]">Diagnoses &amp; prescribes</span>')
GP_CONTINUE_PILL = ('<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-bold '
                    'text-[#1a1c1c] bg-white border-2 border-[#1a1c1c]">Continuation only</span>')


def gp_pill(c):
    if c['category'] != 'gp':
        return ''
    return GP_ASSESS_PILL if c.get('assesses', True) else GP_CONTINUE_PILL


def chip_row(c, limit=None):
    """The clinician's interest chips, behind the markers they carry: lived experience, in person, telehealth, then exercise. A card
    in the deck shows the first `limit` chips; the profile shows them all."""
    markers = (gp_pill(c) + (LIVED_PILL.format(esc(c['lived'])) if c.get('lived') else '') + (IN_PERSON_PILL if c.get('in_person', True) else '') + (TELEHEALTH_PILL if c['telehealth'] else '')
               + (EXERCISE_PILL if c.get('exercise') else '') + (BULK_PILL if c.get('bulk_billed') else ''))
    return markers + ''.join(CHIP.format(esc(x)) for x in c['chips'][:limit])
BOOK_HREF = 'the-doctors.html#{}'

# A diary you can pick a time in, or a form the practice answers. The button says which, and each
# list on The Network puts the diaries first: the easiest people to reach are the first ones you meet.
ONLINE_DIARIES = ('healthengine.com.au', 'halaxy.com/book', 'hotdoc.com.au', 'automedsystems.com.au')


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


# How wide the portrait at the top of a profile is drawn. The hero preload in the <head> uses the same string, so the
# browser fetches the one candidate the <picture> picks, not the full-size file as well.
HERO_SIZES = '(min-width: 1280px) 376px, (min-width: 1024px) 30vw, 80vw'


def srcset(c, size, ext):
    """A portrait's candidates at 320, 640 and full size."""
    base = f"{PORTRAITS}/{c['id']}"
    return f'{base}-320.{ext} 320w, {base}-640.{ext} 640w, {base}.{ext} {size}w'


def picture(c, size, sizes, img_attrs, img_class):
    """<picture> with WebP and JPEG candidates at 320, 640 and full size."""
    base = f"{PORTRAITS}/{c['id']}"
    return (f'<picture><source type="image/webp" srcset="{srcset(c, size, "webp")}" sizes="{sizes}">'
            f'<img {img_attrs} width="{size}" height="{size}" alt="Portrait of {esc(c["name"])}" class="{img_class}" '
            f'srcset="{srcset(c, size, "jpg")}" sizes="{sizes}" src="{base}.jpg"></picture>')


def portrait_span(c, size, tag, extra_class, sizes, img_attrs, img_class):
    return (f'<{tag} class="{extra_class}{PORTRAIT_BOX}" id="portrait-{c["id"]}" style="view-transition-name: portrait-{c["id"]}">'
            f'{picture(c, size, sizes, img_attrs, img_class)}</{tag}>')


DECK_COLUMNS = 4   # cards in a row of the deck at desktop width (lg:grid-cols-4)
DECK_CHIPS = 2   # interest chips on a deck card: four stacked chips made each card a column of pills on a phone


# The line on each Network card: what the clinician helps with, in everyday words. The profile page and search
# results keep the fuller `description`; a clinician without a line here shows that instead.
CARD_LINES = {
    'anubhav-saxena': 'An ADHD assessment that looks at the whole of you: sleep, heart and general health, with a baseline taken before anything starts. He works from measurement, not impression, and reviews you at set times.',
    'anu-saxena': 'A GP who came to medicine through a psychology degree, with a special interest in ADHD, mental health and women’s health. She sees children and adults, in English, Hindi or Urdu.',
    'yogesh-kalra': 'Keeps your ADHD medication going once you’re diagnosed, so you can manage it close to home, bulk billed. He isn’t diagnosing ADHD yet; that’s planned for the future.',
    'allen-macbell': 'More than 15 years of ADHD care for children aged 10 and over, teens and adults, including autism and ADHD together. You see the same doctor from the first appointment to diagnosis, treatment and follow-up.',
    'paula-garrido': 'A clinical psychologist certified in ADHD and autism care, seeing you by video anywhere in Australia. Her care is neuroaffirming and trauma-aware, and helps you understand your strengths as well as your challenges.',
    'kate-row': 'Helps everyone from toddlers to adults build a toolkit of practical coping strategies. She has a lifelong passion for supporting people with disability, and can guide your family through the NDIS.',
    'ellie-putland': 'Gentle, trauma-aware therapy for children, teens and adults, with a soft spot for young people. She works alongside families and stays in touch with the rest of your support team.',
    'lachlan-avent': 'Does ADHD and autism assessments, and offers therapy and parenting support for children, teens and adults. He’s passionate about giving you a safe space to say what’s really going on.',
    'samantha-courtney': 'A credentialed eating disorder clinician for teens and adults. She also supports people through pregnancy, new parenthood, fertility and big life changes, with a strengths-based, trauma-aware approach.',
    'lauren-poulos': 'Early support for young children and their parents, in the clinic or at home, including Parent-Child Interaction Therapy for big behaviours. She also sees teens and adults, and offers parenting support.',
    'alice-bui': 'Trauma-aware therapy in a safe, collaborative space, including for ADHD and autism. She has a special interest in refugees, new arrivals and people from many cultures.',
    'meera-lakhani': 'Focuses on ADHD, autism and learning assessments, to find your or your child’s strengths as well as the hard parts. She has also worked as a psychologist in a school.',
    'trisha-harris': '“I have ADHD and run a business, so I absolutely understand how busy, stressful and chaotic life can get!” A counsellor and mum of four, seeing teens, adults, couples and NDIS participants.',
    'flynn-simonis': 'Occupational therapy for kids that starts with what your child loves: LEGO, Minecraft and Ninja Warrior-style groups, and outdoor adventure camps. He works at the clinic, at home or at school.',
    'lara-schulz': 'Brain mapping and brain training, called neurotherapy, with a chat about your results before any training starts. She trained in California with the founder of Neurofield Neurotherapy.',
    'fiona-alexander': 'A teacher of 25 years who believes “every student learns differently and that diversity in learning is something to be celebrated”. She helps students and families understand how an ADHD brain works.',
    'debbie-hirte': 'Nearly 30 years in schools, including as a gifted and talented specialist. She helps families and schools write learning plans together, and coaches children and teens with ADHD in mind.',
    'romney-taylor': '23 years working with students taught her that “no two minds work the same”. She builds strategies that work at school, at home and in relationships, in a space where students feel heard.',
    'erin-lysle': 'More than 34 years of teaching, now coaching on getting organised, confidence and making friends. Her priority is “meeting each person where they are”.',
    'donna-italiano': 'A high school teacher of more than 20 years who coaches young people on getting organised and handling big feelings. Her approach brings together neuroscience, emotional safety and compassion.',
    'kate-dallimore': 'An ADHD coach with a physio and teaching background and a gentle, trauma-aware approach. She’s drawn to people who haven’t always felt understood, helping them trust themselves and take the next step.',
    'jessica-katsamatsas': 'She believes “therapy should feel like a space where you can take a breath, put the mask down, and be a little more human”. She works mostly with young neurodivergent adults on anxiety, burnout and self-esteem.',
    'chantelle-pin': 'A clinical psychologist who was diagnosed with ADHD as an adult, so she brings lived experience as well as training. She works with neurodivergent children and adults, and is taking on assessments.',
    'sarah-bibo': 'On maternity leave for now. Her research looked at ADHD in children, and she helps adults with anxiety, low mood, trauma, ADHD, autism, eating and body image in a warm, non-judgmental way.',
    'gisele-fortkamp': 'Helps children with ADHD or autism, and their parents, with big feelings, behaviour and self-esteem. She also supports women exploring or adjusting to an ADHD diagnosis. Sessions in English or Portuguese.',
    'lana-hiscock': 'Help with sleep, relationships, pregnancy and new parenthood, in “a supportive and culturally compassionate space shaped by my own diverse background”. Sessions in English, Mandarin or Shanghainese.',
    'valeria-urrutia': 'A “curious, collaborative and flexible” approach to anxiety, low mood, grief and big life changes. Her assessments help you understand yourself and find strategies for everyday life. Sessions in English or Spanish.',
    'ebony-young': 'Practises the skills from your therapy with you, week to week, guided by your psychologist. She believes people grow in confidence when they “feel safe to learn, experiment and explore”.',
    'alexandra-wainwright': 'Practises skills with you at home, at school or out and about, guided by your psychologist. She’s studying psychology and wants you to feel “respected and supported” as you work toward your goals.',
    'eliza-keefe': 'Helps children and adults practise everyday life skills in a calm, supportive space, guided by your psychologist. She’s finishing a Master of Clinical Psychology, with an interest in children and teens.',
    'bart-traynor': 'A straight-talking clinical psychologist who believes support “should help people function better in everyday life, not just feel better in the therapy room”. For work pressure, performance and big life changes.',
    'jeff-leech': 'A clinical psychologist for trauma, anxiety, low mood and performing at your best. He uses talking therapy and activity-based therapy, and has a background in outdoor education.',
    'michael-rehardt': 'A provisional psychologist in the final placement of his Master of Clinical Psychology, with a thoughtful, creative and practical approach. He is also an Aboriginal artist and a former competitive sprinter.',
    'sarah-savage': '“Exercise as Medicine” is her mantra. She uses Pilates and exercise in warm water to build safe programs that make moving feel achievable and enjoyable, with a soft spot for older adults.',
    'yuri-lima': 'Helps you recover from sport and joint injuries and get back to your best. He has a PhD on knee (ACL) injuries in athletes, and involves you in your own recovery at every step.',
    'tom-hissey': 'An Australian Army veteran who has been through back surgery and rehab himself, so he knows what recovery takes. He helps with muscle and joint injuries and getting back to work or sport.',
    'lester-rafanan': 'Physio to recover from injury or surgery, manage ongoing pain or get back to sport, with NDIS support too. A former personal trainer, he builds every plan around your goals.',
    'alex-lawson': '“I know what it’s like to work in high-pressure environments and navigate the demands of a busy brain.” An ADHD coach, teacher and former lawyer who has lived with ADHD for over 30 years.',
}


def deck_card(c, size, rank):
    """rank: the card's place in the first row of the panel shown on arrival (0 is the first), else None."""
    img_attrs = ('loading="eager" fetchpriority="high" decoding="async"' if rank == 0 else
                 'loading="eager" decoding="async"' if rank is not None else 'loading="lazy" decoding="async"')
    sizes = '(min-width: 768px) 198px, 132px'   # the photo's width on a directory card
    img_class = 'w-full h-full object-cover object-[center_30%] transition-transform duration-700 group-hover:scale-[1.02]'
    lived = ' data-lived' if c.get('lived') else ''
    lived += ' data-pinned' if c['id'] in PINNED else ''
    where = (f'<span class="block mt-2 text-[15px] font-extrabold text-[#1a1c1c]">{esc(city(c))}</span>'
             + (f'<span class="block text-[14px] font-semibold text-[#5f5e59]">{esc(suburbs(c))}</span>' if suburbs(c) else ''))
    modes = ' '.join(m for m, on in (('in-person', c.get('in_person', True)), ('telehealth', c['telehealth'])) if on)
    gp = (' data-gp="' + ('assess' if c.get('assesses', True) else 'continue') + '"') if c['category'] == 'gp' else ''
    return f'''<li id="{c['id']}"{lived} class="dir-card" data-name="{esc(c['name'])}" data-region="{esc(city(c))}" data-modes="{modes}" data-state="{state_of(c)}" data-ages="{' '.join(c['ages'])}"{gp}>
  <a class="block group" href="{c['slug']}.html">
    {portrait_span(c, size, 'span', 'block ', sizes, img_attrs, img_class)}
    <span class="block pt-4"><strong class="block text-[22px] font-extrabold tracking-tight text-[#1a1c1c] leading-tight">{esc(c['name'])}</strong><span class="block mt-1 text-[15px] font-semibold text-[#5f5e59]">{esc(c['descriptor'] or c['role'])}</span>{where}</span>
  </a>
  <div class="flex flex-wrap gap-2 pt-3">{chip_row(c, DECK_CHIPS)}</div>
  <p class="deck-ages">{esc(ages_line(c))}</p>
  <p class="deck-bio">{esc(CARD_LINES.get(c['id'], c['description']))}</p>
  <div class="mt-auto pt-4"><a class="btn-press inline-flex items-center gap-2 h-11 px-6 rounded-full bg-[#1a1c1c] text-white text-[15px] font-bold hover:bg-[#2f3130] transition-colors" aria-label="{book_verb(c)} with {esc(c['name'])}" href="{c['slug']}.html">{book_verb(c)} <span class="text-[#f1bc31]" aria-hidden="true">→</span></a></div>
</li>'''


def also_link(c, size, eager=False):
    loading = f'loading="{"eager" if eager else "lazy"}" decoding="async"'
    return (f'<a class="flex items-center gap-4 group min-w-0" href="{c["slug"]}.html">'
            f'{portrait_span(c, size, "span", "block w-20 shrink-0 ", "96px", loading, "w-full h-full object-cover object-[center_30%]")}'
            f'<span class="min-w-0"><strong class="block text-[19px] leading-[1.25] font-extrabold tracking-tight text-[#1a1c1c]">{esc(c["name"])}</strong>'
            f'<span class="block text-[14px] font-semibold text-[#5f5e59]">{subline_html(c)}</span></span></a>')


# Links more than one clinician lists (a practice's team page or social account) describe the practice.
SHARED_LINKS = {u for u, n in Counter(u for c in CLINICIANS if c['schema']['type'] == 'Person'
                                      for u in c['schema']['same_as']).items() if n > 1}


def jsonld(c):
    s = c['schema']
    page = f"{SITE}/{c['slug']}.html"
    image = f"{SITE}/{PORTRAITS}/{c['id']}.jpg"
    job = c['qualifications'].split(',')[0]   # the role; the degrees are hasCredential
    if s['type'] == 'Physician':
        # A doctor is a Person who works for a clinic; schema.org's Physician is an Organization type.
        d = {'@type': 'Person', '@id': page + '#physician',
             'name': c['name'], 'url': page, 'jobTitle': job, 'knowsLanguage': c['languages'], 'image': image,
             'sameAs': [c['book_href']],
             'worksFor': {'@type': 'MedicalClinic', 'name': c['practice'], 'medicalSpecialty': s.get('specialty', 'PrimaryCare'),
                          'address': {'@type': 'PostalAddress', 'addressLocality': s['areas'][0], 'addressRegion': s['state'], 'addressCountry': 'AU'},
                          'areaServed': [{'@type': 'Place', 'name': f"{a}, {s['state']}, Australia"} for a in s['areas']]}}
    elif s['type'] == 'Person':
        w = s['works_for']
        # A link several clinicians share is the practice's page or account, not theirs.
        own = [u for u in s['same_as'] if u not in SHARED_LINKS]
        d = {'@type': 'Person', '@id': page + '#person',
             'name': c['name'], 'url': page, 'jobTitle': job, 'image': image,
             'hasCredential': [{'@type': 'EducationalOccupationalCredential', 'name': n} for n in s['credentials']],
             # Not every practice in the network is a health service: coaching is a ProfessionalService.
             # A clinician who only sees people in one town gets a Place rather than the whole country.
             'worksFor': {'@type': w.get('type', 'MedicalBusiness'), 'name': c['practice'], 'url': w['url'], 'telephone': w['telephone'],
                          'address': {'@type': 'PostalAddress', 'addressLocality': w['locality'], 'addressRegion': w['state'], 'addressCountry': 'AU'},
                          'areaServed': {'@type': s.get('area_type', 'Country'), 'name': s['area']}}}
        if own:
            d['sameAs'] = own
        shared = [u for u in s['same_as'] if u in SHARED_LINKS]
        if shared:
            d['worksFor']['sameAs'] = shared
    else:
        raise BuildError(f"{c['name']}: unknown schema type {s['type']!r}")
    # The fees the profile publishes, as prices an answer engine can read. Rebates are not prices.
    offers = [{'@type': 'Offer', 'name': label, 'price': amount.lstrip('$').replace(',', ''), 'priceCurrency': 'AUD'}
              for amount, label in c['fees']['figures'] if 'rebate' not in label.lower()]
    if offers:
        d['makesOffer'] = offers
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
READ_MORE = ('<details class="group"><summary class="inline-flex items-center gap-3 min-h-11 cursor-pointer list-none '
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
    # `quote`: the line the clinician chose to lead their own practice bio with, word for word, set apart above About
    quote = (f'<blockquote class="m-0 pl-5 border-l-4 border-[#f1bc31] text-[20px] leading-[1.45] font-bold '
             f'tracking-tight text-[#1a1c1c] text-balance">“{esc(c["quote"])}”</blockquote>') if c.get('quote') else ''
    return quote + para(' '.join(lead)) + (READ_MORE.format('Read more', '<div class="mt-4 flex flex-col gap-4">'
                                                    + ''.join(para(t) for t in more) + '</div>') if more else '')


def pathway_html(c):
    """A GP's steps from booking to follow-up: how many appointments, what each is, what it costs."""
    if not c.get('pathway'):
        return ''
    steps = ''.join(f'<li class="py-3 border-b border-[#e8e6df] grid grid-cols-[2.25rem_1fr] gap-x-3">'
                    f'<span class="how-n" style="--tint:#fdf3d6; width:36px; height:36px; font-size:16px" aria-hidden="true">{i}</span>'
                    f'<div><strong class="block text-[17px] font-extrabold text-[#1a1c1c]">{esc(title)}</strong>'
                    f'<span class="block mt-1 text-[17px] text-[#2b2820] max-w-[58ch]">{esc(text)}</span></div></li>'
                    for i, (title, text) in enumerate(c['pathway'], 1))
    return SECTION.format('How it works', f'<ol class="lg:col-span-8 list-none p-0 m-0">{steps}</ol>') + '\n  '


def works_with_html(c):
    """How a GP's care joins up with psychologists, allied health and, for complex presentations, a psychiatrist."""
    if not c.get('works_with'):
        return ''
    para = lambda t: f'<p class="m-0">{esc(t)}</p>'
    body = READ_MORE.format('Psychologists, allied health and psychiatrists', '<div class="mt-4 flex flex-col gap-4">' + ''.join(para(t) for t in c['works_with']) + '</div>')
    return SECTION.format('Working with other clinicians', '<div class="lg:col-span-8 flex flex-col gap-4 text-[17px] leading-relaxed text-[#2b2820] max-w-[62ch]">' + body + '</div>') + '\n  '


def experience_html(c):
    item = lambda x: f'<li class="py-2.5 border-b border-[#e8e6df]">{esc(x)}</li>'
    shown = 3 if c.get('pathway') else EXPERIENCE_SHOWN   # a profile that opens with its steps shows less here
    cut = shown if len(c['experience']) > shown + 1 else len(c['experience'])
    shown, rest = c['experience'][:cut], c['experience'][cut:]
    html_ = '<ul class="list-none p-0 m-0">' + ''.join(item(x) for x in shown) + '</ul>'
    if rest:
        html_ += '<div class="mt-4">' + READ_MORE.format(f'Show {len(rest)} more', '<ul class="list-none p-0 m-0">'
                                                         + ''.join(item(x) for x in rest) + '</ul>') + '</div>'
    return html_


ICON_BUTTON = ('class="inline-flex items-center justify-center w-11 h-11 rounded-full text-[#1a1c1c] bg-[#f6f4ee] '
               'border border-[#e8e6df] hover:bg-white transition-colors" target="_blank" rel="noopener noreferrer"')


# The practice's website says so in words, with the practice's name, so it is plain that it leaves ADHDme for the
# clinic's own site. Instagram keeps its small round icon.
SITE_BUTTON = ('class="inline-flex items-center gap-2 min-h-11 py-2 px-5 rounded-full text-[15px] font-bold text-[#1a1c1c] '
               'bg-white border-2 border-[#1a1c1c] hover:bg-[#f6f4ee] transition-colors" target="_blank" rel="noopener noreferrer"')
EXTERNAL = ('<svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M9 7h8v8"/></svg>')


SITE_NAME = {'REACH ADHD Coaching and Consultancy': 'REACH'}   # the short name the practice goes by, for the button


def link_button(c, kind, label, href):
    aria = esc(LINK_ARIA[kind].format(practice=c['practice'], label=label))
    if kind == 'website':
        return (f'<a {SITE_BUTTON} href="{href}" aria-label="{aria}, opens in a new tab" title="{esc(label)}">'
                f'{ICONS[kind]}<span>{esc(SITE_NAME.get(c["practice"], c["practice"]))} website</span>{EXTERNAL}</a>')
    return f'<a {ICON_BUTTON} href="{href}" aria-label="{aria}" title="{esc(label)}">{ICONS[kind]}</a>'


def render_main(c, size, sizes):
    fees = c['fees']
    pills = ''
    if c['links']:
        pills = ('\n      <div class="flex flex-wrap gap-2 pt-1">'
                 + ''.join(link_button(c, kind, label, href) for kind, label, href in sorted(c['links'], key=lambda l: l[0] != 'website'))
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
<div class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pt-6"><a class="inline-flex items-center gap-2 h-11 text-[15px] font-bold text-[#1a1c1c]" href="{BOOK_HREF.format(c['id'])}">{ARROW_BACK}Back to the clinician network</a></div>
<article class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pt-6 pb-16">
<div class="rounded-3xl bg-white border border-[#e8e6df] p-6 sm:p-10 lg:p-14 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-start">
  <div class="lg:col-span-5 arrive" style="--i:0">{portrait_span(c, size, 'div', '', HERO_SIZES, 'fetchpriority="high" decoding="async"', 'w-full h-full object-cover object-[center_30%]')}</div>
  <div class="lg:col-span-7 flex flex-col gap-5">
    <h1 class="text-[36px] sm:text-[44px] lg:text-[52px] font-extrabold tracking-tight text-[#1a1c1c] leading-[1.02] arrive" style="--i:1">{esc(c['name'])}</h1>
    <p class="text-[15px] font-semibold text-[#5f5e59] arrive" style="--i:2">{meta_line_html(c)}</p>
    <p class="text-[19px] sm:text-[22px] font-medium leading-snug text-[#1a1c1c] max-w-[40ch] text-balance arrive" style="--i:3" data-declared-by="clinician">{esc(c['description'])}</p>
    <div class="flex flex-wrap gap-2 arrive" style="--i:4">{chip_row(c)}</div>
    <div class="flex flex-col items-start gap-3 pt-2 arrive" style="--i:5">
      <a class="btn-press inline-flex items-center gap-2 h-12 px-7 rounded-full bg-[#f1bc31] text-[#1a1c1c] text-[15px] font-bold hover:bg-[#e2ac24] transition-colors" href="{c['book_href']}" target="_blank" rel="noopener noreferrer">{book_verb(c)} with {esc(c['short'])} <span aria-hidden="true">→</span></a>
      <span class="text-[13px] text-[#5f5e59]">{esc(c['book_hint'])}</span>{pills}
    </div>
  </div>
</div>
<div class="mt-12 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16">
  {pathway_html(c)}{SECTION.format('Experience', '<div class="lg:col-span-8 text-[17px]" data-declared-by="clinician">' + experience_html(c) + '</div>')}
  {SECTION.format('About', '<div class="lg:col-span-8 flex flex-col gap-4 text-[17px] leading-relaxed text-[#2b2820] max-w-[62ch]" data-declared-by="clinician">' + about_html(c) + '</div>')}
  {works_with_html(c)}{SECTION.format('Details', '<dl class="lg:col-span-8 m-0">' + ''.join(DETAIL_ROW.format(esc(k), v) for k, v in details) + '</dl>')}
</div>
<section class="rounded-3xl bg-white border border-[#e8e6df] p-6 sm:p-10 mt-12 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-16" data-reveal aria-labelledby="fees-title">
  <h2 id="fees-title" class="lg:col-span-4 text-2xl font-extrabold tracking-tight text-[#1a1c1c]">{esc(fees['heading'])}</h2>
  <div class="lg:col-span-8 flex flex-col gap-5">{figures}
{chr(10).join(f'    <p class="text-[17px] text-[#2b2820] max-w-[62ch] text-balance">{note}</p>' for note in fees['notes'])}
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
    og_image, og_width, og_height = share_image(c, sizes[c['id']])
    tokens = {
        'NAME': c['name'], 'SLUG': c['slug'], 'ID': c['id'], 'SITE': SITE, 'EXPECT_ID': last['id'],
        'DESCRIPTION': meta_description(c), 'OG_TITLE': og_title(c), 'OG_IMAGE': og_image,
        'OG_WIDTH': str(og_width), 'OG_HEIGHT': str(og_height), 'OG_ALT': f'Portrait of {og_title(c)}',
    }
    page = shell
    for k, v in tokens.items():
        page = page.replace('{{' + k + '}}', esc(v))
    page = page.replace('{{MAIN}}', render_main(c, sizes[c['id']], sizes))
    page = page.replace('{{HERO_PRELOAD}}', f'<link rel="preload" as="image" href="{PORTRAITS}/{c["id"]}.webp" '
                        f'imagesrcset="{srcset(c, sizes[c["id"]], "webp")}" imagesizes="{HERO_SIZES}" type="image/webp" '
                        'fetchpriority="high">')
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
         'description': 'Browse Australia’s largest directory of holistic ADHD providers: GPs, psychiatrists, psychologists, allied health and coaches, many by telehealth.',
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
    # Pinned cards lead, then online diaries, then enquiry forms. Stable: CLINICIANS order holds within each group.
    ordered = sorted(CLINICIANS, key=lambda c: (c['id'] not in PINNED, not books_online(c)))
    # The first row of the panel shown on arrival is on the first screen, so its portraits load at once.
    first_row = [c['id'] for c in ordered if c['category'] == DEFAULT_PANEL][:DECK_COLUMNS]
    for category, panel in PANELS.items():
        members = [c for c in ordered if c['category'] == category]
        pat = re.compile(r'(<div role="tabpanel" aria-labelledby="tab-btn-' + panel + '" id="panel-' + panel + r'"[^>]*><ul[^>]*>\n)(.*?)(</ul></div>)', re.S)
        found = pat.findall(deck)
        if not members:
            continue
        if len(found) != 1:
            raise BuildError(f'the-doctors.html: panel "{panel}" needs exactly one <div role="tabpanel" id="panel-{panel}"><ul>…</ul></div> to hold '
                             f'{", ".join(c["name"] for c in members)}; found {len(found)}. Replace the "Expected soon" placeholder with '
                             '<div role="tabpanel" aria-labelledby="tab-btn-' + panel + '" id="panel-' + panel + '" class="hidden"><ul class="dir-list">\n</ul></div>')
        cards = '\n'.join(deck_card(c, sizes[c['id']], first_row.index(c['id']) if c['id'] in first_row else None)
                          for c in members) + '\n'
        deck = pat.sub(lambda m: m.group(1) + cards + m.group(3), deck, count=1)
    if '<!-- BEGIN:GENERATED deck-ld -->' not in deck:
        deck = deck.replace('</main>', '<!-- BEGIN:GENERATED deck-ld --><!-- END:GENERATED deck-ld -->\n</main>', 1)
    return region(deck, 'deck-ld', deck_jsonld(), 'the-doctors.html')


def region(page, name, body, where):
    """Replace the contents of one <!-- BEGIN:GENERATED name --> … <!-- END:GENERATED name --> region."""
    start, end = f'<!-- BEGIN:GENERATED {name} -->', f'<!-- END:GENERATED {name} -->'
    i, j = page.find(start), page.find(end)
    if i < 0 or j < 0 or j < i:
        raise BuildError(f'{where}: no <!-- BEGIN:GENERATED {name} --> … <!-- END:GENERATED {name} --> region to fill')
    if page.find(start, i + 1) >= 0 or page.find(end, j + 1) >= 0:
        raise BuildError(f'{where}: the "{name}" region is marked more than once')
    return page[:i + len(start)] + body + page[j:]


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
    if problems:
        raise BuildError('\n  '.join(['fix these first:'] + problems))


def build():
    check_data()
    sizes = {c['id']: portrait_size(c) for c in CLINICIANS}
    shell = SHELL.read_text(encoding='utf-8')
    out = {ROOT / f"{c['slug']}.html": render_page(c, shell, sizes) for c in CLINICIANS}
    out[DECK] = render_deck(DECK.read_text(encoding='utf-8'), sizes)
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
