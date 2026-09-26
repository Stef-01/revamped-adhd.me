#!/usr/bin/env python3
"""Build blog post pages and the "From the blog" section on our-story.html.

    python3 scripts/build-blog.py          # write the pages
    python3 scripts/build-blog.py --check  # exit 1 if any page on disk differs from what would be written

Owns: blog-*.html in full, the <!-- BLOG --> … <!-- /BLOG --> section on our-story.html, and the title
and hook lines of each blog card on learn.html (the rest of each card, and where it sits, stay hand-made).
A hand edit to any of that is lost on the next build; put the change here instead, and run --check before
committing so a page that has drifted is caught rather than silently reverted.

A post with `landing=True` opens like a landing page instead of a post: a full-width tinted hero with the
title, a longer lede, the illustration and two calls to action, and then reads as an article, with `h2`
subheadings and lists in the body. Body items are a paragraph string, ('h2', text) or ('list', [items]).

Each post page starts from our-story.html's <head> and then rewrites every tag that names the page,
so the post does not ship Our Story's title, description and canonical URL to crawlers and share
cards. Icons are inline SVG: this site carries no icon font.
"""
import pathlib, re, math, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://www.adhdme.au'
INK = '#1c1917'

ICON = ('viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true" focusable="false"')
ARROW_BACK = f'<svg class="w-4 h-4 shrink-0 transition-transform group-hover:-translate-x-0.5" {ICON}><path d="M19 12H5M11 18l-6-6 6-6"/></svg>'
ARROW_NE = (f'<svg class="w-4 h-4 shrink-0 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" '
            f'{ICON}><path d="M7 17 17 7M8 7h9v9"/></svg>')

# ------------------------------------------------------------ illustrations
def blob(x, y, s, fill='#fdfbf7', face='smile', extras=''):
    eyes = f'<circle cx="43" cy="46" r="3.5" fill="{INK}"/><circle cx="57" cy="46" r="3.5" fill="{INK}"/><circle cx="44" cy="44.5" r="1.3" fill="#fff"/><circle cx="58" cy="44.5" r="1.3" fill="#fff"/>'
    mouths = {'smile': f'<path d="M45 56 Q50 62 55 56" fill="none" stroke="{INK}" stroke-linecap="round" stroke-width="3"/>',
              'grin': f'<path d="M44 55 Q50 65 56 55 Z" fill="{INK}"/><path d="M47 57 Q50 62 53 57 Z" fill="#f1bc31"/>',
              'calm': f'<path d="M46 57 Q50 60 54 57" fill="none" stroke="{INK}" stroke-linecap="round" stroke-width="3"/>'}
    return f'''<g transform="translate({x - 50*s} {y - 50*s}) scale({s})"><ellipse cx="50" cy="96" rx="30" ry="4.5" fill="#000" opacity=".12"/>
<path d="M50 16 C68 16, 78 28, 76 50 C74 64, 82 78, 76 90 C68 98, 32 98, 24 90 C18 78, 26 64, 24 50 C22 28, 32 16, 50 16 Z" fill="{fill}" stroke="{INK}" stroke-width="4.5" stroke-linejoin="round"/>{eyes}{mouths[face]}{extras}</g>'''

def sparkle(x, y, s=1, fill='#f5cf6d'):
    return f'<path transform="translate({x} {y}) scale({s})" d="M0 -14 L3 -3 L14 0 L3 3 L0 14 L-3 3 L-14 0 L-3 -3 Z" fill="{fill}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'

