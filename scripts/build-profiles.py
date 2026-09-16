#!/usr/bin/env python3
"""Generate clinician profile pages from one data set.

Usage: python3 scripts/build-profiles.py
Template shell (head, header, footer) is taken from dr-anubhav-saxena.html so
all profiles share the same structure. Edit CLINICIANS below and re-run.
"""
import html, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'dr-anubhav-saxena.html'

def esc(s): return html.escape(s, quote=False)

BADGE = {
    'rec':  ('bg-[#fef3c7] text-[#92400e] border border-[#fde68a]', 'text-[#b91a24]', 'favorite',  'Recommended', '#fde68a'),
    'clin': ('bg-[#eaf4ff] text-[#1e40af] border border-[#bfdbfe]', 'text-[#2563eb]', 'menu_book', 'Clinical',    '#bfdbfe'),
    'prac': ('bg-amber-50 text-amber-900 border border-amber-200/60', 'text-[#b45309]', 'handyman',  'Practical',   '#fde68a'),
}
CHIP = {
    'blue':  ('bg-[#f0f7ff] text-[#1e40af] border border-[#dbeafe]', 'text-[#2563eb]'),
    'amber': ('bg-[#fffbeb] text-[#92400e] border border-[#fde68a]', 'text-[#b45309]'),
    'green': ('bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0]', 'text-[#16a34a]'),
}

# ---------------------------------------------------------------- data
ARTICLES = {
    'executive-dysfunction': ('https://www.additudemag.com/adhd-executive-dysfunction-how-to-be-more-productive-consistent/', 2024, 'You Can’t Train Away ADHD Executive Dysfunction', 'ADDitude Magazine', 'Why executive dysfunction stalls the leap from intention to action, and how to build systems and backstops that make consistent productivity possible.'),
    'neurodivergent-burnout': ('https://www.additudemag.com/autistic-adhd-burnout-neurodivergent-masking/', 2026, 'When Neurodivergent Burnout Reaches Its Breaking Point', 'ADDitude Magazine', 'Recognising autistic and ADHD burnout, from poor focus to social withdrawal, and how neurodiversity-affirming care and unmasking support recovery.'),
    'body-doubling': ('https://www.psychologytoday.com/us/blog/empowered-with-adhd/202408/harnessing-focus-with-body-doubling-a-strategy-for-adhd', 2024, 'Harnessing Focus with “Body Doubling”: A Strategy for ADHD', 'Psychology Today', 'How the simple presence of another person can turn task paralysis into momentum, and practical ways to set up body doubling in daily life.'),
    'women-girls-diagnosis': ('https://www.additudemag.com/adhd-in-women-girls-symptoms-diagnosis-recommendations/', 2022, 'ADHD in Women and Girls: Why Female Symptoms Slip Through Diagnostic Cracks', 'ADDitude Magazine', 'Why ADHD in women and girls is under-recognised and misdiagnosed, and what clinicians should look for when symptoms present differently.'),
    'adult-women-undiagnosed': ('https://www.additudemag.com/adhd-symptoms-adult-women-undiagnosed/', 2023, 'Study: Women with Undiagnosed ADHD Suffer Poor Self-Esteem, Mental Health', 'ADDitude Magazine', 'Research on how missed or late diagnosis affects women’s self-esteem and mental health, and how timely diagnosis changes the picture.'),
    'emotional-resilience': ('https://www.additudemag.com/emotional-resilience-adhd-coping/', 2021, 'How’s Your Emotional Resilience? Learning to Cope with Intense ADHD Feelings', 'ADDitude Magazine', 'Practical ways to build resilience when ADHD feelings run hot, from naming emotions to planning for known triggers.'),
}

