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


GP_COST_PARA = (f'A GP assessment through the network costs <strong>{GP_FEE[0][0]} for the first consultation and {GP_FEE[1][0]} '
                f'for the follow-up, {GP_TOTAL} in total</strong>. The two consultations cover the assessment and the diagnosis. '
                f'Neither attracts a Medicare rebate. Fees are set and charged by the practice. ADHDme takes no commission.')
PSY_COST_PARA = (f'Each psychologist sets their own fee, shown on their profile. With a Mental Health Treatment Plan from a GP, '
                 f'Medicare pays part of the fee for up to 10 sessions a year. At current rates the rebate is {REBATE_REG} a '
                 f'session for a registered psychologist and {REBATE_CLIN} for a clinical psychologist.')
QLD_RULE = ('Queensland changed its rules on 1 December 2025. A specialist GP (one with FRACGP or FACRRM fellowship) '
            'can now diagnose ADHD in an adult and start, adjust and continue stimulant medication without a '
            'psychiatrist signing off first.')
QLD_GP_PARA = (QLD_RULE + ' Queensland GPs have been able to prescribe for children since 2017. '
               'A GP in another state works under that state’s rules, so ask the practice what applies to you.')
NSW_RULE = ('NSW is changing its rules in stages. Since September 2025, GPs who have completed the state’s training '
            'can continue stimulant prescriptions that a psychiatrist started, for patients who are stable on treatment.')
NSW_STAGE_TWO = ('A second stage, rolling out through 2026, lets trained GPs assess, diagnose and start medication '
                 'themselves.')
NSW_GP_PARA = (NSW_RULE + ' ' + NSW_STAGE_TWO + ' What a GP can do depends on where they are in that process. '
               'Check the practice’s page, or ask at the first appointment.')
WHAT_ASSESSMENT = [
    'A history going back to childhood. ADHD is a developmental condition, so the signs need to have been there early, even if nobody named them.',
    'Rating scales, filled in by you and, where possible, by someone who knew you as a child or knows you now.',
    'A check for other causes, including sleep, mood, anxiety, thyroid, substance use and your general health.',
    'A baseline before any medication: heart rate, blood pressure, weight, and questions about whether a stimulant is safe for you.',
    'A written plan with a review date. The Australian guideline asks for reviews at set intervals.',
]