def frame(bg, body, label):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" role="img" aria-label="{label}">
<defs><pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="2" fill="{INK}" opacity=".08"/></pattern></defs>
<rect width="960" height="540" fill="{bg}"/><rect width="960" height="540" fill="url(#dots)"/>{body}</svg>'''

def cover_booking():
    # two steps, browse then book, and a happy blob
    icons = [f'<circle cx="-8" cy="-8" r="20" fill="none" stroke="{INK}" stroke-width="8"/><path d="M7 7 L26 26" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>',
             f'<path d="M-24 2 L-7 19 L25 -15" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>']
    steps = ''.join(f'<g transform="translate({240 + i*260} 200)"><circle r="70" fill="{c}" stroke="{INK}" stroke-width="5"/>{icons[i]}</g>' for i, c in enumerate(['#f5cf6d', '#fdfbf7']))
    arrow = f'<path d="M330 200 H400" stroke="{INK}" stroke-width="7" stroke-linecap="round"/><path d="M385 182 L405 200 L385 218" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    return frame('#f6ecce', steps + arrow + blob(740, 300, 2.4, face='grin') + sparkle(120, 120, 1.3) + sparkle(880, 100, 1, '#f5cf6d') + sparkle(140, 430, .9, '#fdfbf7'), 'A search and a tick with an arrow between them, and a cheerful character')

def cover_body_doubling():
    desk = f'<rect x="150" y="330" width="660" height="24" rx="12" fill="#2f3130" stroke="{INK}" stroke-width="5"/><rect x="330" y="230" width="160" height="100" rx="14" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><rect x="350" y="250" width="120" height="10" rx="5" fill="#e6dfd1"/><rect x="350" y="272" width="90" height="10" rx="5" fill="#e6dfd1"/><rect x="350" y="294" width="105" height="10" rx="5" fill="#f1bc31"/>'
    mug = f'<rect x="560" y="280" width="52" height="50" rx="10" fill="#e6dfd1" stroke="{INK}" stroke-width="4"/><path d="M612 295 a14 14 0 0 1 0 28" fill="none" stroke="{INK}" stroke-width="4"/>'
    return frame('#f6ecce', desk + mug + blob(260, 280, 2.2, face='calm') + blob(720, 280, 2.0, fill='#f5cf6d', face='smile') + sparkle(100, 110, 1.2) + sparkle(870, 120, 1, '#f5cf6d'), 'Two characters working side by side at a desk')

def cover_late_diagnosis():
    ring = ''.join(f'<path d="M{480 + 150*math.cos(a)} {270 + 150*math.sin(a)} a10 10 0 1 0 0.1 0" fill="{c}" stroke="{INK}" stroke-width="3"/>' for a, c in zip([k*math.pi/4 for k in range(8)], ['#f5cf6d','#f5cf6d','#fdfbf7','#e6dfd1']*2))
    bulb = f'<g transform="translate(480 250)"><path d="M-50 -10 a50 50 0 1 1 100 0 c0 30 -22 40 -22 62 h-56 c0 -22 -22 -32 -22 -62 Z" fill="#f5cf6d" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/><rect x="-24" y="56" width="48" height="26" rx="8" fill="#e6dfd1" stroke="{INK}" stroke-width="4"/></g>'
    return frame('#f6ecce', ring + bulb + blob(760, 330, 2.3, face='grin') + blob(200, 340, 1.9, fill='#e6dfd1', face='smile') + sparkle(120, 120, 1.2) + sparkle(860, 110, 1.1, '#f5cf6d'), 'A glowing light bulb with two characters looking pleased')

def cover_what_now():
    # a signpost with three arms and a calm blob reading it
    post = f'<rect x="470" y="150" width="20" height="240" rx="6" fill="#2f3130" stroke="{INK}" stroke-width="4"/>'
    arms = ''.join(f'<g transform="translate(480 {y})"><path d="M-150 -22 H140 L170 0 L140 22 H-150 Z" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/></g>' for y, c in [(170, '#f5cf6d'), (230, '#fdfbf7'), (290, '#e6dfd1')])
    return frame('#f6ecce', post + arms + blob(230, 330, 2.2, face='calm') + blob(760, 340, 2.0, fill='#f5cf6d', face='smile') + sparkle(120, 110, 1.2) + sparkle(860, 110, 1, '#f5cf6d'), 'A signpost with three arms and two characters deciding which way to go')

def cover_beyond_medication():
    # four building blocks stacked, only one of them a pill
    blocks = ''.join(f'<rect x="{x}" y="{y}" width="150" height="90" rx="18" fill="{c}" stroke="{INK}" stroke-width="5"/>' for x, y, c in [(330, 330, '#e6dfd1'), (500, 330, '#fdfbf7'), (415, 230, '#f5cf6d')])
    pill = f'<g transform="translate(490 160) rotate(-20)"><rect x="-60" y="-24" width="120" height="48" rx="24" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><path d="M0 -24 V24" stroke="{INK}" stroke-width="5"/><path d="M0 -24 H60 A24 24 0 0 1 60 24 H0 Z" fill="#f1bc31"/></g>'
    return frame('#f6ecce', blocks + pill + blob(200, 340, 2.2, face='smile') + blob(790, 330, 2.0, fill='#f5cf6d', face='calm') + sparkle(110, 110, 1.2) + sparkle(870, 120, 1, '#f5cf6d'), 'A stack of building blocks with a single pill on top, and two characters beside it')

def cover_exercise():
    # a blob mid-stride on a path, heart above it
    path = f'<path d="M80 400 Q300 300 480 380 T900 360" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round" stroke-dasharray="18 16"/>'
    heart = f'<path transform="translate(560 150) scale(2.2)" d="M0 14 C-18 0 -22 -14 -12 -20 C-6 -24 0 -20 0 -14 C0 -20 6 -24 12 -20 C22 -14 18 0 0 14 Z" fill="#f1bc31" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>'
    legs = f'<path d="M36 92 L22 112 M64 92 L82 108" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    return frame('#f6ecce', path + heart + blob(480, 300, 2.3, fill='#fdfbf7', face='grin', extras=legs) + sparkle(140, 130, 1.2) + sparkle(850, 140, 1, '#f5cf6d') + sparkle(800, 460, .9, '#f5cf6d'), 'A character striding along a dotted path with a heart above')

def cover_workplace():
    # a desk with a laptop, a headset blob, and a tidy row of sticky notes
    desk = f'<rect x="120" y="330" width="720" height="22" rx="11" fill="#2f3130" stroke="{INK}" stroke-width="5"/>'
    laptop = f'<rect x="380" y="240" width="180" height="96" rx="12" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><rect x="400" y="262" width="140" height="10" rx="5" fill="#e6dfd1"/><rect x="400" y="284" width="90" height="10" rx="5" fill="#f1bc31"/>'
    notes = ''.join(f'<rect x="{x}" y="120" width="70" height="70" rx="8" fill="{c}" stroke="{INK}" stroke-width="3" transform="rotate({r} {x+35} 155)"/>' for x, c, r in [(150, '#f5cf6d', -6), (240, '#f5cf6d', 4), (330, '#fdfbf7', -3)])
    headset = f'<path d="M22 46 a28 28 0 0 1 56 0" fill="none" stroke="{INK}" stroke-width="5"/><rect x="16" y="42" width="12" height="18" rx="4" fill="{INK}"/><rect x="72" y="42" width="12" height="18" rx="4" fill="{INK}"/>'
    return frame('#f6ecce', desk + laptop + notes + blob(720, 280, 2.2, fill='#e6dfd1', face='smile', extras=headset) + sparkle(860, 120, 1.1, '#f5cf6d') + sparkle(100, 440, .9, '#fdfbf7'), 'A desk with a laptop, a row of sticky notes and a character wearing a headset')

def cover_nutrition():
    # a plate with three colours, a clock, and a blob with a fork
    plate = f'<circle cx="420" cy="300" r="120" fill="#fdfbf7" stroke="{INK}" stroke-width="6"/><circle cx="420" cy="300" r="96" fill="none" stroke="#e6dfd1" stroke-width="3"/>'
    food = f'<path d="M420 300 L420 210 A90 90 0 0 1 498 255 Z" fill="#fdfbf7" stroke="{INK}" stroke-width="3"/><path d="M420 300 L498 255 A90 90 0 0 1 465 380 Z" fill="#f5cf6d" stroke="{INK}" stroke-width="3"/><path d="M420 300 L465 380 A90 90 0 1 1 420 210 Z" fill="#f1bc31" stroke="{INK}" stroke-width="3"/>'
    clock = f'<circle cx="720" cy="150" r="56" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><path d="M720 150 V112 M720 150 L748 166" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    return frame('#f6ecce', plate + food + clock + blob(760, 340, 2.2, fill='#f5cf6d', face='grin') + sparkle(120, 120, 1.2) + sparkle(130, 440, .9, '#f5cf6d'), 'A plate divided into three colours, a clock, and a cheerful character')

def cover_executive():
    # a tidy checklist beside a tangle, with a blob holding the pen
    tangle = f'<path d="M140 180 C220 90, 300 300, 210 330 S120 230, 250 200 S330 330, 190 400" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round" opacity=".55"/>'
    board = f'<rect x="470" y="120" width="300" height="300" rx="20" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/>'
    rows = ''.join(f'<rect x="510" y="{y}" width="34" height="34" rx="8" fill="{c}" stroke="{INK}" stroke-width="3"/><rect x="565" y="{y+11}" width="{w}" height="12" rx="6" fill="#e6dfd1"/>' for y, c, w in [(160, '#f5cf6d', 160), (225, '#f5cf6d', 120), (290, '#fdfbf7', 150), (355, '#fdfbf7', 90)])
    ticks = ''.join(f'<path d="M517 {y+18} l9 9 l16 -18" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>' for y in (160, 225))
    return frame('#f6ecce', tangle + board + rows + ticks + blob(370, 400, 1.9, fill='#f5cf6d', face='smile') + sparkle(860, 110, 1.1, '#f5cf6d') + sparkle(100, 460, .9, '#fdfbf7'), 'A scribbled tangle beside a checklist with the first two items ticked, and a character between them')

# ------------------------------------------------------------ posts
POSTS = [
 dict(slug='blog-how-booking-works',
      hook='Two steps, and no account needed.',          # the card line and the page's lede
      seo='How booking with ADHDme works, no referral needed',
      description='Browse every clinician without an account, see the fee on each profile, then book or enquire with the practice. No platform fee or upfront payment.', category='How it works', date='2026-09-02', read='3 min', cover=cover_booking,
      title='How booking with ADHDme works: no referral needed to look.',
      body=[
       'Most people with ADHD have spent years dealing with systems that seem built for someone else: forms that ask the same question three times, waitlists with no end date, a referral to get a referral. We built ADHDme to take out as much of that as we could.',
       '<strong>Step one is browsing.</strong> Each clinician in the network has a public profile that says who they are, where they consult, what they focus on, and what an appointment costs before any rebate. You can read all of it without signing up.',
       '<strong>Step two is booking or asking.</strong> When you find a profile that suits you, its button will say Book or Enquire. Book opens that practice’s own diary, where you pick a time. Enquire opens the practice’s own form, and they reply to arrange a time. ADHDme doesn’t charge a platform fee or ask for payment upfront.',
       'We kept the process this short on purpose. ADHD makes executive function scarce, so a booking process that asks a lot of it ends up losing many of the people it was built for.',
       'If you’re not sure which clinician to start with, our GPs are the usual first step, for assessment and prescribing. Psychologists and allied health practitioners help with what comes after, from therapy to workplace adjustments.'],
      sources=[('How it works', 'how-it-works.html'), ('The Network', 'the-doctors.html')]),
 dict(slug='blog-body-doubling',
      hook='Start a task with company nearby.',          # the card line and the page's lede
      seo='Body doubling for ADHD: a simple focus tool',
      description='Body doubling means working while someone else is nearby. Why it can make starting a task easier for people with ADHD, and how to try it tonight.', category='Focus', date='2026-08-19', read='4 min', cover=cover_body_doubling,
      title='Body doubling: the least complicated focus tool there is.',
      body=[
       'Body doubling means doing a task while another person is with you. They don’t have to help, or even do the same thing. They only need to be there, in the room or on a video call, getting on with their own work.',
       'People with ADHD have used it informally for decades, usually without calling it anything. The library was easier to study in than the bedroom, and the kitchen got cleaned faster when a friend was chatting at the table.',
       'Research on why it works is still young. A 2024 study found body doubling helped people with ADHD both start and finish tasks, and earlier work suggests that having other people around nudges the brain’s reward and motivation pathways. What we can say with confidence is that it makes starting easier, and starting is usually the hard part.',
       '<strong>How to try it.</strong> Choose a task you’ve been avoiding and ask someone to sit with you for twenty minutes while they do their own thing. Tell them out loud what you’re going to do, then begin. If nobody is around, a video call with the cameras on works too, and there are plenty of online focus rooms set up for this.',
       'Our clinicians often suggest body doubling alongside other treatment, and it costs nothing to try tonight.'],
      sources=[('Harnessing Focus with Body Doubling, Psychology Today', 'https://www.psychologytoday.com/us/blog/empowered-with-adhd/202408/harnessing-focus-with-body-doubling-a-strategy-for-adhd'), ('Body Doubling for ADHD, Healthline', 'https://www.healthline.com/health/adhd/body-double-adhd')]),
 dict(slug='blog-late-diagnosis',
      hook='Why adults get missed, and what good care looks like.',          # the card line and the page's lede
      seo='Adult ADHD diagnosis: what the research says',
      description='Diagnosed with ADHD as an adult? What the research says about late diagnosis, why adults are often missed, and what good care looks like afterwards.', category='Late diagnosis', date='2026-08-05', read='4 min', cover=cover_late_diagnosis,
      title='Diagnosed with ADHD as an adult? What the research says.',
      body=[
       'Being diagnosed in your thirties, forties or later often brings relief and grief at the same time. There’s relief at finally having a name for the pattern, and grief for the years you spent thinking it was a character flaw. Both feelings are normal, and it’s worth giving yourself room for them.',
       'It can help to know what the science is confident about. In 2021, eighty researchers from twenty-seven countries published the World Federation of ADHD International Consensus Statement, which sets out 208 conclusions backed by large, replicated studies. Among them: ADHD is a real, well-validated condition; it persists into adulthood for most people; it is strongly heritable; and treatment, both medical and non-medical, meaningfully reduces its impact.',
       'The same evidence explains why adults get missed. ADHD looks different after decades of compensating for it. Women in particular tend to be diagnosed later, often after burnout or a child’s diagnosis brings the pattern into view. Masking works for a while, and then it stops working.',
       '<strong>Good care after a late diagnosis.</strong> The Australian clinical guideline recommends an assessment that considers the whole person, a documented baseline before treatment starts, and regular review. In practice, look for a clinician who measures instead of guessing, and who looks at the years before your diagnosis to understand them, without treating them as a record of failure.',
       'If this sounds like you, the clinicians in our network specialise in this kind of conversation. You can read their profiles before you decide anything.'],
      sources=[('World Federation of ADHD International Consensus Statement', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8328933/'), ('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('When Neurodivergent Burnout Reaches Its Breaking Point, ADDitude', 'https://www.additudemag.com/autistic-adhd-burnout-neurodivergent-masking/')]),
 dict(slug='blog-diagnosed-what-now', landing=True, tint='#f6ecce',
      hook='What to decide now, and what can wait.',
      seo='Just diagnosed with ADHD? What to do next',
      description='Just diagnosed with ADHD? What to read first, who to see, what medication and therapy involve in Australia, and which decisions can safely wait.', category='After diagnosis', date='2026-09-16', read='7 min', cover=cover_what_now,
      title='I’ve been diagnosed with ADHD. What now?',
      lede='A diagnosis explains a lot about the past, and it can open many doors at once. You don’t have to go through all of them this week. Below is the order most people find workable, what each step involves, and what it costs in Australia.',
      body=[
       'The first feeling after a diagnosis is usually relief. The second is often closer to vertigo, as medication, therapy, coaching, telling people and a new view of the past all arrive together. It helps to sort out what needs deciding now from what can wait.',
       ('h2', 'Week one: let it sink in'),
       'Nothing clinical has to happen in the first week. Read your assessment report properly, once. Then write down the three things in your life the diagnosis explains best. Those are what treatment should aim at, and it helps to have them in your own words before a clinician asks. If your diagnosis came late, grieving the years before it is real and normal. Our post on <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-late-diagnosis.html">late diagnosis</a> covers this.',
       ('h2', 'Deciding about medication (you can change your mind)'),
       'For most adults, the Australian guideline names stimulant medication as the first-line treatment. It’s the decision people worry over most, and also the easiest one to reverse. A trial starts with a baseline of heart rate, blood pressure and weight and a low starting dose. A few weeks later there’s a review where you say whether the effect was worth it. For some people it changes everything. Others find the side effects outweigh the benefit, and that’s a fine outcome too.',
       'Who can prescribe depends on your state. In Queensland, a specialist GP can now diagnose and prescribe for adults. In NSW this is arriving in stages through 2026. Elsewhere, a psychiatrist usually starts medication and a GP continues it. The GPs in the network say on their profiles what they can do, and the assessment fee is published before you book.',
       ('h2', 'Therapy helps with what medication can’t'),
       'Medication changes attention. It doesn’t undo old habits and workarounds, or the anxiety and low self-worth that build up after decades of being told to try harder. A psychologist can help with those, and therapy doesn’t have to start at the same time as medication. Many people do better starting a month or two in, once they can see what medication did and didn’t fix.',
       'With a Mental Health Treatment Plan from any GP, Medicare pays part of the cost of up to ten sessions a year. All the psychologists in the network offer telehealth, and their fees are on their profiles.',
       ('h2', 'What can wait'),
       ('list', [
        'Telling your employer. You don’t have to, and you can ask for workplace adjustments without disclosing a diagnosis. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-workplace-support.html">workplace support</a> post explains how.',
        'Coaching. It’s most useful once the medication question is settled and you know which parts of the day are still hard.',
        'Overhauling your whole life. A single change sticks better than six made at once.',
        'Supplements and diets. The evidence for them is thin, and the money is better spent on a psychologist. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-nutrition.html">nutrition</a> post covers what does help.']),
       ('h2', 'A plan that works for most people'),
       'In month one, start a medication trial with a GP and write down the three things you want it to change. In month two or three, see a psychologist, usually for six to ten sessions in the first year. Alongside that, make one change on your own. The most common are exercise just before the hardest part of the day, or a fixed wake time. Then review how it’s going before you add anything else.',
       'You get to choose at each step. Read about the clinicians before you book anyone. Each profile is their own account of how they work and what they charge, and a bad fit is the most expensive thing in ADHD care.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('ADHD treatment after diagnosis', 'adhd-treatment-after-diagnosis.html'), ('How booking works', 'how-it-works.html')]),
 dict(slug='blog-adhd-support-beyond-medication', landing=True, tint='#d0e4de',
      hook='Four kinds of help beyond a pill.',
      seo='ADHD support beyond medication: what works',
      description='Therapy, occupational therapy, coaching and daily habits for ADHD: what each one helps with, who provides it, what it costs, and how to choose.', category='Treatment', date='2026-09-09', read='7 min', cover=cover_beyond_medication,
      title='ADHD support beyond medication: what else works.',
      lede='Medication is the best-evidenced single treatment for ADHD, and it still only covers part of what ADHD affects. Whether you take it, can’t take it or would prefer not to, the supports below have evidence behind them, and each one is for something different.',
      body=[
       'A stimulant sharpens attention while it’s active. It won’t teach you a skill, repair a relationship or reorganise your kitchen, and it won’t quiet the voice saying you should have sorted this out years ago. Each support below works on one of those.',
       ('h2', 'Psychological therapy'),
       'Cognitive behavioural therapy adapted for ADHD is the best-studied non-medication treatment for adults. It has moderate effects on symptoms and larger effects on the anxiety, low mood and self-criticism that often come with a late diagnosis. Psychologists also use skills from acceptance and commitment therapy and dialectical behaviour therapy for the same reasons. Therapy is most useful once you know what medication did and didn’t change, which is why many psychologists suggest starting a month or two after a medication trial begins.',
       'With a Mental Health Treatment Plan from a GP, Medicare pays part of the cost of up to ten sessions a year. The psychologists in the network are in Brisbane and available by telehealth Australia-wide, and each profile lists their approach and fee.',
       ('h2', 'Occupational therapy'),
       'If the hard part is the practical side of the day, an occupational therapist can change the task and your surroundings to suit you: the morning routine, how a workspace is set up, sensory needs, the school report. OTs are AHPRA-registered. Their services can be funded by the NDIS, private health extras or a GP chronic condition management plan, but a Mental Health Treatment Plan doesn’t cover them. The network has paediatric OT in Brisbane now.',
       ('h2', 'Coaching'),
       'Coaching is practical, forward-looking work on executive function: starting, planning, finishing, and building systems simple enough to survive a bad week. It isn’t therapy or a health profession, and it’s unregulated, so credentials matter. The coaches in the network trained at the ADHD Coaching Academy, and most hold an International Coaching Federation credential. If you work at least eight hours a week, JobAccess can fund coaching.',
       ('h2', 'Daily habits with evidence'),
       ('list', [
        'Twenty to thirty minutes of moderate aerobic exercise lifts attention for about an hour afterwards, so do it just before the hardest part of your day. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-and-exercise.html">exercise</a> post has more detail, including safety if you take stimulants.',
        'Getting up at the same time each day does more for ADHD symptoms than almost any supplement, and it matters even more if you take stimulants.',
        'Stimulants suppress appetite through the middle of the day. Eating at set times, with a proper breakfast before your dose, protects your weight and mood. The <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-nutrition.html">nutrition</a> post explains how.']),
       ('h2', 'What has little evidence'),
       'Omega-3 shows a small effect at best, mostly in children. Elimination diets have little evidence in adults and carry real risks. Homeopathy has no reliable evidence for any condition, and neurofeedback has mixed results and a high price. None of these is dangerous in itself. The cost is the money and the months they take away from treatments that work.',
       ('h2', 'How to choose'),
       'Start by naming the problem. If it’s how you feel about yourself, try therapy. If it’s the practical side of the day, see an OT. If it’s starting and finishing things, try coaching, and for an afternoon slump, exercise just before it. Try one thing at once, set a date to review it, and read the profiles before you book.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('World Federation of ADHD International Consensus Statement', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8328933/'), ('ADHD treatment after diagnosis', 'adhd-treatment-after-diagnosis.html')]),
 dict(slug='blog-adhd-and-exercise', landing=True, tint='#dad9eb',
      hook='Twenty minutes for an hour of focus.',
      seo='ADHD and exercise: when, how much, and safety',
      description='Exercise gives a small, short-lived lift in attention. When to schedule it, what changes if you take stimulants, and how to keep it going for months.', category='Daily life', date='2026-09-02', read='6 min', cover=cover_exercise,
      title='ADHD and exercise: what it does, when to do it, and how to keep doing it.',
      lede='Exercise is the one lifestyle change for ADHD with a measurable effect on attention. The effect is smaller and shorter than the internet suggests, but if you time it well it’s still one of the best tools you have. This guide covers what the evidence supports and the safety points that change if you take a stimulant.',
      body=[
       ('h2', 'What the evidence shows'),
       'Twenty to thirty minutes of moderate aerobic exercise gives a small to moderate lift in attention, working memory and self-control for roughly an hour afterwards. That finding has held up across studies. Aerobic exercise, meaning anything that keeps you breathing harder for a sustained stretch, has the best support. Mind-body exercise such as yoga shows a small effect, and there are too few studies of coordinative exercise to say.',
       'The effect is a modest addition to medication. Anyone telling you to swap your prescription for a running plan is selling something.',
       ('h2', 'Timing matters more than volume'),
       'Because the effect lasts about an hour, when you exercise matters more than how much. Do it just before the part of the day that asks the most of you, such as a study block or the meeting you’ve been dreading. A brisk twenty minutes at two o’clock does more for a hard afternoon than an hour at six in the morning.',
       ('h2', 'If you take a stimulant'),
       ('list', [
        'Stimulants raise your resting heart rate, so age-based heart-rate zones will overstate how hard you’re working. Go by how it feels and whether you can still talk in full sentences.',
        'Stimulants also suppress appetite, and many people end up training under-fuelled without noticing. Eat something before you go.',
        'Pre-workout caffeine adds to the stimulant’s effect on heart rate and blood pressure, so leave it out.',
        'If you get chest pain, fainting, ongoing palpitations or unusual breathlessness while on a stimulant, stop and see a doctor before you exercise again.',
        'If you work with an exercise physiologist or trainer, tell them what medication you take and when. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="adhd-exercise-physiologist.html">exercise physiology</a> page explains what an accredited exercise physiologist does and how a GP care plan can fund it.']),
       ('h2', 'Keeping it going past February'),
       'People tend to blame motivation when they drop out. The usual cause is an executive function problem: too many steps between deciding to exercise and actually moving. So cut the steps. Keep sessions short and at a fixed time, and lay out your kit the night before or choose something that needs none. A route or class that involves no decisions helps, and so does having someone expect you, which is body doubling by another name. Some quick feedback, from a tracker or a tick on a wall chart, keeps it going.',
       'Two rules help. First, have a minimum session you can do even on your worst day; ten minutes counts. Second, never miss twice. After a lapse, skip the self-criticism, lower the load and rebook straight away. A single missed session matters much less than the week that follows it.',
       ('h2', 'Where to start this week'),
       'Pick the part of your day that goes worst. Three times this week, do twenty minutes of walking, cycling or anything else that gets you breathing harder just before it, and notice whether the following hour feels different. That observation will tell you more than any article, this one included.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('Exercise and Sports Science Australia', 'https://www.essa.org.au/'), ('Body doubling: the least complicated focus tool there is', 'blog-body-doubling.html')]),
 dict(slug='blog-adhd-workplace-support', landing=True, tint='#f6ecce',
      hook='Reasonable adjustments, and how to ask.',
      seo='ADHD at work in Australia: adjustments and funding',
      description='Reasonable adjustments for ADHD at work, whether you need to disclose, what Australian law says, and how JobAccess can fund coaching and equipment.', category='Work', date='2026-08-26', read='7 min', cover=cover_workplace,
      title='ADHD at work: the adjustments that help, and how to ask for them.',
      lede='Most ADHD difficulties at work come from a mismatch between how your brain works and a workplace designed for someone else’s. Australian law gives you a right to reasonable adjustments, and a government fund pays for some of them. This guide covers what to ask for and how to ask.',
      body=[
       ('h2', 'Where it shows up'),
       'The pattern is similar in most jobs: strong in a crisis, weaker in the quiet weeks. Common trouble spots include open-plan noise, long meetings with no agenda, tasks with no deadline or one three months away, emails that need a decision, and the morning after a late night. Knowing your own trouble spots is the first adjustment, because it tells you what to ask for.',
       ('h2', 'Adjustments that help'),
       ('list', [
        'Less noise and interruption: headphones treated as normal, a quiet room you can book, or a hybrid pattern with your deep-work days at home.',
        'Instructions in writing, such as a short summary after a verbal briefing and an agenda before meetings. It takes the other person two minutes and saves you an afternoon.',
        'Long projects broken into check-ins a week apart. Nobody with ADHD has ever been helped by a distant deadline.',
        'A regular check-in with your manager, fifteen minutes a week at the same time. It replaces the anxious guessing about how you’re going.',
        'Flexible hours that fit your medication. If your stimulant is working at nine and gone by four, a day that starts earlier is a better day.',
        'Tools such as noise-cancelling headphones, a second screen, task software or dictation. They’re small and cheap, and often fundable.']),
       ('h2', 'Do you have to disclose?'),
       'No. You have no general obligation to tell an employer about a diagnosis. You can ask for most of the adjustments above without naming a condition, by explaining how you work best; a good manager will agree to headphones and written briefings without needing a medical reason. Disclosure becomes useful when you need the legal protection or the funding described below, and you can limit it to HR or to the person approving the adjustment.',
       'Under the Disability Discrimination Act 1992, ADHD is a disability, and an employer must make reasonable adjustments unless doing so would cause unjustifiable hardship. Most negotiations turn on what counts as reasonable, and the adjustments above are reasonable almost anywhere.',
       ('h2', 'Who pays'),
       'The Employment Assistance Fund, through JobAccess, pays for work-related adjustments for people with disability who work at least eight hours a week, including self-employed people. It covers equipment and, under specialist mental health support, ADHD coaching, at around $1,770.44 a year by one practice’s figure. You apply with supporting documentation from a GP or specialist, and you can ask for an exemption so you don’t have to disclose the diagnosis to your employer. The coaches in the network run free sessions to help with the application, and our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="adhd-coach.html">coaching</a> page has the detail.',
       ('h2', 'How to ask'),
       'Put it in writing, keep it brief, and suggest a solution along with the problem. For example: “I work best with a written summary after briefings and a weekly fifteen-minute check-in. Can we try that for a month?” A trial with a review date is easier to agree to than a permanent change, and once it has worked for a month it usually becomes permanent on its own.',
       'If it goes badly, both the Australian Human Rights Commission and the Fair Work Ombudsman take complaints about disability discrimination at work. Most requests never get that far, and most managers are relieved to be told what would help.'],
      sources=[('JobAccess: Employment Assistance Fund', 'https://www.jobaccess.gov.au/'), ('Australian Human Rights Commission: disability discrimination', 'https://humanrights.gov.au/our-work/disability-rights'), ('ADHD coaching in Australia', 'adhd-coach.html')]),
 dict(slug='blog-adhd-nutrition', landing=True, tint='#d0e4de',
      hook='Eat at set times, even without hunger.',
      seo='ADHD and nutrition: diet, supplements, appetite',
      description='No diet treats ADHD, but stimulants often affect appetite. How to plan meals around that, what the evidence says on supplements, and when to see a GP.', category='Daily life', date='2026-08-19', read='6 min', cover=cover_nutrition,
      title='ADHD and nutrition: what the evidence says.',
      lede='Search “ADHD diet” and you’ll find a hundred confident answers, and the evidence supports almost none of them. It does support regular meals planned around what stimulant medication does to appetite, which is simpler and cheaper than most of what’s on offer. This guide sets out that plan, then what the evidence says about the rest.',
      body=[
       ('h2', 'Appetite on stimulants'),
       'Reduced appetite is the most common side effect of stimulants. Hunger disappears through the middle of the day and comes back hard in the evening. That’s how people end up under-eating until six, over-eating until midnight, and losing weight without meaning to.',
       'The fix is to stop waiting for hunger. Have a substantial breakfast with protein before your dose, while you still have an appetite. After that, eat by the clock: set alarms, and keep food on hand that is small, energy-dense and needs no preparation, because the medication that takes away your appetite also makes lunch feel like admin. That might be a handful of nuts, a yoghurt, a boiled egg or a protein bar in your bag. Dinner can be the biggest meal, since that’s when hunger comes back.',
       ('h2', 'Keep food low-effort'),
       'Meal planning is an executive function task, which is why it fails for the people who need it most. What lasts is five default meals you can make without thinking, a saved grocery order, and the same breakfast each day. It’s meant to be boring. You can have variety on the weekend, when you have more capacity for it.',
       ('h2', 'Supplements and diets'),
       ('list', [
        'Omega-3 fish oil has a small effect at best, mostly in children, and far less than medication. It isn’t harmful, and it isn’t a treatment.',
        'Elimination diets have little evidence in adults and carry real risks of poor nutrition and disordered eating. They aren’t recommended as a routine measure.',
        'Sugar hasn’t been shown to cause ADHD or make it worse. Studies linking eating patterns and ADHD are observational only.',
        'Iron, zinc and vitamin D are worth testing where a deficiency is plausible, then correcting. Never take iron supplements without a test first.',
        'Caffeine adds to a stimulant’s effect on heart rate, anxiety and sleep. If you drink four energy drinks a day and sleep badly, the drinks are part of the cause. Think about how much you have, and when.']),
       ('h2', 'Red flags that need a doctor'),
       'If you lose about five per cent of your weight in three months without meaning to, tell the GP who prescribes your medication, because the dose or timing may need to change. ADHD also comes with higher rates of binge eating and bulimia than in the general population. If eating feels out of control, or you’re compensating for it, see a GP and a clinician experienced in eating disorders, and don’t try to fix it with a diet. The network has a psychologist credentialed in this area, and their profile says so.',
       ('h2', 'Where a dietitian fits'),
       'For most adults with ADHD, the plan above covers what nutrition can offer, and you don’t need a professional for it. Medical nutrition therapy, eating disorders and complex conditions alongside ADHD are work for an Accredited Practising Dietitian, and a GP chronic condition management plan gives a partial Medicare rebate. Tell your GP about all the supplements you take. Most people don’t, and interactions with ADHD medication do happen.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('Dietitians Australia: find an Accredited Practising Dietitian', 'https://dietitiansaustralia.org.au/'), ('ADHD support beyond medication', 'blog-adhd-support-beyond-medication.html')]),
 dict(slug='blog-adhd-executive-functioning', landing=True, tint='#dad9eb',
      hook='The skills that run your week.',
      seo='ADHD and executive functioning: what helps',
      description='Executive function covers starting, planning, finishing, remembering and managing feelings. How ADHD affects it, and the strategies with evidence.', category='Daily life', date='2026-08-12', read='7 min', cover=cover_executive,
      title='ADHD and executive functioning: what it is, and what helps.',
      lede='Attention is the word in the diagnosis, but executive function is what runs your week: starting, planning, holding a thought, finishing, and handling the feeling when things go wrong. Understanding it can change what you try, and what you stop blaming yourself for.',
      body=[
       ('h2', 'What executive function is'),
       'Executive functions are the skills your brain uses to manage itself and turn an intention into something finished. They include working memory, which holds the plan in mind; inhibition, which stops you doing the wrong thing; task initiation, which gets you started on the right one; planning and sequencing; time perception; and emotional regulation. In ADHD these skills are present but unreliable, which is why you can handle a crisis brilliantly and then leave an envelope unopened for three weeks.',
       'This has two consequences. First, the difficulty is real and neurological, so “just try harder” asks the impaired system to fix itself. Second, because the problem lies in how you manage tasks and not in your ability, most of the fixes are structural. They move the managing out of your head and into the world around you.',
       ('h2', 'Why willpower is the wrong tool'),
       'Willpower is itself an executive function. Using it to make up for weak executive function is like borrowing from an overdrawn account, and it’s why people with ADHD are so tired by Wednesday. The strategies that work reduce how much executive function a task needs.',
       ('h2', 'Strategies with evidence'),
       ('list', [
        'Get tasks out of your head. Use one capture point for all of them, on paper or in one app. Working memory is the weakest link, so stop using it as storage.',
        'Make time visible with analogue clocks, timers you can see, and calendar blocks in place of lists. Knowing you have time blindness doesn’t fix it.',
        'Shrink the first step, because task initiation fails on size. “Write the report” never gets started; “Open the document and write one bad sentence” does.',
        'Try body doubling. Having someone with you while you work, in the room or on a call, makes starting easier than any app can. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-body-doubling.html">body doubling</a> post explains it.',
        'Bring deadlines closer. To an ADHD brain a distant deadline doesn’t exist, so break it into check-ins a week apart, with a person attached.',
        'Use routines to cut decisions: the same breakfast, the same bag, the same place for your keys. Each decision you remove saves executive function for something that matters.',
        'Consider medication. Stimulants directly improve working memory and inhibition. They won’t build your systems for you, though they make building them possible.']),
       ('h2', 'Emotional regulation is executive function too'),
       'The flash of anger at something small, the out-of-proportion dread before a phone call, the rejection that feels like a verdict: these are executive function difficulties with feelings, and they aren’t a separate personality flaw. Recognising that is often the biggest relief in the first months after diagnosis. Therapy works on it directly, especially skills from dialectical behaviour therapy, and the psychologists in the network mention it on their profiles.',
       ('h2', 'Who helps with what'),
       'A psychologist works on the emotional side, and on the beliefs about yourself left behind by decades of struggling with executive function. An occupational therapist works on your environment and routines. A coach works on your systems week by week, with accountability built in. Most people need one of these, not all three. Start with the one aimed at the part of your week that goes worst.'],
      sources=[('Barkley, R. A., Executive Functions: What They Are, How They Work, and Why They Evolved, Guilford Press, 2012', 'https://www.guilford.com/books/Executive-Functions/Russell-Barkley/9781462545933'), ('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('ADHD coaching in Australia', 'adhd-coach.html')]),
]

MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
def nice(d):
    y, m, dd = d.split('-'); return f'{int(dd)} {MONTHS[int(m)-1]} {y}'

# ------------------------------------------------------------ render
# Two card shapes, because the two places that show a post want different things. On Our Story the
# cards sit in a row of three and carry no chrome: image, title, hook, matching the Learn tiles.
# On a post page the "More from the blog" pair is a genuine aside, so it keeps its box.
def story_card(p):
    return (f'<a class="group block" href="{p["slug"]}.html">'
            f'<span class="block aspect-[3/2] overflow-hidden rounded-lg bg-[#f6f4ee]">'
            f'<img width="960" height="540" loading="lazy" decoding="async" alt="" class="w-full h-full object-cover" src="assets/blog/{p["slug"]}.svg"></span>'
            f'<span class="block mt-4 text-[22px] leading-[1.25] font-semibold tracking-tight text-[#1a1c1c] group-hover:underline decoration-2 underline-offset-4">{p["title"]}</span>'
            f'<span class="block mt-2 text-[15px] leading-relaxed text-[#5f5e59]">{p["hook"]}</span></a>')


def related_card(p):
    return f'''<a href="{p['slug']}.html" data-reveal class="group rounded-2xl bg-white border border-black/[0.06] flex flex-col overflow-hidden shadow-[0_4px_24px_-4px_rgba(0,0,0,0.05)] hover:-translate-y-1 transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1c1c]">
