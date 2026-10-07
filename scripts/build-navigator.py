#!/usr/bin/env python3
"""Build care-navigator.html: "Who could help?" — tap a kind of clinician to read what they do, then a few
tap-only questions lead to a scrolling list of matches, each shown as an expanded profile card.

    python3 scripts/build-navigator.py          # write the page
    python3 scripts/build-navigator.py --check  # exit 1 if the page on disk differs from what would be written

Owns care-navigator.html in full. Edit TYPES, NEEDS, QUESTIONS or DOMAINS here and rebuild.

Every step is a tap: no typing, no speech, no swiping (the owner's rules). A kind's sheet leads only to
"Help me choose", which keeps that kind as a filter and asks who it is for, what would help most, what
matters most and whether location matters; "Not sure?" on the first screen asks the same without a kind.
An answer nobody remaining fits is never offered, and a question left with nothing to choose between is
skipped. The matching is plain rules, no AI: a clinician is in the list when they see the person it is
for, can be met the way asked, and work on what was picked; a preference narrows the list further unless
nobody would be left. The two pinned GPs lead whenever they are in the list (either may come first), as
on The Network; then how directly each works on it (a reason quoted from their own profile beats a tag),
then somebody in the visitor's own place, then an online diary before an enquiry form.

Everything comes from CLINICIANS in build-profiles.py, so a clinician added there joins the navigator on
the next build, in the right kind, with nothing to edit here. The reasons shown under "Why they fit" are
DOMAINS below, in the clinician's own words. This screen has no word limit (the owner's request), so each
kind carries a full line and each match a full card; the overwhelm check exempts it.

The page shell (head, header, footer) is lifted from how-it-works.html at build time, like the search
pages, so header and footer changes reach it on rebuild. Without JavaScript the kind cards are plain
links to their tab on The Network.
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
OUT = ROOT / 'care-navigator.html'
SLUG = 'care-navigator'

spec = importlib.util.spec_from_file_location('profiles', ROOT / 'scripts' / 'build-profiles.py')
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)
BY_ID = {c['id']: c for c in profiles.CLINICIANS}


def esc(text):
    return html.escape(text, quote=True)


# ---------------------------------------------------------------- reasons, in the clinicians' own words
# Where ADHD gets in the way, and who works on each part of it. who: (clinician id, why), the why quoted from
# the profile (a chip or an experience line), so a card can never claim a focus the profile does not
# declare. These are the strongest matches in the navigator and the reason printed under a name.
DOMAINS = [
 dict(key='school', label='School', tint='#f1bc31', aspects=[
  dict(key='focus', label='Concentrating in class', who=[
   ('fiona-alexander', 'Executive functioning · Students & families'),
   ('romney-taylor', 'Executive functioning · Students'),
   ('debbie-hirte', 'Executive functioning · Children & teens'),
   ('flynn-simonis', 'Paediatric OT · Home & school visits')]),
  dict(key='homework', label='Homework and deadlines', who=[
   ('fiona-alexander', 'Executive functioning · Able & gifted learners'),
   ('erin-lysle', 'Executive functioning · Self-confidence'),
   ('romney-taylor', 'Executive functioning · Students'),
   ('debbie-hirte', 'Executive functioning · Gifted & talented'),
   ('hannah-gray', 'Students & early career · Organisation & follow-through')]),
  dict(key='friends', label='Friendships at school', who=[
   ('erin-lysle', 'Social skills · Self-confidence'),
   ('flynn-simonis', 'Group social and movement programs for children'),
   ('ellie-putland', 'Young people · Trauma-informed')]),
  dict(key='system', label='School support and adjustments', who=[
   ('debbie-hirte', 'Co-designing Individual Education Plans with families and schools'),
   ('meera-lakhani', 'Educational & developmental · Previously a psychologist in a school'),
   ('flynn-simonis', 'FCA report writing · Home & school visits'),
   ('lachlan-avent', 'Autism & ADHD assessment · Children to adults')]),
 ]),
 dict(key='work', label='Work', tint='#cfe4f6', aspects=[
  dict(key='done', label='Starting and finishing tasks', who=[
   ('fiona-alexander', 'Executive functioning'),
   ('kate-dallimore', 'Executive functioning · Trauma-informed'),
   ('donna-italiano', 'Executive functioning · Emotional regulation'),
   ('romney-taylor', 'Executive functioning · Advocacy & inclusion'),
   ('alex-lawson', 'Executive functioning · Adults, students & parents'),
   ('hannah-gray', 'Organisation, procrastination and follow-through in study and work'),
   ('richard-hostiadi', 'ADHD at work · Men’s mental health'),
   ('shwetha-murthy', 'Men at work · Parents & carers')]),
  dict(key='burnout', label='Stress and burnout', who=[
   ('jessica-katsamatsas', 'Anxiety, burnout, low self-esteem'),
   ('kate-dallimore', 'Ongoing stress, anxiety, overwhelm'),
   ('jeff-leech', 'Trauma, anxiety, depression and performance'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed'),
   ('tracey-dale', 'Burnout & life transitions · EMDR'),
   ('canice-curtis', 'Mental health after major life changes or disasters'),
   ('richard-hostiadi', 'Real insight into demanding, high-pressure work')]),
  dict(key='confidence', label='Confidence and handling feedback', who=[
   ('erin-lysle', 'Self-confidence'),
   ('jessica-katsamatsas', 'Low self-esteem · Neurodivergent adults'),
   ('donna-italiano', 'Emotional regulation · Neurodivergent-affirming')]),
  dict(key='career', label='Career decisions', who=[
   ('kate-row', 'Career counselling and post-schooling decision making'),
   ('bart-traynor', 'Career and performance pressures · Life transitions'),
   ('romney-taylor', 'Advocacy & inclusion'),
   ('kate-dallimore', 'Mentoring and leadership across healthcare and education')]),
 ]),
 dict(key='home', label='Home', tint='#dbe9d3', aspects=[
  dict(key='routines', label='Daily routines and chores', who=[
   ('donna-italiano', 'Executive functioning · Emotional regulation'),
   ('kate-dallimore', 'Executive functioning'),
   ('flynn-simonis', 'Sensory profiles and functional challenges, in clinic and at home'),
   ('ebony-young', 'Skills practice · Works with your psychologist'),
   ('alexandra-wainwright', 'Skills practice · NDIS support work'),
   ('eliza-keefe', 'Practises life skills with you · Children & teens')]),
  dict(key='parenting', label='Parenting a child with ADHD', who=[
   ('lachlan-avent', 'Triple P Stepping Stones parenting practitioner'),
   ('lauren-poulos', 'PCIT & early intervention · Toddlers & children'),
   ('flynn-simonis', 'Paediatric OT · Parent training'),
   ('debbie-hirte', 'Children & teens'),
   ('gisele-fortkamp', 'Children & parents · Women’s wellbeing'),
   ('nzubechi-oguoma', 'Family therapy · Ages 5+'),
   ('shwetha-murthy', 'Parents & carers · ADHD in families'),
   ('beth-hansen', 'ADHD in parents · Late-identified ADHD'),
   ('kay-walls', 'Mothers & postnatal · ADHD in adult women')]),
  dict(key='emotions', label='Meltdowns and emotional outbursts', who=[
   ('donna-italiano', 'Emotional regulation'),
   ('ellie-putland', 'Young people · CBT, ACT & DBT'),
   ('flynn-simonis', 'Emotional regulation needs in children')]),
  dict(key='body', label='Sleep and physical health', who=[
   ('anubhav-saxena', 'Baseline physical screening · Integrative care'),
   ('sarah-savage', 'Exercise as medicine · Pilates & hydrotherapy'),
   ('anu-saxena', 'Mental health focus · Women’s health'),
   ('lana-hiscock', 'Sleep · Perinatal & postnatal'),
   ('richard-hostiadi', 'Lifestyle medicine'),
   ('sally-mcleod', 'Perimenopause and its interaction with ADHD and mental health')]),
 ]),
 dict(key='relationships', label='Relationships', tint='#fbd8cf', aspects=[
  dict(key='partner', label='Partner and family relationships', who=[
   ('jessica-katsamatsas', 'Relationship difficulties and attachment wounds'),
   ('kate-row', 'Communication and social skills building'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed'),
   ('trisha-harris', 'Teens, adults & couples'),
   ('gisele-fortkamp', 'Level 1 Couples Counselling, Gottman Institute'),
   ('lana-hiscock', 'Neurodiversity, relationships, sleep, perinatal mental health'),
   ('nzubechi-oguoma', 'Family therapy · Ages 5+'),
   ('matthew-persello', 'LGBTQIA+ · Teens 13+ & adults')]),
  dict(key='rejection', label='Rejection sensitivity', who=[
   ('jessica-katsamatsas', 'Attachment wounds · Low self-esteem'),
   ('donna-italiano', 'Emotional regulation'),
   ('paula-garrido', 'ADHD & autism certified · Trauma-informed')]),
  dict(key='social', label='Making and keeping friends', who=[
   ('erin-lysle', 'Social skills'),
   ('kate-row', 'Social skills building'),
   ('flynn-simonis', 'Group social programs for children')]),
  dict(key='conflict', label='Arguments and conflict', who=[
   ('kate-row', 'Communication skills · CBT, ACT & MI'),
   ('ellie-putland', 'DBT · Working collaboratively with families'),
   ('lachlan-avent', 'Emotion Focussed Therapy'),
   ('nzubechi-oguoma', 'Family therapy · Trauma & PTSD'),
   ('tracey-dale', 'DBT, EMDR, Narrative Therapy')]),
 ]),
 dict(key='health', label='Health', tint='#dad9eb', aspects=[
  dict(key='assessment', label='ADHD assessment and diagnosis', who=[
   ('anubhav-saxena', 'Structured adult ADHD assessment'),
   ('anu-saxena', 'Endorsed ADHD prescriber course'),
   ('allen-macbell', 'Children 10 and over, teens and adults'),
   ('lachlan-avent', 'Autism & ADHD assessment'),
   ('meera-lakhani', 'Autism & ADHD assessment · Cognitive assessment'),
   ('chantelle-pin', 'Clinical psychologist · Taking on assessments'),
   ('beth-hansen', 'Late-identified ADHD · ADHD in women'),
   ('sally-mcleod', 'Women & girls · Late diagnosis'),
   ('kay-walls', 'ADHD in adult women · Mothers & postnatal'),
   ('hannah-gray', 'Students & early career · New to assessment'),
   ('natalie-cook', 'Complex adult ADHD · Evidence-based'),
   ('richard-hostiadi', 'Adult ADHD assessments and ongoing management'),
   ('shwetha-murthy', 'A structured assessment of how ADHD has shown up over time'),
   ('bill-liley', 'Whole-person care · 40+ years in practice'),
   ('john-ruberry', 'Access to ADHD care · Mental health'),
   ('jae-cho', 'General psychiatry · ADHD'),
   ('rajitha-de-silva', 'Consultant psychiatrist · Adults'),
   ('heather-mcauliffe', 'Neurodevelopmental assessment · Neurodivergent clinician'),
   ('valeria-urrutia', 'Assessments · Grief & life changes')]),
  dict(key='medication', label='ADHD medication', who=[
   ('anubhav-saxena', 'Baseline cardiovascular and metabolic screening'),
   ('anu-saxena', 'Mental health focus · Endorsed ADHD prescriber course'),
   ('allen-macbell', 'Same doctor from assessment to follow-up'),
   ('yogesh-kalra', 'Continues ADHD medication · Bulk billed'),
   ('beth-hansen', 'General practice with a special interest in mental health and adult ADHD'),
   ('bill-liley', 'Rural generalist GP, more than 40 years of clinical experience'),
   ('hannah-gray', 'General practice with a strong interest in mental health and adult ADHD'),
   ('john-ruberry', 'Strong interest in mental health and ADHD treatment'),
   ('kay-walls', 'Specialist general practice, with a background in mental health'),
   ('natalie-cook', 'Assessing and managing adults with ADHD, including complex cases'),
   ('richard-hostiadi', 'Adult ADHD assessments and ongoing management'),
   ('sally-mcleod', 'Thorough, evidence-based assessment · Teens & adults'),
   ('shwetha-murthy', 'Specialist GP with a particular interest in adult ADHD'),
   ('jae-cho', 'Specialist psychiatrist · ADHD · Trauma-informed'),
   ('rajitha-de-silva', 'Consultant psychiatrist · Anxiety & mood')]),
  dict(key='mood', label='Anxiety and low mood', who=[
   ('jessica-katsamatsas', 'Anxiety, burnout, low self-esteem'),
   ('jeff-leech', 'Anxiety & depression · Schema therapy & ACT'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed'),
   ('ellie-putland', 'Trauma-informed · CBT, ACT & DBT'),
   ('alice-bui', 'Trauma-informed · CALD & refugee clients'),
   ('rajitha-de-silva', 'Anxiety & mood · Culturally sensitive'),
   ('valeria-urrutia', 'Anxiety, low mood, grief, life changes'),
   ('matthew-persello', 'Men’s mental health · Strengths-based, solution-focused'),
   ('canice-curtis', 'Trauma & EMDR · Men’s mental health'),
   ('tracey-dale', 'Burnout & life transitions · EMDR'),
   ('lana-hiscock', 'Perinatal & postnatal · CBT, DBT, ACT'),
   ('sarah-bibo', 'Anxiety, low mood, trauma, eating and body image'),
   ('michael-rehardt', 'Building clinical experience across a range of presentations')]),
  dict(key='complex', label='Complex or overlapping conditions', who=[
   ('jae-cho', 'General psychiatry · Trauma-informed'),
   ('rajitha-de-silva', 'Over 16 years caring for adults'),
   ('natalie-cook', 'Complex cases with psychiatrists and other specialists'),
   ('heather-mcauliffe', 'Collaborative care · Consults with paediatricians and psychiatrists'),
   ('canice-curtis', 'Complex trauma and ADHD · Ages 15+')]),
  dict(key='exercise', label='Exercise, sport and movement', who=[
   ('sarah-savage', 'Exercise as Medicine · Pilates & hydrotherapy'),
   ('lester-rafanan', 'Strength & conditioning · Return to sport'),
   ('yuri-lima', 'Sports rehabilitation · Orthopaedic rehab'),
   ('tom-hissey', 'Runners, HYROX athletes and footballers · Return to function'),
   ('ashleigh-feltham', 'Accredited practising dietitian · Personal trainer'),
   ('kate-dallimore', 'ADHD coach with a background in physiotherapy')]),
  dict(key='pain', label='Pain, injury and recovery', who=[
   ('lester-rafanan', 'Injury and surgery recovery, chronic pain'),
   ('tom-hissey', 'Musculoskeletal physio · Return to function'),
   ('yuri-lima', 'Orthopaedic rehab · PhD, ACL injuries'),
   ('sarah-savage', 'Pilates & hydrotherapy · Older adults')]),
  dict(key='brain', label='Brain mapping and neurotherapy', who=[
   ('lara-schulz', 'QEEG brain mapping · Neurostimulation')]),
 ]),
 dict(key='food', label='Food and diet', tint='#f6d58a', aspects=[
  dict(key='eating', label='Appetite and eating problems', who=[
   ('samantha-courtney', 'Eating disorders · CEDC-MH credentialed'),
   ('ashleigh-feltham', 'Eating disorders · Neurodivergent-affirming'),
   ('anubhav-saxena', 'Baseline physical screening'),
   ('sarah-bibo', 'Eating & body image · Neurodivergent clients')]),
  dict(key='restrictive', label='Restrictive eating', who=[
   ('ashleigh-feltham', 'Restrictive eating and challenges around food')]),
  dict(key='nutrition', label='Healthy eating and nutrition', who=[
   ('ashleigh-feltham', 'Accredited practising dietitian · Personal trainer')]),
 ]),
]


# ---------------------------------------------------------------- kinds of clinician
# The cards on the first screen, in the order a visitor reads them. sub: what the profession covers, as a short
# comma list (benchmarked against Healthdirect's one-line descriptions of each profession); it describes the
# kind, not every person in it, so nothing here claims every psychologist does talk therapy.
# what / good / referral: the sheet a card opens. Kept short on purpose (CLAUDE.md: blocks of about 15
# words). A kind with nobody in it is left off the page.
TYPES = [
 dict(key='gp', label='GP', plural='GPs', tint='#f1bc31',
      sub='Diagnosis, medication, reviews',
      what='Can assess ADHD and prescribe medication, depending on your state, then keep it reviewed.',
      sessions='A long first visit, then reviews', good=['A diagnosis', 'Medication', 'Reviews'],
      referral='No referral needed.'),
 dict(key='psychologist', label='Psychologist', plural='psychologists', tint='#8fc3ec',
      sub='Assessment, therapy, strategies',
      what='What each offers differs: some assess and diagnose, others focus on therapy, strategies or parenting support.',
      sessions='Usually 50-minute sessions', good=['Assessment', 'Therapy', 'Strategies'],
      referral='No referral needed. A GP plan can get you a Medicare rebate.'),
 dict(key='psychiatrist', label='Psychiatrist', plural='psychiatrists', tint='#9dd6cf',
      sub='Complex care, medication',
      what='A specialist doctor for complex or overlapping conditions and harder medication questions.',
      sessions='A first consultation, then reviews', good=['Complex care', 'Medication', 'A second opinion'],
      referral='You need a GP referral, which also gets you the Medicare rebate.'),
 dict(key='coach', label='ADHD coach', plural='ADHD coaches', tint='#f7a58c',
      sub='Routines, focus, study',
      what='Practical help with routines, planning and getting things done. Most here are former teachers.',
      sessions='Weekly or fortnightly, often online', good=['Routines', 'Study', 'Getting organised'],
      referral='No referral needed. Not covered by Medicare.'),
 dict(key='ot', label='Occupational therapist', plural='occupational therapists', tint='#9fd08f',
      sub='Everyday skills, school, sensory',
      what='Routines and strategies for children and teens, built at home, at school or in the clinic.',
      sessions='In the clinic, at home or at school', good=['Daily routines', 'School', 'Sensory needs'],
      referral='No referral needed. The NDIS or private health may help with fees.'),
 dict(key='counselling', label='Counsellor', plural='counsellors and social workers', tint='#e3bf8a',
      sub='Stress, relationships, life changes',
      what='Counsellors and mental health social workers: someone to talk things through with.',
      sessions='In person or online', good=['Stress', 'Relationships', 'Life changes'],
      referral='No referral needed. Some offer Medicare rebates with a GP plan.'),
 dict(key='physio', label='Physiotherapist', plural='physiotherapists', tint='#b7b0f0',
      sub='Pain, injury, movement',
      what='Helps you recover from pain or injury and keep moving, at a pace that suits you.',
      sessions='Hands-on care and exercises', good=['Pain', 'Injury', 'Getting active'],
      referral='No referral needed.'),
 dict(key='ep', label='Exercise physiologist', plural='exercise physiologists', tint='#f2a7c8',
      sub='Exercise, movement, wellbeing',
      what='Exercise built around you and what you enjoy, for focus, sleep and mood.',
      sessions='A program built for you', good=['Movement', 'Sleep', 'Mood'],
      referral='No referral needed.'),
 dict(key='dietitian', label='Dietitian', plural='dietitians', tint='#f6d58a',
      sub='Food, nutrition, eating',
      what='Practical help with food and nutrition, including eating disorders and restrictive eating.',
      sessions='Online, wherever you are', good=['Eating', 'Nutrition', 'Restrictive eating'],
      referral='No referral needed. Private health or the NDIS may help with fees.'),
 dict(key='assistant', label='Therapy assistant', plural='therapy assistants', tint='#dad9eb',
      sub='Skills practice, NDIS support',
      what='Practises skills with you between sessions, supervised by your psychologist.',
      sessions='Between your psychology sessions', good=['Practising skills', 'Routines', 'NDIS support'],
      referral='Works alongside your psychologist. Often funded by the NDIS.'),
 dict(key='neuro', label='Neurotherapy', plural='neurotherapy practitioners', tint='#dbe9d3',
      sub='Brain mapping, training',
      what='Brain mapping (QEEG) and neurotherapy sessions, in the clinic.',
      sessions='An assessment, then training sessions', good=['Brain mapping', 'Training sessions'],
      referral='No referral needed. In person only.'),
 dict(key='allied', label='Allied health', plural='allied health clinicians', tint='#e8e6df',
      sub='Allied health support',
      what='More ways forward beyond medication, from clinicians who understand ADHD.',
      sessions='Set with the practice', good=['Support', 'Skills'],
      referral='No referral needed.'),
]
TYPE_BY_KEY = {t['key']: t for t in TYPES}
CATEGORY_TYPE = {'gp': 'gp', 'psychologist': 'psychologist', 'psychiatrist': 'psychiatrist', 'coach': 'coach',
                 'occupational-therapy': 'ot', 'physiotherapy': 'physio', 'exercise-physiology': 'ep'}


def kind(c):
    """Which card a clinician sits under. Allied health is several professions, told apart by the role."""
    if c['category'] in CATEGORY_TYPE:
        return CATEGORY_TYPE[c['category']]
    role = c['role'].lower()
    if 'neurotherapy' in role:
        return 'neuro'
    if 'dietitian' in role or 'nutritionist' in role:
        return 'dietitian'
    if 'therapy assistant' in role:
        return 'assistant'
    if 'counsellor' in role or 'social worker' in role:
        return 'counselling'
    return 'allied'


# ---------------------------------------------------------------- what they offer, and where it helps
# Two things a visitor picks: the kind of help (a service) and where ADHD gets in the way (an area of life, then
# a part of it). A clinician offers a service, or works on an area, only on the evidence of their own profile: a
# reason quoted under DOMAINS (strength 2), an expertise tag or words in their chips, summary and experience
# (strength 1), or what every one of their kind does (strength 1). Nothing is assumed of a whole profession that
# only some of it does: a psychologist is "someone to talk to" only when their profile names a therapy.
SERVICES = [
 dict(key='diagnosis', label='Find out if it’s ADHD', chip='Finding out if it’s ADHD'),
 dict(key='medication', label='Medication', chip='Medication'),
 dict(key='talk', label='Someone to talk to', chip='Someone to talk to'),
 dict(key='strategies', label='Practical strategies', chip='Practical strategies'),
 dict(key='move', label='Exercise and movement', chip='Exercise and movement'),
]
SERVICE_TAGS = {'assessment': 'diagnosis', 'medication': 'medication', 'psychiatry': 'medication',
                'therapy': 'talk', 'counselling': 'talk',
                'executive-function': 'strategies', 'coaching': 'strategies', 'therapy-assistant': 'strategies',
                'occupational-therapy': 'strategies', 'education': 'strategies', 'social-skills': 'strategies',
                'parenting': 'strategies', 'early-intervention': 'strategies', 'nutrition': 'strategies',
                'physiotherapy': 'move', 'exercise-physiology': 'move'}
SERVICE_WORDS = {'diagnosis': r'\bassess|\bdiagnos', 'medication': r'\bprescrib|\bmedication',
                 'talk': r'\btherap(y|ies|ist|eutic)\b|\bcbt\b|\bact\b|\bdbt\b|\bemdr\b|\bschema\b|\bcounsell|\bpsychotherap',
                 'strategies': r'\bstrateg|\bskills?\b|\bexecutive|\broutines?\b|\bcoach|\bparent'}
# "Exercise and movement" is never read off loose words ("strengths-based", "sport psychology"): it comes from the
# profession (physio, exercise physiology), the expertise tag, or a place in the exercise aspect below.
KIND_SERVICES = {'gp': ['diagnosis', 'medication'], 'psychiatrist': ['diagnosis', 'medication'], 'psychologist': [],
                 'coach': ['strategies'], 'ot': ['strategies'], 'counselling': ['talk'], 'physio': ['strategies', 'move'],
                 'ep': ['strategies', 'move'], 'dietitian': ['strategies'], 'assistant': ['strategies'], 'neuro': [], 'allied': []}
# Who can offer each kind of help at all, whatever words a profile uses: only a doctor prescribes; only a GP,
# psychiatrist or psychologist can diagnose ADHD (an OT's functional assessment or a QEEG brain map is not an
# ADHD diagnosis); and "therapy" in "occupational therapy" or "therapy assistant" is not somebody to talk to.
SERVICE_KINDS = {'diagnosis': ('gp', 'psychiatrist', 'psychologist'), 'medication': ('gp', 'psychiatrist'),
                 'talk': ('psychologist', 'psychiatrist', 'counselling')}
# Areas of life are the domains above. A tag or a kind can place somebody in an area; only a quoted reason
# places them in a particular part of it.
AREA_TAGS = {
    'school': ['education', 'students', 'social-skills'],
    'work': ['performance'],
    'home': ['parenting', 'family', 'early-intervention', 'occupational-therapy', 'therapy-assistant', 'executive-function'],
    'relationships': ['relationships', 'family'],
    'health': ['trauma', 'mental-health', 'perinatal', 'emotional-regulation', 'complex-care', 'physical-health', 'psychiatry',
               'assessment', 'medication', 'lifestyle', 'physiotherapy', 'exercise-physiology', 'integrative', 'mens-health',
               'womens-health', 'neurotherapy', 'brain-mapping'],
    'food': ['eating-disorders', 'nutrition'],
}
KIND_AREAS = {'gp': ['health'], 'psychiatrist': ['health'], 'psychologist': ['health'], 'coach': ['school', 'work', 'home'],
              'ot': ['school', 'home'], 'counselling': ['relationships', 'health'], 'physio': ['health'], 'ep': ['health'],
              'dietitian': ['food', 'health'], 'assistant': ['home', 'school'], 'neuro': ['health'], 'allied': ['health']}
# Words that tie one of a clinician's chips to a service or an area, so the reason shown is the chip that says why.
CHIP_WORDS = {
    'diagnosis': ('assess', 'diagnos'), 'medication': ('medication', 'prescrib'),
    'talk': ('therap', 'cbt', 'act', 'dbt', 'counsel', 'emdr', 'schema'), 'strategies': ('executive', 'skills', 'routine', 'strateg', 'coach', 'parent'),
    'move': ('exercise', 'sport', 'movement', 'pilates', 'strength', 'trainer', 'athlet', 'rehab'),
    'school': ('school', 'student', 'study', 'education', 'learn', 'class'), 'work': ('work', 'career', 'performance', 'burnout', 'leader'),
    'home': ('home', 'parent', 'family', 'routine', 'child', 'toddler'), 'relationships': ('relationship', 'couple', 'partner', 'social', 'friend', 'attachment'),
    'health': ('anx', 'mood', 'trauma', 'depress', 'stress', 'health', 'medic', 'assess', 'sleep', 'pain', 'injur', 'screen'),
    'food': ('eat', 'food', 'nutri', 'diet'),
}


def short(line, room=72):
    return line if len(line) <= room else line[:line.rfind(' ', 0, room)].rstrip(' ,;:·') + '…'


def says(text, key):
    """Whether a line of a profile says `key`: whole words for a service ("ACT" is not "practitioner")."""
    low = text.lower()
    pattern = SERVICE_WORDS.get(key)
    return bool(re.search(pattern, low)) if pattern else any(w in low for w in CHIP_WORDS[key])


def chip_for(c, key):
    """Their own words for why they match: a chip that says it, else the first experience line that does, else
    their role. The practice's name never counts ("Therapy Co" is not therapy)."""
    for chip in c['chips']:
        if says(chip, key):
            return chip
    for line in c['experience']:
        if says(line.replace(c['practice'], ''), key):
            return short(line)
    return c['descriptor'] or c['role']