# ---------------------------------------------------------------- pages
# title: the h1. seo: <title>, og:title, twitter:title (no trailing full stop). description: meta and
# share-card description. lede: the paragraph under the h1. who: which clinicians to list, with a
# heading and a plain note about what that list is and is not. sections: (h2, [paragraph html, or
# ('list', [items])]). faqs: (question, answer) pairs, also emitted as FAQPage JSON-LD.
PAGES = [
 dict(slug='adhd-doctor-gold-coast', group='place',
      seo='ADHD doctor Gold Coast: who to see and costs',
      title='ADHD doctor on the Gold Coast.',
      description=f'ADHD care on the Gold Coast: psychologists and an exercise physiologist in Bundall, plus a GP assessment by phone for {GP_TOTAL} in total.',
      lede='ADHDme has psychologists and an exercise physiologist at Atlantis Recovery Centre in Bundall. Its two GPs are in Sydney and see people remotely.',
      who=[gold_coast, gps_remote, qld_psychologists], who_heading='Who you can see from the Gold Coast',
      who_note='Bundall clinicians see people in person. The others also work by telehealth.',
      sections=[
       ('In person in Bundall', [
        f'{a("Atlantis Recovery Centre", "bart-traynor.html")} is an allied health centre at 25 Upton Street, Bundall. It has clinical psychologists, a provisional psychologist, an exercise physiologist and physiotherapists. The practice says its approach, which combines therapy with movement-based work, suits ADHD, anxiety and trauma. Each psychology client starts with a comprehensive assessment. You book on the practice’s HotDoc page, which opens in a new tab. No referral needed, and you don’t need an account.',
        'A psychologist can assess ADHD and treat it with therapy but cannot prescribe. The practice quotes its fee when you book. It works with DVA, the NDIS, private health funds, WorkCover and GP Mental Health Treatment Plans.']),
       ('A GP assessment by phone', [
        f'The network’s two GPs are in Sydney and both see people remotely. {a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} offers phone consultations and {a("Dr Anu Saxena", "dr-anu-saxena.html")} offers telehealth, so you can start with either without travelling. When you book, ask whether the whole assessment can be done remotely or whether any part needs to be in person.',
        GP_COST_PARA,
        QLD_GP_PARA]),
       ('Psychologists an hour up the M1', [
        f'GOALS Psychology is in Fortitude Valley, with level access from the car park and an hour of free client parking. Neutral Minds Psychology is in Ashgrove. At GOALS, {a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")} do formal ADHD and autism assessments with a written report. The psychologists at both clinics also offer telehealth.',
        PSY_COST_PARA]),
       ('After the diagnosis', [
        f'The {a("treatment after diagnosis", "adhd-treatment-after-diagnosis.html")} page covers what usually follows: medication and its reviews, therapy, occupational therapy, coaching, and things you can do yourself. On the Gold Coast, {a("Sarah Savage", "sarah-savage.html")} provides exercise physiology in person.']),
      ],
      faqs=[
       ('Is there an ADHD doctor on the Gold Coast in the ADHDme network?', 'There are psychologists and an exercise physiologist at Atlantis Recovery Centre in Bundall, but no Gold Coast GP yet. The network’s two GPs see people remotely from Sydney.'),
       ('Can a GP diagnose ADHD in Queensland?', 'Yes. Since 1 December 2025 a specialist GP in Queensland can diagnose ADHD in adults and prescribe stimulant medication, and Queensland GPs have prescribed for children since 2017.'),
       ('Do I need a referral?', 'No referral needed. You book or enquire directly with the practice, and a GP can write a Mental Health Treatment Plan if you want a Medicare rebate on psychology sessions.'),
       ('What does it cost on the Gold Coast?', f'Atlantis Recovery Centre quotes its fee when you book and accepts DVA, NDIS, private health, WorkCover and Medicare plans. A GP assessment by phone is {GP_TOTAL} across two consultations, with no Medicare rebate.'),
       ('Does the Gold Coast clinic offer telehealth?', 'The Bundall clinic has not declared telehealth, so its profiles don’t list it. The Brisbane psychologists and the Sydney GPs do see people remotely.'),
      ],
      related=['adhd-gp-brisbane', 'adhd-assessment-queensland', 'adhd-psychologist-brisbane', 'adhd-exercise-physiologist']),

 dict(slug='adhd-gp-brisbane', group='place',
      seo='ADHD GP Brisbane: diagnosis, medication, costs',
      title='ADHD GP in Brisbane.',
      description=f'Queensland GPs can now diagnose adult ADHD and prescribe. Who sees Brisbane patients in the ADHDme network, and a GP assessment by phone for {GP_TOTAL}.',
      lede='Queensland is the first state to let GPs diagnose adult ADHD and prescribe. ADHDme’s two GPs are in Sydney and see Brisbane patients remotely.',
      who=any_of(gps_remote, brisbane_psychologists, brisbane_allied), who_heading='Who sees Brisbane patients',
      who_note='The GPs are listed first, then the psychologists and the occupational therapist.',
      sections=[
       ('What a Queensland GP can now do', [
        QLD_GP_PARA,
        'For Brisbane patients, this removes the longest wait: months for a psychiatrist to confirm what a GP had already seen. You still need a full assessment, which means a long first appointment, a baseline and a review.']),
       ('The network’s GPs', [
        f'ADHDme’s two GPs practise in Sydney and both see people remotely. {a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} offers phone consultations and {a("Dr Anu Saxena", "dr-anu-saxena.html")} offers telehealth, so you can start with either without travelling. A NSW GP follows NSW rules on medication, which are changing in stages through 2026. Ask the practice what can be started by phone.',
        'Brisbane GPs will be listed here as they join. Each clinician joins individually and declares how they work, so the network grows slowly.']),
       ('What the assessment involves', [('list', WHAT_ASSESSMENT)]),
       ('What it costs', [
        GP_COST_PARA,
        PSY_COST_PARA]),
       ('Psychologist assessment in Brisbane', [
        f'If you want a formal assessment but not medication, two Brisbane psychologists in the network do ADHD and autism assessments in person: {a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")}, both at GOALS Psychology in Fortitude Valley. A GP can later use a psychologist’s report when considering medication.']),
      ],
      faqs=[
       ('Can a GP in Brisbane prescribe ADHD medication for adults?', 'Yes, since 1 December 2025, if the GP holds FRACGP or FACRRM fellowship. They can diagnose, then start, adjust and continue medication, though each practice decides whether it offers this.'),
       ('Does ADHDme have a Brisbane GP?', 'Not yet. The network’s two GPs are in Sydney and see people remotely, and Brisbane psychologists and an occupational therapist are in the network now.'),
       ('Do I need a referral to see an ADHD GP?', 'No referral needed. You only need a referral for a psychiatrist, and Queensland’s reform lets a GP take that role for many adults.'),
       ('How long does an ADHD assessment take with a GP?', 'Two appointments: a long first consultation and a follow-up. Some people need an extra 30-minute clinical review for more history or records, and the practice explains the cost before booking it.'),
      ],
      related=['adhd-assessment-queensland', 'adhd-doctor-gold-coast', 'adhd-psychologist-brisbane', 'adhd-assessment-online']),

 dict(slug='adhd-assessment-queensland', group='place',
      seo='ADHD assessment Queensland: three routes, costs',
      title='ADHD assessment in Queensland.',
      description='How ADHD assessment works in Queensland since the December 2025 reform: GP, psychologist or psychiatrist. No referral needed for a GP or psychologist.',
      lede='In Queensland, a GP, psychologist or psychiatrist can assess ADHD. ADHDme lists GPs and psychologists who see Queensland patients.',
      who_heading='Who sees Queensland patients',
      who=[gps_remote, qld_psychologists, qld_allied], who_note='Rooms in Brisbane and Bundall. The GPs and Brisbane clinicians also work by telehealth.',
      sections=[
       ('Route one: a GP', [
        QLD_GP_PARA,
        f'In the network, {a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} takes phone consultations and {a("Dr Anu Saxena", "dr-anu-saxena.html")} offers telehealth, both from Sydney. They follow NSW rules on medication, but the assessment itself is the same in any state. ' + GP_COST_PARA]),
       ('Route two: a psychologist', [
        f'A psychologist can assess and diagnose ADHD and treat it with therapy, but cannot prescribe. In Brisbane, {a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")} at GOALS Psychology do ADHD and autism assessments, in person in Fortitude Valley or by telehealth. A GP or psychiatrist often works from a psychologist’s assessment report. On the Gold Coast, the clinical psychologists at {a("Atlantis Recovery Centre", "bart-traynor.html")} in Bundall start each client with a comprehensive assessment, and the practice says its approach suits ADHD.',
        PSY_COST_PARA]),
       ('Route three: a psychiatrist', [
        'You need a GP referral to see a psychiatrist. In Queensland the wait for a first appointment is commonly months, and the fee is commonly several hundred dollars above the Medicare rebate. ADHDme does not list psychiatrists. The 2025 reform was introduced because, for many adults, the psychiatrist step added waiting time without adding much to what a well-trained GP could assess.',
        'A psychiatrist is still the right choice when the picture is complicated: another serious mental illness, a history that makes stimulants risky, or a child younger than a GP is allowed to treat.']),
       ('What an assessment involves', [('list', WHAT_ASSESSMENT)]),
       ('Outside Brisbane', [
        'The Brisbane clinicians and both GPs also work by phone or telehealth, so you can start today from Cairns, Townsville, Toowoomba or the Sunshine Coast. Parts of the assessment that need a room, such as a physical baseline before medication, can often be done by your local GP using the assessing clinician’s letter. Ask the practice how they handle this.',
        f'For more on telehealth, see {a("ADHD assessment online", "adhd-assessment-online.html")}.']),
      ],
      faqs=[
       ('Can a GP diagnose ADHD in Queensland?', 'Yes, for adults, since 1 December 2025, if the GP holds FRACGP or FACRRM fellowship. Queensland GPs have prescribed for children since 2017.'),
       ('How much does an ADHD assessment cost in Queensland?', f'A GP assessment through the network is {GP_TOTAL} across two consultations, with no Medicare rebate. Psychologists set their own assessment fees, shown on their profiles, and a private psychiatrist usually costs the most and has the longest wait.'),
       ('Do I need a referral for an ADHD assessment?', 'No referral needed for a GP or a psychologist. A psychiatrist needs a GP referral.'),
       ('Can I be assessed by telehealth in Queensland?', 'Yes. Both network GPs see people remotely and the Brisbane psychologists offer telehealth. The practice will tell you if any part needs to be done in person.'),
       ('What happens after the diagnosis?', 'You and your clinicians plan treatment together. It can include medication with a prescriber, therapy with a psychologist, occupational therapy, coaching and things you can do yourself, as set out on the treatment after diagnosis page.'),
      ],
      related=['adhd-gp-brisbane', 'adhd-doctor-gold-coast', 'adhd-assessment-online', 'adhd-treatment-after-diagnosis']),

 dict(slug='adhd-assessment-sydney', group='place',
      seo='ADHD assessment Sydney: GP, $498, no referral',
      title='ADHD assessment in Sydney.',
      description=f'Two GPs assess and diagnose ADHD in Beecroft, Double Bay and Hornsby. {GP_TOTAL} across two consultations, no referral needed, with phone and telehealth options.',
      lede='Two ADHDme GPs assess ADHD in Beecroft, Double Bay and Hornsby, with the fee published before you book.',
      who=nsw_clinical, who_heading='ADHD clinicians in Sydney',
      who_note='Both GPs assess and diagnose.',
      sections=[
       ('The two GPs', [
        f'{a("Dr Anubhav Saxena", "dr-anubhav-saxena.html")} works at Beecroft Family &amp; Skin Cancer Clinic in Beecroft and Double Bay, and takes phone consultations. His assessment starts with a documented physical baseline and considers ADHD alongside sleep, cardiovascular and metabolic health.',
        f'{a("Dr Anu Saxena", "dr-anu-saxena.html")} works at Bay Health Clinic in Double Bay and Hornsby, and by telehealth. She came to medicine through psychology, has completed an endorsed ADHD prescriber course, and speaks Hindi, Urdu and English.',
        'You book both through their practices’ Healthengine pages, which open in a new tab. Both GPs have declared a commercial or personal connection with ADHDme, and this is shown on each profile.']),
       ('What it costs', [GP_COST_PARA,
        'Some people need an extra 30-minute clinical review for further history, records or a medical assessment. If you do, the practice explains why and discusses the cost before booking it.']),
       ('What the assessment involves', [('list', WHAT_ASSESSMENT)]),
       ('Medication in NSW in 2026', [
        NSW_GP_PARA,
        'Whatever the rules allow, the network’s GPs take a baseline before starting anything, write a plan and review at set intervals.']),
       ('Therapy alongside', [
        f'{a("Paula Garrido", "paula-garrido.html")} is a clinical psychologist based in Sydney who works entirely by telehealth. She is certified in ADHD and autism clinical services and takes a neuroaffirming, trauma-informed approach. ' + PSY_COST_PARA]),
      ],
      faqs=[
       ('Can a GP diagnose ADHD in NSW?', 'NSW is bringing this in stages: trained GPs have continued existing stimulant prescriptions since September 2025, and assessing, diagnosing and starting medication is rolling out through 2026. The network’s GPs assess ADHD now; ask the practice what they can prescribe.'),
       ('How much is an ADHD assessment in Sydney?', f'{GP_FEE[0][0]} for the first consultation and {GP_FEE[1][0]} for the follow-up, {GP_TOTAL} in total, with no Medicare rebate.'),
       ('Do I need a referral?', 'No referral needed. You book both GPs directly on their practice’s Healthengine page.'),
       ('Where in Sydney?', 'Dr Anubhav Saxena is in Beecroft and Double Bay, and Dr Anu Saxena is in Double Bay and Hornsby. Dr Anubhav Saxena also offers phone consultations, and Dr Anu Saxena offers telehealth.'),
      ],
      related=['adhd-assessment-online', 'adhd-treatment-after-diagnosis', 'adhd-psychologist', 'adhd-assessment-queensland']),

 dict(slug='adhd-assessment-online', group='place',
      seo='ADHD assessment online: what telehealth can do',
      title='ADHD assessment online.',
      description='Get assessed for ADHD by phone or telehealth anywhere in Australia, with no referral. Which parts can be done remotely and which need a clinic visit.',
      lede='Most of an ADHD assessment is a conversation, so it works by phone or video. A few parts still need to be in person.',
      who=telehealth_clinical, who_heading='Who works by phone or telehealth',
      who_note='Everyone listed offers remote appointments.',
      sections=[
       ('What can be done remotely', [
        'The developmental history, the rating scales, the check for other causes and the diagnosis itself can all be done by phone or video. So can therapy, which the network’s Brisbane and online psychologists offer by telehealth.',
        'Booking works the same way as in person. The button on each profile opens the practice’s booking page or enquiry form in a new tab. No referral needed, and you don’t need an account. ' + GP_COST_PARA]),
       ('What needs an in-person visit', [
        'A physical baseline before medication: heart rate, blood pressure, weight, and anything the history raises. Some practices ask your local GP to take these and send the results. Others ask you to come in once. Check how the practice handles this before you book.',
        'Medication. Stimulant prescribing is regulated by each state, and prescribers follow the rules of the state they practise in. ' + QLD_RULE + ' ' + NSW_RULE + ' ' + NSW_STAGE_TWO + ' The practice will tell you what can be started remotely.']),
       ('Therapy by telehealth', [
        f'All the Brisbane psychologists offer telehealth, and {a("Paula Garrido", "paula-garrido.html")}’s clinic is online only. ' + PSY_COST_PARA,
        'Any GP can write a Mental Health Treatment Plan, including your own, and it works the same way for a telehealth psychologist.']),
       ('Choosing a clinician you won’t meet in person', [
        'Each profile is the clinician’s own account of how they work, who they see, what they focus on and what they charge. On The Network page, the chips under each name let you filter quickly: neuroaffirming, trauma-informed, assessment, children, adults.']),
      ],
      faqs=[
       ('Can ADHD be diagnosed online in Australia?', 'Yes. The history, rating scales and diagnostic conversation can be done by phone or video. The physical baseline before medication is usually done in person, by the practice or your local GP.'),
       ('Can I get ADHD medication through telehealth?', 'It depends on the state the prescriber practises in, and sometimes the state you live in. Queensland lets specialist GPs start adult stimulant medication, NSW is phasing it in through 2026, and the practice will tell you what applies.'),
       ('Is telehealth psychology covered by Medicare?', 'Yes. Under a Mental Health Treatment Plan, telehealth sessions get the same rebate as in-person sessions, for up to 10 sessions a year.'),
       ('Do I need a referral for a telehealth ADHD assessment?', 'No referral needed. You book or enquire directly with each clinician.'),
      ],
      related=['adhd-assessment-queensland', 'adhd-assessment-sydney', 'adhd-psychologist', 'adhd-treatment-after-diagnosis']),

 dict(slug='adhd-treatment-after-diagnosis', group='after',
      seo='ADHD treatment after diagnosis: what happens next',
      title='ADHD treatment after diagnosis.',
      description='After an ADHD diagnosis: medication, therapy, OT and coaching. Who provides each, and how Medicare covers up to 10 psychology sessions a year.',
      lede='Treatment usually combines medication, therapy, occupational therapy, coaching and changes you make yourself. You don’t have to start everything at once.',
      who=None, who_heading=None, who_note=None,
      sections=[
       ('Medication and reviews', [
        'For most adults, the Australian guideline recommends stimulant medication (methylphenidate or lisdexamfetamine) as first-line treatment. Non-stimulants are used where a stimulant is unsuitable or not tolerated. You decide with a prescriber, and the first weeks are spent finding the dose and timing that fit your day.',
        'Good prescribing includes a baseline before the first dose, reviews at set intervals, and ongoing checks of heart rate, blood pressure, sleep, appetite and weight. Who can prescribe depends on the state. ' + QLD_RULE + ' ' + NSW_RULE + ' ' + NSW_STAGE_TWO,
        f'In the network, the {a("GPs", GP_PANEL)} handle medication questions.']),
       ('Therapy with a psychologist', [
        'Medication helps with attention. Therapy helps with what often comes with a late diagnosis: years of workarounds, and anxiety, low mood and shame. Common approaches are cognitive behavioural therapy adapted for ADHD, acceptance and commitment therapy, and dialectical behaviour therapy skills. Each psychologist in the network lists the ones they use.',
        PSY_COST_PARA + f' The network’s {a("psychologists", PSY_PANEL)} are in Brisbane and available by telehealth Australia-wide.']),
       ('Occupational therapy for daily life', [
        f'If the hard part is getting through the day (mornings, routines, or a home or classroom that isn’t working), an occupational therapist adjusts the environment and the task. In the network, {a("Flynn Simonis", "flynn-simonis.html")} works with children in Brisbane, in clinic, at home or at school. The practice quotes its fee when you book. A Mental Health Treatment Plan does not cover OT, but the NDIS, private health extras and a GP’s chronic condition management plan often do.']),
       ('Coaching', [
        f'Coaching is practical work on executive function: starting, planning, finishing, and building systems that make those easier. It is not therapy or medical treatment. The network’s {a("coaches", COACH_PANEL)} are in Perth and online. Coaching can be funded through JobAccess for anyone working at least eight hours a week, at around {JOBACCESS} a year according to the practice. See {a("ADHD coaching", "adhd-coach.html")} for details.']),
       ('Things you can do yourself', [
        'Three habits have better evidence than any supplement. Twenty to thirty minutes of moderate aerobic exercise gives a small to moderate lift in attention for about an hour, so it helps to exercise right before demanding work. A regular sleep and wake time matters even more when you take a stimulant. Regular meals, planned around the midday appetite dip a stimulant causes, help protect your weight and mood.',
        f'For exercise, including safety on stimulant medication, see {a("ADHD and exercise physiology", "adhd-exercise-physiologist.html")}. On the Gold Coast, {a("Sarah Savage", "sarah-savage.html")} offers this in person.']),
       ('How it fits together', [
        'Most people use only some of this. A common pattern is medication with a GP, six to ten psychology sessions in the first year, and one or two of the changes you make yourself. Some people never take medication and do well with therapy and coaching. You choose the order, and you can read each clinician’s profile before deciding.']),
      ],
      faqs=[
       ('What is the first-line treatment for adult ADHD in Australia?', 'The Australian guideline recommends stimulant medication as first-line for most adults, together with psychoeducation, and non-stimulants where a stimulant is unsuitable. Therapy, occupational therapy and coaching help with what medication does not.'),
       ('Do I have to take medication after an ADHD diagnosis?', 'No. You decide with a prescriber, and some people choose therapy, coaching and lifestyle changes instead or first.'),
       ('How often are reviews after starting ADHD medication?', 'Often at first while the dose is adjusted, then at set intervals. The Australian guideline asks for scheduled reviews.'),
       ('Does Medicare cover ADHD treatment?', f'Partly. Psychology under a Mental Health Treatment Plan gets a rebate of {REBATE_REG} or {REBATE_CLIN} a session for up to 10 sessions a year, but GP consultations for ADHD in the network have no rebate, and OT and coaching are funded in other ways.'),
      ],
      related=['adhd-psychologist', 'adhd-occupational-therapist', 'adhd-coach', 'adhd-exercise-physiologist']),

 dict(slug='adhd-exercise-physiologist', group='profession',
      seo='ADHD exercise physiologist: benefits and funding',
      title='ADHD and exercise physiology.',
      description='How an exercise physiologist helps with ADHD, exercising safely on stimulants, and funding through a GP care plan. In person in Bundall on the Gold Coast.',
      lede='Exercise has a measurable effect on attention, and stimulants change how it should be prescribed. ADHDme’s exercise physiologist is on the Gold Coast.',
      who=exercise_physiologists, who_heading='Exercise physiology in the network',
      who_note='Sees people in person.',
      sections=[
       ('What the evidence supports', [
        'Twenty to thirty minutes of moderate aerobic exercise gives a small to moderate lift in attention and executive function for about an hour afterwards. That hour is useful directly before study or demanding work. Aerobic exercise has the strongest evidence. Mind-body exercise shows a small effect, and there are too few studies of coordination exercise to say.',
        'Exercise adds to treatment and does not replace it. The effect is modest and short-lived, and decisions about medication stay with your prescriber.']),
       ('How stimulants change the prescription', [
        'Stimulants raise resting heart rate, so standard age-based heart-rate zones overstate effort. A good exercise physiologist uses perceived exertion and the talk test instead. Appetite suppression means many people start a session under-fuelled. Pre-workout caffeine adds to the stimulant’s effect on heart rate and blood pressure, so it is best dropped.',
        'If you have chest pain, fainting, sustained palpitations or unusual breathlessness on a stimulant, stop and see a doctor. An exercise physiologist who works with ADHD should ask for your medication list, including when you take it, and record your resting heart rate and blood pressure at the start.']),
       ('Making exercise stick', [
        'Dropping out usually comes down to executive function more than motivation, so the design of the program matters. Short sessions at a fixed time, little set-up, variety, quick feedback and someone expecting you all help. A minimum session you can always manage, and a rule of never missing twice, does more than an ambitious plan.']),
       ('How to fund it', [
        'You can see an exercise physiologist under a GP’s chronic condition management plan. It gives a partial Medicare rebate on up to five allied health sessions a calendar year, shared across all allied health. Your GP decides whether ADHD can be the chronic condition on the plan; it is lifelong, so it is worth asking. The NDIS, DVA and private health extras are other common routes, and the Gold Coast practice accepts all three.',
        f'To find an exercise physiologist elsewhere, ESSA’s public directory lists accredited exercise physiologists by suburb: {a("essa.org.au", "https://www.essa.org.au/")}. The network’s {a("GPs", GP_PANEL)} can write the plan.']),
       ('In the network', [
        f'{a("Sarah Savage", "sarah-savage.html")} is the senior exercise physiologist at Atlantis Recovery Centre in Bundall. She takes an “exercise as medicine” approach using Pilates, Functional Range Conditioning and hydrotherapy, and has a particular interest in older adults. The practice quotes its fee when you book.']),
      ],
      faqs=[
       ('Can exercise replace ADHD medication?', 'No. Exercise gives a modest lift in attention for about an hour after a session, and medication decisions stay with your prescriber.'),
       ('Is exercise physiology covered by Medicare for ADHD?', 'It can be, under a GP chronic condition management plan, which gives a partial rebate on up to five allied health sessions a year. Your GP decides whether ADHD is the qualifying condition.'),
       ('Is it safe to exercise on stimulant medication?', 'For most people, yes, with some changes: go by effort instead of heart-rate zones, eat before training and skip caffeine pre-workouts. Stop and see a doctor if you have chest pain, fainting or sustained palpitations.'),
       ('Does ADHDme have an exercise physiologist?', 'Yes: Sarah Savage at Atlantis Recovery Centre in Bundall, on the Gold Coast. Elsewhere, ESSA’s directory lists accredited exercise physiologists near you.'),
      ],
      related=['adhd-treatment-after-diagnosis', 'adhd-doctor-gold-coast', 'adhd-coach', 'adhd-occupational-therapist']),

 dict(slug='adhd-psychologist', group='profession',
      seo='ADHD psychologist: assessment, therapy, costs',
      title='ADHD psychologists: assessment and therapy.',
      description=f'ADHD psychologists assess, diagnose and provide therapy. With a GP’s Mental Health Treatment Plan, Medicare pays {REBATE_REG} or {REBATE_CLIN} a session.',
      lede='Psychologists assess, diagnose and treat ADHD with therapy, but can’t prescribe. ADHDme lists psychologists in Brisbane, on the Gold Coast and online.',
      who=psychologists, who_heading='The psychologists in the network',
      who_note='Brisbane and online psychologists offer telehealth. The Gold Coast clinic sees people in person.',
      sections=[
       ('What an ADHD psychologist does', [
        'Assessment includes a developmental history, rating scales, sometimes cognitive testing, and a written report. Not all psychologists in the network assess. Those who do say so on their profile.',
        'Therapy for ADHD includes cognitive behavioural therapy adapted for ADHD, acceptance and commitment therapy and dialectical behaviour therapy skills. It often also deals with the shame, anxiety and low mood that can follow a late diagnosis. Each psychologist lists their approaches on their profile.',
        'A psychologist does not prescribe. If you want medication, the psychologist works alongside a GP or psychiatrist.']),
       ('Psychologist, clinical psychologist or provisional psychologist', [
        f'All three are registered with AHPRA. A clinical psychologist has completed an endorsed postgraduate program, and their sessions attract a higher Medicare rebate: {REBATE_CLIN} a session, compared with {REBATE_REG} for a registered psychologist. A provisional psychologist is completing supervised registration under a registered psychologist, and their fee and Medicare position differ. The network has all three, and each profile shows which one the psychologist is.']),
       ('What it costs', [
        PSY_COST_PARA,
        'Any GP can write a Mental Health Treatment Plan, and you need one to claim the rebate. The network’s GPs can write one, and so can your own GP.']),
       ('Choosing a psychologist', [
        'Start with the chips under each name on The Network page. They let you find neuroaffirming, trauma-informed, assessment, children, teens, adults, eating disorders, perinatal or a particular therapy. Then read the profile, which describes who the psychologist sees and how they work, and gives the fee.']),
      ],
      faqs=[
       ('Can a psychologist diagnose ADHD in Australia?', 'Yes. A psychologist can assess and diagnose ADHD and write a report, but cannot prescribe medication.'),
       ('How much does an ADHD psychologist cost?', f'Fees are on each psychologist’s profile. With a Mental Health Treatment Plan, Medicare pays back {REBATE_REG} a session for a registered psychologist and {REBATE_CLIN} for a clinical psychologist, for up to 10 sessions a year.'),
       ('Do I need a referral to see an ADHD psychologist?', 'No referral needed to book. You need a Mental Health Treatment Plan from a GP to claim the Medicare rebate.'),
       ('Can I see an ADHD psychologist by telehealth?', 'Yes. The network’s Brisbane and online psychologists offer telehealth, with the same Medicare rebate as in person. The Gold Coast clinic sees people in its rooms.'),
      ],
      related=['adhd-psychologist-brisbane', 'adhd-assessment-online', 'adhd-treatment-after-diagnosis', 'adhd-assessment-queensland']),

 dict(slug='adhd-psychologist-brisbane', group='profession',
      seo='ADHD psychologist Brisbane: assessment, telehealth',
      title='ADHD psychologist in Brisbane.',
      description='Eight ADHD psychologists at GOALS Psychology in Fortitude Valley and Neutral Minds in Ashgrove. ADHD and autism assessment, therapy and telehealth.',
      lede='ADHD and autism assessment and therapy at GOALS Psychology in Fortitude Valley and Neutral Minds Psychology in Ashgrove, for children through to adults.',
      who=brisbane_psychologists, who_heading='Psychologists with rooms in Brisbane',
      who_note='All also offer telehealth. Fees are on each profile.',
      sections=[
       ('The two clinics', [
        f'<strong>GOALS Psychology, Fortitude Valley.</strong> {profiles.GOALS_ACCESS}. Sessions are fifty minutes and booked on the clinic’s Halaxy page. Some of its psychologists also visit homes, schools and community settings. Each profile shows the fee and Medicare position, and says so if a fee is not published.',
        f'<strong>Neutral Minds Psychology, Ashgrove.</strong> This is {a("Jessica Katsamatsas", "jessica-katsamatsas.html")}’s practice. She works with neurodivergent adults in a neurodiversity-affirming, trauma-informed way, in Ashgrove and by telehealth Australia-wide.']),
       ('Assessment in Brisbane', [
        f'{a("Lachlan Avent", "lachlan-avent.html")} and {a("Meera Lakhani", "meera-lakhani.html")} do ADHD and autism assessments at GOALS for children, teenagers and adults. Meera is an educational and developmental psychologist and also does cognitive assessments. Psychologists assess and diagnose but do not prescribe. For medication, see {a("ADHD GP in Brisbane", "adhd-gp-brisbane.html")}.']),
       ('What it costs', [PSY_COST_PARA]),
       ('Who sees whom', [
        f'Toddlers and early intervention: {a("Lauren Poulos", "lauren-poulos.html")} and {a("Kate Row", "kate-row.html")}. Young people and families: {a("Ellie Putland", "ellie-putland.html")}. Eating disorders and perinatal mental health: {a("Samantha Courtney", "samantha-courtney.html")}. Refugee and newly arrived clients: {a("Alice Bui", "alice-bui.html")}. Neurodivergent adults: {a("Jessica Katsamatsas", "jessica-katsamatsas.html")}. The chips on The Network page show the same information.']),
      ],
      faqs=[
       ('Where are the ADHD psychologists in Brisbane?', 'At GOALS Psychology in Fortitude Valley, which has level access and one hour of free client parking, and Neutral Minds Psychology in Ashgrove. All of them also offer telehealth.'),
       ('Can I get an ADHD assessment from a psychologist in Brisbane?', 'Yes. Lachlan Avent and Meera Lakhani at GOALS Psychology assess ADHD and autism in children, teenagers and adults.'),
       ('Is there parking?', 'Yes. GOALS Psychology has level access from a same-level car park, with one hour of free client parking in the centre.'),
       ('Do I need a referral?', 'No referral needed to book. To claim the Medicare rebate, you need a Mental Health Treatment Plan from a GP.'),
      ],
      related=['adhd-psychologist', 'adhd-gp-brisbane', 'adhd-doctor-gold-coast', 'adhd-occupational-therapist']),

 dict(slug='adhd-occupational-therapist', group='profession',
      seo='ADHD occupational therapist: help with daily life',
      title='ADHD occupational therapist.',
      description='How an occupational therapist helps with ADHD routines at home and school, and how OT is funded through the NDIS or a GP plan. Paediatric OT in Brisbane.',
      lede='An occupational therapist adapts tasks and spaces so mornings, homework and home life work better. ADHDme lists one paediatric OT, in Brisbane.',
      who=occupational_therapists, who_heading='Occupational therapy in the network',
      who_note='In clinic, at home, at school and by telehealth.',
      sections=[
       ('What an OT does for ADHD', [
        'For children, OT uses play to build the skills home and school ask for. It covers sensory needs, routines that hold up on a bad morning, and reports for school, the NDIS or a functional capacity assessment. Some sessions happen in the clinic and some at home or school, where the difficulty shows up.',
        'For adults, OT covers the systems of daily life, from a morning routine to how a workspace is set up, and workplace adjustments. The network’s OT works with children, and the network is looking for an OT who works with adults.']),
       ('OT, psychology or coaching', [
        'A psychologist works on thoughts, feelings and behaviour, and can assess and diagnose. A coach works on executive function and accountability, and coaching is not a registered health profession. An occupational therapist is AHPRA-registered and works on function: the task, the environment and the skill. Success is measured by whether your day goes better.']),
       ('How it is funded', [
        'The practice quotes its fee when you book. A Mental Health Treatment Plan does not cover occupational therapy. The NDIS covers it for participants with OT in their plan, private health extras often do, and a GP’s chronic condition management plan gives a partial Medicare rebate on up to five allied health sessions a year, shared across disciplines.']),
       ('In the network', [
        f'{a("Flynn Simonis", "flynn-simonis.html")} is a registered occupational therapist at GOALS Psychology in Fortitude Valley, Brisbane. Flynn works with children in clinic, at home and at school, and writes functional capacity assessment reports. You book on the clinic’s Halaxy page.']),
      ],
      faqs=[
       ('Does an occupational therapist treat ADHD?', 'Yes, by working on function: routines, sensory needs, the environment and the skills daily life needs. An OT does not diagnose ADHD or prescribe.'),
       ('Is ADHD occupational therapy covered by Medicare?', 'Partly, under a GP chronic condition management plan, which gives a rebate on up to five allied health sessions a year. A Mental Health Treatment Plan does not cover OT, but the NDIS and private health extras often do.'),
       ('Does ADHDme have an occupational therapist?', 'Yes, one, who works with children in Brisbane. The network is looking to add occupational therapy for adults with ADHD.'),
      ],
      related=['adhd-treatment-after-diagnosis', 'adhd-psychologist-brisbane', 'adhd-coach', 'adhd-exercise-physiologist']),

 dict(slug='adhd-coach', group='profession',
      seo='ADHD coaching in Australia: costs and JobAccess',
      title='ADHD coaching in Australia.',
      description='ADHD coaching in Perth, Sutherland and online, what a session costs, and how JobAccess can fund it if you work at least eight hours a week.',
      lede='ADHD coaching is practical help with starting, planning and finishing tasks. It isn’t therapy, and coaching isn’t a registered health profession.',
      who=coaches, who_heading='The coaches in the network',
      who_note='Six coaches at REACH in Perth, and Alex Lawson in Sutherland. All also work online.',
      sections=[
       ('What coaching covers', [
        'A coach works with you on executive function in your actual week, such as the task you keep putting off or the plan that falls apart by Wednesday. Sessions are practical and focus on what comes next. A coach does not assess, diagnose or treat. If the difficulty is mood, anxiety or trauma, see a psychologist.',
        'The six REACH coaches trained at the ADHD Coaching Academy (ADDCA), and most hold an International Coaching Federation credential. Alex Lawson completed the PESI ADHD Coaching Course. Coaching is unregulated, so check a coach’s training wherever you look.']),
       ('Who pays', [
        f'If you work or are self-employed for at least eight hours a week, the Employment Assistance Fund through JobAccess covers ADHD coaching as specialist mental health support. REACH puts the amount at around {JOBACCESS} a year including GST, indexed. You apply with supporting documents from a GP or specialist, and you can ask for an exemption so you don’t have to disclose the diagnosis to your employer. REACH runs free sessions to help with the application.',
        'REACH is not a registered NDIS provider, but it says self-managed and plan-managed participants can still claim session fees. For children, the practice says the NDIS is usually the only funding option.']),
       ('The coaches', [
        'The six REACH coaches taught for between two and three decades each, in classrooms, gifted and talented programs, early childhood and secondary schools. Alex Lawson taught high school for almost a decade, worked in law before that, and has ADHD himself. Each profile says who that coach sees.']),
      ],
      faqs=[
       ('Is ADHD coaching covered by Medicare or the NDIS?', 'Medicare does not cover it, but JobAccess can if you work at least eight hours a week. Self-managed and plan-managed NDIS participants can often claim it, and for children the NDIS is usually the only option.'),
       ('What is the difference between an ADHD coach and a psychologist?', 'A psychologist is AHPRA-registered, can assess and diagnose, and treats with therapy. A coach is unregulated and works on executive function and accountability, and many people see both.'),
       ('Can I do ADHD coaching online?', 'Yes. All the coaches work online. REACH also sees people in Perth, and Lawson ADHD Solutions in Sutherland.'),
       ('How much does ADHD coaching cost?', 'REACH quotes its fee when you enquire, and Lawson ADHD Solutions charges $85 for a 55-minute session.'),
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


def short(p):
    """The page's own title, as people see it in the H1, for the links between these pages."""
    return p['title'].rstrip('.')


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


# Sections and answers open on demand, so a page shows its topics and questions first.
SUMMARY = 'flex items-center justify-between gap-6 cursor-pointer list-none [&::-webkit-details-marker]:hidden'
PLUS = ('<span class="shrink-0 w-8 h-8 rounded-full border border-[#e8e6df] flex items-center justify-center text-[#1a1c1c] '
        'transition-transform group-open:rotate-45" aria-hidden="true"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></span>')


def prose(sections):
    out = []
    for i, (h, blocks) in enumerate(sections):
        parts = []
        for b in blocks:
            if isinstance(b, tuple) and b[0] == 'list':
                parts.append('<ul class="mt-4 space-y-3 pl-5 list-disc marker:text-[#f1bc31]">' + ''.join(f'<li class="{P}">{item}</li>' for item in b[1]) + '</ul>')
            else:
                parts.append(f'<p class="mt-4 {P}">{b}</p>')
        out.append(f'<details class="group border-t border-[#e8e6df] py-5"><summary class="{SUMMARY}"><h2 id="s{i}" class="text-[19px] sm:text-[21px] font-bold tracking-tight text-[#1a1c1c]">{esc(h)}</h2>{PLUS}</summary>{"".join(parts)}</details>')
    return ''.join(out)


def faq_section(faqs):
    items = ''.join(
        f'<details class="group py-5 border-t border-[#e8e6df]"><summary class="{SUMMARY}"><h3 class="text-[17px] font-bold text-[#1a1c1c]">{esc(q)}</h3>{PLUS}</summary>'
        f'<p class="mt-2 {P}">{esc(ans)}</p></details>' for q, ans in faqs)
    return f'<section aria-labelledby="faq-title" class="mt-14"><h2 id="faq-title" class="{H2}">Common questions</h2><div class="mt-4">{items}</div></section>'


def related_section(p):
    links = ''.join(
        f'<li><a class="group block rounded-2xl bg-white border border-[#e8e6df] p-5 hover:border-[#1a1c1c]/30 transition-colors" href="{r}.html">'
        f'<span class="block text-[17px] font-bold text-[#1a1c1c] group-hover:underline decoration-[#f1bc31] decoration-2 underline-offset-4">{esc(short(BY_SLUG[r]))}</span></a></li>'
        for r in p['related'])
    return f'''<section class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pb-16" aria-labelledby="related-title">
<h2 id="related-title" class="text-[15px] font-bold text-[#5f5e59]">Related pages</h2>
<ul class="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 list-none p-0 m-0">{links}</ul>
<p class="mt-6 text-[15px] font-semibold text-[#5f5e59]"><a class="hover:text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="{HUB}.html">All ADHD care pages</a></p>
</section>'''


def banner():
    return f'''<section class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pb-12">
<div class="p-8 md:p-12 rounded-3xl bg-[#f1bc31] border border-black/10 flex flex-col lg:flex-row items-center justify-between gap-8 text-center lg:text-left">
<div class="max-w-xl"><h2 class="text-[32px] sm:text-[40px] font-extrabold text-on-surface tracking-tight leading-tight">Ready to find your clinician?</h2></div>
<div class="flex flex-col items-center lg:items-end gap-2.5 shrink-0"><a class="{CTA_DARK}" href="{PROFILE}">Find your clinician {ARROW}</a>
<p class="text-[13px] text-black/75 font-medium">No account or sign-up needed.</p></div>
</div></section>'''


def jsonld(p):
    url = f'{SITE}/{p["slug"]}.html'
    graph = [
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': p['seo'], 'description': p['description'],
         'inLanguage': 'en-AU', 'isPartOf': {'@id': SITE + '/#site'}},
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
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pt-6 pb-4">
<a class="inline-flex items-center gap-2 h-11 text-[15px] font-bold text-[#1a1c1c]" href="{HUB}.html">{profiles.ARROW_BACK}ADHD care</a>
<h1 class="hero-in mt-4 max-w-[22ch] text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-[#1a1c1c]">{esc(p['title'])}</h1>
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
HUB_DESCRIPTION = 'ADHDme guides to ADHD care in Australia by city, by profession and after a diagnosis. Each lists local clinicians, fees and whether you need a referral.'


def hub_page(head, header, footer):
    groups = ''
    for key, label in GROUPS:
        items = ''.join(
            f'<li><a class="group block py-5 border-t border-[#e8e6df]" href="{p["slug"]}.html">'
            f'<span class="block text-[22px] leading-[1.25] font-extrabold tracking-tight text-[#1a1c1c] group-hover:underline decoration-[#f1bc31] decoration-2 underline-offset-4">{esc(short(p))}</span></a></li>'
            for p in PAGES if p['group'] == key)
        groups += f'<section class="mt-12" aria-labelledby="g-{key}"><h2 id="g-{key}" class="{H2}">{label}</h2><ul class="mt-4 list-none p-0 m-0">{items}</ul></section>'
    url = f'{SITE}/{HUB}.html'
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', '@id': url, 'url': url, 'name': HUB_SEO,
          'description': HUB_DESCRIPTION, 'inLanguage': 'en-AU',
          'hasPart': [{'@type': 'WebPage', 'url': f'{SITE}/{p["slug"]}.html', 'name': p['seo']} for p in PAGES]}
    return f'''{head_for(head, HUB, HUB_SEO, HUB_DESCRIPTION)}{header}<main id="main" class="w-full bg-[#FAFAF7]">
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pt-10 pb-16">
<h1 class="hero-in mt-6 max-w-[22ch] text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-[#1a1c1c]">ADHD care, by place and by profession.</h1>
<p class="hero-in hero-in-2 mt-5 max-w-[64ch] text-[19px] leading-[1.6] text-[#5f5e59]">Short guides to ADHD care in Australia, with costs and clinicians.</p>
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