<div class="aspect-video overflow-hidden bg-[#f6f1e6]"><img width="960" height="540" loading="lazy" decoding="async" src="assets/blog/{p['slug']}.svg" alt="" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"></div>
<div class="p-5 sm:p-6 flex flex-col gap-3 flex-1">
<div class="flex items-center justify-between gap-2 text-[13px] font-bold"><span class="whitespace-nowrap px-2.5 py-1 rounded-full bg-[#f1bc31]/20 text-[#674d00] uppercase tracking-wider">{p['category']}</span><span class="text-neutral-500 font-medium">{p['read']} read</span></div>
<h3 class="font-editorial-quote text-[22px] leading-snug text-on-surface group-hover:text-[#1d64c2] transition-colors">{p['title']}</h3>
<p class="text-[15px] text-on-surface-variant leading-relaxed">{p['hook']}</p>
<div class="mt-auto pt-3 border-t border-black/[0.06] flex items-center justify-between text-[13px]"><span class="text-neutral-500 font-medium">{nice(p['date'])}</span><span class="inline-flex items-center gap-1 font-bold text-[#1d64c2]">Read{ARROW_NE}</span></div>
</div></a>'''


def section():
    return f'''<!-- BLOG --><section id="blog" class="w-full pb-16 lg:pb-20 px-5 md:px-8 lg:px-12 max-w-[1200px] mx-auto">
