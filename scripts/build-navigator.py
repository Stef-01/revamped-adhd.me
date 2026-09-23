#!/usr/bin/env python3
"""Build care-navigator.html: a two-level bubble map from where ADHD gets in the way to the clinicians
whose profiles say they work on exactly that.

    python3 scripts/build-navigator.py          # write the page
    python3 scripts/build-navigator.py --check  # exit 1 if the page on disk differs from what would be written

Owns care-navigator.html in full. Edit DOMAINS here and rebuild.

Deterministic on purpose: a domain (School, Work, Home, Relationships, Health) opens four aspects, and an
aspect opens a fixed list of clinicians. Each entry names the clinician by id and gives the reason in the
words of their own profile (a chip or an experience line), so the page cannot claim a focus the profile
does not declare. The build refuses an id that is not in CLINICIANS. Every result panel is rendered
into the HTML, so without JavaScript the page is the whole tree as a list; the script only chooses which
panel shows and where the bubbles sit.

The page shell (head, header, footer) is lifted from how-it-works.html at build time, like the search
pages, so header and footer changes reach it on rebuild.
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


# ---------------------------------------------------------------- the tree
# tint: the landing page's door colours, one per domain. who: (clinician id, why), the why quoted from
# the profile. A clinician can sit under several aspects; a reason is always in their own words.
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
   ('debbie-hirte', 'Executive functioning · Gifted & talented')]),
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
   ('romney-taylor', 'Executive functioning · Advocacy & inclusion')]),
  dict(key='burnout', label='Stress and burnout', who=[
   ('jessica-katsamatsas', 'Anxiety, burnout, low self-esteem'),
   ('kate-dallimore', 'Ongoing stress, anxiety, overwhelm'),
   ('jeff-leech', 'Trauma, anxiety, depression and performance'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed')]),
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
   ('flynn-simonis', 'Sensory profiles and functional challenges, in clinic and at home')]),
  dict(key='parenting', label='Parenting a child with ADHD', who=[
   ('lachlan-avent', 'Triple P Stepping Stones parenting practitioner'),
   ('lauren-poulos', 'PCIT & early intervention · Toddlers & children'),
   ('flynn-simonis', 'Paediatric OT · Parent training'),
   ('debbie-hirte', 'Children & teens')]),
  dict(key='emotions', label='Meltdowns and emotional outbursts', who=[
   ('donna-italiano', 'Emotional regulation'),
   ('ellie-putland', 'Young people · CBT, ACT & DBT'),
   ('flynn-simonis', 'Emotional regulation needs in children')]),
  dict(key='body', label='Sleep and physical health', who=[
   ('anubhav-saxena', 'Baseline physical screening · Integrative care'),
   ('sarah-savage', 'Exercise as medicine · Pilates & hydrotherapy'),
   ('anu-saxena', 'Mental health focus · Women’s health')]),
 ]),
 dict(key='relationships', label='Relationships', tint='#fbd8cf', aspects=[
  dict(key='partner', label='Partner and family relationships', who=[
   ('jessica-katsamatsas', 'Relationship difficulties and attachment wounds'),
   ('kate-row', 'Communication and social skills building'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed')]),
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
   ('lachlan-avent', 'Emotion Focussed Therapy')]),
 ]),
 dict(key='health', label='Health', tint='#dad9eb', aspects=[
  dict(key='assessment', label='ADHD assessment and diagnosis', who=[
   ('anubhav-saxena', 'Structured adult ADHD assessment'),
   ('anu-saxena', 'Endorsed ADHD prescriber course'),
   ('lachlan-avent', 'Autism & ADHD assessment'),
   ('meera-lakhani', 'Autism & ADHD assessment · Cognitive assessment')]),
  dict(key='medication', label='ADHD medication', who=[
   ('anubhav-saxena', 'Baseline cardiovascular and metabolic screening'),
   ('anu-saxena', 'Mental health focus · Endorsed ADHD prescriber course')]),
  dict(key='mood', label='Anxiety and low mood', who=[
   ('jessica-katsamatsas', 'Anxiety, burnout, low self-esteem'),
   ('jeff-leech', 'Anxiety & depression · Schema therapy & ACT'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed'),
   ('ellie-putland', 'Trauma-informed · CBT, ACT & DBT'),
   ('alice-bui', 'Trauma-informed · CALD & refugee clients')]),
  dict(key='eating', label='Appetite and eating problems', who=[
   ('samantha-courtney', 'Eating disorders · CEDC-MH credentialed'),
   ('anubhav-saxena', 'Baseline physical screening')]),
 ]),
]

# ---------------------------------------------------------------- icons
# One line drawing per bubble, inline SVG on a 24-box, stroked in the bubble's own text colour.
ICONS = {
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


def icon(key):
    return (f'<svg class="bubble__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[key]}</svg>')


for d in DOMAINS:
    assert len(d['aspects']) == 4, f"{d['label']}: four aspects, not {len(d['aspects'])}"
    assert d['key'] in ICONS, f"{d['label']}: no icon"
    for asp in d['aspects']:
        assert f"{d['key']}:{asp['key']}" in ICONS, f"{d['label']} › {asp['label']}: no icon"
        for cid, _ in asp['who']:
            if cid not in BY_ID:
                raise SystemExit(f'build-navigator: {d["label"]} › {asp["label"]} names unknown clinician {cid!r}')

SEO = 'ADHD care navigator: pick where it gets in the way, meet who helps'
DESCRIPTION = ('School, work, home, relationships or health: pick the place ADHD gets in the way and the part of it, '
               'and see the clinicians whose profiles say they work on exactly that.')


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


# ---------------------------------------------------------------- the map
# Bubbles are buttons positioned by the script on a square stage. No connector lines: the ring says what
# belongs to the centre, a soft halo in the domain tint sits behind the chosen domain, and each ring springs
# out of the centre with a short stagger, so the motion is the connection. Before anyone taps, the domain
# bubbles drift slowly on their own small orbits. Both respect prefers-reduced-motion. Colours are the
# domain tints. With JavaScript off the stage is hidden and the list shows.
STYLE = '''<style>
.nav-stage{position:relative;aspect-ratio:1/1;max-width:640px;margin:0 auto;}
.nav-halo{position:absolute;left:50%;top:50%;width:64%;aspect-ratio:1/1;transform:translate(-50%,-50%) scale(.6);border-radius:50%;background:radial-gradient(circle,var(--tint,#f6f4ee) 0%,var(--tint,#f6f4ee) 35%,rgba(250,250,247,0) 72%);opacity:0;pointer-events:none;transition:opacity .6s ease,transform .7s cubic-bezier(.2,.8,.2,1),background .4s;}
.nav-halo.is-on{opacity:.9;transform:translate(-50%,-50%) scale(1);}
.bubble{position:absolute;left:var(--x);top:var(--y);transform:translate(-50%,-50%) scale(var(--s,1));width:var(--w,22%);aspect-ratio:1/1;display:flex;flex-direction:column;gap:6px;align-items:center;justify-content:center;text-align:center;padding:9%;margin:0;border:2.5px solid #1a1c1c;background:var(--tint,#f6f4ee);color:#1a1c1c;font:700 15px/1.2 inherit;font-family:inherit;cursor:pointer;border-radius:52% 48% 47% 53%/56% 44% 56% 44%;box-shadow:0 6px 18px -8px rgba(0,0,0,.25);transition:left .6s cubic-bezier(.34,1.45,.64,1),top .6s cubic-bezier(.34,1.45,.64,1),transform .5s cubic-bezier(.34,1.5,.64,1),opacity .35s,width .45s cubic-bezier(.2,.8,.2,1),margin .5s ease,background .3s,color .3s;}
.bubble__icon{width:24px;height:24px;flex:none;opacity:.85;}
.bubble.is-centre .bubble__icon{width:30px;height:30px;}
.bubble:nth-child(odd){border-radius:47% 53% 55% 45%/44% 58% 42% 56%;}
.bubble:hover,.bubble:focus-visible{transform:translate(-50%,-50%) scale(calc(var(--s,1) * 1.06));outline:none;}
.bubble:focus-visible{box-shadow:0 0 0 4px #fff,0 0 0 6.5px #1a1c1c;}
.bubble[hidden]{display:none;}
.bubble.is-centre{--w:30%;font-size:18px;box-shadow:0 10px 26px -10px rgba(0,0,0,.35);}
.bubble.is-dim{opacity:.35;}
.bubble.is-on{background:#1a1c1c;color:#fff;}
.nav-stage.is-idle .bubble{animation:nav-drift 8s ease-in-out infinite alternate;}
.nav-stage.is-idle .bubble:nth-child(2){animation-duration:9.5s;animation-delay:-3s;}
.nav-stage.is-idle .bubble:nth-child(3){animation-duration:7s;animation-delay:-5s;}
.nav-stage.is-idle .bubble:nth-child(4){animation-duration:10s;animation-delay:-2s;}
.nav-stage.is-idle .bubble:nth-child(5){animation-duration:8.5s;animation-delay:-6.5s;}
.nav-stage.is-idle .bubble:nth-child(6){animation-duration:7.5s;animation-delay:-1s;}
@keyframes nav-drift{0%{margin:0 0 0 0}30%{margin:-7px 0 0 5px}60%{margin:5px 0 0 -6px}100%{margin:-4px 0 0 -7px}}
.nav-crumb{display:none;flex-wrap:wrap;gap:8px;justify-content:center;}
.nav-crumb button{font:600 14px/1 inherit;font-family:inherit;padding:8px 14px;border-radius:999px;border:1.5px solid #e8e6df;background:#fff;color:#1a1c1c;cursor:pointer;}
.nav-crumb button:hover{border-color:#1a1c1c;}
.nav-crumb button[aria-current="true"]{background:#1a1c1c;color:#fff;border-color:#1a1c1c;}
.js .nav-list{display:none;}
.no-js .nav-stage,.no-js .nav-crumb,.no-js .nav-results{display:none;}
.nav-results[hidden]{display:none;}
@media (max-width:520px){.bubble{font-size:12px;line-height:1.15;padding:7%;gap:4px;}.bubble__icon{width:18px;height:18px;}.bubble.is-centre{font-size:14px;}.bubble.is-centre .bubble__icon{width:24px;height:24px;}}
@media (prefers-reduced-motion:reduce){.bubble,.nav-halo{transition:none;}.nav-stage.is-idle .bubble{animation:none;}}
</style>'''

SCRIPT = r'''<script>
(function(){
  var stage=document.getElementById('nav-stage'),halo=document.getElementById('nav-halo'),crumb=document.getElementById('nav-crumb'),results=document.getElementById('nav-results'),intro=document.getElementById('nav-intro');
  if(!stage)return;
  var TREE=JSON.parse(document.getElementById('nav-tree').textContent);
  var state={domain:null,aspect:null};
  var reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function bubble(id){return stage.querySelector('[data-bubble="'+id+'"]');}
  function place(el,x,y,w,s){el.style.setProperty('--x',x+'%');el.style.setProperty('--y',y+'%');if(w)el.style.setProperty('--w',w+'%');el.style.setProperty('--s',s==null?1:s);}
  function ring(n,r){var out=[];for(var i=0;i<n;i++){var a=-Math.PI/2+i*2*Math.PI/n;out.push([50+r*Math.cos(a),50+r*Math.sin(a)]);}return out;}
  // A ring grows out of the centre: each bubble starts there at size zero and springs to its place, one
  // after another. The motion is what says "these belong to the centre"; there are no lines to say it.
  function spawn(el,x,y,w,i){
    if(reduced||!el.hidden){el.hidden=false;place(el,x,y,w,1);return;}
    el.hidden=false;el.style.transition='none';place(el,50,50,w,0);void el.offsetWidth;
    el.style.transition='';el.style.transitionDelay=(i*70)+'ms';place(el,x,y,w,1);
    el.addEventListener('transitionend',function done(){el.style.transitionDelay='';el.removeEventListener('transitionend',done);});
  }
  function render(){
    var domains=TREE.map(function(d){return d.key;});
    stage.querySelectorAll('.bubble').forEach(function(b){b.classList.remove('is-centre','is-dim','is-on');b.setAttribute('aria-pressed','false');});
    if(!state.domain){
      stage.querySelectorAll('.bubble[data-bubble^="a:"]').forEach(function(b){b.hidden=true;});
      var small=window.innerWidth<520,pts=ring(domains.length,small?35:37);
      domains.forEach(function(k,i){var b=bubble('d:'+k);b.classList.remove('is-centre');spawn(b,pts[i][0],pts[i][1],small?28:24,i);});
      halo.classList.remove('is-on');stage.classList.add('is-idle');
      crumb.style.display='none';results.hidden=true;intro.hidden=false;
    }else{
      stage.classList.remove('is-idle');
      var d=TREE.filter(function(x){return x.key===state.domain;})[0],c=bubble('d:'+d.key);
      stage.querySelectorAll('.bubble').forEach(function(b){var id=b.getAttribute('data-bubble');if(id!=='d:'+d.key&&id.indexOf('a:'+d.key+':')!==0)b.hidden=true;});
      c.hidden=false;c.classList.add('is-centre');c.setAttribute('aria-pressed','true');place(c,50,50,30,1);
      halo.style.setProperty('--tint',c.style.getPropertyValue('--tint'));halo.classList.add('is-on');
      var small=window.innerWidth<520,pts=ring(4,small?34:36);
      d.aspects.forEach(function(a,i){var b=bubble('a:'+d.key+':'+a.key);spawn(b,pts[i][0],pts[i][1],small?31:27,i);
        if(state.aspect){if(a.key===state.aspect){b.classList.add('is-on');b.setAttribute('aria-pressed','true');}else b.classList.add('is-dim');}});
      crumb.style.display='flex';crumb.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-current',String(x.getAttribute('data-domain')===d.key));});
      intro.hidden=true;
      results.querySelectorAll('[data-panel]').forEach(function(p){p.hidden=p.getAttribute('data-panel')!==(state.aspect?d.key+':'+state.aspect:'');});
      results.hidden=!state.aspect;
    }
  }
  stage.addEventListener('click',function(e){var b=e.target.closest('.bubble');if(!b)return;var id=b.getAttribute('data-bubble').split(':');
    if(id[0]==='d'){state=(state.domain===id[1])?{domain:null,aspect:null}:{domain:id[1],aspect:null};}
    else{state.aspect=(state.aspect===id[2])?null:id[2];}
    render();if(state.aspect&&window.innerWidth<768){setTimeout(function(){results.scrollIntoView({behavior:'smooth',block:'start'});},300);}});
  crumb.addEventListener('click',function(e){var x=e.target.closest('button');if(!x)return;var k=x.getAttribute('data-domain');state=k?{domain:k,aspect:null}:{domain:null,aspect:null};render();});
  render();
})();
</script>'''


def who_card(cid, why):
    """One clinician under an aspect: portrait, name, role and place, and the declared reason.

    Built here rather than from profiles.also_link. The reason chip has to sit in the same text column as
    the name, which also_link has no slot for; the portrait has to be top-aligned so every row in the grid
    starts on one line; and a clinician appears under many aspects, so the portrait cannot carry
    also_link's id and view-transition-name without repeating both a dozen times on one page.
    """
    c = BY_ID[cid]
    portrait = (f'<span class="block w-[72px] shrink-0 self-start {profiles.PORTRAIT_BOX}">'
                + profiles.picture(c, profiles.portrait_size(c), '72px', 'loading="lazy" decoding="async"',
                                   'w-full h-full object-cover object-[center_30%]') + '</span>')
    return (f'<li class="h-full"><a class="group flex h-full gap-4 min-w-0" href="{c["slug"]}.html">{portrait}'
            f'<span class="min-w-0 flex-1 flex flex-col">'
            f'<strong class="block text-[17px] leading-[1.3] font-extrabold tracking-tight text-[#1a1c1c] '
            f'group-hover:underline decoration-[#f1bc31] decoration-2 underline-offset-4">{esc(c["name"])}</strong>'
            f'<span class="block mt-1 text-[14px] leading-[1.35] font-semibold text-[#5f5e59]">{esc(profiles.subline(c))}</span>'
            f'<span class="block mt-auto pt-2.5"><span class="inline-block px-2.5 py-1 rounded-full text-[12px] '
            f'leading-[1.35] font-semibold text-[#5f5e59] bg-[#f6f4ee] border border-[#e8e6df]">{esc(why)}</span></span>'
            f'</span></a></li>')


def build():
    shell = SHELL.read_text(encoding='utf-8')
    head = head_for(shell[:shell.index('<body')])
    header = header_for(shell[shell.index('<body'):shell.index('<main')])
    footer = shell[shell.index('<footer'):]
    footer = footer.replace('<script src="analytics-config.js" defer></script>', SCRIPT + '\n<script src="analytics-config.js" defer></script>', 1)

    bubbles, crumbs, panels, listing = [], ['<button type="button" data-domain="">Start again</button>'], [], []
    for d in DOMAINS:
        bubbles.append(f'<button type="button" class="bubble" data-bubble="d:{d["key"]}" style="--tint:{d["tint"]}" aria-pressed="false" hidden>{icon(d["key"])}<span>{esc(d["label"])}</span></button>')
        crumbs.append(f'<button type="button" data-domain="{d["key"]}">{esc(d["label"])}</button>')
        items = []
        for asp in d['aspects']:
            bubbles.append(f'<button type="button" class="bubble" data-bubble="a:{d["key"]}:{asp["key"]}" style="--tint:{d["tint"]}" aria-pressed="false" hidden>{icon(f"{d['key']}:{asp['key']}")}<span>{esc(asp["label"])}</span></button>')
            cards = ''.join(who_card(cid, why) for cid, why in asp['who'])
            panels.append(f'<div data-panel="{d["key"]}:{asp["key"]}" hidden><h2 class="text-[24px] font-extrabold tracking-tight text-[#1a1c1c]">{esc(d["label"])} <span aria-hidden="true">›</span> {esc(asp["label"])}</h2>'
                          f'<p class="mt-2 text-[15px] text-[#5f5e59]">Clinicians whose profiles say they work on this. The reason is in their own words.</p>'
                          f'<ul class="mt-6 grid grid-cols-1 md:grid-cols-2 auto-rows-fr gap-8 list-none p-0 m-0">{cards}</ul></div>')
            items.append(f'<li class="py-4"><h3 class="text-[17px] font-bold text-[#1a1c1c]">{esc(asp["label"])}</h3><ul class="mt-4 grid grid-cols-1 md:grid-cols-2 auto-rows-fr gap-8 list-none p-0 m-0">{cards}</ul></li>')
        listing.append(f'<section class="pt-10 border-t border-[#e8e6df]"><h2 class="text-[24px] font-extrabold tracking-tight text-[#1a1c1c]">{esc(d["label"])}</h2><ul class="list-none p-0 m-0 divide-y divide-[#e8e6df]">{"".join(items)}</ul></section>')

    tree = [dict(key=d['key'], aspects=[dict(key=a['key']) for a in d['aspects']]) for d in DOMAINS]
    url = f'{SITE}/{SLUG}.html'
    ld = {'@context': 'https://schema.org', '@type': 'WebPage', '@id': url, 'url': url, 'name': SEO, 'description': DESCRIPTION, 'inLanguage': 'en-AU'}
    return f'''{head}{header}<main id="main" class="w-full bg-[#FAFAF7]">
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pt-10 pb-6 text-center">
<h1 class="hero-in text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-[#1a1c1c] max-w-[18ch] mx-auto">Where does ADHD get in the way?</h1>
<p id="nav-intro" class="hero-in hero-in-2 mt-5 text-[19px] leading-[1.6] text-[#5f5e59] max-w-[52ch] mx-auto">Choose a pressure point you’d like support with, then select the area of life it relates to. We’ll help you find clinicians who understand what you’re navigating.</p>
<div id="nav-crumb" class="nav-crumb mt-6" aria-label="Change domain">{''.join(crumbs)}</div>
</div>
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pb-10">
<div id="nav-stage" class="nav-stage hero-in hero-in-3" role="group" aria-label="Care navigator"><div id="nav-halo" class="nav-halo" aria-hidden="true"></div>{''.join(bubbles)}</div>
<section id="nav-results" class="nav-results max-w-[900px] mx-auto pt-10 border-t border-[#e8e6df]" aria-live="polite" hidden>{''.join(panels)}
<p class="mt-10"><a class="btn-press inline-flex items-center gap-2 h-12 px-7 rounded-full bg-[#1a1c1c] text-white text-[15px] font-bold hover:bg-[#2f3130] transition-all shadow-[0_4px_16px_rgba(0,0,0,0.15)] hover:-translate-y-0.5" href="the-doctors.html">See the whole network <span class="text-[#f1bc31]" aria-hidden="true">→</span></a></p>
</section>
<div class="nav-list max-w-[900px] mx-auto">{''.join(listing)}</div>
</div>
</main>
<script id="nav-tree" type="application/json">{json.dumps(tree, separators=(',', ':'))}</script>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{footer}'''


def main(argv):
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
