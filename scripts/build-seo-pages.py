#!/usr/bin/env python3
"""Build the search-landing pages: one page per high-intent query (ADHD doctor Gold Coast, ADHD GP
Brisbane, ADHD psychologist, and so on) plus the adhd-services.html index that links them.

    python3 scripts/build-seo-pages.py          # write the pages
    python3 scripts/build-seo-pages.py --check  # exit 1 if any page on disk differs from what would be written

Owns: every page in PAGES, in full, and adhd-services.html. A hand edit to any of them is lost on the
next build; put the change here instead, and run --check before committing.

These pages are deliberately out of the way. They are not in the header or the mobile menu; the only
route to them from the rest of the site is the small "ADHD care near you" link in every footer, which
points at adhd-services.html. They exist for somebody arriving from a search, so each one answers its
query in the first screen, says plainly what the network does and does not have for that query today,
and then hands over to the profiles. The clinician lists come from CLINICIANS in build-profiles.py, so a
page cannot promise a clinician the network does not have, and the fee figures are the same constants
the profiles use.

The page shell (head, header, footer) is lifted from how-it-works.html at build time and rewritten,
the way build-blog.py lifts Our Story's, so the pages pick up header and footer changes on rebuild.
"""
import html
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://www.adhdme.au'
SHELL = ROOT / 'how-it-works.html'
HUB = 'adhd-services'

spec = importlib.util.spec_from_file_location('profiles', ROOT / 'scripts' / 'build-profiles.py')
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)
CLINICIANS = profiles.CLINICIANS


def esc(text):
    return html.escape(text, quote=True)


# ---------------------------------------------------------------- selectors
# Each page names the clinicians it can honestly point at. The filters read the same fields the
# profiles are built from, so a page follows the data when a clinician joins or moves.
def state(c):
    s = c['schema']
    return s.get('state') or s.get('works_for', {}).get('state')


def gps(c): return c['category'] == 'gp'
def gps_remote(c): return gps(c) and c['telehealth']
def psychologists(c): return c['category'] == 'psychologist'
def qld_psychologists(c): return psychologists(c) and state(c) == 'QLD'
def qld_allied(c): return c['category'] == 'allied' and state(c) == 'QLD'
def locality(c): return c['schema'].get('works_for', {}).get('locality')
def brisbane_psychologists(c): return psychologists(c) and locality(c) in ('Fortitude Valley', 'Ashgrove')
def brisbane_allied(c): return c['category'] == 'allied' and locality(c) == 'Fortitude Valley'
def gold_coast(c): return locality(c) == 'Bundall'
def exercise_physiologists(c): return 'Exercise Physiologist' in c['role']
def occupational_therapists(c): return 'Occupational' in c['role']
def coaches(c): return c['category'] == 'coach'
def telehealth_clinical(c): return c['telehealth'] and c['category'] in ('gp', 'psychologist', 'allied')
def nsw_clinical(c): return state(c) == 'NSW' and c['category'] in ('gp', 'psychologist')
def any_of(*fs): return lambda c: any(f(c) for f in fs)


# ---------------------------------------------------------------- shared copy
GP_FEE = profiles.GP_FEES['figures']            # [('$299', 'Initial consultation'), ('$199', 'Follow-up consultation')]
GP_TOTAL = '$498'
REBATE_REG, REBATE_CLIN = profiles.MBS_REBATE_REGISTERED, profiles.MBS_REBATE_CLINICAL
JOBACCESS = '$1,770.44'
assert GP_TOTAL in profiles.GP_FEES['notes'][0]
assert JOBACCESS in profiles.REACH_FEES['notes'][1]

PROFILE = 'the-doctors.html'
GP_PANEL = 'the-doctors.html#panel-gps'
PSY_PANEL = 'the-doctors.html#panel-psychologists'
ALLIED_PANEL = 'the-doctors.html#panel-allied-health'
COACH_PANEL = 'the-doctors.html#panel-coaches'


def a(text, href):
    ext = ' target="_blank" rel="noopener noreferrer"' if href.startswith('http') else ''
    return (f'<a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" '
            f'href="{href}"{ext}>{text}</a>')


GP_COST_PARA = (f'A GP assessment through the network is <strong>{GP_FEE[0][0]} for the first consultation and {GP_FEE[1][0]} '
                f'for the follow-up, {GP_TOTAL} in total</strong>. The two together are the assessment and the diagnosis. '
                f'There is no Medicare rebate on either. The practice sets and charges the fee, and ADHDme receives no part of it.')
PSY_COST_PARA = (f'Each psychologist sets their own fee, and it is on their profile. With a Mental Health Treatment Plan '
                 f'from a GP, Medicare pays part of up to 10 sessions a year: {REBATE_REG} a session for a registered '
                 f'psychologist and {REBATE_CLIN} for a clinical psychologist, at the current rates.')
QLD_RULE = ('Queensland changed its rules on 1 December 2025. A specialist GP, meaning one with FRACGP or FACRRM '
            'fellowship, can now diagnose ADHD in an adult and start, adjust and continue stimulant medication without '
            'a psychiatrist signing off first.')
QLD_GP_PARA = (QLD_RULE + ' Queensland GPs have been able to prescribe for children since 2017. '
               'A GP who practises in another state works under that state’s rules, so ask the practice what applies to you.')
NSW_RULE = ('NSW is changing its rules in stages. Since September 2025, GPs who have completed the state’s training '
            'can continue stimulant prescriptions that a psychiatrist started, for a patient who is stable on treatment.')
NSW_STAGE_TWO = ('A second stage, in which trained GPs assess, diagnose and start medication themselves, is rolling out '
                 'through 2026.')
NSW_GP_PARA = (NSW_RULE + ' ' + NSW_STAGE_TWO + ' What a given GP can do on the day depends on where they are in that '
               'process, so the honest answer is on the practice’s own page, and in the first conversation.')
WHAT_ASSESSMENT = [
    'A history that goes back to childhood, because ADHD is a developmental condition and the pattern has to have been there early, even if nobody named it.',
    'Rating scales, filled in by you and where possible by somebody who knew you as a child or knows you now.',
    'A look at what else could explain the picture: sleep, mood, anxiety, thyroid, substance use, and the rest of your health.',
    'A baseline before any medication: heart rate, blood pressure, weight, and the questions that decide whether a stimulant is safe for you.',
    'A plan, in writing, with a review date. The Australian guideline asks for review at set intervals rather than only when something goes wrong.',
]