<div data-reveal class="flex items-end justify-between gap-4 mb-8">
<div><h2 class="font-display-hero text-[32px] sm:text-[40px] leading-[1.1] font-extrabold tracking-tight text-on-surface mt-2">From the blog.</h2></div>
<a class="text-[15px] font-semibold text-[#1a1c1c] underline decoration-2 underline-offset-4 whitespace-nowrap hover:text-[#5f5e59] transition-colors" href="learn.html">All articles <span aria-hidden="true">→</span></a>
</div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-x-8 gap-y-12">{''.join(story_card(p) for p in sorted(POSTS, key=lambda p: p['date'], reverse=True)[:3])}</div>
</section><!-- /BLOG -->'''


def head_for(p, head):
    """Our Story's <head>, rewritten for this post: every tag that names the page has to change, or
    the post ships Our Story's title, description and canonical URL to every crawler and share card."""
    url = f'{SITE}/{p["slug"]}.html'
    subs = [
        (r'<title>.*?</title>', f'<title>{p["seo"]} · ADHDme</title>'),
        (r'<meta name="description" content=".*?">', f'<meta name="description" content="{p["description"]}">'),
        (r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{url}">'),
        (r'<meta property="og:url" content=".*?">', f'<meta property="og:url" content="{url}">'),
        (r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{p["seo"]}">'),
        (r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{p["description"]}">'),
        (r'<meta name="twitter:title" content=".*?">', f'<meta name="twitter:title" content="{p["seo"]}">'),
        (r'<meta name="twitter:description" content=".*?">', f'<meta name="twitter:description" content="{p["description"]}">'),
    ]
    for pat, rep in subs:
        head, n = re.subn(pat, lambda _m, r=rep: r, head, count=1)
        if not n:
            raise SystemExit(f'build-blog: our-story.html has no {pat!r} to rewrite for {p["slug"]}')
    preload = f'<link rel="preload" as="image" href="assets/blog/{p["slug"]}.svg" fetchpriority="high">'
    head = head.replace('<link rel="stylesheet"', preload + '\n<link rel="stylesheet"', 1)
    return head


def body_block(b):
    """A body item: a paragraph string, ('h2', text) or ('list', [items])."""
    if isinstance(b, str):
        return f'<p class="text-[17px] leading-[1.7] text-on-surface/85">{b}</p>'
    kind, value = b
    if kind == 'h2':
        return f'<h2 class="text-[24px] font-extrabold tracking-tight text-[#1a1c1c] pt-4">{value}</h2>'
    if kind == 'list':
        return '<ul class="space-y-3 pl-5 list-disc marker:text-[#f1bc31]">' + ''.join(f'<li class="text-[17px] leading-[1.7] text-on-surface/85">{i}</li>' for i in value) + '</ul>'
    raise SystemExit(f'build-blog: unknown body item {kind!r}')


def opening(p):
    """How a post starts. A landing post opens full-width, in its own tint, with the title, a longer
    lede, the illustration and two calls to action, so it reads as a destination rather than a diary
    entry; then the article proper follows. An ordinary post keeps the small header and the cover."""
    meta = f'<span class="whitespace-nowrap px-2.5 py-1 rounded-full bg-[#f1bc31]/20 text-[#674d00] uppercase tracking-wider">{p["category"]}</span><span class="text-neutral-500 font-medium">{nice(p["date"])} · {p["read"]} read · The ADHDme team</span>'
    if not p.get('landing'):
        return f'''<article class="max-w-[760px] mx-auto px-5 md:px-8 lg:px-12 pt-12 pb-10">