CLINICIANS = [
    dict(slug='dr-anubhav-saxena', name='Dr Anubhav Saxena', short='Dr Saxena', creds='MBBS, FRACGP',
         category='General Practitioner • Prescriber &amp; Integrative Care', img='assets/dr-anubhav-saxena-profile.jpg',
         verified='AHPRA Registered', location='Sydney &amp; Nationwide Telehealth (AU)',
         chips=[('videocam','Telehealth','blue'),('prescriptions','ADHD Prescriber','amber'),('dot','Zero-shame care','dot'),('bolt','Next Available: Tomorrow','green')],
         accepting='<span class="font-semibold text-black">Accepting New Patients</span> • Initial consults &amp; second opinions',
         book_href='https://healthengine.com.au/doctor/nsw/beecroft/dr-anubhav-saxena/p123180?utm_source=adhdme&utm_medium=referral&utm_campaign=network', book_label='Book with Dr Saxena', book_external=True,
         fee_badge='AU Eligible',
         fees=[('Initial Intake Consultation (45 mins)','Consult $299 • Medicare Rebate -$0','$299'),('Review &amp; Titration (20 mins)','Consult $199 • Medicare Rebate -$0','$199')],
         fee_note='No upfront pre-payment. Card charged only after appointment.',
         quote='Adult ADHD care should never feel like an interrogation. Our sessions are calm, collaborative, and designed entirely around your executive capacity.',
         promises=[('videocam_off','#2563eb','Camera Optional'),('receipt_long','#d97706','Written Summary'),('favorite','#2563eb','Zero Judgment')],
         bio=['Anubhav trained at the University of Sydney and works in Double Bay and Beecroft. He works from measurement rather than impression, and takes an integrative view: ADHD is looked at alongside sleep, cardiovascular and metabolic health rather than on its own, with a documented baseline before anything starts and review at set intervals rather than only when a problem gets loud enough to prompt a call.',
              'He also does aged-care and home visits, and gives a good deal of his spare time to the long-suffering cause of the Parramatta Eels.'],
         focus=['Structured adult ADHD assessment','Baseline cardiovascular &amp; metabolic screening','Integrative and preventive care','Chronic disease management'],
         details=[('Languages','English, Hindi, Urdu'),('Qualifications','MBBS, FRACGP, MPhil, BSc(Adv), DCH'),('Appointments','Long first appointment, scheduled reviews'),('Consulting Mode','Practice appointments &amp; phone consultations')],
         stepfree='Yes', newpatients='Yes',
         articles=[('executive-dysfunction','rec'),('neurodivergent-burnout','clin'),('body-doubling','prac')]),

    dict(slug='dr-anu-saxena', name='Dr Anu Saxena', short='Dr Anu Saxena', creds='MD, FRACGP',
         category='General Practitioner • Mental Health &amp; Women’s Health', img='assets/dr-anu-saxena.jpg',
         verified='AHPRA Registered', location='Bay Health Clinic • Double Bay &amp; Hornsby',
         chips=[('psychology','Mental health focus','blue'),('prescriptions','Endorsed ADHD Prescriber','amber'),('dot','Women’s health','dot'),('translate','Hindi &amp; Urdu','green')],
         accepting='<span class="font-semibold text-black">Accepting New Patients</span> • Practice appointments in Double Bay &amp; Hornsby',
         book_href='https://healthengine.com.au/doctor/nsw/double-bay/dr-anusha-saxena/p160121', book_label='Book with Dr Anu Saxena', book_external=True,
         fee_badge='AU Eligible',
         fees=[('Initial Intake Consultation (45 mins)','Consult $299 • Medicare Rebate -$0','$299'),('Review &amp; Titration (20 mins)','Consult $199 • Medicare Rebate -$0','$199')],
         fee_note='No upfront pre-payment. Card charged only after appointment.',
         quote='I came to medicine through psychology. Culturally sensitive, holistic and patient-centred care is not an add-on for me, it is the whole point.',
         promises=[('diversity_3','#2563eb','Culturally Sensitive'),('spa','#d97706','Holistic Care'),('favorite','#2563eb','Zero Judgment')],
         bio=['Anu is an experienced GP at Bay Health Clinic in Double Bay, and a Fellow of the Royal Australian College of General Practitioners. She came to medicine through psychology, a Bachelor of Psychology with First Class Honours at the University of Sydney, then her MD at the Australian National University, with a background in psychiatry and general medicine: hospital training across NSW, including Blacktown and Bathurst, rotations in cardiology, paediatrics and psychiatry, and the Sydney Child Health Program through the Sydney Children’s Hospital Network. She holds a Diploma of Child Health.',
              'Her clinical interests are ADHD, mental health, women’s health and functional medicine. She has completed an endorsed ADHD prescriber course, is training in Focused Psychological Strategies, and is completing further qualifications in functional medicine, nutrition, lifestyle medicine and health coaching. Of Indian origin and speaking Hindi and Urdu, she values culturally sensitive, holistic and patient-centred care. Outside medicine she enjoys travelling, learning about different cultures, charity and community work, and staying active through sport, cricket and tennis included.'],
         focus=['Adult ADHD assessment and prescribing','Mental health in general practice','Women’s health','Functional and lifestyle medicine'],
         details=[('Languages','English, Hindi, Urdu'),('Qualifications','MD, FRACGP, BPsych(Hons), DCH'),('Appointments','Appointment lengths set with the practice'),('Consulting Mode','Practice appointments in Double Bay &amp; Hornsby')],
         stepfree='Not declared', newpatients='Yes',
         articles=[('women-girls-diagnosis','rec'),('adult-women-undiagnosed','clin'),('emotional-resilience','prac')]),

]