# ---------------------------------------------------------------- pages
# title: the h1. seo: <title>, og:title, twitter:title (no trailing full stop). description: meta and
# share-card description. lede: the paragraph under the h1. who: which clinicians to list, with a
# heading and a plain note about what that list is and is not. sections: (h2, [paragraph html, or
# ('list', [items])]). faqs: (question, answer) pairs, also emitted as FAQPage JSON-LD.
PAGES = [
 dict(slug='adhd-doctor-gold-coast', group='place',
      seo='ADHD doctor on the Gold Coast: who to see, and what it costs',
      title='ADHD doctor on the Gold Coast: who to see, and what it costs.',
      description='Clinical psychologists and an exercise physiologist with rooms in Bundall, a GP assessment by phone, and Brisbane clinics an hour up the M1. What each can do for ADHD on the Gold Coast, stated plainly.',
      lede='The Gold Coast now has ADHDme clinicians in the room: a psychology and exercise physiology team at Atlantis Recovery Centre in Bundall. What it does not have yet is a GP who prescribes, so this page says who does what, where the assessment comes from, and what it costs.',
      who=[gold_coast, gps_remote, qld_psychologists], who_heading='Who a Gold Coast patient can see',
      who_note='The Bundall team sees people in their rooms. Both GPs are Sydney-based and see people remotely. The Brisbane psychologists have rooms in Fortitude Valley and Ashgrove and also work by telehealth.',
      sections=[
       ('In the room, in Bundall', [
        f'{a("Atlantis Recovery Centre", "bart-traynor.html")} is an allied-health centre at 25 Upton Street, Bundall, with clinical psychologists, a provisional psychologist, an exercise physiologist and physiotherapists under one roof. The practice says its model, which blends therapy with movement-based work, suits ADHD, anxiety and trauma, and that each psychology journey starts with a comprehensive assessment. Booking is on the practice’s HotDoc page, in a new tab, with no referral and no account.',
        'A psychologist can assess ADHD and treat it with therapy, but cannot prescribe. The practice publishes no fee; it quotes one when you book, and works with DVA, the NDIS, private health funds, WorkCover, and GP Mental Health Treatment Plans.']),
       ('A GP assessment by phone', [
        f'The network’s GPs are in Sydney, and both see people remotely: {a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} by phone consultation and {a("Dr Anu Saxena", "dr-anu-saxena.html")} by telehealth, so a Gold Coast patient can start with either without travelling. Whether the whole assessment can be done remotely, and what has to happen in person, is the practice’s call, so ask when you book.',
        GP_COST_PARA,
        'One thing to know about medication. ' + QLD_GP_PARA]),
       ('Psychologists an hour up the M1', [
        f'GOALS Psychology is in Fortitude Valley, with level access from the car park and an hour of free client parking, and Neutral Minds Psychology is in Ashgrove. Two of the GOALS psychologists, {a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")}, do formal ADHD and autism assessment with a written report; every psychologist at both clinics also sees people by telehealth.',
        PSY_COST_PARA]),
       ('After the diagnosis', [
        f'Diagnosis is the start, not the end. The {a("treatment after diagnosis", "adhd-treatment-after-diagnosis.html")} page walks through what usually follows: medication and its reviews, therapy, occupational therapy for daily life, coaching, and the parts you can do yourself. On the Gold Coast, {a("Sarah Savage", "sarah-savage.html")} covers the exercise part in person.']),
      ],
      faqs=[
       ('Is there an ADHD doctor on the Gold Coast in the ADHDme network?', 'Psychologists and an exercise physiologist, yes, at Atlantis Recovery Centre in Bundall. A GP who assesses and prescribes, not yet on the Gold Coast; the network’s two GPs both see people remotely from Sydney.'),
       ('Can a GP diagnose ADHD in Queensland?', 'Yes. Since 1 December 2025 a specialist GP in Queensland can diagnose ADHD in an adult and prescribe stimulant medication. GPs have been able to prescribe for children in Queensland since 2017.'),
       ('Do I need a referral?', 'No. Every clinician on ADHDme is booked or enquired with directly, on the practice’s own page. A GP will write a Mental Health Treatment Plan if you want Medicare to pay part of psychology sessions.'),
       ('What does it cost on the Gold Coast?', f'Atlantis Recovery Centre quotes its fee when you book and accepts DVA, NDIS, private health, WorkCover and Medicare plans. The GP assessment by phone is {GP_TOTAL} in total across two consultations, with no Medicare rebate.'),
       ('Does the Gold Coast clinic offer telehealth?', 'It has not declared telehealth, so the profiles do not claim it. The Brisbane psychologists and the Sydney GP do.'),
      ],
      related=['adhd-gp-brisbane', 'adhd-assessment-queensland', 'adhd-psychologist-brisbane', 'adhd-exercise-physiologist']),

 dict(slug='adhd-gp-brisbane', group='place',
      seo='ADHD GP in Brisbane: assessment without the psychiatrist wait',
      title='ADHD GP in Brisbane: assessment without the psychiatrist wait.',
      description='Queensland GPs can now diagnose and treat adult ADHD. What that means in Brisbane, who in the ADHDme network sees Brisbane patients, and what it costs.',
      lede='Queensland is the first state to let a GP diagnose adult ADHD and prescribe for it. That changes what a Brisbane search for an ADHD GP can find. Here is where the ADHDme network stands today, stated plainly.',
      who=any_of(gps_remote, brisbane_psychologists, brisbane_allied), who_heading='Who sees Brisbane patients today',
      who_note='Both GPs are in Sydney and see people remotely; no Brisbane GP has joined the network yet. The psychologists and the occupational therapist have rooms in Fortitude Valley and Ashgrove.',
      sections=[
       ('What a Queensland GP can now do', [
        QLD_GP_PARA,
        'For a Brisbane patient this removes the step that used to take longest: waiting months for a psychiatrist to confirm what a GP had already seen. It does not remove the assessment itself. A good GP assessment is still a long first appointment, a baseline, and a review.']),
       ('The GPs in the network, and where they are', [
        f'ADHDme’s two GPs both practise in Sydney, and both see people remotely: {a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} by phone consultation and {a("Dr Anu Saxena", "dr-anu-saxena.html")} by telehealth, so a Brisbane patient can start with either without travelling. A NSW GP works under NSW rules on medication, which are moving in stages through 2026, so ask the practice what can be started by phone and what cannot.',
        'Brisbane GPs will be listed here as they join. The network grows by clinicians declaring how they work rather than by ADHDme signing them up in bulk, which is slower and the reason the list is honest.']),
       ('What the assessment involves', [('list', WHAT_ASSESSMENT)]),
       ('What it costs', [
        GP_COST_PARA,
        PSY_COST_PARA]),
       ('Psychologist assessment in Brisbane', [
        f'If what you want is a formal assessment rather than medication, two Brisbane psychologists in the network do ADHD and autism assessment in the room: {a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")}, both at GOALS Psychology in Fortitude Valley. A psychologist’s report can also be what a GP works from when medication is considered later.']),
      ],
      faqs=[
       ('Can a GP in Brisbane prescribe ADHD medication for adults?', 'Yes, since 1 December 2025, if the GP holds FRACGP or FACRRM fellowship. They can diagnose, start medication, adjust it and continue it. Whether a particular practice offers this is up to the practice.'),
       ('Does ADHDme have a Brisbane GP?', 'Not yet. The network’s two GPs are in Sydney and both see people remotely. Brisbane psychologists and an occupational therapist are in the network now.'),
       ('Do I need a referral to see an ADHD GP?', 'No. A GP is booked directly. A referral is only needed for a psychiatrist, which is exactly the step Queensland’s reform lets a GP replace for many adults.'),
       ('How long does an ADHD assessment take with a GP?', 'Two appointments in the network’s model: a long first consultation and a follow-up. Some people need an extra 30-minute clinical review where more history or records are needed, and the practice explains the cost of that before it is booked.'),
      ],
      related=['adhd-assessment-queensland', 'adhd-doctor-gold-coast', 'adhd-psychologist-brisbane', 'adhd-assessment-online']),

 dict(slug='adhd-assessment-queensland', group='place',
      seo='ADHD assessment in Queensland: the three routes, and what each costs',
      title='ADHD assessment in Queensland: the three routes, and what each costs.',
      description='GP, psychologist or psychiatrist: how ADHD assessment works in Queensland after the 2025 reform, what it involves, what it costs, and who in the ADHDme network sees Queensland patients.',
      lede='Queensland now has three routes to an ADHD diagnosis: a GP, a psychologist, or a psychiatrist. They differ in what they can do afterwards, how long they take and what they cost. This page sets the three side by side and says which of them the ADHDme network can offer a Queensland patient today.',
      who_heading='Who sees Queensland patients today',
      who=[gps_remote, qld_psychologists, qld_allied], who_note='In-person rooms are in Brisbane and, at Atlantis Recovery Centre, in Bundall on the Gold Coast. The Brisbane clinicians and the GP also work by phone or telehealth, which is how the rest of the state reaches them for now. Cairns and Townsville are on the network’s planned list.',
      sections=[
       ('Route one: a GP', [
        QLD_GP_PARA,
        f'In the network, {a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} takes phone consultations and {a("Dr Anu Saxena", "dr-anu-saxena.html")} works by telehealth, both from Sydney. They work under NSW rules on medication; the assessment itself does not depend on which state you are in. ' + GP_COST_PARA]),
       ('Route two: a psychologist', [
        f'A psychologist can assess and diagnose ADHD, and treat it with therapy, but cannot prescribe. In Brisbane, {a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")} at GOALS Psychology do ADHD and autism assessment, in the room in Fortitude Valley or by telehealth. A psychologist’s assessment report is often what a GP or psychiatrist then works from. On the Gold Coast, the clinical psychologists at {a("Atlantis Recovery Centre", "bart-traynor.html")} in Bundall start every psychology journey with a comprehensive assessment; the practice says its model suits ADHD.',
        PSY_COST_PARA]),
       ('Route three: a psychiatrist', [
        'A psychiatrist needs a GP referral, and in Queensland the wait for a first appointment is commonly months and the fee commonly several hundred dollars above the Medicare rebate. ADHDme does not list psychiatrists. The 2025 reform exists because, for many adults, the psychiatrist step added waiting without adding much to what a well-trained GP could see.',
        'A psychiatrist is still the right route where the picture is complicated: another serious mental illness alongside, a history that makes stimulants risky, or a child under the age a GP is allowed to treat.']),
       ('What an assessment involves, whichever route', [('list', WHAT_ASSESSMENT)]),
       ('Outside Brisbane', [
        'Every clinician in the network who sees Queensland patients also works by phone or telehealth, so a patient in Cairns, Townsville, Toowoomba or the Sunshine Coast can start today. The parts of an assessment that need a room, such as a physical baseline before medication, can often be done by your own local GP with the assessing clinician’s letter; ask the practice how they handle it.',
        f'For telehealth in detail, see {a("ADHD assessment online", "adhd-assessment-online.html")}.']),
      ],
      faqs=[
       ('Can a GP diagnose ADHD in Queensland?', 'Yes, since 1 December 2025, for adults, if the GP holds FRACGP or FACRRM fellowship. For children, Queensland GPs have prescribed since 2017.'),
       ('How much does an ADHD assessment cost in Queensland?', f'Through the network’s GP model, {GP_TOTAL} across two consultations, no Medicare rebate. A psychologist’s assessment is priced by the psychologist and shown on their profile. A private psychiatrist is usually the most expensive route, and the one with the longest wait.'),
       ('Do I need a referral for an ADHD assessment?', 'Not for a GP or a psychologist. Only a psychiatrist needs a GP referral.'),
       ('Can I be assessed by telehealth in Queensland?', 'Yes. Both of the network’s GPs see people remotely, and every listed psychologist works by telehealth. The practice will tell you which parts, if any, need to happen in person.'),
       ('What happens after the diagnosis?', 'Treatment is chosen with you: medication with a prescriber, therapy with a psychologist, occupational therapy for daily life, coaching, and the parts you can do yourself. The treatment after diagnosis page sets it out.'),
      ],
      related=['adhd-gp-brisbane', 'adhd-doctor-gold-coast', 'adhd-assessment-online', 'adhd-treatment-after-diagnosis']),

 dict(slug='adhd-assessment-sydney', group='place',
      seo='ADHD assessment in Sydney with a GP: $498, no referral',
      title='ADHD assessment in Sydney with a GP: no referral, no waitlist to join.',
      description=f'Two Sydney GPs assess and diagnose ADHD in Beecroft, Double Bay and Hornsby. {GP_TOTAL} across two consultations, booked on the practice’s own page. Where NSW GP prescribing stands in 2026.',
      lede='Two GPs in the ADHDme network assess ADHD in Sydney, in Beecroft, Double Bay and Hornsby. The fee is published before you book, and booking is on the practice’s own page. This page says what the assessment involves, what it costs, and what NSW’s changing rules mean for medication afterwards.',
      who=nsw_clinical, who_heading='ADHD clinicians in Sydney',
      who_note='The two GPs assess and diagnose. Paula Garrido is a Sydney-based clinical psychologist who works by telehealth only.',
      sections=[
       ('The two GPs, and where they are', [
        f'{a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} works at Beecroft Family &amp; Skin Cancer Clinic, in Beecroft and Double Bay, and takes phone consultations. His assessment starts from a documented physical baseline and looks at ADHD alongside sleep, cardiovascular and metabolic health rather than on its own.',
        f'{a("Dr Anu Saxena", "dr-anu-saxena.html")} works at Bay Health Clinic in Double Bay and Hornsby, and by telehealth. She came to medicine through psychology, has completed an endorsed ADHD prescriber course, and speaks Hindi and Urdu as well as English.',
        'Both are booked on Healthengine, the practice’s own diary, in a new tab. Both have declared a commercial or personal connection with ADHDme, which is stated on each profile.']),
       ('What it costs', [GP_COST_PARA,
        'Some people need an additional 30-minute clinical review where further history, records or a medical assessment are needed. If that applies to you, the practice explains why and discusses the cost before it is booked.']),
       ('What the assessment involves', [('list', WHAT_ASSESSMENT)]),
       ('Medication in NSW, in 2026', [
        NSW_GP_PARA,
        'Whatever the rules allow on the day, the network’s GPs work the same way: a baseline before anything starts, a documented plan, and review at set intervals.']),
       ('Therapy alongside', [
        f'{a("Paula Garrido", "paula-garrido.html")} is a Sydney-based clinical psychologist working entirely by telehealth, certified in ADHD and autism clinical services, with a neuroaffirming and trauma-informed approach. ' + PSY_COST_PARA]),
      ],
      faqs=[
       ('Can a GP diagnose ADHD in NSW?', 'NSW is introducing this in stages. Trained GPs have continued existing stimulant prescriptions since September 2025, and the stage in which trained GPs assess, diagnose and start medication is rolling out through 2026. The GPs in the network assess ADHD now; ask the practice what they can prescribe on the day.'),
       ('How much is an ADHD assessment in Sydney?', f'{GP_FEE[0][0]} for the first consultation and {GP_FEE[1][0]} for the follow-up, {GP_TOTAL} in total, with no Medicare rebate. The practice sets and charges the fee.'),
       ('Do I need a referral?', 'No. Both GPs are booked directly on their practice’s Healthengine page.'),
       ('Where in Sydney?', 'Beecroft and Double Bay (Dr Anubhav Saxena), and Double Bay and Hornsby (Dr Anu Saxena). Both also see people remotely: phone consultations with Dr Anubhav Saxena, telehealth with Dr Anu Saxena.'),
      ],
      related=['adhd-assessment-online', 'adhd-treatment-after-diagnosis', 'adhd-psychologist', 'adhd-assessment-queensland']),

 dict(slug='adhd-assessment-online', group='place',
      seo='ADHD assessment online in Australia: what telehealth can and cannot do',
      title='ADHD assessment online: what telehealth can and cannot do.',
      description='A GP assessment by phone and psychologists by telehealth, Australia-wide, with published fees and no referral. What can be done on a screen, what needs a room, and how state rules on medication apply.',
      lede='Most of an ADHD assessment is a conversation, and a conversation travels. In the ADHDme network both GPs see people remotely and every psychologist works by telehealth, so a patient anywhere in Australia can start this week. Some parts still need a room. This page says which.',
      who=telehealth_clinical, who_heading='Who works by phone or telehealth',
      who_note='Everybody listed has declared remote appointments. The telehealth marker on each profile is set from what the clinician actually declares, not assumed.',
      sections=[
       ('What can be done remotely', [
        'The developmental history, the rating scales, the conversation about what else could explain the picture, and the diagnosis itself can all be done by phone or video. So can therapy, which is why every psychologist in the network offers it.',
        f'Booking is the same as in person: the profile’s button opens the practice’s own diary or enquiry form in a new tab, with no account and no referral. ' + GP_COST_PARA]),
       ('What needs a room', [
        'A physical baseline before medication: heart rate, blood pressure, weight, and anything the history raises. Some practices ask your own local GP to do this and send the numbers; some ask you to come in once. Ask the practice how they handle it before you book, so there is no surprise.',
        'Medication itself. Stimulant prescribing is regulated state by state, and a prescriber works under the rules of the state they practise in. ' + QLD_RULE + ' ' + NSW_RULE + ' ' + NSW_STAGE_TWO + ' The practice will tell you what can be started remotely and what cannot.']),
       ('Therapy by telehealth', [
        f'Every psychologist in Brisbane and every online-only one works by telehealth. {a("Paula Garrido", "paula-garrido.html")}’s clinic is online only. The Brisbane clinics see people either way. ' + PSY_COST_PARA,
        'A Mental Health Treatment Plan can be written by any GP, including your own local one, and the telehealth psychologist claims against it the same way.']),
       ('Choosing a clinician you will never meet in person', [
        'Read the profile the way you would read a person. Each one is the clinician’s own account of how they work, who they see, what they focus on and what they charge, in their words. The chips under each name on The Network page are the quickest filter: neuroaffirming, trauma-informed, assessment, children, adults.']),
      ],
      faqs=[
       ('Can ADHD be diagnosed online in Australia?', 'Yes. The history, rating scales and diagnostic conversation can be done by phone or video. A physical baseline before medication is usually done in person, by the assessing practice or your local GP.'),
       ('Can I get ADHD medication through telehealth?', 'It depends on the state the prescriber practises in and, in some cases, the state you live in. Queensland allows specialist GPs to start adult stimulant medication; NSW is phasing it in through 2026. The practice tells you what applies.'),
       ('Is telehealth psychology covered by Medicare?', 'Yes, under a Mental Health Treatment Plan, at the same rebate as in-person sessions, for up to 10 sessions a year.'),
       ('Do I need a referral for a telehealth ADHD assessment?', 'No. Every clinician on ADHDme is booked or enquired with directly.'),
      ],
      related=['adhd-assessment-queensland', 'adhd-assessment-sydney', 'adhd-psychologist', 'adhd-treatment-after-diagnosis']),

 dict(slug='adhd-treatment-after-diagnosis', group='after',
      seo='ADHD treatment after diagnosis: what actually happens next',
      title='ADHD treatment after diagnosis: what actually happens next.',
      description='Medication and its reviews, therapy, occupational therapy, coaching, and the parts you can do yourself. What each one is for, who provides it, what it costs, and how they fit together.',
      lede='A diagnosis answers one question and opens several. This page is the map of what usually follows, in the order most people meet it, with who provides each part in the ADHDme network and what it costs. None of it is compulsory and none of it has to happen at once.',
      who=None, who_heading=None, who_note=None,
      sections=[
       ('Medication, and the reviews that go with it', [
        'For most adults the Australian guideline names stimulant medication, methylphenidate or lisdexamfetamine, as first-line treatment, with non-stimulants where a stimulant is unsuitable or not tolerated. The decision is made with a prescriber, not by a page, and the first weeks are about finding the dose and the timing that fit your day.',
        'What good prescribing looks like: a baseline before the first dose, a review at set intervals rather than only when something goes wrong, and someone checking heart rate, blood pressure, sleep, appetite and weight as it goes. Who can prescribe depends on the state: ' + QLD_RULE + ' ' + NSW_RULE + ' ' + NSW_STAGE_TWO,
        f'In the network, medication questions sit with the {a("GPs", GP_PANEL)}.']),
       ('Therapy with a psychologist', [
        'Medication changes attention. It does not, on its own, undo years of workarounds, or the anxiety, low mood and shame that commonly travel with a late diagnosis. That is what therapy is for. Cognitive behavioural therapy adapted for ADHD, acceptance and commitment therapy and dialectical behaviour therapy skills all have a place, and the psychologists in the network name which they use.',
        PSY_COST_PARA + f' The {a("psychologists", PSY_PANEL)} in the network are in Brisbane and by telehealth Australia-wide.']),
       ('Occupational therapy for daily life', [
        f'Where the difficulty is the mechanics of the day, mornings, routines, a home or a classroom that does not work, an occupational therapist looks at the environment and the task rather than the person. In the network, {a("Flynn Simonis", "flynn-simonis.html")} does this for children in Brisbane, in clinic, at home or at school. Fees are quoted by the clinic; a Mental Health Treatment Plan does not cover OT, but the NDIS, private health extras and a GP’s chronic condition management plan commonly do.']),
       ('Coaching', [
        f'Coaching is not therapy and not treatment. It is practical work on executive function: starting, planning, finishing, and building the systems that make those easier. The {a("coaches", COACH_PANEL)} in the network are in Perth and online, and coaching can be government-funded through JobAccess for anyone working at least eight hours a week, at around {JOBACCESS} a year by the practice’s own figure. The {a("ADHD coaching", "adhd-coach.html")} page has the detail.']),
       ('The parts you can do yourself', [
        'Three things have better evidence than any supplement. Twenty to thirty minutes of moderate aerobic exercise gives a small to moderate lift in attention for about an hour afterwards, so it is worth placing directly before demanding work. A regular sleep and wake time matters more on a stimulant, not less. And regular meals, planned around the appetite dip a stimulant causes through the middle of the day, protect weight and mood.',
        f'On exercise specifically, including safety on stimulant medication, see {a("ADHD and exercise physiology", "adhd-exercise-physiologist.html")}. On the Gold Coast, {a("Sarah Savage", "sarah-savage.html")} does this work in person.']),
       ('How the pieces fit', [
        'Nobody needs all of this. A common shape is: medication with a GP, six to ten sessions with a psychologist in the first year, and one or two of the self-directed parts. Some people never take medication and do well with therapy and coaching. The order is yours, and the profiles are there so you can read each clinician before you decide anything.']),
      ],
      faqs=[
       ('What is the first-line treatment for adult ADHD in Australia?', 'The Australian guideline names stimulant medication as first-line for most adults, alongside psychoeducation, with non-stimulants where a stimulant is unsuitable. Therapy, occupational therapy and coaching address what medication does not.'),
       ('Do I have to take medication after an ADHD diagnosis?', 'No. It is a decision made with a prescriber, and some people choose therapy, coaching and lifestyle changes instead or first.'),
       ('How often are reviews after starting ADHD medication?', 'Frequently at first while the dose is found, then at set intervals. The Australian guideline asks for scheduled review rather than review only when a problem appears.'),
       ('Does Medicare cover ADHD treatment?', f'Partly. Psychology under a Mental Health Treatment Plan attracts a rebate of {REBATE_REG} or {REBATE_CLIN} a session for up to 10 sessions a year. GP consultations for ADHD in the network are private, with no rebate. OT and coaching have their own funding routes.'),
      ],
      related=['adhd-psychologist', 'adhd-occupational-therapist', 'adhd-coach', 'adhd-exercise-physiologist']),

 dict(slug='adhd-exercise-physiologist', group='profession',
      seo='ADHD exercise physiologist: what exercise can do, and how to fund it',
      title='ADHD and exercise physiology: what exercise can do, and how to fund it.',
      description='What an exercise physiologist does for ADHD, what the evidence supports, why stimulant medication changes the safety rules, and how a GP care plan can fund sessions. Exercise physiology on the Gold Coast in the ADHDme network.',
      lede='Exercise has a real, measurable effect on attention, and stimulant medication changes how exercise should be prescribed. An exercise physiologist is the clinician who knows both. The network has one, on the Gold Coast; this page says what to look for anywhere, and what to ask your GP.',
      who=exercise_physiologists, who_heading='Exercise physiology in the network',
      who_note='In the room at Atlantis Recovery Centre in Bundall, on the Gold Coast. The practice quotes its fee when you book.',
      sections=[
       ('What the evidence supports', [
        'Twenty to thirty minutes of moderate aerobic exercise gives a small to moderate lift in attention and executive function for about an hour afterwards. Placed directly before a study block or a demanding piece of work, that hour is useful. Aerobic exercise has the best support; mind-body exercise shows a small effect; there are too few studies of coordinative exercise to say.',
        'Exercise is an addition to treatment, not a replacement for it. Its effect is modest and short-lived, and the medication decision stays with the prescriber.']),
       ('Why stimulants change the prescription', [
        'Stimulants raise resting heart rate, so age-predicted heart-rate zones overstate effort and a good exercise physiologist prescribes by perceived exertion and the talk test instead. Appetite suppression means many people arrive under-fuelled. Pre-workout caffeine adds to the stimulant’s effect on heart rate and blood pressure and should be dropped.',
        'Chest pain, fainting, sustained palpitations or unusual breathlessness on a stimulant mean stop and see a doctor. An exercise physiologist who works with ADHD should ask for your medication list, including the time you take it, and record resting heart rate and blood pressure at the start.']),
       ('Designing exercise that lasts', [
        'Dropout is an executive-function problem, not a motivation problem, so the design matters more than the program. Short sessions, a fixed time, low set-up, variety, immediate feedback and somebody expecting you all help. A minimum session you can always do, and a rule of never missing twice, does more than an ambitious plan.']),
       ('How to fund it', [
        'An exercise physiologist can be seen under a GP’s chronic condition management plan, which gives a partial Medicare rebate on up to five allied health sessions a calendar year, shared across all allied health. Whether ADHD qualifies as the chronic condition on the plan is the GP’s call; it is a lifelong condition, so ask. The NDIS, DVA and private health extras are the other common routes, and all three are accepted at the Gold Coast practice.',
        f'For an exercise physiologist elsewhere, ESSA’s public directory lists accredited exercise physiologists by suburb: {a("essa.org.au", "https://www.essa.org.au/")}. The {a("GPs", GP_PANEL)} in the network can write the plan.']),
       ('In the network', [
        f'{a("Sarah Savage", "sarah-savage.html")} is the senior exercise physiologist at Atlantis Recovery Centre in Bundall, working from an “exercise as medicine” approach with Pilates, Functional Range Conditioning and hydrotherapy, and a particular interest in older adults. Her profile is her own account of how she works. The practice publishes no fee and quotes one when you book.']),
      ],
      faqs=[
       ('Can exercise replace ADHD medication?', 'No. It gives a modest lift in attention for about an hour after a session. It is an addition to treatment; medication decisions are for your prescriber.'),
       ('Is exercise physiology covered by Medicare for ADHD?', 'It can be, under a GP chronic condition management plan, with a partial rebate on up to five allied health sessions a year. The GP decides whether ADHD is the qualifying condition on the plan.'),
       ('Is it safe to exercise on stimulant medication?', 'For most people, yes, with adjustments: prescribe by effort rather than heart-rate zones, eat before training, drop caffeine pre-workouts, and stop and see a doctor for chest pain, fainting or sustained palpitations.'),
       ('Does ADHDme have an exercise physiologist?', 'Yes, one: Sarah Savage at Atlantis Recovery Centre in Bundall, on the Gold Coast. For anywhere else, ESSA’s directory lists accredited exercise physiologists near you.'),
      ],
      related=['adhd-treatment-after-diagnosis', 'adhd-doctor-gold-coast', 'adhd-coach', 'adhd-occupational-therapist']),

 dict(slug='adhd-psychologist', group='profession',
      seo='ADHD psychologist: assessment and therapy, in Brisbane, on the Gold Coast or by telehealth',
      title='ADHD psychologist: assessment and therapy, in Brisbane, on the Gold Coast or by telehealth.',
      description='What an ADHD psychologist does and does not do, how the Medicare rebate works, and the psychologists in the ADHDme network, each with their own account of how they work and what they charge.',
      lede='A psychologist can assess ADHD, diagnose it, and treat it with therapy. A psychologist cannot prescribe. Knowing that one line saves a lot of people a wrong first appointment. The rest of this page is what an ADHD psychologist actually does, what it costs, and who in the network does it.',
      who=psychologists, who_heading='The psychologists in the network',
      who_note='Rooms in Brisbane and on the Gold Coast, and one clinic that is online only. The Brisbane and online psychologists work by telehealth; the Gold Coast clinic has not declared it. Each profile is the psychologist’s own account of their work and fees.',
      sections=[
       ('What an ADHD psychologist does', [
        'Assessment: a developmental history, rating scales, sometimes cognitive testing, and a written report. Some psychologists in the network do this, and their profiles say so.',
        'Therapy: cognitive behavioural therapy adapted for ADHD, acceptance and commitment therapy, dialectical behaviour therapy skills, and the work that a late diagnosis often needs on shame, anxiety and low mood. Each psychologist names their approaches on their profile.',
        'Not medication. A psychologist does not prescribe. If medication is part of what you want, the psychologist works alongside a GP or psychiatrist rather than instead of one.']),
       ('Psychologist, clinical psychologist, provisional psychologist', [
        f'All three are registered with AHPRA. A clinical psychologist has completed an endorsed postgraduate program and attracts a higher Medicare rebate, {REBATE_CLIN} a session against {REBATE_REG} for a registered psychologist. A provisional psychologist is completing supervised registration and is supervised by a registered psychologist; the profile says so, and the fee and Medicare position differ. The network has all three, and the wording is on each profile.']),
       ('What it costs', [
        PSY_COST_PARA,
        'A Mental Health Treatment Plan is written by a GP, any GP, and is what turns a private fee into a partly rebated one. The GPs in the network can write one; so can your own.']),
       ('Choosing', [
        'Read the chips under each name on The Network page first. They are the quickest way to find neuroaffirming, trauma-informed, assessment, children, teens, adults, eating disorders, perinatal, or a particular therapy. Then read the profile: it is the psychologist’s own description of who they see and how they work, and the fee is on it.']),
      ],
      faqs=[
       ('Can a psychologist diagnose ADHD in Australia?', 'Yes. A psychologist can assess and diagnose ADHD and write a report. A psychologist cannot prescribe medication.'),
       ('How much does an ADHD psychologist cost?', f'Each psychologist sets their own fee, shown on their profile. Under a Mental Health Treatment Plan, Medicare pays back {REBATE_REG} a session for a registered psychologist and {REBATE_CLIN} for a clinical psychologist, for up to 10 sessions a year.'),
       ('Do I need a referral to see an ADHD psychologist?', 'No, to book. Yes, in the form of a Mental Health Treatment Plan from a GP, if you want the Medicare rebate.'),
       ('Can I see an ADHD psychologist by telehealth?', 'Yes. The Brisbane and online psychologists in the network work by telehealth, at the same Medicare rebate as in person. The Gold Coast clinic sees people in its rooms.'),
      ],
      related=['adhd-psychologist-brisbane', 'adhd-assessment-online', 'adhd-treatment-after-diagnosis', 'adhd-assessment-queensland']),

 dict(slug='adhd-psychologist-brisbane', group='profession',
      seo='ADHD psychologist in Brisbane: Fortitude Valley and Ashgrove',
      title='ADHD psychologist in Brisbane: Fortitude Valley and Ashgrove.',
      description='Eight Brisbane psychologists in the ADHDme network, at GOALS Psychology in Fortitude Valley and Neutral Minds Psychology in Ashgrove, with ADHD and autism assessment, therapy, telehealth and published fees.',
      lede='Brisbane is where most of the network’s psychologists are: GOALS Psychology in Fortitude Valley and Neutral Minds Psychology in Ashgrove. Between them they cover ADHD and autism assessment, therapy for children through to adults, and telehealth for anyone who would rather not drive.',
      who=brisbane_psychologists, who_heading='Psychologists with rooms in Brisbane',
      who_note='Every one of them also works by telehealth. Fees are on each profile, set by the psychologist.',
      sections=[
       ('The two clinics', [
        f'<strong>GOALS Psychology, Fortitude Valley.</strong> {profiles.GOALS_ACCESS}. Fifty-minute sessions, booked on the clinic’s Halaxy page. Some of its psychologists also do home, school and community visits. The clinic sets its own fees and publishes its Medicare position on each profile; where a fee is not published, the profile says so rather than guessing.',
        f'<strong>Neutral Minds Psychology, Ashgrove.</strong> {a("Jessica Katsamatsas", "jessica-katsamatsas.html")}’s practice, working with neurodivergent adults in a neurodiversity-affirming, trauma-informed way, in Ashgrove and by telehealth Australia-wide.']),
       ('Assessment in Brisbane', [
        f'{a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")} do ADHD and autism assessment at GOALS, for children, teenagers and adults. Meera is an educational and developmental psychologist and also does cognitive assessment. A psychologist assesses and diagnoses but does not prescribe; the {a("Brisbane GP", "adhd-gp-brisbane.html")} page covers the medication route.']),
       ('What it costs', [PSY_COST_PARA]),
       ('Who sees whom', [
        f'Toddlers and early intervention: {a("Lauren Poulos", "lauren-poulos.html")} and {a("Kate Row", "kate-row.html")}. Young people and families: {a("Ellie Putland", "ellie-putland.html")}. Eating disorders and perinatal mental health: {a("Samantha Courtney", "samantha-courtney.html")}. Refugee and newly arrived clients: {a("Alice Bui", "alice-bui.html")}. Neurodivergent adults: {a("Jessica Katsamatsas", "jessica-katsamatsas.html")}. The chips on The Network page carry the same information at a glance.']),
      ],
      faqs=[
       ('Where are the ADHD psychologists in Brisbane?', 'GOALS Psychology in Fortitude Valley, with level access and free one-hour client parking, and Neutral Minds Psychology in Ashgrove. All of them also work by telehealth.'),
       ('Can I get an ADHD assessment from a psychologist in Brisbane?', 'Yes. Lachlan Avent and Meera Lakhani at GOALS Psychology do ADHD and autism assessment for children, teenagers and adults.'),
       ('Is there parking?', 'GOALS Psychology has level access from a same-level car park with free one-hour client parking in the centre.'),
       ('Do I need a referral?', 'No, to book. A Mental Health Treatment Plan from a GP is needed if you want the Medicare rebate on sessions.'),
      ],
      related=['adhd-psychologist', 'adhd-gp-brisbane', 'adhd-doctor-gold-coast', 'adhd-occupational-therapist']),

 dict(slug='adhd-occupational-therapist', group='profession',
      seo='ADHD occupational therapist: help with the mechanics of the day',
      title='ADHD occupational therapist: help with the mechanics of the day.',
      description='What an occupational therapist does for ADHD, for children and adults, how it differs from therapy and coaching, and how it is funded. Paediatric OT in Brisbane in the ADHDme network.',
      lede='When the hard part of ADHD is the day itself, mornings, homework, a classroom, a kitchen, the mess, an occupational therapist changes the task and the environment rather than trying to change the person. This page says what that looks like, who pays for it, and who does it in the network.',
      who=occupational_therapists, who_heading='Occupational therapy in the network',
      who_note='Paediatric OT in Brisbane, in clinic, at home or at school, and by telehealth.',
      sections=[
       ('What an OT does for ADHD', [
        'For a child: play-led work on the skills the classroom and the home are asking for, sensory needs, routines that survive a bad morning, and reports for school, the NDIS or a functional capacity assessment. Some of it happens in the clinic and some in the places where the difficulty actually is, which is why home and school visits matter.',
        'For an adult: the systems of daily life, from a morning routine to how a workspace is laid out, and workplace adjustments. The network’s OT works with children; adult ADHD OT is one of the gaps it is looking to fill.']),
       ('OT, psychology and coaching: which is which', [
        'A psychologist works on thinking, feeling and behaviour, and can assess and diagnose. A coach works on executive function and accountability, and is not a registered health profession. An occupational therapist is AHPRA-registered and works on function: the task, the environment and the skill, measured by whether the day goes better.']),
       ('How it is funded', [
        'The clinic quotes its fee when you book. A Mental Health Treatment Plan does not cover occupational therapy. The NDIS does, for participants with OT in their plan; private health extras commonly do; and a GP’s chronic condition management plan gives a partial Medicare rebate on up to five allied health sessions a year, shared across disciplines.']),
       ('In the network', [
        f'{a("Flynn Simonis", "flynn-simonis.html")} is a registered occupational therapist at GOALS Psychology in Fortitude Valley, Brisbane, working with children in clinic, at home and at school, and writing functional capacity assessment reports. Booking is on the clinic’s own Halaxy page.']),
      ],
      faqs=[
       ('Does an occupational therapist treat ADHD?', 'Yes, by working on function: routines, sensory needs, the environment and the skills the day requires. OT does not diagnose ADHD or prescribe.'),
       ('Is ADHD occupational therapy covered by Medicare?', 'Partly, under a GP chronic condition management plan, with a rebate on up to five allied health sessions a year. A Mental Health Treatment Plan does not cover OT. The NDIS and private extras are the other common routes.'),
       ('Does ADHDme have an occupational therapist?', 'Yes, one, working with children in Brisbane. Adult ADHD occupational therapy is a gap the network is looking to fill.'),
      ],
      related=['adhd-treatment-after-diagnosis', 'adhd-psychologist-brisbane', 'adhd-coach', 'adhd-exercise-physiologist']),

 dict(slug='adhd-coach', group='profession',
      seo='ADHD coaching in Australia: what a coach does, and who pays for it',
      title='ADHD coaching in Australia: what a coach does, and who pays for it.',
      description='What ADHD coaching is and is not, the credentials to look for, and how JobAccess can fund it for anyone working eight hours a week. Six credentialed coaches in the ADHDme network, in Perth and online.',
      lede='Coaching is the practical end of ADHD care: starting, planning, finishing, and building the systems that make those easier. It is not therapy and not treatment, and it is not a registered health profession, which makes the credentials and the funding worth understanding before you enquire.',
      who=coaches, who_heading='The coaches in the network',
      who_note='All six are at REACH ADHD Coaching and Consultancy, in Perth and online Australia-wide. Coaching is arranged by enquiry rather than booked from a diary, and the fee is quoted before anything is booked.',
      sections=[
       ('What coaching is, and is not', [
        'A coach works with you on executive function in your actual week: the task you keep not starting, the plan that falls over by Wednesday, the system that would work if it were simpler. Sessions are practical and forward-looking. A coach does not assess, diagnose or treat, and a coach is not a substitute for a psychologist where the difficulty is mood, anxiety or trauma.',
        'Every coach in the network trained at the ADHD Coaching Academy (ADDCA) and most hold an International Coaching Federation credential. Because coaching is unregulated, those are the two things to check anywhere.']),
       ('Who pays', [
        f'If you work, or are self-employed, at least eight hours a week, the Employment Assistance Fund through JobAccess covers ADHD coaching under specialist mental health support. The practice puts it at around {JOBACCESS} including GST a year, indexed. You apply with supporting documentation from a GP or specialist, and can ask for an exemption rather than disclose the diagnosis to your employer. REACH runs free sessions to help with the application.',
        'REACH is not a registered NDIS provider, but says self-managed and plan-managed participants can still claim session fees. For children, the practice says the NDIS is usually the only funding route.']),
       ('The coaches', [
        'All six came to coaching from teaching, between two and three decades each, in classrooms, gifted-and-talented programs, early childhood and secondary education. That shows in the work: students and families are the common thread, and the profiles say who each coach sees.']),
      ],
      faqs=[
       ('Is ADHD coaching covered by Medicare or the NDIS?', 'Not by Medicare. JobAccess can fund it for anyone working at least eight hours a week. Self-managed and plan-managed NDIS participants can often claim it; for children the NDIS is usually the only route.'),
       ('What is the difference between an ADHD coach and a psychologist?', 'A psychologist is AHPRA-registered, can assess and diagnose, and treats with therapy. A coach is unregulated and works on executive function and accountability. Many people use both.'),
       ('Can I do ADHD coaching online?', 'Yes. Every coach in the network works online Australia-wide, and in person in Perth.'),
       ('How much does ADHD coaching cost?', 'REACH quotes a fee when you enquire, before anything is booked, and JobAccess funding can cover it for people in work.'),
      ],
      related=['adhd-treatment-after-diagnosis', 'adhd-psychologist', 'adhd-exercise-physiologist', 'adhd-assessment-online']),
]