def evidence(c):
    """The parts of a profile that say what somebody does: chips, summary and experience, lower-cased, without the
    practice's own name."""
    return ' '.join(c['chips'] + [c['description']] + c['experience']).replace(c['practice'], '').lower()


def offers(c):
    """{service: (strength, why)} for the kind of help a clinician offers."""
    out = {}
    for d in DOMAINS:
        for asp in d['aspects']:
            service = {'health:assessment': 'diagnosis', 'health:medication': 'medication', 'health:exercise': 'move'}.get(f"{d['key']}:{asp['key']}")
            if service:
                for cid, why in asp['who']:
                    if cid == c['id']:
                        out.setdefault(service, (2, why))
    tags = profiles.EXPERTISE.get(c['id'], profiles.EXPERTISE_DEFAULT[c['category']])
    text = evidence(c)
    found = [SERVICE_TAGS[t] for t in tags if t in SERVICE_TAGS] + KIND_SERVICES[kind(c)]
    found += [k for k, pattern in SERVICE_WORDS.items() if re.search(pattern, text)]
    for service in found:
        out.setdefault(service, (1, chip_for(c, service)))
    for service, allowed in SERVICE_KINDS.items():
        if kind(c) not in allowed:
            out.pop(service, None)
    if kind(c) == 'gp' and not c.get('assesses', True):
        out.pop('diagnosis', None)                     # a continuation prescriber does not diagnose
    return out