# ---------------------------------------------------------------- render
def chip(icon, label, style):
    if style == 'dot':
        return f'<span class="px-3 py-1 bg-amber-50/80 text-amber-900 border border-amber-200/50 rounded-full text-xs font-medium flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-[#b91a24]"></span>{label}</span>'
    box, ic = CHIP[style]
    return f'<span class="px-3 py-1 {box} rounded-full text-xs font-medium flex items-center gap-1.5"><span class="material-symbols-outlined text-xs {ic}">{icon}</span>{label}</span>'

def fee_row(name, sub, out):
    return f'<div class="p-3.5 rounded-2xl bg-[#faf9f6] border border-[#eeebe5] flex items-center justify-between gap-3"><div><div class="font-semibold text-xs text-black">{name}</div><div class="text-[11px] text-neutral-500">{sub}</div></div><div class="text-right shrink-0"><span class="text-[10px] uppercase font-semibold text-neutral-400 block">Out-of-Pocket</span><span class="font-bold text-base text-black">{out}</span></div></div>'

def promise(icon, color, label):
    return f'<div class="p-4 rounded-2xl bg-[#faf9f6] text-center flex flex-col items-center justify-center border border-[#eeebe5] hover:bg-[#f3f1ec] transition-colors"><span class="material-symbols-outlined text-[{color}] mb-1.5 text-xl">{icon}</span><span class="text-xs text-black font-semibold">{label}</span></div>'

def focus_item(t):
    return f'<div class="flex items-start gap-2.5 p-3 rounded-2xl bg-[#faf9f6] border border-[#eeebe5]"><span class="material-symbols-outlined text-base text-[#785a00] shrink-0 mt-0.5">check_circle</span><span class="text-xs font-medium text-neutral-800">{t}</span></div>'

def detail(label, value):
    return f'<div class="p-3 rounded-2xl bg-[#faf9f6] border border-[#eeebe5] flex flex-col gap-1"><span class="text-[11px] font-semibold text-neutral-500">{label}</span><span class="text-xs font-bold text-neutral-800">{value}</span></div>'

def yesno(label, value):
    ok = value == 'Yes'
    cls = 'text-[#166534] bg-[#f0fdf4] border border-[#bbf7d0]' if ok else 'text-neutral-600 bg-[#f3f1ec] border border-[#e6e2da]'
    return f'<div class="p-3 rounded-2xl bg-[#faf9f6] border border-[#eeebe5] flex items-center justify-between"><span class="text-[11px] font-semibold text-neutral-500">{label}</span><span class="text-xs font-bold {cls} px-2 py-0.5 rounded-full">{value}</span></div>'

def article(key, kind, short):
    href, year, title, source, desc = ARTICLES[key]
    box, ic, icon, badge, hover = BADGE[kind]
    return f'''<a href="{href}" target="_blank" rel="noopener noreferrer" class="group rounded-2xl bg-[#faf9f6] border border-[#eeebe5] flex flex-col overflow-hidden transition-all hover:bg-white hover:border-[{hover}] hover:shadow-md hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#f1bc31]">
<div class="aspect-video overflow-hidden bg-[#eeebe5]"><img loading="lazy" decoding="async" src="assets/articles/{key}.jpg" alt="" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"></div>
<div class="p-5 flex flex-col justify-between gap-4 flex-1">
<div class="space-y-2.5">
<div class="flex items-center justify-between gap-2"><span class="px-2 py-0.5 rounded-full {box} font-label-sm text-[11px] font-bold flex items-center gap-1"><span class="material-symbols-outlined text-xs {ic}" style="font-variation-settings: 'FILL' 1;">{icon}</span>{badge}</span><span class="text-xs text-neutral-400 font-medium">{year}</span></div>
<h4 class="font-bold text-sm text-black leading-snug group-hover:text-[#1d64c2] transition-colors">{esc(title)}</h4>
<p class="text-[11px] text-neutral-500 font-medium">{esc(source)}</p>
</div>
<div class="pt-2 border-t border-[#eeebe5] flex items-center justify-end"><span class="inline-flex items-center gap-1 text-xs font-bold text-[#1d64c2] group-hover:text-[#1e40af] transition-colors">Read<span class="material-symbols-outlined text-sm transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5">north_east</span></span></div>
</div>
</a>'''