GROUPS = [('place', 'By place'), ('profession', 'By profession'), ('after', 'After a diagnosis')]
BY_SLUG = {p['slug']: p for p in PAGES}
for p in PAGES:
    for r in p['related']:
        assert r in BY_SLUG, f'{p["slug"]} links to unknown page {r}'

# ---------------------------------------------------------------- render
H2 = 'text-[24px] font-extrabold tracking-tight text-[#1a1c1c]'
P = 'text-[17px] leading-[1.7] text-[#1a1c1c]/85'
CTA_DARK = ('btn-press inline-flex items-center gap-2 h-12 px-7 rounded-full bg-[#1a1c1c] text-white text-[15px] font-bold '
            'hover:bg-[#2f3130] transition-all shadow-[0_4px_16px_rgba(0,0,0,0.15)] hover:-translate-y-0.5')
CTA_LIGHT = ('btn-press inline-flex items-center gap-2 h-12 px-7 rounded-full bg-white border border-[#e8e6df] text-[#1a1c1c] '
             'text-[15px] font-bold hover:bg-[#f6f4ee] transition-colors')
ARROW = '<span class="text-[#f1bc31]" aria-hidden="true">→</span>'


def head_for(shell_head, slug, seo, description):
    url = f'{SITE}/{slug}.html'
    subs = [
        (r'<!-- ADHDme - .*? -->', f'<!-- ADHDme - {seo} (generated by scripts/build-seo-pages.py) -->'),
        (r'<title>.*?</title>', f'<title>{esc(seo)} · ADHDme</title>'),
        (r'<meta name="description" content=".*?">', f'<meta name="description" content="{esc(description)}">'),
        (r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{url}">'),
        (r'<meta property="og:url" content=".*?">', f'<meta property="og:url" content="{url}">'),
        (r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{esc(seo)}">'),
        (r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{esc(description)}">'),
        (r'<meta name="twitter:title" content=".*?">', f'<meta name="twitter:title" content="{esc(seo)}">'),
        (r'<meta name="twitter:description" content=".*?">', f'<meta name="twitter:description" content="{esc(description)}">'),
        (r'<link rel="preload" as="image" [^>]*>\n', ''),
    ]
    head = shell_head
    for pat, rep in subs:
        head, n = re.subn(pat, lambda _m, r=rep: r, head, count=1, flags=re.S)
        if not n:
            raise SystemExit(f'build-seo-pages: how-it-works.html has no {pat!r} to rewrite for {slug}')
    return head


def header_for(shell_header):
    """The header with no item marked current: these pages sit outside the primary navigation."""
    active = ('aria-current="page" class="whitespace-nowrap px-2 lg:px-5 py-2 rounded-full text-[14px] lg:text-[15px] font-semibold '
              'bg-[#1a1c1c] text-white shadow-sm transition-all" href="how-it-works.html"')
    inactive = ('class="whitespace-nowrap px-2 lg:px-5 py-2 rounded-full text-[14px] lg:text-[15px] font-semibold text-[#1a1c1c]/80 '
                'hover:text-[#1a1c1c] hover:bg-black/5 transition-all" href="how-it-works.html"')
    if shell_header.count(active) != 1 or shell_header.count('<a aria-current="page" href="how-it-works.html">') != 1:
        raise SystemExit('build-seo-pages: how-it-works.html header does not mark How it works current where expected')
    return shell_header.replace(active, inactive).replace('<a aria-current="page" href="how-it-works.html">', '<a href="how-it-works.html">')


def breadcrumb(items):
    crumbs = []
    for i, (text, href) in enumerate(items):
        last = i == len(items) - 1
        if last:
            crumbs.append(f'<li aria-current="page" class="text-[#1a1c1c] font-semibold">{esc(text)}</li>')
        else:
            crumbs.append(f'<li><a class="hover:text-[#1a1c1c] hover:underline underline-offset-4" href="{href}">{esc(text)}</a></li>'
                          f'<li aria-hidden="true">/</li>')
    return (f'<nav aria-label="Breadcrumb" class="text-[13px] font-medium text-[#5f5e59]"><ol class="flex flex-wrap items-center gap-2 list-none p-0 m-0">'
            + ''.join(crumbs) + '</ol></nav>')


def who_section(p):
    if not p['who']:
        return ''
    filters = p['who'] if isinstance(p['who'], (list, tuple)) else [p['who']]
    people = []
    for f in filters:
        people += [c for c in CLINICIANS if f(c) and c not in people]
    if not people:
        raise SystemExit(f'build-seo-pages: {p["slug"]} selects no clinicians; fix the filter or drop the section')
    cards = ''.join(f'<li>{profiles.also_link(c, profiles.portrait_size(c))}</li>' for c in people)
    return f'''<section class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 py-12" aria-labelledby="who-title">
<div class="pt-10 border-t border-[#e8e6df]">
<h2 id="who-title" class="{H2}">{esc(p['who_heading'])}</h2>
<p class="mt-3 max-w-[64ch] {P}">{esc(p['who_note'])}</p>
<ul class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-8 list-none p-0 m-0">{cards}</ul>
<p class="mt-8"><a class="{CTA_DARK}" href="{PROFILE}">See the whole network {ARROW}</a></p>
</div></section>'''


def prose(sections):
    out = []
    for i, (h, blocks) in enumerate(sections):
        parts = []
        for b in blocks:
            if isinstance(b, tuple) and b[0] == 'list':
                parts.append('<ul class="mt-4 space-y-3 pl-5 list-disc marker:text-[#f1bc31]">' + ''.join(f'<li class="{P}">{item}</li>' for item in b[1]) + '</ul>')
            else:
                parts.append(f'<p class="mt-4 {P}">{b}</p>')
        out.append(f'<section aria-labelledby="s{i}" class="mt-12 first:mt-0"><h2 id="s{i}" class="{H2}">{esc(h)}</h2>{"".join(parts)}</section>')
    return ''.join(out)


def faq_section(faqs):
    items = ''.join(
        f'<div class="py-5 border-t border-[#e8e6df]"><h3 class="text-[17px] font-bold text-[#1a1c1c]">{esc(q)}</h3>'
        f'<p class="mt-2 {P}">{esc(ans)}</p></div>' for q, ans in faqs)
    return f'<section aria-labelledby="faq-title" class="mt-14"><h2 id="faq-title" class="{H2}">Questions people ask</h2><div class="mt-4">{items}</div></section>'


def related_section(p):
    links = ''.join(
        f'<li><a class="group block rounded-2xl bg-white border border-[#e8e6df] p-5 hover:border-[#1a1c1c]/30 transition-colors" href="{r}.html">'
        f'<span class="block text-[17px] font-bold text-[#1a1c1c] group-hover:underline decoration-[#f1bc31] decoration-2 underline-offset-4">{esc(BY_SLUG[r]["seo"])}</span></a></li>'
        for r in p['related'])
    return f'''<section class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pb-16" aria-labelledby="related-title">
<h2 id="related-title" class="text-[15px] font-bold text-[#5f5e59]">More ADHD care pages</h2>
<ul class="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 list-none p-0 m-0">{links}</ul>
<p class="mt-6 text-[15px] font-semibold text-[#5f5e59]"><a class="hover:text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="{HUB}.html">All ADHD care pages</a></p>
</section>'''


def banner():
    return f'''<section class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pb-12">
<div class="p-8 md:p-12 rounded-3xl border border-[#b9d6ee] flex flex-col lg:flex-row items-center justify-between gap-8 text-center lg:text-left" style="background: linear-gradient(180deg, #dcedfa 0%, #cfe4f6 55%, #c3dcf2 100%);">
<div class="max-w-xl space-y-3"><h2 class="text-[32px] sm:text-[40px] font-extrabold text-on-surface tracking-tight leading-tight">Ready to find your clinician?</h2>
<p class="text-[15px] text-[#1e547a] font-medium">Read the clinicians, then book or enquire on the practice’s own page.</p></div>
<div class="flex flex-col items-center lg:items-end gap-2.5 shrink-0"><a class="{CTA_DARK}" href="{PROFILE}">Find your clinician {ARROW}</a>
<p class="text-[13px] text-[#1e547a] font-medium">No account or sign-up required.</p></div>
</div></section>'''


def jsonld(p):
    url = f'{SITE}/{p["slug"]}.html'
    graph = [
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': p['seo'], 'description': p['description'],
         'inLanguage': 'en-AU', 'isPartOf': {'@type': 'WebSite', 'name': 'ADHDme', 'url': SITE + '/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'ADHDme', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'ADHD care', 'item': f'{SITE}/{HUB}.html'},
            {'@type': 'ListItem', 'position': 3, 'name': p['seo'], 'item': url}]},
        {'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': ans}} for q, ans in p['faqs']]},
    ]
    return '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False) + '</script>'