def areas(c):
    """({area: (strength, why)}, {area:aspect: why}) — where in life a clinician works, and on which parts of it."""
    area, aspect = {}, {}
    for d in DOMAINS:
        for asp in d['aspects']:
            for cid, why in asp['who']:
                if cid == c['id']:
                    aspect[f"{d['key']}:{asp['key']}"] = why
                    area.setdefault(d['key'], (2, why))
    tags = profiles.EXPERTISE.get(c['id'], profiles.EXPERTISE_DEFAULT[c['category']])
    for key, wanted in AREA_TAGS.items():
        if set(tags) & set(wanted):
            area.setdefault(key, (1, chip_for(c, key)))
    for key in KIND_AREAS[kind(c)]:
        if key == 'school' and not set(c['ages']) & {'children', 'teens'}:
            continue
        area.setdefault(key, (1, chip_for(c, key)))
    return area, aspect


# ---------------------------------------------------------------- the questions
# At most eight, each answered with one tap: who it is for, whether ADHD has been diagnosed, the kind of help,
# where it gets in the way and which part of that (the old navigator's areas and their parts), what matters
# most, the preferred language, and Final-Algorithm's "Does location matter?". The page only offers an answer
# somebody still in the list can satisfy, so no tap leads to an empty list, and a question left with nothing to
# choose between is answered for the visitor and skipped. A visitor who picked a kind first keeps it as a filter.
def languages():
    """Every language besides English that somebody in the network works in, in the order they appear."""
    seen = []
    for c in profiles.CLINICIANS:
        for lang in c['languages']:
            if lang != 'English' and lang not in seen:
                seen.append(lang)
    return seen


QUESTIONS = [
 dict(key='who', title='Who is it for?', icon='who:me', options=[
  dict(value='adults', label='Me', icon='who:me', chip='For me'),
  dict(value='teens', label='My teenager', icon='who:teen', chip='For my teenager'),
  dict(value='children', label='My child', icon='who:child', chip='For my child')]),
 dict(key='diagnosed', title='Has ADHD been diagnosed?', icon='diag:yes', options=[
  dict(value='yes', label='Yes', icon='diag:yes', chip='Diagnosed'),
  dict(value='no', label='Not yet', icon='diag:no', chip='Not diagnosed yet'),
  dict(value='unsure', label='Not sure', icon='diag:unsure', chip='Not sure about diagnosis')]),
 dict(key='help', title='What kind of help?', icon='need:talk',
      options=[dict(value=v['key'], label=v['label'], icon='help:' + v['key'], chip=v['chip']) for v in SERVICES]
      + [dict(value='any', label='Not sure yet', icon='diag:unsure', chip='Any kind of help')]),
 dict(key='area', title='Where is it getting in the way?', icon='home', options=
      [dict(value=d['key'], label=d['label'], icon=d['key'] if d['key'] != 'food' else 'need:food', chip=d['label']) for d in DOMAINS]
      + [dict(value='any', label='Not sure', icon='diag:unsure', chip='Anywhere in life')]),
 dict(key='aspect', title='Which part of it?', icon='need:focus', options=
      [dict(value=f"{d['key']}:{a['key']}", label=a['label'], area=d['key'],
            icon=f"{d['key']}:{a['key']}", chip=a['label'])
       for d in DOMAINS for a in d['aspects']]
      + [dict(value='any', label='Something else', icon='diag:unsure', chip='Something else')]),
 dict(key='pref', title='What matters most to you?', icon='pref:any', options=[
  dict(value='diary', label='Booking online today', icon='pref:diary', chip='Booking online today'),
  dict(value='lived', label='They have ADHD too', icon='pref:lived', chip='They have ADHD too'),
  dict(value='ndis', label='Using NDIS funding', icon='pref:ndis', chip='NDIS funding'),
  dict(value='bulk', label='Bulk billing', icon='pref:bulk', chip='Bulk billing'),
  dict(value='any', label='Nothing in particular', icon='pref:any', chip='')]),
 dict(key='lang', title='Preferred language?', icon='pref:lang', options=
      [dict(value='any', label='English is fine', icon='pref:lang', chip='')]
      + [dict(value=lang, label=lang, icon='pref:lang', chip='Speaks ' + lang) for lang in languages()]),
 dict(key='where', title='Does location matter?', icon='meet:person', options=[
  dict(value='any', label='Anywhere', sub='Online is fine', icon='meet:online', chip='Online is fine'),
  dict(value='near', label='Near a place', sub='In person if I can', icon='meet:person', chip='')]),
]
assert len(QUESTIONS) <= 9, 'the owner caps the questionnaire at nine questions'


def places():
    """Where somebody in the network sees people in person, busiest first, as the city line on their profile."""
    seen = {}
    for c in profiles.CLINICIANS:
        if c.get('in_person', True) is not False:
            seen[profiles.city(c)] = seen.get(profiles.city(c), 0) + 1
    return [p for p, _ in sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))]