def render_main(c):
    ph = c.get('placeholder', False)
    ext = ' target="_blank" rel="noopener noreferrer"' if c['book_external'] else ''
    verified_cls = 'bg-[#f1bc31] text-[#251a00] border border-[#e2d5bd]' if not ph else 'bg-[#f3f1ec] text-neutral-700 border border-[#e6e2da]'
    verified_icon = 'verified' if not ph else 'pending'
    top_note = '' if not ph else '<div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#fef3c7] border border-[#fde68a] text-[#92400e] text-xs font-semibold tracking-wide"><span class="material-symbols-outlined text-sm">pending</span>Profile in progress</div>'
    book_note = '' if c['book_external'] else ''
    book_hint = '<span class="text-[11px] text-neutral-500 text-center lg:text-left">Opens the practice’s booking page in a new tab.</span>' if c['book_external'] else ''
    return f'''<main id="main" class="w-full min-h-[calc(100vh-80px)] bg-gradient-to-b from-[#fffbeb]/70 via-[#f0f7ff]/60 to-[#f9f9f8]"><div class="w-full bg-[#fbfbfa] min-h-[calc(100vh-80px)] pb-20">
<div class="w-full border-b border-[#ebd8ab]/50 bg-[#fffdfa]/80 py-3.5 backdrop-blur-sm"><div class="max-w-7xl mx-auto px-6 sm:px-12 flex flex-wrap items-center justify-between gap-3"><a class="inline-flex items-center gap-2 font-label-md text-sm text-neutral-600 hover:text-black transition-colors group font-semibold" href="the-doctors.html"><span class="material-symbols-outlined text-base transition-transform group-hover:-translate-x-0.5">arrow_back</span><span>Back to clinicians</span></a><div class="flex flex-wrap items-center gap-2">{top_note}<div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#f4f7fa] border border-[#d9e2ec] text-[#1e3a8a] text-xs font-semibold tracking-wide"><span class="w-2 h-2 rounded-full bg-[#2563eb] animate-pulse"></span><span>{c['category']}</span></div></div></div></div>
<div class="max-w-7xl mx-auto px-6 sm:px-12 pt-10"><div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
<div class="lg:col-span-5 flex flex-col gap-8">
<div data-reveal class="relative bg-white rounded-3xl p-6 border border-[#eae8e3] shadow-sm flex flex-col sm:flex-row lg:flex-col items-center lg:items-start gap-6"><div class="relative shrink-0"><div class="w-48 h-48 sm:w-56 sm:h-56 lg:w-full lg:h-72 rounded-2xl overflow-hidden shadow-inner bg-[#f5f4f0]"><img fetchpriority="high" decoding="async" alt="{c['name']}" class="w-full h-full object-cover object-top" src="{c['img']}"></div><div class="absolute -bottom-3 left-1/2 -translate-x-1/2 {verified_cls} font-label-sm text-xs font-bold px-3.5 py-1 rounded-full shadow-sm flex items-center gap-1.5 whitespace-nowrap"><span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">{verified_icon}</span><span>{c['verified']}</span></div></div>
<div class="flex flex-col gap-4 w-full"><div class="space-y-1.5 text-center lg:text-left"><div class="flex flex-wrap items-center justify-center lg:justify-start gap-2.5"><h1 class="text-2xl sm:text-3xl font-bold font-headline-lg text-black tracking-tight">{c['name']}</h1><span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#f4f7fa] text-[#1d64c2] border border-[#d9e2ec]">{c['creds']}</span></div><p class="text-xs text-neutral-500 flex items-center justify-center lg:justify-start gap-1"><span class="material-symbols-outlined text-sm text-[#2563eb]">location_on</span><span>{c['location']}</span></p></div>
<div class="flex flex-wrap gap-1.5 justify-center lg:justify-start">{''.join(chip(*x) for x in c['chips'])}</div>
<div class="pt-4 border-t border-[#eae8e3] flex flex-col gap-3"><div class="text-xs text-neutral-500 text-center lg:text-left">{c['accepting']}</div><a class="btn-press w-full inline-flex items-center justify-center gap-2 h-12 px-7 rounded-full bg-black text-white font-label-md text-sm hover:bg-neutral-800 transition-all shadow-sm hover:-translate-y-0.5 group" href="{c['book_href']}"{ext}><span class="font-bold">{c['book_label']}</span><span class="text-[#f1bc31] font-headline-md leading-none group-hover:translate-x-1 transition-transform">→</span></a>{book_hint}</div></div></div>
<div data-reveal="1" class="bg-white rounded-3xl p-6 border border-[#eae8e3] shadow-sm flex flex-col gap-4"><div class="flex items-center justify-between"><div class="flex items-center gap-2.5"><span class="w-8 h-8 rounded-full bg-[#f1bc31]/20 flex items-center justify-center text-primary"><span class="material-symbols-outlined text-lg">calculate</span></span><h3 class="font-headline-md text-base font-bold text-black">Medicare &amp; Fee Transparency</h3></div><span class="px-2.5 py-0.5 bg-[#fffbeb] text-[#92400e] border border-[#fde68a] text-[11px] font-bold rounded-full flex items-center gap-1"><span class="material-symbols-outlined text-xs text-[#b45309]" style="font-variation-settings: 'FILL' 1;">verified</span>{c['fee_badge']}</span></div><div class="space-y-2.5">{''.join(fee_row(*f) for f in c['fees'])}</div><div class="flex items-center gap-1.5 text-[11px] text-neutral-500"><span class="material-symbols-outlined text-sm text-[#785a00]">verified_user</span><span>{c['fee_note']}</span></div></div>
</div>
<div class="lg:col-span-7 flex flex-col gap-8">
<div data-reveal="1" class="bg-white rounded-3xl p-8 border border-[#eae8e3] shadow-sm flex flex-col gap-6"><div class="flex items-center gap-3"><span class="w-9 h-9 rounded-full bg-[#f1bc31]/20 flex items-center justify-center text-primary"><span class="material-symbols-outlined text-xl">psychology</span></span><h2 class="font-headline-md text-xl font-bold text-black">Neurodivergence Philosophy</h2></div><blockquote class="font-editorial-quote text-xl sm:text-2xl text-neutral-800 italic leading-relaxed pl-5 border-l-2 border-[#f1bc31]">“{c['quote']}”</blockquote><div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">{''.join(promise(*p) for p in c['promises'])}</div></div>
<div data-reveal="2" class="bg-white rounded-3xl p-8 border border-[#eae8e3] shadow-sm flex flex-col gap-5"><div class="flex items-center gap-3"><span class="w-9 h-9 rounded-full bg-[#f1bc31]/20 flex items-center justify-center text-primary"><span class="material-symbols-outlined text-xl">clinical_notes</span></span><h3 class="font-headline-md text-xl font-bold text-black">Clinical Background &amp; Approach</h3></div><div class="space-y-3">{''.join(f'<p class="text-sm {"text-neutral-700" if i==0 else "text-neutral-600"} leading-relaxed">{p}</p>' for i,p in enumerate(c['bio']))}</div>
<div class="pt-3 border-t border-[#eeebe5]"><h4 class="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-3">Core Clinical Focus</h4><div class="grid grid-cols-1 sm:grid-cols-2 gap-3">{''.join(focus_item(t) for t in c['focus'])}</div></div>
<div class="pt-3 border-t border-[#eeebe5]"><h4 class="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-3">Practice Details &amp; Credentials</h4><div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">{''.join(detail(*d) for d in c['details'])}{yesno('Step-Free Access', c['stepfree'])}{yesno('Taking New Patients', c['newpatients'])}</div></div></div>
</div></div>
<div data-reveal class="mt-10 bg-white rounded-3xl p-8 border border-[#eae8e3] shadow-sm flex flex-col gap-6"><div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2"><div class="flex items-center gap-3"><span class="w-9 h-9 rounded-full bg-[#f1bc31]/20 flex items-center justify-center text-primary"><span class="material-symbols-outlined text-xl">auto_stories</span></span><div><h3 class="font-headline-md text-xl font-bold text-black">Recent Articles Liked &amp; Recommended</h3><p class="text-xs text-neutral-500">External essays, clinical perspectives, and neurodiversity insights {c['short']} shares with patients</p></div></div><span class="px-3 py-1 bg-[#faf9f6] text-xs font-semibold rounded-full text-neutral-600 border border-[#eeebe5] self-start sm:self-auto">Curated Reads</span></div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">{''.join(article(k, kind, c['short']) for k, kind in c['articles'])}</div></div>
</div></div></main>'''

def main():
    tpl = TEMPLATE.read_text()
    head = tpl[:tpl.index('<main')]
    tail = tpl[tpl.index('</main>') + 7:]
    for c in CLINICIANS:
        page_head = re.sub(r'<title>.*?</title>', f'<title>ADHDme - {esc(c["name"])}</title>', head, count=1)
        (ROOT / f"{c['slug']}.html").write_text(page_head + render_main(c) + tail)
        print('built', f"{c['slug']}.html")

if __name__ == '__main__':
    main()
