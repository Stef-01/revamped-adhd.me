#!/usr/bin/env python3
"""Build blog post pages and the "From the blog" section on our-story.html.

    python3 scripts/build-blog.py          # write the pages
    python3 scripts/build-blog.py --check  # exit 1 if any page on disk differs from what would be written

Owns: blog-*.html in full, and the <!-- BLOG --> … <!-- /BLOG --> section on our-story.html. A hand
edit to any of that is lost on the next build; put the change here instead, and run --check before
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
def blob(x, y, s, fill='#d96b52', face='smile', extras=''):
    eyes = f'<circle cx="43" cy="46" r="3.5" fill="{INK}"/><circle cx="57" cy="46" r="3.5" fill="{INK}"/><circle cx="44" cy="44.5" r="1.3" fill="#fff"/><circle cx="58" cy="44.5" r="1.3" fill="#fff"/>'
    mouths = {'smile': f'<path d="M45 56 Q50 62 55 56" fill="none" stroke="{INK}" stroke-linecap="round" stroke-width="3"/>',
              'grin': f'<path d="M44 55 Q50 65 56 55 Z" fill="{INK}"/><path d="M47 57 Q50 62 53 57 Z" fill="#f87171"/>',
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
    # two big numbered steps and a happy blob
    steps = ''.join(f'<g transform="translate({240 + i*260} 200)"><circle r="70" fill="{c}" stroke="{INK}" stroke-width="5"/><text y="24" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="64" fill="{INK}">{i+1}</text></g>' for i, c in enumerate(['#f5cf6d', '#9be5b5']))
    arrow = f'<path d="M330 200 H400" stroke="{INK}" stroke-width="7" stroke-linecap="round"/><path d="M385 182 L405 200 L385 218" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    return frame('#f6ecce', steps + arrow + blob(740, 300, 2.4, face='grin') + sparkle(120, 120, 1.3) + sparkle(880, 100, 1, '#f2a7c8') + sparkle(140, 430, .9, '#9be5b5'), 'Two numbered steps with an arrow between them and a cheerful character')

def cover_body_doubling():
    desk = f'<rect x="150" y="330" width="660" height="24" rx="12" fill="#2f3130" stroke="{INK}" stroke-width="5"/><rect x="330" y="230" width="160" height="100" rx="14" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><rect x="350" y="250" width="120" height="10" rx="5" fill="#e6dfd1"/><rect x="350" y="272" width="90" height="10" rx="5" fill="#e6dfd1"/><rect x="350" y="294" width="105" height="10" rx="5" fill="#f1bc31"/>'
    mug = f'<rect x="560" y="280" width="52" height="50" rx="10" fill="#8fbfe3" stroke="{INK}" stroke-width="4"/><path d="M612 295 a14 14 0 0 1 0 28" fill="none" stroke="{INK}" stroke-width="4"/>'
    return frame('#d0e4de', desk + mug + blob(260, 280, 2.2, face='calm') + blob(720, 280, 2.0, fill='#f5cf6d', face='smile') + sparkle(100, 110, 1.2) + sparkle(870, 120, 1, '#f2a7c8'), 'Two characters working side by side at a desk')

def cover_late_diagnosis():
    ring = ''.join(f'<path d="M{480 + 150*math.cos(a)} {270 + 150*math.sin(a)} a10 10 0 1 0 0.1 0" fill="{c}" stroke="{INK}" stroke-width="3"/>' for a, c in zip([k*math.pi/4 for k in range(8)], ['#f5cf6d','#f2a7c8','#9be5b5','#8fbfe3']*2))
    bulb = f'<g transform="translate(480 250)"><path d="M-50 -10 a50 50 0 1 1 100 0 c0 30 -22 40 -22 62 h-56 c0 -22 -22 -32 -22 -62 Z" fill="#f5cf6d" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/><rect x="-24" y="56" width="48" height="26" rx="8" fill="#e6dfd1" stroke="{INK}" stroke-width="4"/></g>'
    return frame('#dad9eb', ring + bulb + blob(760, 330, 2.3, face='grin') + blob(200, 340, 1.9, fill='#8fbfe3', face='smile') + sparkle(120, 120, 1.2) + sparkle(860, 110, 1.1, '#f2a7c8'), 'A glowing light bulb with two characters looking pleased')

def cover_what_now():
    # a signpost with three arms and a calm blob reading it
    post = f'<rect x="470" y="150" width="20" height="240" rx="6" fill="#8b6f47" stroke="{INK}" stroke-width="4"/>'
    arms = ''.join(f'<g transform="translate(480 {y})"><path d="M-150 -22 H140 L170 0 L140 22 H-150 Z" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/></g>' for y, c in [(170, '#f5cf6d'), (230, '#9be5b5'), (290, '#8fbfe3')])
    return frame('#f6ecce', post + arms + blob(230, 330, 2.2, face='calm') + blob(760, 340, 2.0, fill='#f2a7c8', face='smile') + sparkle(120, 110, 1.2) + sparkle(860, 110, 1, '#f2a7c8'), 'A signpost with three arms and two characters deciding which way to go')

def cover_beyond_medication():
    # four building blocks stacked, only one of them a pill
    blocks = ''.join(f'<rect x="{x}" y="{y}" width="150" height="90" rx="18" fill="{c}" stroke="{INK}" stroke-width="5"/>' for x, y, c in [(330, 330, '#8fbfe3'), (500, 330, '#9be5b5'), (415, 230, '#f5cf6d')])
    pill = f'<g transform="translate(490 160) rotate(-20)"><rect x="-60" y="-24" width="120" height="48" rx="24" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><path d="M0 -24 V24" stroke="{INK}" stroke-width="5"/><path d="M0 -24 H60 A24 24 0 0 1 60 24 H0 Z" fill="#d96b52"/></g>'
    return frame('#d0e4de', blocks + pill + blob(200, 340, 2.2, face='smile') + blob(790, 330, 2.0, fill='#f5cf6d', face='calm') + sparkle(110, 110, 1.2) + sparkle(870, 120, 1, '#f2a7c8'), 'A stack of building blocks with a single pill on top, and two characters beside it')

def cover_exercise():
    # a blob mid-stride on a path, heart above it
    path = f'<path d="M80 400 Q300 300 480 380 T900 360" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round" stroke-dasharray="18 16"/>'
    heart = f'<path transform="translate(560 150) scale(2.2)" d="M0 14 C-18 0 -22 -14 -12 -20 C-6 -24 0 -20 0 -14 C0 -20 6 -24 12 -20 C22 -14 18 0 0 14 Z" fill="#d96b52" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>'
    legs = f'<path d="M36 92 L22 112 M64 92 L82 108" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    return frame('#dad9eb', path + heart + blob(480, 300, 2.3, fill='#9be5b5', face='grin', extras=legs) + sparkle(140, 130, 1.2) + sparkle(850, 140, 1, '#f2a7c8') + sparkle(800, 460, .9, '#f5cf6d'), 'A character striding along a dotted path with a heart above')

def cover_workplace():
    # a desk with a laptop, a headset blob, and a tidy row of sticky notes
    desk = f'<rect x="120" y="330" width="720" height="22" rx="11" fill="#2f3130" stroke="{INK}" stroke-width="5"/>'
    laptop = f'<rect x="380" y="240" width="180" height="96" rx="12" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><rect x="400" y="262" width="140" height="10" rx="5" fill="#e6dfd1"/><rect x="400" y="284" width="90" height="10" rx="5" fill="#f1bc31"/>'
    notes = ''.join(f'<rect x="{x}" y="120" width="70" height="70" rx="8" fill="{c}" stroke="{INK}" stroke-width="3" transform="rotate({r} {x+35} 155)"/>' for x, c, r in [(150, '#f5cf6d', -6), (240, '#f2a7c8', 4), (330, '#9be5b5', -3)])
    headset = f'<path d="M22 46 a28 28 0 0 1 56 0" fill="none" stroke="{INK}" stroke-width="5"/><rect x="16" y="42" width="12" height="18" rx="4" fill="{INK}"/><rect x="72" y="42" width="12" height="18" rx="4" fill="{INK}"/>'
    return frame('#f6ecce', desk + laptop + notes + blob(720, 280, 2.2, fill='#8fbfe3', face='smile', extras=headset) + sparkle(860, 120, 1.1, '#f2a7c8') + sparkle(100, 440, .9, '#9be5b5'), 'A desk with a laptop, a row of sticky notes and a character wearing a headset')

def cover_nutrition():
    # a plate with three colours, a clock, and a blob with a fork
    plate = f'<circle cx="420" cy="300" r="120" fill="#fdfbf7" stroke="{INK}" stroke-width="6"/><circle cx="420" cy="300" r="96" fill="none" stroke="#e6dfd1" stroke-width="3"/>'
    food = f'<path d="M420 300 L420 210 A90 90 0 0 1 498 255 Z" fill="#9be5b5" stroke="{INK}" stroke-width="3"/><path d="M420 300 L498 255 A90 90 0 0 1 465 380 Z" fill="#f5cf6d" stroke="{INK}" stroke-width="3"/><path d="M420 300 L465 380 A90 90 0 1 1 420 210 Z" fill="#d96b52" stroke="{INK}" stroke-width="3"/>'
    clock = f'<circle cx="720" cy="150" r="56" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/><path d="M720 150 V112 M720 150 L748 166" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    return frame('#d0e4de', plate + food + clock + blob(760, 340, 2.2, fill='#f2a7c8', face='grin') + sparkle(120, 120, 1.2) + sparkle(130, 440, .9, '#f5cf6d'), 'A plate divided into three colours, a clock, and a cheerful character')

def cover_executive():
    # a tidy checklist beside a tangle, with a blob holding the pen
    tangle = f'<path d="M140 180 C220 90, 300 300, 210 330 S120 230, 250 200 S330 330, 190 400" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round" opacity=".55"/>'
    board = f'<rect x="470" y="120" width="300" height="300" rx="20" fill="#fdfbf7" stroke="{INK}" stroke-width="5"/>'
    rows = ''.join(f'<rect x="510" y="{y}" width="34" height="34" rx="8" fill="{c}" stroke="{INK}" stroke-width="3"/><rect x="565" y="{y+11}" width="{w}" height="12" rx="6" fill="#e6dfd1"/>' for y, c, w in [(160, '#9be5b5', 160), (225, '#9be5b5', 120), (290, '#fdfbf7', 150), (355, '#fdfbf7', 90)])
    ticks = ''.join(f'<path d="M517 {y+18} l9 9 l16 -18" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>' for y in (160, 225))
    return frame('#dad9eb', tangle + board + rows + ticks + blob(370, 400, 1.9, fill='#f5cf6d', face='smile') + sparkle(860, 110, 1.1, '#f2a7c8') + sparkle(100, 460, .9, '#9be5b5'), 'A scribbled tangle beside a checklist with the first two items ticked, and a character between them')

# ------------------------------------------------------------ posts
POSTS = [
 dict(slug='blog-how-booking-works',
      hook='Two steps. No account.',          # the card line and the page's lede
      seo='No referral needed to look: how booking with ADHDme works',
      description='Browse every clinician, see real fees on the practice&#x27;s page, and book in two steps. No account, no upfront fee.', category='How it works', date='2026-09-02', read='3 min', cover=cover_booking,
      title='No referral needed to look. How booking with ADHDme works.',
      body=[
       'Most people with ADHD have already spent years navigating systems that seem designed for someone else. Forms that ask the same thing three times. Waitlists with no end date. A referral to get a referral. We built ADHDme to remove as much of that as we could.',
       '<strong>Step one is browsing.</strong> Every clinician in the network has a public profile: who they are, where they consult, what they focus on, and what an appointment costs before any rebate. You can read all of it without signing up. There is no gate between you and the information.',
       '<strong>Step two is booking, or asking.</strong> When a profile feels right, its button says Book or Enquire. Book opens that practice’s own diary: you pick a time, and that is it. Enquire opens the practice’s own form, and they reply to arrange a time. ADHDme does not charge a platform fee and does not ask for payment upfront.',
       'That is deliberately the whole process. Executive function is exactly the resource ADHD makes scarce, so a booking flow that demands a lot of it is a booking flow that quietly filters out the people it exists for.',
       'If you are unsure which clinician to start with, our GPs are the usual first step for assessment and prescribing. Psychologists and allied health practitioners support what comes after, from therapy to workplace adjustments.'],
      sources=[('How it works', 'how-it-works.html'), ('The Network', 'the-doctors.html')]),
 dict(slug='blog-body-doubling',
      hook='Sit with someone. Start.',          # the card line and the page's lede
      seo='Body doubling: the least complicated focus tool there is',
      description='Body doubling, the least complicated focus tool there is. Why working beside someone else can be enough to start, and how to try it.', category='Focus', date='2026-08-19', read='4 min', cover=cover_body_doubling,
      title='Body doubling: the least complicated focus tool there is.',
      body=[
       'Body doubling is the practice of doing a task while another person is present. They do not have to help. They do not even have to be doing the same thing. They just have to be there, in the room or on a video call, quietly getting on with their own work.',
       'People with ADHD have used it informally for decades, usually without a name for it. The library was easier to study in than the bedroom. The kitchen got cleaned faster when a friend was chatting at the table. The name came later; the effect was always real.',
       'Why does it work? The honest answer is that the research is still young. A 2024 study found body doubling helped people with ADHD both start and finish tasks, and earlier work suggests social presence nudges the brain’s reward and motivation pathways. What we know for certain is that it lowers the cost of starting, and starting is usually the hard part.',
       '<strong>How to try it.</strong> Pick one task you have been avoiding. Ask someone to sit with you for twenty minutes while they do their own thing. Say out loud what you are going to do. Then begin. If nobody is around, a video call with the camera on works, and so do the many online focus rooms built for exactly this.',
       'Our clinicians often suggest body doubling alongside other treatment. It costs nothing to try tonight.'],
      sources=[('Harnessing Focus with Body Doubling, Psychology Today', 'https://www.psychologytoday.com/us/blog/empowered-with-adhd/202408/harnessing-focus-with-body-doubling-a-strategy-for-adhd'), ('Body Doubling for ADHD, Healthline', 'https://www.healthline.com/health/adhd/body-double-adhd')]),
 dict(slug='blog-late-diagnosis',
      hook='Kinder than you expect.',          # the card line and the page's lede
      seo='Diagnosed as an adult? What the research actually says',
      description='Diagnosed as an adult? What the research actually says about late ADHD diagnosis. The evidence is clearer, and kinder, than most people expect.', category='Late diagnosis', date='2026-08-05', read='4 min', cover=cover_late_diagnosis,
      title='Diagnosed as an adult? What the research actually says.',
      body=[
       'A diagnosis in your thirties, forties or later tends to arrive with a strange mix of relief and grief. Relief, because there is finally a name for the pattern. Grief, for the years spent believing it was a character flaw. Both are normal, and both deserve room.',
       'It also helps to know what the science is confident about. In 2021, eighty researchers from twenty-seven countries published the World Federation of ADHD International Consensus Statement: 208 conclusions backed by large, replicated studies. Among them: ADHD is a real, well-validated condition. It persists into adulthood for most people. It is strongly heritable. And treatment, medical and non-medical, meaningfully reduces its impact.',
       'The same evidence explains why adults are missed. ADHD looks different when you have spent decades compensating for it. Women in particular are diagnosed later, often after burnout or a child’s diagnosis brings the pattern into view. Masking works until it does not.',
       '<strong>What good care looks like after a late diagnosis.</strong> The Australian clinical guideline recommends assessment that considers the whole person, a documented baseline before treatment starts, and regular review. In practice that means a clinician who measures rather than guesses, and who treats the years before diagnosis as context rather than evidence of failure.',
       'If any of this sounds like you, the clinicians in our network specialise in exactly this conversation. You can read their profiles before you decide anything.'],
      sources=[('World Federation of ADHD International Consensus Statement', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8328933/'), ('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('When Neurodivergent Burnout Reaches Its Breaking Point, ADDitude', 'https://www.additudemag.com/autistic-adhd-burnout-neurodivergent-masking/')]),
 dict(slug='blog-diagnosed-what-now', landing=True, tint='#f6ecce',
      hook='One thing at a time.',
      seo='I have been diagnosed with ADHD. What now?',
      description='Just diagnosed with ADHD? The first weeks, in order: what to read, who to see, what medication and therapy actually involve, and what can wait. A calm map, not a to-do list.', category='After diagnosis', date='2026-09-16', read='7 min', cover=cover_what_now,
      title='I have been diagnosed with ADHD. What now?',
      lede='A diagnosis explains the past and opens a lot of doors at once. You do not have to walk through all of them this week. Here is the order most people find workable, with what each step involves and what it costs in Australia.',
      body=[
       'The first feeling after a diagnosis is usually relief, and the second is usually a kind of vertigo: medication, therapy, coaching, telling people, the years that suddenly make sense. It all arrives together. The useful move is to separate what needs deciding now from what does not.',
       ('h2', 'Week one: let it land'),
       'Nothing clinical has to happen in the first week. Read your assessment report properly, once. Write down the three things in your life that the diagnosis most explains; those are the ones treatment should aim at, and it helps to have them in your own words before a clinician asks. If the diagnosis came late, the grief for the years before it is real and normal. Our post on <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-late-diagnosis.html">late diagnosis</a> is about exactly that.',
       ('h2', 'Decide about medication, without deciding forever'),
       'For most adults, the Australian guideline names stimulant medication as first-line treatment. It is also the decision people agonise over most, and the one that is easiest to reverse. A trial is a trial: a baseline of heart rate, blood pressure and weight, a low starting dose, and a review a few weeks later where you say whether the effect was worth it. Some people find it changes everything; some find the side effects outweigh the benefit; both are allowed.',
       'Who can prescribe depends on your state. In Queensland a specialist GP can now diagnose and prescribe for adults. In NSW that is arriving in stages through 2026. Elsewhere a psychiatrist usually starts it and a GP continues it. The GPs in the network say on their profiles what they can do, and the assessment fee is published before you book.',
       ('h2', 'Therapy is for what medication does not touch'),
       'Medication changes attention. It does not undo the habits, the workarounds, or the anxiety and low self-worth that come from decades of being told to try harder. That is the job of a psychologist, and it does not have to start at the same time as medication. Many people do better starting therapy a month or two in, once they can see what medication did and did not fix.',
       'A Mental Health Treatment Plan from any GP means Medicare pays part of up to ten sessions a year. Every psychologist in the network works by telehealth, and each profile carries the fee.',
       ('h2', 'What can wait'),
       ('list', [
        'Telling your employer. There is no obligation, and workplace adjustments can be requested without a diagnosis being disclosed. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-workplace-support.html">workplace support</a> post covers it.',
        'Coaching. Useful once the medication question is settled and you know which parts of the day are still hard.',
        'Rebuilding every system in your life. One change at a time sticks; six at once do not.',
        'Supplements and diets. The evidence is thin, and the money is better spent on a psychologist. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-nutrition.html">nutrition</a> post says what does help.']),
       ('h2', 'A shape that works for most people'),
       'Month one: medication trial with a GP, and the three things you want it to change written down. Month two or three: a psychologist, six to ten sessions in the first year. Alongside, one self-directed change, most often exercise placed before the hardest part of the day, or a fixed wake time. Then a review, and only then the next thing.',
       'The one rule underneath all of it: you are choosing, not being processed. Read the clinicians before you book anyone. Each profile is their own account of how they work and what it costs, and a bad fit is the most expensive thing in ADHD care.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('ADHD treatment after diagnosis', 'adhd-treatment-after-diagnosis.html'), ('How booking works', 'how-it-works.html')]),
 dict(slug='blog-adhd-support-beyond-medication', landing=True, tint='#d0e4de',
      hook='Four things, none of them a pill.',
      seo='ADHD support beyond medication: what else actually works',
      description='Therapy, occupational therapy, coaching, and the daily habits with real evidence. What each one does for ADHD, who provides it, what it costs, and how to choose without trying everything.', category='Treatment', date='2026-09-09', read='7 min', cover=cover_beyond_medication,
      title='ADHD support beyond medication: what else actually works.',
      lede='Medication is the best-evidenced single treatment for ADHD, and it is still only part of the picture. Whether you take it, cannot take it, or would rather not, these are the other supports with evidence behind them, and what each one is for.',
      body=[
       'A stimulant sharpens attention for the hours it is active. It does not teach a skill, repair a relationship, redesign a kitchen, or quiet the voice that says you should have managed this years ago. Everything below works on one of those.',
       ('h2', 'Psychological therapy'),
       'Cognitive behavioural therapy adapted for ADHD is the best-studied non-medication treatment for adults, with moderate effects on symptoms and larger effects on the anxiety, low mood and self-criticism that travel with a late diagnosis. Acceptance and commitment therapy and dialectical behaviour therapy skills are used for the same reasons. It is most useful once you know what medication did and did not change, which is why many psychologists suggest starting a month or two after a medication trial rather than the same week.',
       'A Mental Health Treatment Plan from a GP means Medicare pays part of up to ten sessions a year. The psychologists in the network are in Brisbane and by telehealth Australia-wide; each profile names their approach and their fee.',
       ('h2', 'Occupational therapy'),
       'When the difficulty is the mechanics of the day, an occupational therapist changes the task and the environment rather than the person: the morning routine, the layout of a workspace, sensory needs, the school report. It is AHPRA-registered, funded by the NDIS, private extras or a GP chronic condition management plan, and not by a Mental Health Treatment Plan. The network has paediatric OT in Brisbane today.',
       ('h2', 'Coaching'),
       'Coaching is not therapy and not a health profession. It is practical, forward-looking work on executive function: starting, planning, finishing, and building systems simple enough to survive a bad week. Because it is unregulated, credentials matter; the coaches in the network trained at the ADHD Coaching Academy and most hold an International Coaching Federation credential. If you work at least eight hours a week, JobAccess can fund it.',
       ('h2', 'The three daily habits with evidence'),
       ('list', [
        '<strong>Exercise.</strong> Twenty to thirty minutes of moderate aerobic exercise lifts attention for about an hour afterwards. Put it directly before the hardest part of the day. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-and-exercise.html">exercise</a> post has the detail, including safety on stimulants.',
        '<strong>Sleep.</strong> A fixed wake time, every day, does more for ADHD symptoms than almost any supplement, and stimulants make it matter more.',
        '<strong>Regular meals.</strong> Stimulants suppress appetite through the middle of the day. Eating by the clock, with a proper breakfast before the dose, protects weight and mood. See the <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-adhd-nutrition.html">nutrition</a> post.']),
       ('h2', 'What has little evidence'),
       'Omega-3 shows a small effect at best, mostly in children. Elimination diets have little adult evidence and real risks. Homeopathy has no reliable evidence for any condition. Neurofeedback has mixed results and a high price. None of these are dangerous in themselves; the cost is the money and the months they take from things that work.',
       ('h2', 'Choosing without trying everything'),
       'Name the problem first. If it is feelings about yourself, therapy. If it is the mechanics of the day, OT. If it is starting and finishing, coaching. If it is the afternoon slump, exercise before it. One at a time, with a review date, and the profiles read before anything is booked.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('World Federation of ADHD International Consensus Statement', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8328933/'), ('ADHD treatment after diagnosis', 'adhd-treatment-after-diagnosis.html')]),
 dict(slug='blog-adhd-and-exercise', landing=True, tint='#dad9eb',
      hook='An hour of focus, earned in twenty minutes.',
      seo='ADHD and exercise: what it does, when to do it, and staying safe on stimulants',
      description='Exercise gives a real, short-lived lift in attention. How big the effect is, when in the day to place it, why stimulant medication changes the safety rules, and how to design exercise you will still be doing in March.', category='Daily life', date='2026-09-02', read='6 min', cover=cover_exercise,
      title='ADHD and exercise: what it does, when to do it, and how to keep doing it.',
      lede='Exercise is the one lifestyle change for ADHD with a measurable effect on attention, and it is smaller and shorter than the internet says. Used precisely, it is still one of the best tools you have. Here is what the evidence supports, and the safety points that change if you take a stimulant.',
      body=[
       ('h2', 'What it does, honestly'),
       'Twenty to thirty minutes of moderate aerobic exercise gives a small to moderate lift in attention, working memory and self-control for roughly an hour afterwards. That is the finding that has replicated. Aerobic exercise, meaning anything that gets you breathing harder for a sustained stretch, has the best support. Mind-body exercise such as yoga shows a small effect. Coordinative exercise has too few studies to call.',
       'It does not replace medication. The effect is an addition, and a modest one. Anyone telling you to swap your prescription for a running plan is selling something.',
       ('h2', 'Place it, do not just do it'),
       'Because the effect lasts about an hour, timing matters more than volume. Put the session directly before the part of the day that needs the most from you: a study block, the meeting you dread, the admin you keep not doing. A brisk twenty minutes at two o’clock does more for a hard afternoon than an hour at six in the morning.',
       ('h2', 'If you take a stimulant, read this part'),
       ('list', [
        'Stimulants raise resting heart rate, so age-based heart-rate zones overstate how hard you are working. Go by how it feels and whether you can still talk in sentences.',
        'Stimulants suppress appetite. Many people train under-fuelled without noticing. Eat something before you go.',
        'Pre-workout caffeine adds to the stimulant’s effect on heart rate and blood pressure. Drop it.',
        'Chest pain, fainting, sustained palpitations or unusual breathlessness on a stimulant mean stop, and see a doctor before the next session.',
        'If you work with an exercise physiologist or trainer, tell them your medication and when you take it. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="adhd-exercise-physiologist.html">exercise physiology</a> page covers what an accredited one does and how a GP care plan can fund it.']),
       ('h2', 'Designing exercise that survives February'),
       'Dropping out is not a motivation problem. It is an executive-function problem: too many steps between the intention and the first movement. So design for the steps, not the willpower. Short sessions at a fixed time. Kit laid out the night before, or no kit at all. A route or a class that needs no decisions. Somebody expecting you, which is body doubling by another name. Immediate feedback, whether a tracker or a tick on a wall chart.',
       'Two rules that work. First, a minimum session you can always do, even at your worst; ten minutes counts. Second, never miss twice: after a lapse, no commentary, lower load, rebook on the spot. The lapse is not the problem. The week after the lapse is.',
       ('h2', 'Where to start this week'),
       'Pick the one part of your day that goes worst. Put twenty minutes of walking, cycling, or anything that gets you breathing harder directly before it, three times this week. Note whether the hour after felt different. That single observation tells you more than any article, including this one.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('Exercise and Sports Science Australia', 'https://www.essa.org.au/'), ('Body doubling: the least complicated focus tool there is', 'blog-body-doubling.html')]),
 dict(slug='blog-adhd-workplace-support', landing=True, tint='#f6ecce',
      hook='Adjustments, not excuses.',
      seo='ADHD workplace support in Australia: adjustments, disclosure and funding',
      description='What reasonable adjustments for ADHD look like at work, whether you have to disclose, what the law says in Australia, and how JobAccess can fund coaching and equipment. Practical, and specific.', category='Work', date='2026-08-26', read='7 min', cover=cover_workplace,
      title='ADHD at work: the adjustments that help, and how to ask for them.',
      lede='Most ADHD at work is not a performance problem. It is a fit problem between a brain and an environment designed for a different one. Australian law gives you a right to reasonable adjustments, and a government fund will pay for some of them. Here is what to ask for, and how.',
      body=[
       ('h2', 'Where it shows up'),
       'The same pattern, in most jobs: strong in a crisis, weak in the quiet weeks. Open-plan noise. Meetings that run long with no agenda. Tasks with no deadline, or a deadline three months away. Emails that need a decision. The morning after a late night. Knowing this about yourself is the first adjustment, because it tells you what to ask for.',
       ('h2', 'Adjustments that actually work'),
       ('list', [
        '<strong>Noise and interruption.</strong> Headphones as a norm, a quiet room to book, or a hybrid pattern with the deep-work days at home.',
        '<strong>Instructions in writing.</strong> A short written summary after a verbal briefing, and agendas before meetings. This costs the other person two minutes and saves you an afternoon.',
        '<strong>Deadlines made near.</strong> A long project broken into check-ins a week apart. Nobody with ADHD has ever been helped by a distant deadline.',
        '<strong>A regular check-in with your manager.</strong> Fifteen minutes a week, same time. It replaces the anxious guessing about how you are doing.',
        '<strong>Flexible hours around medication.</strong> If your stimulant is working at nine and gone by four, a day that starts earlier is a better day.',
        '<strong>Tools.</strong> Noise-cancelling headphones, a second screen, task software, dictation. Small, cheap, and often fundable.']),
       ('h2', 'Do you have to disclose?'),
       'No. There is no general obligation to tell an employer about a diagnosis. You can ask for most of the adjustments above without naming a condition, framed as how you work best; a good manager agrees to headphones and written briefings without a medical reason. Disclosure becomes useful when you need the legal protection or the funding below, and it can be limited to HR or to the person approving the adjustment.',
       'Under the Disability Discrimination Act 1992, ADHD is a disability, and an employer must make reasonable adjustments unless doing so would cause unjustifiable hardship. That word, reasonable, is where most negotiations live. The adjustments above are reasonable almost everywhere.',
       ('h2', 'Who pays'),
       'The Employment Assistance Fund, through JobAccess, funds work-related adjustments for people with disability who work at least eight hours a week, including self-employed people. That covers equipment and, under specialist mental health support, ADHD coaching, at around $1,770.44 a year by one practice’s figure. You apply with supporting documentation from a GP or specialist, and you can ask for an exemption rather than disclose the diagnosis to your employer. The coaches in the network run free sessions to help with the application; our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="adhd-coach.html">coaching</a> page has the detail.',
       ('h2', 'How to ask'),
       'In writing, briefly, with a proposed solution rather than a problem. “I work best with a written summary after briefings and a weekly fifteen-minute check-in. Can we try that for a month?” A trial with a review date is easier to say yes to than a permanent change, and once it has worked for a month it usually becomes permanent on its own.',
       'If it goes badly, the Australian Human Rights Commission and the Fair Work Ombudsman both take complaints about disability discrimination at work. Most requests never get near that. Most managers are relieved to be told what would help.'],
      sources=[('JobAccess: Employment Assistance Fund', 'https://www.jobaccess.gov.au/'), ('Australian Human Rights Commission: disability discrimination', 'https://humanrights.gov.au/our-work/disability-rights'), ('ADHD coaching in Australia', 'adhd-coach.html')]),
 dict(slug='blog-adhd-nutrition', landing=True, tint='#d0e4de',
      hook='Eat by the clock, not the appetite.',
      seo='ADHD and nutrition: what the evidence says, and what to do about appetite on stimulants',
      description='No diet treats ADHD, and one thing about eating matters a great deal: what stimulants do to appetite. How to plan around it, the supplements with honest evidence, and the red flags that need a doctor.', category='Daily life', date='2026-08-19', read='6 min', cover=cover_nutrition,
      title='ADHD and nutrition: the evidence, stated plainly.',
      lede='Search “ADHD diet” and you will find a hundred confident answers. The evidence supports almost none of them. What it does support is simpler, cheaper and more useful: regular meals, planned around what stimulant medication does to appetite. This is that plan, and the honest state of the rest.',
      body=[
       ('h2', 'Appetite on stimulants: the thing that actually matters'),
       'Reduced appetite is the commonest stimulant side effect. Hunger vanishes through the middle of the day and comes back hard in the evening, which is how people end up under-eating until six and over-eating until midnight, and losing weight without meaning to.',
       'The fix is to stop relying on hunger as the signal. A substantial breakfast with protein before the dose, while appetite is still there. Then eating by the clock: alarms at set times, and food that is small, energy-dense and needs no preparation, because the medication that removes your appetite also makes lunch feel like admin. A handful of nuts, a yoghurt, a boiled egg, a protein bar in the bag. Dinner can be the biggest meal; that is when hunger returns.',
       ('h2', 'Make food low-effort'),
       'Meal planning is an executive-function task, which is why it fails for the people who most need it. What lasts is five default meals you can make without thinking, a saved grocery order, and the same breakfast every day. Boring is the point. Variety can come at the weekend when there is capacity for it.',
       ('h2', 'The supplements and diets, honestly'),
       ('list', [
        '<strong>Omega-3 fish oil.</strong> A small effect at best, mostly in children, far below medication. Not harmful, not a treatment.',
        '<strong>Elimination diets.</strong> Little adult evidence, and real risks of nutritional inadequacy and disordered eating. Not routine.',
        '<strong>Sugar.</strong> Has not been shown to cause or worsen ADHD. Links between eating pattern and ADHD are observational only.',
        '<strong>Iron, zinc, vitamin D.</strong> Test where a deficiency is plausible, then correct it. Never supplement iron blind.',
        '<strong>Caffeine.</strong> Adds to a stimulant’s effect on heart rate, anxiety and sleep. Four energy drinks a day and poor sleep is a cause and effect, not a coincidence. Ask yourself how much, and when.']),
       ('h2', 'Red flags that need a doctor'),
       'Unintended weight loss of about five per cent in three months: tell the prescribing GP, because the dose or timing may need changing. ADHD carries higher rates of binge eating and bulimia than the general population; if eating feels out of control, or you are compensating for it, that is a conversation for a GP and an eating-disorder-experienced clinician, not a diet. The network has a psychologist credentialed in exactly this, and the profile says so.',
       ('h2', 'Where a dietitian fits'),
       'For most adults with ADHD, the plan above is the whole of what nutrition can offer, and it needs no professional. Medical nutrition therapy, eating disorders, and complex conditions alongside ADHD belong with an Accredited Practising Dietitian, and a GP chronic condition management plan gives a partial Medicare rebate. Tell the GP every supplement you take; most people do not, and interactions with ADHD medication are real.'],
      sources=[('Australian Evidence-Based Clinical Practice Guideline for ADHD', 'https://adhdguideline.aadpa.com.au/'), ('Dietitians Australia: find an Accredited Practising Dietitian', 'https://dietitiansaustralia.org.au/'), ('ADHD support beyond medication', 'blog-adhd-support-beyond-medication.html')]),
 dict(slug='blog-adhd-executive-functioning', landing=True, tint='#dad9eb',
      hook='Not a character flaw. A set of skills.',
      seo='ADHD and executive functioning: what it is, and what actually helps',
      description='Executive function is the part of ADHD nobody warned you about: starting, planning, finishing, remembering, regulating. What it is, why willpower is the wrong tool, and the handful of strategies with evidence behind them.', category='Daily life', date='2026-08-12', read='7 min', cover=cover_executive,
      title='ADHD and executive functioning: what it is, and what actually helps.',
      lede='Attention is the name on the diagnosis. Executive function is the part that actually runs your week: starting, planning, holding a thought, finishing, and managing the feeling when it goes wrong. Understanding it changes what you try, and what you stop blaming yourself for.',
      body=[
       ('h2', 'What executive function is'),
       'Executive functions are the brain’s management layer: the set of skills that turn an intention into a finished thing. Working memory, which holds the plan in mind. Inhibition, which stops the wrong thing. Task initiation, which starts the right thing. Planning and sequencing. Time perception. Emotional regulation. In ADHD they are unreliable rather than absent, which is why you can run a crisis brilliantly and not open an envelope for three weeks.',
       'Two consequences follow. One, the difficulty is real and neurological, so “just try harder” is asking the impaired system to fix itself. Two, because the difficulty is in the management layer rather than in ability, the fixes are mostly structural: move the management outside your head.',
       ('h2', 'Why willpower is the wrong tool'),
       'Willpower is executive function. Using it to compensate for weak executive function is borrowing from an overdrawn account, and it is why people with ADHD are so tired by Wednesday. The strategies that work reduce the amount of executive function a task needs, rather than trying to supply more of it.',
       ('h2', 'Strategies with evidence'),
       ('list', [
        '<strong>Externalise everything.</strong> One capture point for every task, on paper or in one app, and never in your head. Working memory is the weakest link; stop using it as storage.',
        '<strong>Make time visible.</strong> Analogue clocks, timers you can see, calendar blocks rather than lists. Time blindness is not fixed by knowing about it.',
        '<strong>Shrink the first step.</strong> Task initiation fails on size. “Write the report” never starts. “Open the document and write one bad sentence” does.',
        '<strong>Body doubling.</strong> Somebody present while you work, in the room or on a call, lowers the cost of starting more than any app. Our <a class="font-semibold text-[#1a1c1c] underline decoration-[#f1bc31] decoration-2 underline-offset-4" href="blog-body-doubling.html">body doubling</a> post explains it.',
        '<strong>Deadlines made near.</strong> A distant deadline does not exist to an ADHD brain. Break it into check-ins a week apart, with a person attached.',
        '<strong>Routines over decisions.</strong> Same breakfast, same bag, same place for the keys. Every decision removed is executive function saved for something that matters.',
        '<strong>Medication.</strong> Stimulants improve working memory and inhibition directly. They do not build the systems; they make building them possible.']),
       ('h2', 'Emotional regulation is executive function too'),
       'The flash of anger at a small thing, the disproportionate dread before a phone call, the rejection that lands like a verdict: these are executive-function difficulties with feelings, not a separate personality flaw. Naming that is often the biggest relief in the first months after diagnosis. Therapy, especially dialectical behaviour therapy skills, works on it directly, and the psychologists in the network name that on their profiles.',
       ('h2', 'Who helps with what'),
       'A psychologist works on the emotional side and on the beliefs about yourself that decades of executive-function failure leave behind. An occupational therapist works on the environment and the routines. A coach works on the systems, week by week, with accountability built in. Most people need one of the three, not all of them, and the one they need is the one aimed at the part of the week that goes worst.'],
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
<div data-reveal class="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
<div><h2 class="font-display-hero text-[32px] sm:text-[40px] leading-[1.1] font-extrabold tracking-tight text-on-surface mt-2">From the blog.</h2></div>
</div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-x-8 gap-y-12">{''.join(story_card(p) for p in POSTS)}</div>
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
<div><h2 class="text-2xl font-extrabold tracking-tight text-black">Ready to find your clinician?</h2><p class="text-[15px] text-black/75 font-medium mt-1">Browse profiles freely. No account or sign-up required.</p></div>
<a class="btn-press shrink-0 h-12 px-7 rounded-full bg-[#1a1c1c] text-white font-bold text-[15px] flex items-center gap-2 hover:-translate-y-0.5 transition-all" href="the-doctors.html">Find your clinician <span class="text-[#f1bc31]" aria-hidden="true">→</span></a></div>
</article>
<section class="max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12 pb-16 lg:pb-20"><h2 class="text-[15px] font-bold text-[#785a00] mb-5">More from the blog</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-6">{more}</div></section>
</main>
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
    return out


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