<a class="inline-flex items-center gap-2 text-[15px] font-semibold text-neutral-600 hover:text-black transition-colors group mb-8" href="our-story.html#blog">{ARROW_BACK}Back to Our Story</a>
<div class="flex items-center gap-3 text-[13px] font-bold mb-4">{meta}</div>
<h1 class="hero-in font-display-hero text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.08] font-extrabold tracking-tight text-on-surface mb-6">{p['title']}</h1>
<p class="hero-in hero-in-2 font-editorial-quote text-[22px] leading-relaxed text-on-surface-variant mb-8">{p['hook']}</p>
<div class="hero-in hero-in-3 rounded-3xl overflow-hidden border border-black/[0.06] shadow-sm mb-10 aspect-video bg-[#f6f1e6]"><img width="960" height="540" fetchpriority="high" decoding="async" src="assets/blog/{p['slug']}.svg" alt="" class="w-full h-full object-cover"></div>'''
    return f'''<section class="w-full border-b border-black/[0.06]" style="background: {p['tint']};" aria-labelledby="post-title">
<div class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pt-12 pb-14 lg:pt-20 lg:pb-20 grid grid-cols-1 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] gap-10 lg:gap-16 items-center">
<div>
<div class="hero-in flex flex-wrap items-center gap-3 text-[13px] font-bold">{meta}</div>
<h1 id="post-title" class="hero-in hero-in-2 mt-5 font-display-hero text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-on-surface max-w-[20ch]">{p['title']}</h1>
<p class="hero-in hero-in-2 mt-5 text-[19px] leading-[1.6] text-[#5f5e59] max-w-[58ch]">{p['lede']}</p>
<div class="hero-in hero-in-3 mt-8 flex flex-wrap gap-3">
<a class="btn-press inline-flex items-center gap-2 h-12 px-7 rounded-full bg-[#1a1c1c] text-white text-[15px] font-bold hover:bg-[#2f3130] transition-all shadow-[0_4px_16px_rgba(0,0,0,0.15)] hover:-translate-y-0.5" href="the-doctors.html">Find your clinician <span class="text-[#f1bc31]" aria-hidden="true">→</span></a>
<a class="btn-press inline-flex items-center gap-2 h-12 px-7 rounded-full bg-white/70 border border-black/10 text-[#1a1c1c] text-[15px] font-bold hover:bg-white transition-colors" href="#guide">Read the guide <span aria-hidden="true">↓</span></a>
</div>
</div>
<div class="hero-in hero-in-3 rounded-3xl overflow-hidden border border-black/[0.06] shadow-sm aspect-video bg-[#f6f1e6]"><img width="960" height="540" fetchpriority="high" decoding="async" src="assets/blog/{p['slug']}.svg" alt="" class="w-full h-full object-cover"></div>
</div></section>
<article id="guide" class="max-w-[760px] mx-auto px-5 md:px-8 lg:px-12 pt-12 pb-10 scroll-mt-24">
<p class="hero-in hero-in-2 font-editorial-quote text-[22px] leading-relaxed text-on-surface-variant mb-8">{p['hook']}</p>'''


def post_ld(p):
    """BlogPosting structured data, so a post is eligible for article results in search."""
    import json, html as _html
    url = f'{SITE}/{p["slug"]}.html'
    org = {'@type': 'Organization', 'name': 'ADHDme', 'url': SITE + '/',
           'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/brand/icon-512.png'}}
    headline = re.sub(r'<[^>]+>', '', _html.unescape(p['title'])).rstrip('.')
    d = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': headline[:110],
         'description': _html.unescape(p['description']), 'datePublished': p['date'], 'dateModified': p['date'],
         'author': org, 'publisher': org, 'image': f'{SITE}/assets/brand/og.png', 'inLanguage': 'en-AU',
         'articleSection': p['category'], 'mainEntityOfPage': {'@type': 'WebPage', '@id': url}, 'url': url}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + '</script>'


def post_page(p, head, footer, others):
    paras = ''.join(body_block(b) for b in p['body'])
    EXT = ' target="_blank" rel="noopener noreferrer"'
    src = ''.join(f'<li><a class="font-semibold text-[#1d64c2] hover:underline" href="{h}"{EXT if h.startswith("http") else ""}>{t}</a></li>' for t, h in p['sources'])
    more = ''.join(related_card(o) for o in others)
    return f'''{head}<main id="main" class="w-full bg-surface">
{opening(p)}
<div class="space-y-6">{paras}</div>
<div class="mt-10 p-6 rounded-2xl bg-[#faf9f6] border border-[#eeebe5]"><h2 class="text-[15px] font-bold text-[#5f5e59] mb-3">Sources and further reading</h2><ul class="space-y-2 text-sm">{src}</ul></div>
<div class="mt-10 bg-[#f1bc31] rounded-3xl p-8 flex flex-col sm:flex-row items-center justify-between gap-6 border border-black/10">
<div><h2 class="text-2xl font-extrabold tracking-tight text-black">Ready to find your clinician?</h2><p class="text-[15px] text-black/75 font-medium mt-1">Profiles are free to browse, and you don’t need an account.</p></div>
<a class="btn-press shrink-0 h-12 px-7 rounded-full bg-[#1a1c1c] text-white font-bold text-[15px] flex items-center gap-2 hover:-translate-y-0.5 transition-all" href="the-doctors.html">Find your clinician <span class="text-[#f1bc31]" aria-hidden="true">→</span></a></div>
</article>
<section class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pb-16 lg:pb-20"><h2 class="text-[15px] font-bold text-[#785a00] mb-5">More from the blog</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-6">{more}</div></section>
</main>
{post_ld(p)}
{footer}'''


def build():
    """Every file this script owns, as {path: text}."""
    story = (ROOT / 'our-story.html').read_text(encoding='utf-8')
    head = story[:story.index('<main')]
    footer = story[story.index('<footer'):]
    out = {}
    for p in POSTS:
        out[ROOT / 'assets/blog' / f"{p['slug']}.svg"] = p['cover']()
        i = POSTS.index(p)
        others = [POSTS[(i + k) % len(POSTS)] for k in (1, 2)]  # the pair after this one, wrapping
        out[ROOT / f"{p['slug']}.html"] = post_page(p, head_for(p, head), footer, others)
    if '<!-- BLOG -->' not in story:
        raise SystemExit('build-blog: our-story.html has no <!-- BLOG --> … <!-- /BLOG --> section to fill')
    out[ROOT / 'our-story.html'] = re.sub(r'<!-- BLOG -->.*?<!-- /BLOG -->', lambda _m: section(), story, count=1, flags=re.S)
    out[ROOT / 'learn.html'] = learn_cards((ROOT / 'learn.html').read_text(encoding='utf-8'))
    return out


def learn_cards(learn):
    """learn.html with each blog card's title and hook taken from POSTS, so a retitled post cannot leave
    its Learn card behind. Cards are placed by hand; only their two lines of text come from here."""
    by_slug = {p['slug']: p for p in POSTS}
    pat = re.compile(r'(<a class="group block" href="(blog-[a-z-]+)\.html">.*?<span class="block mt-4[^"]*">)(.*?)'
                     r'(</span><span class="block mt-2[^"]*">)(.*?)(</span></a>)', re.S)

    def fill(m):
        post = by_slug.get(m.group(2))
        if post is None:
            raise SystemExit(f'build-blog: learn.html links to {m.group(2)}.html, which is not in POSTS')
        return m.group(1) + post['title'] + m.group(4) + post['hook'] + m.group(6)
    return pat.sub(fill, learn)


def main(argv):
    out = build()
    stale = [q for q, text in out.items() if not q.exists() or q.read_text(encoding='utf-8') != text]
    if '--check' in argv:
        for q in stale:
            print(f'out of date: {q.relative_to(ROOT)}')
        print('blog is up to date' if not stale else f'{len(stale)} file(s) differ; run python3 scripts/build-blog.py')
        return 1 if stale else 0
    for q, text in out.items():
        q.write_text(text, encoding='utf-8', newline='')
        print(('wrote  ' if q in stale else 'same   ') + str(q.relative_to(ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