# ---------------------------------------------------------------- icons
# One line drawing per card, inline SVG on a 24-box, stroked in the text colour.
# The old navigator's drawings for each area of life and each part of it.
OLD_ICONS = {
 'school': '<path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H20v14H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5V6.5M20 18v2.5H6.5"/>',
 'work': '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 12h18"/>',
 'home': '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v10h13V10"/><path d="M10 20v-6h4v6"/>',
 'relationships': '<path d="M12 20.5s-8-4.8-8-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 8 2.7c0 5.4-8 10.2-8 10.2z"/>',
 'health': '<path d="M9.5 3h5v6.5H21v5h-6.5V21h-5v-6.5H3v-5h6.5z"/>',
 'school:focus': '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>',
 'school:homework': '<path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19z"/><path d="M14 7l3 3"/>',
 'school:friends': '<circle cx="9" cy="8" r="3.2"/><circle cx="16.5" cy="9.5" r="2.6"/><path d="M3 19c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><path d="M15 13.5c3 0 5.5 2 5.5 5"/>',
 'school:system': '<path d="M3 20h18"/><path d="M5 20V9l7-5 7 5v11"/><path d="M9 20v-5h6v5"/><path d="M12 8v3"/>',
 'work:done': '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 12.5l3 3 5-6"/>',
 'work:burnout': '<rect x="3" y="8" width="15" height="8" rx="2"/><path d="M18 10.5h2.5v3H18"/><path d="M6.5 11v2"/>',
 'work:confidence': '<path d="M7 11v9H4v-9z"/><path d="M7 11l4-7c1.5 0 2.5 1 2.5 2.5V10h5a2 2 0 0 1 2 2.3l-1 6A2 2 0 0 1 17.5 20H7"/>',
 'work:career': '<circle cx="12" cy="12" r="8.5"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
 'home:routines': '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
 'home:parenting': '<circle cx="9" cy="6.5" r="3"/><circle cx="17" cy="11" r="2.2"/><path d="M3.5 20c0-3.6 2.5-6 5.5-6s5.5 2.4 5.5 6"/><path d="M15 20c0-2.4 1-4 2.5-4s2.5 1.6 2.5 4"/>',
 'home:emotions': '<path d="M7 16a4 4 0 0 1-.5-8 5.5 5.5 0 0 1 10.6 1.2A3.4 3.4 0 0 1 17 16"/><path d="M13 13l-2 4h3l-2 4"/>',
 'home:body': '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
 'relationships:partner': '<path d="M9 18s-6-3.6-6-7.6A3.2 3.2 0 0 1 9 8.4a3.2 3.2 0 0 1 6 2c0 4-6 7.6-6 7.6z"/><path d="M15.5 6.5a3 3 0 0 1 5.5 1.7c0 3-4 5.6-5.2 6.3"/>',
 'relationships:rejection': '<path d="M12 20.5s-8-4.8-8-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 8 2.7c0 5.4-8 10.2-8 10.2z"/><path d="M12 7.6l-1.5 4 3 2-1.5 4"/>',
 'relationships:social': '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 14.5c1 1.3 2.2 2 3.5 2s2.5-.7 3.5-2"/><path d="M9.5 9.5h.01M14.5 9.5h.01"/>',
 'relationships:conflict': '<path d="M4 5h9v7H8l-3 2.5V12H4z"/><path d="M13 9h7v7h-1v2.5L16 16h-3v-2"/>',
 'health:assessment': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
 'health:medication': '<rect x="3.5" y="8.5" width="17" height="7" rx="3.5" transform="rotate(-35 12 12)"/><path d="M9 7.8l6 8.4"/>',
 'health:mood': '<path d="M7 17a4 4 0 0 1-.5-8 5.5 5.5 0 0 1 10.6 1.2A3.4 3.4 0 0 1 17 17z"/>',
 'health:eating': '<path d="M6 3v7a2.5 2.5 0 0 0 5 0V3M8.5 3v18"/><path d="M17 3c-2 1.5-2.5 5-2.5 8h2.5v10"/>',
}
ICONS = {
 **OLD_ICONS,
 'diag:yes': '<circle cx="12" cy="12" r="8.5"/><path d="M8 12.5l2.7 2.7L16 9.5"/>',
 'diag:no': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M9 11h6M9 15h4"/>',
 'diag:unsure': '<circle cx="12" cy="12" r="8.5"/><path d="M9.6 9.5a2.5 2.5 0 0 1 4.8.8c0 1.7-2.4 2.2-2.4 3.7M12 17h.01"/>',
 'help:diagnosis': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
 'help:medication': '<rect x="3.5" y="8.5" width="17" height="7" rx="3.5" transform="rotate(-35 12 12)"/><path d="M9 7.8l6 8.4"/>',
 'help:talk': '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12.5h5"/>',
 'help:strategies': '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 12.5l3 3 5-6"/>',
 'help:move': '<circle cx="15" cy="5" r="1.8"/><path d="M4 20l4-7 4 2 2-4 3 1.5"/><path d="M11 15l-1.5 5M14 11l4 2"/>',
 'health:exercise': '<circle cx="15" cy="5" r="1.8"/><path d="M4 20l4-7 4 2 2-4 3 1.5"/><path d="M11 15l-1.5 5M14 11l4 2"/>',
 'health:pain': '<path d="M5 9h2l1.5-3 3 10 2.5-7 1.5 3h4"/><path d="M4 17h16"/>',
 'health:brain': '<path d="M9 4.5A3.5 3.5 0 0 0 5.5 8v1A3 3 0 0 0 4 11.5 3.5 3.5 0 0 0 6 15a3.5 3.5 0 0 0 3 3.5h1V4.5z"/><path d="M15 4.5A3.5 3.5 0 0 1 18.5 8v1a3 3 0 0 1 1.5 2.5 3.5 3.5 0 0 1-2 3.5 3.5 3.5 0 0 1-3 3.5h-1V4.5z"/>',
 'health:complex': '<circle cx="9" cy="10" r="5"/><circle cx="15" cy="14" r="5"/>',
 'food:eating': '<path d="M6 3v7a2.5 2.5 0 0 0 5 0V3M8.5 3v18"/><path d="M17 3c-2 1.5-2.5 5-2.5 8h2.5v10"/>',
 'food:restrictive': '<circle cx="12" cy="13" r="7.5"/><path d="M7 8l10 10"/>',
 'food:nutrition': '<path d="M12 8c-1.6-1.6-6-1.8-6.8 2.6C4.4 15 7.5 21 10 21c.9 0 1.3-.5 2-.5s1.1.5 2 .5c2.5 0 5.6-6 4.8-10.4C18 6.2 13.6 6.4 12 8z"/><path d="M12 8c0-2 1-4 3-5"/>',
 'gp': '<path d="M5 3v6a5 5 0 0 0 10 0V3"/><path d="M10 14v1.5a5.5 5.5 0 0 0 11 0V13"/><circle cx="21" cy="11" r="2"/>',
 'psychologist': '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12.5h5"/>',
 'psychiatrist': '<circle cx="12" cy="12" r="8.5"/><path d="M12 8v8M8 12h8"/>',
 'coach': '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>',
 'ot': '<path d="M8 13V6.5a1.5 1.5 0 0 1 3 0V12M11 11V4.5a1.5 1.5 0 0 1 3 0V12M14 11.5V6a1.5 1.5 0 0 1 3 0v8a6 6 0 0 1-6 6h-1a6 6 0 0 1-4.6-2.2L3.5 15a1.6 1.6 0 0 1 2.4-2.1L8 15"/>',
 'counselling': '<path d="M4 5h9v7H8l-3 2.5V12H4z"/><path d="M13 9h7v7h-1v2.5L16 16h-3v-2"/>',
 'physio': '<path d="M8.5 8.5l7 7"/><path d="M8.2 4.9a2.3 2.3 0 1 0-3.3 3.3 2.3 2.3 0 1 0 3.3-3.3z"/><path d="M19.1 15.8a2.3 2.3 0 1 0-3.3 3.3 2.3 2.3 0 1 0 3.3-3.3z"/>',
 'ep': '<circle cx="14" cy="4.5" r="1.9"/><path d="M9 21l2.5-5.5 3 2.5v3.5M7.5 12l2.5-4 3.5 1 2 3.5H19M10 8l-1.2 5.5"/>',
 'assistant': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M8.5 11l2 2 4-4M8.5 16.5h7"/>',
 'neuro': '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
 'dietitian': '<path d="M12 8c-1.6-1.6-6-1.8-6.8 2.6C4.4 15 7.5 21 10 21c.9 0 1.3-.5 2-.5s1.1.5 2 .5c2.5 0 5.6-6 4.8-10.4C18 6.2 13.6 6.4 12 8z"/><path d="M12 8c0-2 1-4 3-5"/>',
 'need:food': '<path d="M6 3v7a2.5 2.5 0 0 0 5 0V3M8.5 3v18"/><path d="M17 3c-2 1.5-2.5 5-2.5 8h2.5v10"/>',
 'pref:any': '<circle cx="12" cy="12" r="8.5"/><path d="M8 12.5l2.7 2.7L16 9.5"/>',
 'pref:diary': '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16M9 14.5l2 2 4-4"/>',
 'pref:lived': '<path d="M12 20.5s-8-4.8-8-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 8 2.7c0 5.4-8 10.2-8 10.2z"/><path d="M9.5 12.5h5"/>',
 'pref:ndis': '<path d="M4 7h16v12H4z"/><path d="M8 7V5h8v2M4 12h16"/>',
 'pref:bulk': '<circle cx="12" cy="12" r="8.5"/><path d="M14.5 9.3c-.6-.9-1.6-1.4-2.7-1.4-1.6 0-2.8.9-2.8 2.2 0 3 5.8 1.5 5.8 4.4 0 1.3-1.3 2.3-3 2.3-1.3 0-2.4-.6-3-1.6M12 6v1.8M12 16.7v1.8"/>',
 'pref:lang': '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5a13 13 0 0 1 0 17M12 3.5a13 13 0 0 0 0 17"/>',
 'allied': '<path d="M12 20.5s-8-4.8-8-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 8 2.7c0 5.4-8 10.2-8 10.2z"/>',
 'who:me': '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-3.9 3.1-6.5 7-6.5s7 2.6 7 6.5"/>',
 'who:teen': '<circle cx="9" cy="8" r="3.2"/><circle cx="16.5" cy="9.5" r="2.6"/><path d="M3 19c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><path d="M15 13.5c3 0 5.5 2 5.5 5"/>',
 'who:child': '<circle cx="9" cy="6.5" r="3"/><circle cx="17" cy="11" r="2.2"/><path d="M3.5 20c0-3.6 2.5-6 5.5-6s5.5 2.4 5.5 6"/><path d="M15 20c0-2.4 1-4 2.5-4s2.5 1.6 2.5 4"/>',
 'need:diagnosis': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
 'need:medication': '<rect x="3.5" y="8.5" width="17" height="7" rx="3.5" transform="rotate(-35 12 12)"/><path d="M9 7.8l6 8.4"/>',
 'need:talk': '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12.5h5"/>',
 'need:focus': '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>',
 'need:school': '<path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H20v14H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5V6.5M20 18v2.5H6.5"/>',
 'need:mood': '<path d="M7 17a4 4 0 0 1-.5-8 5.5 5.5 0 0 1 10.6 1.2A3.4 3.4 0 0 1 17 17z"/>',
 'need:family': '<path d="M12 20.5s-8-4.8-8-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 8 2.7c0 5.4-8 10.2-8 10.2z"/>',
 'need:body': '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
 'meet:person': '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
 'meet:online': '<rect x="2" y="6" width="13" height="12" rx="2.5"/><path d="M15 10.5 22 7v10l-7-3.5z"/>',
 'meet:either': '<circle cx="12" cy="12" r="8.5"/><path d="M8 12.5l2.7 2.7L16 9.5"/>',
 'row:helps': '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
 'row:sessions': '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
 'row:cost': '<circle cx="12" cy="12" r="8.5"/><path d="M14.5 9.3c-.6-.9-1.6-1.4-2.7-1.4-1.6 0-2.8.9-2.8 2.2 0 3 5.8 1.5 5.8 4.4 0 1.3-1.3 2.3-3 2.3-1.3 0-2.4-.6-3-1.6M12 6v1.8M12 16.7v1.8"/>',
}


