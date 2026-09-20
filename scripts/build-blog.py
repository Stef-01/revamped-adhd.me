#!/usr/bin/env python3
"""Build blog post pages and the "From the blog" section on our-story.html.

    python3 scripts/build-blog.py          # write the pages
    python3 scripts/build-blog.py --check  # exit 1 if any page on disk differs from what would be written

Owns: blog-*.html in full, and the <!-- BLOG --> … <!-- /BLOG --> section on our-story.html. A hand
edit to any of that is lost on the next build; put the change here instead, and run --check before
committing so a page that has drifted is caught rather than silently reverted.

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
       '<strong>Step two is booking.</strong> When a profile feels right, the Book button takes you straight to that practice’s own booking page. You pick a time, and that is it. ADHDme does not charge a platform fee and does not ask for payment upfront.',
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
    return f'''<!-- BLOG --><section id="blog" class="w-full pb-16 lg:pb-20 px-gutter-mobile lg:px-gutter max-w-[1240px] mx-auto">
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


def post_page(p, head, footer, others):
    paras = ''.join(f'<p class="text-[17px] leading-[1.7] text-on-surface/85">{b}</p>' for b in p['body'])
    EXT = ' target="_blank" rel="noopener noreferrer"'
    src = ''.join(f'<li><a class="font-semibold text-[#1d64c2] hover:underline" href="{h}"{EXT if h.startswith("http") else ""}>{t}</a></li>' for t, h in p['sources'])
    more = ''.join(related_card(o) for o in others)
    return f'''{head}<main id="main" class="w-full bg-surface">
<article class="max-w-[760px] mx-auto px-gutter-mobile lg:px-gutter pt-12 pb-10">
<a class="inline-flex items-center gap-2 text-[15px] font-semibold text-neutral-600 hover:text-black transition-colors group mb-8" href="our-story.html#blog">{ARROW_BACK}Back to Our Story</a>
<div class="flex items-center gap-3 text-[13px] font-bold mb-4"><span class="whitespace-nowrap px-2.5 py-1 rounded-full bg-[#f1bc31]/20 text-[#674d00] uppercase tracking-wider">{p['category']}</span><span class="text-neutral-500 font-medium">{nice(p['date'])} · {p['read']} read · The ADHDme team</span></div>
<h1 class="hero-in font-display-hero text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.08] font-extrabold tracking-tight text-on-surface mb-6">{p['title']}</h1>
<p class="hero-in hero-in-2 font-editorial-quote text-[22px] leading-relaxed text-on-surface-variant mb-8">{p['hook']}</p>
<div class="hero-in hero-in-3 rounded-3xl overflow-hidden border border-black/[0.06] shadow-sm mb-10 aspect-video bg-[#f6f1e6]"><img width="960" height="540" fetchpriority="high" decoding="async" src="assets/blog/{p['slug']}.svg" alt="" class="w-full h-full object-cover"></div>
<div class="space-y-6">{paras}</div>
<div class="mt-10 p-6 rounded-2xl bg-[#faf9f6] border border-[#eeebe5]"><h2 class="text-[15px] font-bold text-[#5f5e59] mb-3">Sources and further reading</h2><ul class="space-y-2 text-sm">{src}</ul></div>
<div class="mt-10 bg-[#f1bc31] rounded-3xl p-8 flex flex-col sm:flex-row items-center justify-between gap-6 border border-black/10">
<div><h2 class="text-2xl font-extrabold tracking-tight text-black">Ready to find your clinician?</h2><p class="text-[15px] text-black/75 font-medium mt-1">Browse profiles freely. No account or sign-up required.</p></div>
<a class="btn-press shrink-0 h-12 px-7 rounded-full bg-black text-white font-bold text-[15px] flex items-center gap-2 hover:-translate-y-0.5 transition-all" href="the-doctors.html">Find your clinician <span class="text-[#f1bc31]" aria-hidden="true">→</span></a></div>
</article>
<section class="max-w-[1240px] mx-auto px-gutter-mobile lg:px-gutter pb-16 lg:pb-20"><h2 class="text-[15px] font-bold text-[#785a00] mb-5">More from the blog</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-6">{more}</div></section>
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
        others = [o for o in POSTS if o is not p]
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