def page(p, head, header, footer):
    return f'''{head_for(head, p['slug'], p['seo'], p['description'])}{header}<main id="main" class="w-full bg-[#FAFAF7]">
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pt-10 pb-4">
{breadcrumb([('ADHDme', 'index.html'), ('ADHD care', f'{HUB}.html'), (p['seo'], f'{p["slug"]}.html')])}
<h1 class="hero-in mt-6 max-w-[22ch] text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-[#1a1c1c]">{esc(p['title'])}</h1>
<p class="hero-in hero-in-2 mt-5 max-w-[64ch] text-[19px] leading-[1.6] text-[#5f5e59]">{esc(p['lede'])}</p>
<div class="hero-in hero-in-3 mt-8 flex flex-wrap gap-3"><a class="{CTA_DARK}" href="{PROFILE}">Find your clinician {ARROW}</a><a class="{CTA_LIGHT}" href="how-it-works.html">How booking works</a></div>
</div>
{who_section(p)}
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pb-16"><div class="max-w-[760px]{'' if p['who'] else ' pt-10 border-t border-[#e8e6df]'}">
{prose(p['sections'])}
{faq_section(p['faqs'])}
</div></div>
{banner()}
{related_section(p)}
</main>
{jsonld(p)}
{footer}'''


HUB_SEO = 'ADHD care in Australia by place and profession'
HUB_DESCRIPTION = 'Every ADHDme guide to getting ADHD care: by city and state, by profession, and what follows a diagnosis. Each one says plainly what the network has today and what it costs.'