def icon(key, cls='nav-ic'):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[key]}</svg>')


ARROW = '<span class="nav-arrow" aria-hidden="true">→</span>'

SEO = 'ADHD care navigator: who could help?'
DESCRIPTION = ('Not sure who to see for ADHD? Tap a GP, psychologist, coach or therapist to see what they do, '
               'or answer a few quick taps to find your match.')


# ---------------------------------------------------------------- shell
def head_for(shell_head):
    url = f'{SITE}/{SLUG}.html'
    subs = [
        (r'<!-- ADHDme - .*? -->', f'<!-- ADHDme - Care navigator (generated by scripts/build-navigator.py) -->'),
        (r'<title>.*?</title>', f'<title>{esc(SEO)} · ADHDme</title>'),
        (r'<meta name="description" content=".*?">', f'<meta name="description" content="{esc(DESCRIPTION)}">'),
        (r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{url}">'),
        (r'<meta property="og:url" content=".*?">', f'<meta property="og:url" content="{url}">'),
        (r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{esc(SEO)}">'),
        (r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{esc(DESCRIPTION)}">'),
        (r'<meta name="twitter:title" content=".*?">', f'<meta name="twitter:title" content="{esc(SEO)}">'),
        (r'<meta name="twitter:description" content=".*?">', f'<meta name="twitter:description" content="{esc(DESCRIPTION)}">'),
        (r'<link rel="preload" as="image" [^>]*>\n', ''),
    ]
    head = shell_head
    for pat, rep in subs:
        head, n = re.subn(pat, lambda _m, r=rep: r, head, count=1, flags=re.S)
        if not n:
            raise SystemExit(f'build-navigator: how-it-works.html has no {pat!r} to rewrite')
    return head.replace('<link rel="stylesheet"', STYLE + '\n<link rel="stylesheet"', 1)


def header_for(shell_header):
    active = ('aria-current="page" class="whitespace-nowrap px-2 lg:px-5 py-2 rounded-full text-[14px] lg:text-[15px] font-semibold '
              'bg-[#1a1c1c] text-white shadow-sm transition-all" href="how-it-works.html"')
    inactive = ('class="whitespace-nowrap px-2 lg:px-5 py-2 rounded-full text-[14px] lg:text-[15px] font-semibold text-[#1a1c1c]/80 '
                'hover:text-[#1a1c1c] hover:bg-black/5 transition-all" href="how-it-works.html"')
    if shell_header.count(active) != 1 or shell_header.count('<a aria-current="page" href="how-it-works.html">') != 1:
        raise SystemExit('build-navigator: how-it-works.html header does not mark How it works current where expected')
    out = shell_header.replace(active, inactive).replace('<a aria-current="page" href="how-it-works.html">', '<a href="how-it-works.html">')
    nav_inactive = ('class="whitespace-nowrap px-2 lg:px-5 py-2 rounded-full text-[14px] lg:text-[15px] font-semibold text-[#1a1c1c]/80 '
                    'hover:text-[#1a1c1c] hover:bg-black/5 transition-all" href="care-navigator.html"')
    nav_active = ('aria-current="page" class="whitespace-nowrap px-2 lg:px-5 py-2 rounded-full text-[14px] lg:text-[15px] font-semibold '
                  'bg-[#1a1c1c] text-white shadow-sm transition-all" href="care-navigator.html"')
    if out.count(nav_inactive) != 1 or out.count('<a href="care-navigator.html">Navigator<span') != 1:
        raise SystemExit('build-navigator: how-it-works.html header has no Navigator item to mark current')
    return out.replace(nav_inactive, nav_active).replace('<a href="care-navigator.html">Navigator<span', '<a aria-current="page" href="care-navigator.html">Navigator<span')


# ---------------------------------------------------------------- the page
STYLE = """<style>
.nav{max-width:980px;margin:0 auto;}
.nav-screen:focus{outline:none;}
.nav-h{font-size:30px;line-height:1.1;font-weight:800;letter-spacing:-.02em;color:#1a1c1c;margin:0;}
.nav-h:focus{outline:none;}
@media (min-width:640px){.nav-h{font-size:38px;}}
.nav-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;list-style:none;padding:0;margin:0;}
@media (min-width:720px){.nav-grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;}}
.nav-tile,.nav-opt{display:flex;font:inherit;color:#1a1c1c;text-decoration:none;text-align:left;background:#fff;border:1.5px solid #e8e6df;border-radius:22px;box-shadow:0 4px 0 #e8e6df;cursor:pointer;transition:transform .15s ease,box-shadow .15s ease,background .2s,border-color .2s;-webkit-tap-highlight-color:transparent;}
.nav-tile:hover,.nav-opt:hover{transform:translateY(-2px);box-shadow:0 6px 0 #e8e6df;}
.nav-tile:active,.nav-opt:active{transform:translateY(3px);box-shadow:0 1px 0 #e8e6df;}
.nav-tile:focus-visible,.nav-opt:focus-visible,.nav-btn:focus-visible,.nav-chip:focus-visible,.nav-back:focus-visible{outline:3px solid #1a1c1c;outline-offset:3px;}
.nav-tile{flex-direction:column;align-items:flex-start;gap:12px;width:100%;height:100%;min-height:150px;padding:18px;}
.nav-tile__text{display:flex;flex-direction:column;gap:4px;min-width:0;margin-top:auto;}
.nav-tile strong{display:block;font-size:18px;line-height:1.2;font-weight:800;letter-spacing:-.01em;}
.nav-tile .nav-sub{font-size:15px;line-height:1.35;color:#5f5e59;}
.nav-badge{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:14px;background:var(--tint,#f6f4ee);color:#1a1c1c;flex:none;}
.nav-ic{width:24px;height:24px;flex:none;}
.nav-grid__wide{grid-column:1/-1;}
.nav-choose{display:flex;align-items:center;justify-content:space-between;gap:16px;width:100%;padding:20px 22px;font:inherit;font-size:18px;font-weight:800;color:#1a1c1c;background:#f1bc31;border:1.5px solid #e2ac24;border-radius:22px;box-shadow:0 4px 0 #c99a1a;cursor:pointer;transition:transform .15s ease,box-shadow .15s ease;}
.nav-choose:hover{transform:translateY(-2px);box-shadow:0 6px 0 #c99a1a;}
.nav-choose:active{transform:translateY(3px);box-shadow:0 1px 0 #c99a1a;}
.nav-choose:focus-visible{outline:3px solid #1a1c1c;outline-offset:3px;}
.nav-arrow{font-weight:800;}
.nav-top{display:flex;align-items:center;gap:12px;margin-bottom:26px;min-height:48px;}
.nav-back{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 16px 0 12px;font:inherit;font-size:15px;font-weight:700;color:#1a1c1c;background:transparent;border:1.5px solid #e8e6df;border-radius:999px;cursor:pointer;}
.nav-back:hover{background:#f6f4ee;}
.nav-top .nav-back{width:44px;padding:0;justify-content:center;flex:none;}
.nav-ring{display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;flex:none;border:3px solid #1a1c1c;border-radius:999px;background:#fff;color:#1a1c1c;}
.nav-ring .nav-ic{width:22px;height:22px;}
.nav-bar{position:relative;flex:1;height:14px;border-radius:7px;background:#ebe8e0;overflow:hidden;}
.nav-bar__fill{position:absolute;left:0;top:0;bottom:0;width:0;min-width:14px;border-radius:7px;background:#f1bc31;box-shadow:inset 0 3px 0 rgba(255,255,255,.35);transition:width .5s cubic-bezier(.34,1.3,.64,1);}
.nav-opts{display:grid;grid-template-columns:1fr;gap:12px;margin-top:22px;}
@media (min-width:640px){.nav-opts{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;}}
.nav-opt{align-items:center;gap:14px;width:100%;min-height:68px;padding:12px 18px;font-size:18px;font-weight:700;}
.nav-opt[aria-pressed="true"]{background:#fdf3d6;border-color:#f1bc31;box-shadow:0 4px 0 #e2ac24;}
.nav-opt .nav-badge{width:40px;height:40px;border-radius:12px;background:#f6f4ee;}
.nav-opts--two{grid-template-columns:repeat(2,minmax(0,1fr));}
.nav-opts--two .nav-opt{flex-direction:column;align-items:flex-start;gap:12px;min-height:132px;padding:18px;}
.nav-opt__text{display:flex;flex-direction:column;gap:2px;}
.nav-opt__sub{font-size:15px;font-weight:500;color:#5f5e59;}
.nav-places{margin-top:22px;}
.nav-places__row{display:flex;flex-wrap:wrap;gap:10px;}
.nav-place{display:inline-flex;align-items:center;min-height:46px;padding:0 18px;font:inherit;font-size:16px;font-weight:700;color:#1a1c1c;background:#fff;border:1.5px solid #e8e6df;border-radius:999px;box-shadow:0 3px 0 #e8e6df;cursor:pointer;transition:transform .15s ease,box-shadow .15s ease;}
.nav-place:hover{transform:translateY(-1px);}
.nav-place:active{transform:translateY(3px);box-shadow:none;}
.nav-place[aria-pressed="true"]{background:#fdf3d6;border-color:#f1bc31;box-shadow:0 3px 0 #e2ac24;}
.nav-place:focus-visible{outline:3px solid #1a1c1c;outline-offset:3px;}
.nav-places__note{margin:12px 0 0;font-size:14px;color:#5f5e59;}
.nav-opt[aria-pressed="true"] .nav-badge{background:#f1bc31;}
.nav-answers{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
.nav-chip{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:0 14px;font:inherit;font-size:14px;font-weight:700;color:#1a1c1c;background:#fdf3d6;border:1.5px solid #ebd8ab;border-radius:999px;cursor:pointer;}
.nav-chip:hover{background:#fbe7b0;}
.nav-count{margin:6px 0 0;font-size:16px;font-weight:600;color:#5f5e59;}
.nav-note{margin:14px 0 0;padding:12px 16px;font-size:15px;line-height:1.45;color:#1a1c1c;background:#f6f4ee;border-radius:14px;}
.nav-list{list-style:none;padding:0;margin:20px 0 0;display:grid;gap:22px;}
.nav-prof{background:#fff;border:1.5px solid #e8e6df;border-radius:24px;box-shadow:0 4px 0 #e8e6df;overflow:hidden;}
.nav-prof__photo{position:relative;aspect-ratio:4/3;background:#f6f4ee;}
.nav-prof__photo img{display:block;width:100%;height:100%;object-fit:cover;object-position:center 30%;}
@media (min-width:720px){.nav-prof{display:grid;grid-template-columns:280px minmax(0,1fr);}.nav-prof__photo{aspect-ratio:auto;min-height:100%;}}
.nav-prof__fit{position:absolute;top:14px;left:14px;padding:4px 11px;font-size:12.5px;font-weight:800;line-height:1.4;border-radius:999px;color:#1a1c1c;background:#fff;border:1px solid #cfcac0;}
.nav-prof__fit[data-fit="2"]{background:#f1bc31;border-color:#e2ac24;}
.nav-prof__fit[data-fit="1"]{color:#fff;background:#1a1c1c;border-color:#1a1c1c;}
.nav-prof__body{display:flex;flex-direction:column;gap:10px;min-width:0;padding:18px 20px 22px;}
.nav-prof__name{margin:0;font-size:24px;line-height:1.15;font-weight:800;letter-spacing:-.02em;}
.nav-prof__name a{color:#1a1c1c;text-decoration:none;}
.nav-prof__name a:hover{text-decoration:underline;text-decoration-color:#f1bc31;text-decoration-thickness:2px;text-underline-offset:4px;}
.nav-prof__meta{margin:-4px 0 0;font-size:15px;font-weight:600;color:#5f5e59;}
.nav-prof__place{display:flex;align-items:center;gap:6px;margin:-4px 0 0;font-size:15px;font-weight:700;color:#1a1c1c;}
.nav-prof__why{padding:14px 16px;background:#fdf3d6;border:1px solid #ebd8ab;border-radius:16px;}
.nav-kicker{display:block;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#8a6a12;}
.nav-prof__reasons{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:8px;}
.nav-prof__reasons li{display:grid;grid-template-columns:18px minmax(0,1fr);column-gap:8px;font-size:14.5px;line-height:1.4;color:#3a382f;}
.nav-prof__reasons li::before{content:'✓';font-weight:800;color:#c99a1a;}
.nav-prof__reasons strong{display:block;font-weight:800;color:#1a1c1c;}
.nav-prof__desc{margin:0;font-size:16px;line-height:1.5;color:#1a1c1c;}
.nav-prof__chips{display:flex;flex-wrap:wrap;gap:8px;}
.nav-prof__facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:2px 0 0;padding-top:12px;border-top:1px solid #e8e6df;}
.nav-prof__facts dt{font-size:12px;font-weight:700;color:#5f5e59;}
.nav-prof__facts dd{margin:2px 0 0;font-size:14px;line-height:1.35;font-weight:700;color:#1a1c1c;}
.nav-prof__go{align-self:flex-start;margin-top:4px;}
.nav-end{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px;}
.nav-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:0 22px;font:inherit;font-size:15px;font-weight:800;color:#1a1c1c;text-decoration:none;background:#fff;border:1.5px solid #e8e6df;border-radius:999px;box-shadow:0 3px 0 #e8e6df;cursor:pointer;}
.nav-btn--go{background:#f1bc31;border-color:#e2ac24;box-shadow:0 3px 0 #c99a1a;}
.nav-btn--dark{color:#fff;background:#1a1c1c;border-color:#1a1c1c;box-shadow:0 3px 0 #000;}
.nav-sheet{width:100%;max-width:100%;max-height:88vh;margin:auto 0 0;padding:0;color:#1a1c1c;background:#fff;border:0;border-radius:28px 28px 0 0;box-shadow:0 -10px 40px rgba(0,0,0,.18);}
@media (min-width:640px){.nav-sheet{width:min(560px,calc(100% - 32px));margin:auto;border-radius:28px;}}
.nav-sheet::backdrop{background:rgba(26,28,28,.45);}
.nav-sheet[open]{animation:nav-up .28s cubic-bezier(.2,.8,.2,1);}
@keyframes nav-up{from{transform:translateY(40px);opacity:0}to{transform:none;opacity:1}}
.nav-sheet__in{position:relative;padding:26px 22px 24px;}
@media (min-width:640px){.nav-sheet__in{padding:32px 32px 30px;}}
.nav-sheet__close{position:absolute;top:14px;right:14px;width:44px;height:44px;display:inline-flex;align-items:center;justify-content:center;font:inherit;font-size:22px;color:#1a1c1c;background:#f6f4ee;border:0;border-radius:999px;cursor:pointer;}
.nav-sheet h2{margin:14px 0 0;font-size:28px;line-height:1.1;font-weight:800;letter-spacing:-.02em;}
.nav-sheet__what{margin:10px 0 0;font-size:17px;line-height:1.5;color:#1a1c1c;}
.nav-facts{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:12px;}
.nav-facts li{display:flex;align-items:flex-start;gap:12px;font-size:16px;line-height:1.4;font-weight:600;}
.nav-ic--row{width:20px;height:20px;margin-top:1px;}
.nav-sheet__act{display:grid;gap:10px;margin-top:22px;}
.nav-sheet__act .nav-btn{width:100%;}
.no-js .nav-js{display:none !important;}
@media (prefers-reduced-motion:reduce){.nav-tile,.nav-opt,.nav-choose{transition:none;}.nav-sheet[open]{animation:none;}}
</style>"""

SCRIPT = r"""<script>
(function(){
  var nav=document.getElementById('nav');if(!nav)return;
  var D=JSON.parse(document.getElementById('nav-data').textContent),W=D.words;
  var sheet=document.getElementById('nav-sheet'),list=document.getElementById('nav-list');
  var cards={};Array.prototype.forEach.call(list.children,function(li){cards[li.getAttribute('data-id')]=li;});
  var ORDER=['who','diagnosed','help','area','aspect','pref','lang','where'];
  var state={},auto={},trail=[];
  var flip=Math.random()<0.5?1:-1;   // which pinned GP leads, decided once per visit, as on The Network
  var MIN=3;   // a results list never shows fewer than three people (the owner's rule)
  function each(sel,fn,root){Array.prototype.forEach.call((root||nav).querySelectorAll(sel),fn);}
  function screen(name){return nav.querySelector('[data-screen="'+name+'"]');}
  function set(v){return v!==undefined&&v!==null&&v!=='any';}
  function prefOk(c,v){
    if(!set(v))return true;
    if(v==='diary')return c.b;if(v==='lived')return c.lv;if(v==='ndis')return c.nd;if(v==='bulk')return c.bb;
    return true;
  }
  function langOk(c,v){return !set(v)||c.g.indexOf(v)!==-1;}
  // What each answer asks of a clinician. An answer narrows the list only once it is given.
  var FITS={
    who:function(c){return c.a.indexOf(state.who)!==-1;},
    help:function(c){return !set(state.help)||!!c.v[state.help];},
    area:function(c){return !set(state.area)||!!c.r[state.area];},
    aspect:function(c){return !set(state.aspect)||!!c.x[state.aspect];},
    pref:function(c){return prefOk(c,state.pref);},
    lang:function(c){return langOk(c,state.lang);}
  };
  function pool(upto){
    var stop=upto?ORDER.indexOf(upto):ORDER.length;
    return D.people.filter(function(c){
      if(state.type&&c.t!==state.type)return false;
      for(var i=0;i<stop;i++){var q=ORDER[i];if(state[q]!==undefined&&FITS[q]&&!FITS[q](c))return false;}
      return true;});
  }
  // The answers somebody still in the list can satisfy: an option nobody fits is never offered.
  function available(q){
    var p=pool(q),out=[];
    each('.nav-opt',function(b){
      var v=b.getAttribute('data-v'),ok=true;
      if(v!=='any'){
        if(q==='who')ok=p.some(function(c){return c.a.indexOf(v)!==-1;});
        else if(q==='help')ok=!(v==='diagnosis'&&state.diagnosed==='yes')&&p.some(function(c){return c.v[v];});
        else if(q==='area')ok=p.some(function(c){return c.r[v];});
        else if(q==='aspect')ok=b.getAttribute('data-area')===state.area&&p.some(function(c){return c.x[v];});
        else if(q==='pref')ok=p.some(function(c){return prefOk(c,v);});
        else if(q==='lang')ok=p.some(function(c){return langOk(c,v);});
      }
      if(q==='aspect'&&v==='any')ok=true;
      if(ok)out.push(v);},screen(q));
    return out;
  }
  // A question with nothing to choose between is answered for the visitor and skipped.
  function settle(q,dry){
    if(state[q]!==undefined)return true;
    if(q==='diagnosed'||q==='where')return false;
    var value;
    if(q==='who'){var ages=available('who');if(ages.length===1)value=ages[0];}
    else if(q==='aspect'&&!set(state.area))value='any';
    else{
      var real=available(q).filter(function(v){return v!=='any';});
      if((q==='help'||q==='area'||q==='aspect')&&real.length<2)value=real.length?real[0]:'any';
      else if((q==='pref'||q==='lang')&&!real.length)value='any';
    }
    if(value===undefined)return false;
    if(!dry){state[q]=value;auto[q]=1;}
    return true;
  }
  function next(){for(var i=0;i<ORDER.length;i++){if(!settle(ORDER[i]))return ORDER[i];}return 'results';}
  function go(name,back){
    var current=nav.querySelector('[data-screen]:not([hidden])');
    if(!back&&current&&current.getAttribute('data-screen')!==name)trail.push(current.getAttribute('data-screen'));
    each('[data-screen]',function(s){s.hidden=s.getAttribute('data-screen')!==name;});
    if(name==='results')render();else if(name!=='start')ask(name);
    var bar=document.querySelector('header'),top=nav.getBoundingClientRect().top+window.pageYOffset-((bar&&bar.offsetHeight)||0)-12;
    if(window.pageYOffset>top)window.scrollTo(0,top);
    var h=screen(name).querySelector('.nav-h');if(h&&name!=='start')h.focus({preventScroll:true});
  }
  // A question on screen: how far along, which answers are on offer, and which is already chosen.
  function ask(name){
    // The bar moves through the eight places a question can take, so it only ever goes forward; a skipped
    // question is a longer step. The words count only the questions actually asked.
    var scr=screen(name),pct=Math.round(100*(ORDER.indexOf(name)+1)/(ORDER.length+1));
    var asked=ORDER.slice(0,ORDER.indexOf(name)).filter(function(q){return state[q]!==undefined&&!auto[q];}).length;
    scr.querySelector('.nav-bar__fill').style.width=pct+'%';
    scr.querySelector('[data-step]').textContent='Question '+(asked+1);
    if(name==='aspect')scr.querySelector('.nav-h').textContent=D.aspectTitle[state.area]||scr.querySelector('.nav-h').textContent;
    var offer=available(name),v=state[name],near=name==='where'&&v!==undefined&&v!=='any';
    each('.nav-opt',function(b){var x=b.getAttribute('data-v');b.hidden=offer.indexOf(x)===-1;b.setAttribute('aria-pressed',String(x===v||(near&&x==='near')));},scr);
    var places=scr.querySelector('[data-places]');
    if(places){places.hidden=!near;each('.nav-place',function(b){b.setAttribute('aria-pressed',String(near&&b.getAttribute('data-place')===v));},places);}
  }
  function fits(c,where){return where==='any'||where===''?c.o:((c.p&&c.city===where)||c.o);}
  function render(){
    var where=state.where,note='';
    var people=D.people.filter(function(c){return (!state.type||c.t===state.type)&&(!state.who||FITS.who(c));});
    // Narrow by each answer in turn; an answer that would leave nobody is set aside, and the page says so.
    function narrow(arr,fn,msg){var b=arr.filter(fn);if(b.length||!arr.length)return b;note=note||msg;return arr;}
    var near=where===undefined?people:people.filter(function(c){return fits(c,where);});
    if(where!==undefined&&!near.length&&where!=='any')near=people.filter(function(c){return c.o;});
    if(where==='any'&&!near.length&&people.length){near=people;note=W.noneOnline;}
    if(auto.who)note=note||W.agesOnly+W.ages[state.who]+'.';
    var picked=narrow(near,FITS.help,W.noneExact);
    picked=narrow(picked,FITS.area,W.noneExact);
    picked=narrow(picked,FITS.aspect,W.noneExact);
    picked=narrow(picked,FITS.pref,W.nonePref);
    picked=narrow(picked,FITS.lang,W.noneLang);
    var local=function(c){return set(where)&&where!==''&&c.p&&c.city===where;};
    if(where===''||(set(where)&&picked.length&&!picked.some(local)))note=note||W.noneNear;
    picked=picked.map(function(c,i){
      var kh=set(state.help)&&c.v[state.help]?c.v[state.help][0]:0;
      var ka=set(state.aspect)&&c.x[state.aspect]?2:(set(state.area)&&c.r[state.area]?Math.min(c.r[state.area][0],set(state.aspect)?1:2):0);
      var diag=(state.diagnosed==='no'||state.diagnosed==='unsure')&&!set(state.help)&&c.v.diagnosis?0.5:0;
      return {c:c,k:Math.max(kh,ka),s:kh+ka+diag+(local(c)?0.5:0),i:i};})
      .sort(function(x,y){return ((y.c.pin?1:0)-(x.c.pin?1:0))||(x.c.pin&&y.c.pin?(x.i-y.i)*flip:0)||(y.s-x.s)||((y.c.b?1:0)-(x.c.b?1:0))||(x.i-y.i);});
    // Never fewer than three: when the answers leave one or two, the list is topped up from the rest of the
    // network, a kind not already in the list first, then whoever works most directly on what was picked.
    // The visitor's own answers about who it is for and where still hold. These carry an "Also worth a look" tag.
    if(picked.length<MIN&&picked.length<D.people.length){
      var have={},kinds={};picked.forEach(function(p){have[p.c.i]=1;kinds[p.c.t]=1;});
      var extra=D.people.filter(function(c){return !have[c.i]&&(!state.who||FITS.who(c))&&(where===undefined||fits(c,where));})
        .map(function(c,i){
          var kh=set(state.help)&&c.v[state.help]?c.v[state.help][0]:0;
          var ka=set(state.aspect)&&c.x[state.aspect]?2:(set(state.area)&&c.r[state.area]?Math.min(c.r[state.area][0],set(state.aspect)?1:2):0);
          return {c:c,k:Math.max(kh,ka),s:kh+ka+(local(c)?0.5:0),i:i,extra:true};});
      var rank=function(x,y){return ((kinds[x.c.t]?0:1)-(kinds[y.c.t]?0:1))*-1||(y.s-x.s)||((y.c.b?1:0)-(x.c.b?1:0))||(x.i-y.i);};
      while(picked.length<MIN&&extra.length){extra.sort(rank);var p=extra.shift();picked.push(p);kinds[p.c.t]=1;}
      note=note||W.toppedUp;
    }
    var asked=set(state.help)||set(state.area),shown={};
    picked.forEach(function(p){
      var c=p.c,li=cards[c.i];shown[c.i]=1;li.hidden=false;
      var reasons=[];
      if(set(state.help)&&c.v[state.help])reasons.push([D.labels.help[state.help],c.v[state.help][1]]);
      if(set(state.aspect)&&c.x[state.aspect])reasons.push([D.labels.aspect[state.aspect],c.x[state.aspect]]);
      else if(set(state.area)&&c.r[state.area])reasons.push([D.labels.area[state.area],c.r[state.area][1]]);
      if(set(state.pref)&&prefOk(c,state.pref))reasons.push([D.chips.pref[state.pref],'']);
      if(set(state.lang)&&langOk(c,state.lang))reasons.push([W.speaks+state.lang,'']);
      if(local(c))reasons.push([W.inPerson+where.split(',')[0],'']);else if(where!==undefined&&c.o)reasons.push([W.online,'']);
      var ul=li.querySelector('[data-reasons]');ul.innerHTML='';
      reasons.forEach(function(r){var x=document.createElement('li'),t=document.createElement('span'),b=document.createElement('strong');
        b.textContent=r[0];t.appendChild(b);if(r[1])t.appendChild(document.createTextNode(r[1]));x.appendChild(t);ul.appendChild(x);});
      li.querySelector('[data-whybox]').hidden=!reasons.length;
      var fit=li.querySelector('[data-fit]');fit.hidden=!asked;
      if(p.extra){fit.hidden=false;fit.textContent=W.also;fit.setAttribute('data-fit','x');}
      else if(asked){fit.textContent=W.fit[p.k];fit.setAttribute('data-fit',String(p.k));}
      list.appendChild(li);
    });
    Object.keys(cards).forEach(function(id){if(!shown[id])cards[id].hidden=true;});
    var n=picked.length;
    document.getElementById('nav-count').textContent=!n?W.none:(n+' '+(n===1?W.one:W.many));
    var noteEl=document.getElementById('nav-note');noteEl.hidden=!note;noteEl.textContent=note;
    var chips=[],t=state.type?D.types[state.type]:null;
    if(t)chips.push(['type',t.label]);
    ORDER.forEach(function(k){
      var v=state[k];if(v===undefined||auto[k])return;
      var label=k==='where'?(v==='any'?D.chips.where.any:v===''?W.elsewhere:W.near+v.split(',')[0]):(D.chips[k]||{})[v];
      if(label)chips.push([k,label]);
    });
    document.getElementById('nav-answers').innerHTML=chips.map(function(c){return '<button type="button" class="nav-chip" data-edit="'+c[0]+'">'+c[1]+' <span aria-hidden="true">✎</span></button>';}).join('');
  }
  function openSheet(type){
    each('[data-role]',function(s){s.hidden=s.getAttribute('data-role')!==type;},sheet);
    sheet.setAttribute('aria-labelledby','role-'+type);
    if(sheet.showModal)sheet.showModal();else sheet.setAttribute('open','');
  }
  function closeSheet(){if(sheet.close)sheet.close();else sheet.removeAttribute('open');}
  function answer(q,v,el){
    state[q]=v;delete auto[q];
    if(q==='area'){delete state.aspect;delete auto.aspect;}
    if(el)each(el.className.indexOf('nav-place')!==-1?'.nav-place':'.nav-opt',function(b){b.setAttribute('aria-pressed',String(b===el));},el.closest('[data-screen]'));
    setTimeout(function(){go(next());},170);
  }
  // Changing an answer can change what later questions offer, so those it decided for the visitor are asked again.
  function edit(k){
    ORDER.slice(ORDER.indexOf(k)).forEach(function(q){if(q===k||auto[q]||(k==='area'&&q==='aspect')){delete state[q];delete auto[q];}});
    go(k);
  }
  function restart(type){state=type?{type:type}:{};auto={};trail=type?['start']:[];}
  nav.addEventListener('click',function(e){
    var el=e.target.closest('[data-type],[data-start],[data-v],[data-place],[data-back],[data-edit],[data-restart]');if(!el)return;
    if(el.hasAttribute('data-type')){e.preventDefault();openSheet(el.getAttribute('data-type'));return;}
    if(el.hasAttribute('data-start')){restart();go(next());return;}
    if(el.hasAttribute('data-v')){
      var q=el.closest('[data-screen]').getAttribute('data-screen'),v=el.getAttribute('data-v');
      if(q==='where'&&v==='near'){   // reveal the places; the answer is the place tapped next
        each('.nav-opt',function(b){b.setAttribute('aria-pressed',String(b===el));},el.closest('[data-screen]'));
        var places=el.closest('[data-screen]').querySelector('[data-places]');places.hidden=false;
        var first=places.querySelector('.nav-place');if(first)first.focus({preventScroll:true});
        places.scrollIntoView({behavior:'smooth',block:'nearest'});return;}
      answer(q,v,el);return;}
    if(el.hasAttribute('data-place')){answer('where',el.getAttribute('data-place'),el);return;}
    if(el.hasAttribute('data-back')){go(trail.pop()||'start',true);return;}
    if(el.hasAttribute('data-edit')){var k=el.getAttribute('data-edit');
      if(k==='type'){restart();go('start');return;}
      edit(k);return;}
    if(el.hasAttribute('data-restart')){restart();go('start');return;}
  });
  sheet.addEventListener('click',function(e){
    if(e.target===sheet){closeSheet();return;}
    var el=e.target.closest('[data-close],[data-choose]');if(!el)return;
    if(el.hasAttribute('data-close')){closeSheet();return;}
    closeSheet();restart(el.getAttribute('data-choose'));go(next(),true);
  });
})();
</script>"""


def card(c, kinds):
    """One match, expanded: photo, who and where, why they fit, their own summary and chips, three facts,
    and the way to their profile. Every card has the same parts in the same order, so scrolling down the
    list reads like turning pages. The script fills in why they fit from the answers."""
    t = TYPE_BY_KEY[kinds[c['id']]]
    first = c['short'].split()[0] if not c['short'].startswith('Dr ') else c['short']
    fig = c['fees']['figures'][0] if c['fees'].get('figures') else None
    if fig and fig[1].endswith(', from'):          # "Initial consultation, from" reads as "From $270 · initial consultation"
        cost = f'From {fig[0]} · {fig[1][:-6][0].lower() + fig[1][1:-6]}'
    else:
        cost = f'{fig[0]} · {fig[1][0].lower() + fig[1][1:]}' if fig else 'Quoted by the practice'
    facts = [('Sees', profiles.ages_line(c).replace('For ', '', 1).capitalize() or 'Ask the practice'),
             ('Cost', cost),
             ('Booking', 'Book online' if profiles.books_online(c) else 'Enquire first')]
    photo = profiles.picture(c, profiles.portrait_size(c), '(min-width: 720px) 280px, 100vw',
                             'loading="lazy" decoding="async"', '')
    return (f'<li class="nav-prof" data-id="{c["id"]}" hidden>'
            f'<div class="nav-prof__photo">{photo}<span class="nav-prof__fit" data-fit hidden></span></div>'
            f'<div class="nav-prof__body">'
            f'<h3 class="nav-prof__name"><a href="{c["slug"]}.html">{esc(c["name"])}</a></h3>'
            f'<p class="nav-prof__meta">{esc(t["label"])} · {esc(c["practice"])}</p>'
            f'<p class="nav-prof__place">{icon("meet:person", "nav-ic nav-ic--row")}{esc(profiles.city(c))}</p>'
            f'<div class="nav-prof__why" data-whybox hidden><span class="nav-kicker">Why they fit</span>'
            f'<ul class="nav-prof__reasons" data-reasons></ul></div>'
            f'<p class="nav-prof__desc">{esc(c["description"])}</p>'
            f'<div class="nav-prof__chips">{profiles.chip_row(c, 3)}</div>'
            f'<dl class="nav-prof__facts">' + ''.join(f'<div><dt>{k}</dt><dd>{esc(v)}</dd></div>' for k, v in facts) + '</dl>'
            f'<a class="nav-btn nav-btn--go nav-prof__go" href="{c["slug"]}.html">View {esc(first)}’s profile {ARROW}</a>'
            f'</div></li>')


def tile(t, count):
    panel = {'gp': 'gps', 'psychologist': 'psychologists', 'psychiatrist': 'psychiatrists', 'coach': 'coaches',
             'ot': 'occupational-therapy', 'physio': 'physiotherapy', 'ep': 'exercise-physiology'}.get(t['key'], 'allied-health')
    return (f'<li><a class="nav-tile" href="the-doctors.html#panel-{panel}" data-type="{t["key"]}" style="--tint:{t["tint"]}" '
            f'aria-haspopup="dialog"><span class="nav-badge">{icon(t["key"])}</span>'
            f'<span class="nav-tile__text"><strong>{esc(t["label"])}</strong><span class="nav-sub">{esc(t["sub"])}</span></span></a></li>')


def role(t, count):
    # One sentence-case list: "A diagnosis, medication, reviews", acronyms (NDIS) kept as they are.
    helps = ', '.join([t['good'][0]] + [g if g[:2].isalpha() and g[:2].isupper() else g[0].lower() + g[1:] for g in t['good'][1:]])
    rows = ''.join(f'<li>{icon("row:" + k, "nav-ic nav-ic--row")}<span><span class="sr-only">{label}: </span>{esc(v)}</span></li>'
                   for k, label, v in (('helps', 'Helps with', helps), ('sessions', 'Sessions', t['sessions']),
                                       ('cost', 'Referral and cost', t['referral'])))
    return (f'<section data-role="{t["key"]}" hidden><span class="nav-badge" style="--tint:{t["tint"]}">{icon(t["key"])}</span>'
            f'<h2 id="role-{t["key"]}">{esc(t["label"])}</h2><p class="nav-sheet__what">{esc(t["what"])}</p>'
            f'<ul class="nav-facts">{rows}</ul>'
            f'<div class="nav-sheet__act"><button type="button" class="nav-btn nav-btn--go" data-choose="{t["key"]}">Help me choose {ARROW}</button></div></section>')


def question(q):
    def option(o):
        label = (f'<span class="nav-opt__text"><span>{esc(o["label"])}</span><span class="nav-opt__sub">{esc(o["sub"])}</span></span>'
                 if o.get('sub') else f'<span>{esc(o["label"])}</span>')
        area = f' data-area="{o["area"]}"' if o.get('area') else ''
        return (f'<button type="button" class="nav-opt" data-v="{esc(o["value"])}"{area} aria-pressed="false">'
                f'<span class="nav-badge">{icon(o["icon"])}</span>{label}</button>')
    extra = ''
    if q['key'] == 'where':
        chips = ''.join(f'<button type="button" class="nav-place" data-place="{esc(p)}">{esc(p.split(",")[0])}</button>' for p in places())
        extra = (f'<div class="nav-places" data-places hidden><div class="nav-places__row" role="group" aria-label="Places">{chips}'
                 f'<button type="button" class="nav-place" data-place="">Somewhere else</button></div>'
                 f'<p class="nav-places__note">Online options still show.</p></div>')
    return (f'<section class="nav-screen" data-screen="{q["key"]}" hidden aria-labelledby="q-{q["key"]}">'
            f'<div class="nav-top"><button type="button" class="nav-back" data-back aria-label="Back"><span aria-hidden="true">←</span></button>'
            f'<span class="nav-ring">{icon(q["icon"])}</span>'
            f'<span class="nav-bar" aria-hidden="true"><span class="nav-bar__fill"></span></span><span class="sr-only" data-step></span></div>'
            f'<h2 id="q-{q["key"]}" class="nav-h" tabindex="-1">{esc(q["title"])}</h2>'
            f'<div class="nav-opts{" nav-opts--two" if q["key"] == "where" else ""}" role="group" aria-labelledby="q-{q["key"]}">'
            f'{"".join(option(o) for o in q["options"])}</div>{extra}</section>')


def state_of(c):
    s = c['schema']
    return s.get('state') or s.get('works_for', {}).get('state') or ''


def build():
    shell = SHELL.read_text(encoding='utf-8')
    head = head_for(shell[:shell.index('<body')])
    header = header_for(shell[shell.index('<body'):shell.index('<main')])
    footer = shell[shell.index('<footer'):]
    footer = footer.replace('<script src="analytics-config.js" defer></script>', SCRIPT + '\n<script src="analytics-config.js" defer></script>', 1)

    kinds = {c['id']: kind(c) for c in profiles.CLINICIANS}
    counts = {t['key']: sum(1 for k in kinds.values() if k == t['key']) for t in TYPES}
    present = [t for t in TYPES if counts[t['key']]]
    # Same order as The Network: pinned GPs first, then online diaries, then enquiries, then CLINICIANS order.
    ordered = sorted(profiles.CLINICIANS, key=lambda c: (c['id'] not in profiles.PINNED, not profiles.books_online(c)))
    people = [dict(i=c['id'], t=kinds[c['id']], a=c['ages'], o=bool(c['telehealth']), p=c.get('in_person', True) is not False,
                   s=state_of(c), city=profiles.city(c), v={k: list(x) for k, x in offers(c).items()},
                   r={k: list(x) for k, x in areas(c)[0].items()}, x=areas(c)[1], pin=c['id'] in profiles.PINNED,
                   b=profiles.books_online(c), lv=bool(c.get('lived')), g=[l for l in c['languages'] if l != 'English'],
                   nd='ndis' in profiles.EXPERTISE.get(c['id'], profiles.EXPERTISE_DEFAULT[c['category']]),
                   bb=bool(c.get('bulk_billed'))) for c in ordered]
    data = dict(
        people=people,
        types={t['key']: dict(label=t['label']) for t in present},
        # How each answer reads back: as a chip on the results, and as the label of a line under "Why they fit".
        chips={q['key']: {o['value']: o['chip'] for o in q['options']} for q in QUESTIONS},
        labels={q['key']: {o['value']: o['label'] for o in q['options']} for q in QUESTIONS},
        aspectArea={f"{d['key']}:{a['key']}": d['key'] for d in DOMAINS for a in d['aspects']},
        aspectTitle={'school': 'What about school?', 'work': 'What about work?', 'home': 'What about home?',
                     'relationships': 'What about relationships?', 'health': 'What about your health?', 'food': 'What about food?'},
        words=dict(matches='Your matches', one='clinician fits.', many='clinicians, best first.', none='No one fits all of that yet.',
                   nonePref='No one fits that preference as well. These fit everything else.',
                   noneLang='No one here speaks that language yet. These fit everything else.',
                   noneOnline='No one here works online for that yet. These see people in person.',
                   agesOnly='Everyone here for this works with ', ages={'adults': 'adults', 'teens': 'teenagers', 'children': 'children'},
                   speaks='Speaks ',
                   inPerson='Sees people in person in ', online='Works online, wherever you are',
                   fit=['Worth considering', 'Good fit', 'Strong fit'], near='Near ', elsewhere='Somewhere else',
                   noneNear='No one sees people in person there yet. These work online.',
                   noneExact='No exact match for that yet. These could still help.',
                   toppedUp='Fewer than three fit all of that, so a few others worth a look are here too.', also='Also worth a look'),
    )
    tiles = ''.join(tile(t, counts[t['key']]) for t in present)
    roles = ''.join(role(t, counts[t['key']]) for t in present)
    questions = ''.join(question(q) for q in QUESTIONS)
    cards = ''.join(card(c, kinds) for c in ordered)

    url = f'{SITE}/{SLUG}.html'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': SEO, 'description': DESCRIPTION, 'inLanguage': 'en-AU',
         'isPartOf': {'@id': f'{SITE}/#site'}, 'breadcrumb': {'@id': url + '#breadcrumb'}},
        {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'ADHDme', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Care Navigator', 'item': url}]}]}
    return f"""{head}{header}<main id="main" class="w-full bg-[#FAFAF7]">
<div id="nav" class="nav px-5 md:px-8 pt-10 pb-20">
<section class="nav-screen" data-screen="start" aria-labelledby="nav-title">
<h1 id="nav-title" class="hero-in text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-[#1a1c1c]">Who could help?</h1>
<p class="hero-in hero-in-2 mt-3 mb-7 text-[17px] leading-[1.5] text-[#5f5e59] max-w-[46ch]">Tap one to see what they do. Not sure? A few taps find your match.</p>
<ul class="nav-grid hero-in hero-in-3">{tiles}<li class="nav-grid__wide nav-js"><button type="button" class="nav-choose" data-start>Not sure? Help me choose {ARROW}</button></li></ul>
</section>
{questions}
<section class="nav-screen" data-screen="results" hidden aria-labelledby="nav-results-title">
<div class="nav-top"><button type="button" class="nav-back" data-back aria-label="Back"><span aria-hidden="true">←</span></button></div>
<h2 id="nav-results-title" class="nav-h" tabindex="-1">Your matches</h2>
<p id="nav-count" class="nav-count" aria-live="polite"></p>
<div id="nav-answers" class="nav-answers"></div>
<p id="nav-note" class="nav-note" hidden></p>
<ul id="nav-list" class="nav-list">{cards}</ul>
<div class="nav-end"><button type="button" class="nav-btn" data-restart>Start again</button><a class="nav-btn nav-btn--dark" href="the-doctors.html">See the whole network</a></div>
</section>
</div>
<dialog id="nav-sheet" class="nav-sheet"><div class="nav-sheet__in"><button type="button" class="nav-sheet__close" data-close aria-label="Close">×</button>{roles}</div></dialog>
</main>
<script id="nav-data" type="application/json">{json.dumps(data, ensure_ascii=False, separators=(',', ':'))}</script>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{footer}"""


def check():
    """Fail the build rather than ship a navigator that would silently drop somebody, or a question without a drawing."""
    for d in DOMAINS:
        if d['key'] not in {'food'} and d['key'] not in ICONS:
            raise SystemExit(f'build-navigator: area {d["label"]} has no icon')
        for asp in d['aspects']:
            if f"{d['key']}:{asp['key']}" not in ICONS:
                raise SystemExit(f'build-navigator: {d["label"]} › {asp["label"]} has no icon')
            for cid, _ in asp['who']:
                if cid not in BY_ID:
                    raise SystemExit(f'build-navigator: {d["label"]} › {asp["label"]} names unknown clinician {cid!r}')
    for c in profiles.CLINICIANS:
        if not offers(c) and not areas(c)[0]:
            raise SystemExit(f'build-navigator: {c["name"]} matches no answer, so no visitor would ever be shown them')
    for q in QUESTIONS:
        for o in q['options']:
            if o.get('icon') and o['icon'] not in ICONS:
                raise SystemExit(f'build-navigator: {q["key"]} › {o["label"]} has no icon {o["icon"]!r}')
    for t in TYPES:
        if t['key'] not in ICONS:
            raise SystemExit(f'build-navigator: kind {t["key"]!r} has no icon')


def main(argv):
    check()
    text = build()
    stale = not OUT.exists() or OUT.read_text(encoding='utf-8') != text
    if '--check' in argv:
        print('care navigator is up to date' if not stale else 'out of date: care-navigator.html; run python3 scripts/build-navigator.py')
        return 1 if stale else 0
    OUT.write_text(text, encoding='utf-8', newline='')
    print(('wrote  ' if stale else 'same   ') + OUT.name)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