def hub_page(head, header, footer):
    groups = ''
    for key, label in GROUPS:
        items = ''.join(
            f'<li><a class="group block py-5 border-t border-[#e8e6df]" href="{p["slug"]}.html">'
            f'<span class="block text-[22px] leading-[1.25] font-extrabold tracking-tight text-[#1a1c1c] group-hover:underline decoration-[#f1bc31] decoration-2 underline-offset-4">{esc(p["seo"])}</span>'
            f'<span class="block mt-2 text-[15px] leading-relaxed text-[#5f5e59]">{esc(p["description"])}</span></a></li>'
            for p in PAGES if p['group'] == key)
        groups += f'<section class="mt-12" aria-labelledby="g-{key}"><h2 id="g-{key}" class="{H2}">{label}</h2><ul class="mt-4 list-none p-0 m-0">{items}</ul></section>'
    url = f'{SITE}/{HUB}.html'
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', '@id': url, 'url': url, 'name': HUB_SEO,
          'description': HUB_DESCRIPTION, 'inLanguage': 'en-AU',
          'hasPart': [{'@type': 'WebPage', 'url': f'{SITE}/{p["slug"]}.html', 'name': p['seo']} for p in PAGES]}
    return f'''{head_for(head, HUB, HUB_SEO, HUB_DESCRIPTION)}{header}<main id="main" class="w-full bg-[#FAFAF7]">
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pt-10 pb-16">
{breadcrumb([('ADHDme', 'index.html'), ('ADHD care', f'{HUB}.html')])}
<h1 class="hero-in mt-6 max-w-[22ch] text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-[#1a1c1c]">ADHD care, by place and by profession.</h1>
<p class="hero-in hero-in-2 mt-5 max-w-[64ch] text-[19px] leading-[1.6] text-[#5f5e59]">Short guides to getting ADHD care in Australia. Each one answers a question people actually search, says what the ADHDme network has for it today, and what it does not, and gives the cost before you book anything.</p>
<div class="max-w-[760px]">{groups}</div>
</div>
{banner()}
</main>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{footer}'''


def build():
    shell = SHELL.read_text(encoding='utf-8')
    head = shell[:shell.index('<body')]
    header = shell[shell.index('<body'):shell.index('<main')]
    footer = shell[shell.index('<footer'):]
    out = {ROOT / f'{HUB}.html': hub_page(head, header_for(header), footer)}
    for p in PAGES:
        out[ROOT / f'{p["slug"]}.html'] = page(p, head, header_for(header), footer)
    return out


def main(argv):
    out = build()
    stale = [q for q, text in out.items() if not q.exists() or q.read_text(encoding='utf-8') != text]
    if '--check' in argv:
        for q in stale:
            print(f'out of date: {q.relative_to(ROOT)}')
        print('search pages are up to date' if not stale else f'{len(stale)} file(s) differ; run python3 scripts/build-seo-pages.py')
        return 1 if stale else 0
    for q, text in out.items():
        q.write_text(text, encoding='utf-8', newline='')
        print(('wrote  ' if q in stale else 'same   ') + str(q.relative_to(ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
