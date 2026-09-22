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
  dict(key='focus', label='Focus in class', who=[
   ('fiona-alexander', 'Executive functioning · Students & families'),
   ('romney-taylor', 'Executive functioning · Students'),
   ('debbie-hirte', 'Executive functioning · Children & teens'),
   ('flynn-simonis', 'Paediatric OT · Home & school visits')]),
  dict(key='homework', label='Homework and deadlines', who=[
   ('fiona-alexander', 'Executive functioning · Able & gifted learners'),
   ('erin-lysle', 'Executive functioning · Self-confidence'),
   ('romney-taylor', 'Executive functioning · Students'),
   ('debbie-hirte', 'Executive functioning · Gifted & talented')]),
  dict(key='friends', label='Friendships', who=[
   ('erin-lysle', 'Social skills · Self-confidence'),
   ('flynn-simonis', 'Group social and movement programs for children'),
   ('ellie-putland', 'Young people · Trauma-informed')]),
  dict(key='system', label='Getting the school on side', who=[
   ('debbie-hirte', 'Co-designing Individual Education Plans with families and schools'),
   ('meera-lakhani', 'Educational & developmental · Previously a psychologist in a school'),
   ('flynn-simonis', 'FCA report writing · Home & school visits'),
   ('lachlan-avent', 'Autism & ADHD assessment · Children to adults')]),
 ]),
 dict(key='work', label='Work', tint='#cfe4f6', aspects=[
  dict(key='done', label='Getting things done', who=[
   ('fiona-alexander', 'Executive functioning'),
   ('kate-dallimore', 'Executive functioning · Trauma-informed'),
   ('donna-italiano', 'Executive functioning · Emotional regulation'),
   ('romney-taylor', 'Executive functioning · Advocacy & inclusion')]),
  dict(key='burnout', label='Stress and burnout', who=[
   ('jessica-katsamatsas', 'Anxiety, burnout, low self-esteem'),
   ('kate-dallimore', 'Ongoing stress, anxiety, overwhelm'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed')]),
  dict(key='confidence', label='Confidence and feedback', who=[
   ('erin-lysle', 'Self-confidence'),
   ('jessica-katsamatsas', 'Low self-esteem · Neurodivergent adults'),
   ('donna-italiano', 'Emotional regulation · Neurodivergent-affirming')]),
  dict(key='career', label='Career and what next', who=[
   ('kate-row', 'Career counselling and post-schooling decision making'),
   ('romney-taylor', 'Advocacy & inclusion'),
   ('kate-dallimore', 'Mentoring and leadership across healthcare and education')]),
 ]),
 dict(key='home', label='Home', tint='#dbe9d3', aspects=[
  dict(key='routines', label='Routines and the daily grind', who=[
   ('donna-italiano', 'Executive functioning · Emotional regulation'),
   ('kate-dallimore', 'Executive functioning'),
   ('flynn-simonis', 'Sensory profiles and functional challenges, in clinic and at home')]),
  dict(key='parenting', label='Parenting a child with ADHD', who=[
   ('lachlan-avent', 'Triple P Stepping Stones parenting practitioner'),
   ('lauren-poulos', 'PCIT & early intervention · Toddlers & children'),
   ('flynn-simonis', 'Paediatric OT · Parent training'),
   ('debbie-hirte', 'Children & teens')]),
  dict(key='emotions', label='Big feelings at home', who=[
   ('donna-italiano', 'Emotional regulation'),
   ('ellie-putland', 'Young people · CBT, ACT & DBT'),
   ('flynn-simonis', 'Emotional regulation needs in children')]),
  dict(key='body', label='Sleep, food and the body', who=[
   ('anubhav-saxena', 'Baseline physical screening · Integrative care'),
   ('samantha-courtney', 'Eating disorders · CEDC-MH credentialed'),
   ('anu-saxena', 'Mental health focus · Women’s health')]),
 ]),
 dict(key='relationships', label='Relationships', tint='#fbd8cf', aspects=[
  dict(key='partner', label='Partner and family', who=[
   ('jessica-katsamatsas', 'Relationship difficulties and attachment wounds'),
   ('kate-row', 'Communication and social skills building'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed')]),
  dict(key='rejection', label='Rejection and sensitivity', who=[
   ('jessica-katsamatsas', 'Attachment wounds · Low self-esteem'),
   ('donna-italiano', 'Emotional regulation'),
   ('paula-garrido', 'ADHD & autism certified · Trauma-informed')]),
  dict(key='social', label='Making and keeping friends', who=[
   ('erin-lysle', 'Social skills'),
   ('kate-row', 'Social skills building'),
   ('flynn-simonis', 'Group social programs for children')]),
  dict(key='conflict', label='Conflict and repair', who=[
   ('kate-row', 'Communication skills · CBT, ACT & MI'),
   ('ellie-putland', 'DBT · Working collaboratively with families'),
   ('lachlan-avent', 'Emotion Focussed Therapy')]),
 ]),
 dict(key='health', label='Health', tint='#dad9eb', aspects=[
  dict(key='assessment', label='Getting assessed', who=[
   ('anubhav-saxena', 'Structured adult ADHD assessment'),
   ('anu-saxena', 'Endorsed ADHD prescriber course'),
   ('lachlan-avent', 'Autism & ADHD assessment'),
   ('meera-lakhani', 'Autism & ADHD assessment · Cognitive assessment')]),
  dict(key='medication', label='Medication and the body', who=[
   ('anubhav-saxena', 'Baseline cardiovascular and metabolic screening'),
   ('anu-saxena', 'Mental health focus · Endorsed ADHD prescriber course')]),
  dict(key='mood', label='Anxiety and low mood', who=[
   ('jessica-katsamatsas', 'Anxiety, burnout, low self-esteem'),
   ('paula-garrido', 'Neuroaffirming · Trauma-informed'),
   ('ellie-putland', 'Trauma-informed · CBT, ACT & DBT'),
   ('alice-bui', 'Trauma-informed · CALD & refugee clients')]),
  dict(key='eating', label='Eating and appetite', who=[
   ('samantha-courtney', 'Eating disorders · CEDC-MH credentialed'),
   ('anubhav-saxena', 'Baseline physical screening')]),
 ]),
]

for d in DOMAINS:
    assert len(d['aspects']) == 4, f"{d['label']}: four aspects, not {len(d['aspects'])}"
    for asp in d['aspects']:
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
    active = ('aria-current="page" class="whitespace-nowrap px-3.5 lg:px-5 py-2 rounded-full text-[15px] font-semibold '
              'bg-[#1a1c1c] text-white shadow-sm transition-all" href="how-it-works.html"')
    inactive = ('class="whitespace-nowrap px-3.5 lg:px-5 py-2 rounded-full text-[15px] font-semibold text-[#1a1c1c]/80 '
                'hover:text-[#1a1c1c] hover:bg-black/5 transition-all" href="how-it-works.html"')
    if shell_header.count(active) != 1 or shell_header.count('<a aria-current="page" href="how-it-works.html">') != 1:
        raise SystemExit('build-navigator: how-it-works.html header does not mark How it works current where expected')
    return shell_header.replace(active, inactive).replace('<a aria-current="page" href="how-it-works.html">', '<a href="how-it-works.html">')


# ---------------------------------------------------------------- the map
# Bubbles are buttons positioned by the script on a square stage; the ink lines between them are one SVG
# underneath, redrawn on each change with a small, seeded wobble so they read as hand-drawn, like the map
# on Our Story. Colours are the domain tints. With JavaScript off the stage is hidden and the list shows.
STYLE = '''<style>
.nav-stage{position:relative;aspect-ratio:1/1;max-width:640px;margin:0 auto;}
.nav-lines{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible;}
.nav-lines path{fill:none;stroke:#1a1c1c;stroke-width:2.2;stroke-linecap:round;opacity:.55;}
.bubble{position:absolute;left:var(--x);top:var(--y);transform:translate(-50%,-50%) scale(var(--s,1));width:var(--w,22%);aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;text-align:center;padding:8%;margin:0;border:2.5px solid #1a1c1c;background:var(--tint,#f6f4ee);color:#1a1c1c;font:700 15px/1.2 inherit;font-family:inherit;cursor:pointer;border-radius:52% 48% 47% 53%/56% 44% 56% 44%;box-shadow:0 6px 18px -8px rgba(0,0,0,.25);transition:left .55s cubic-bezier(.2,.8,.2,1),top .55s cubic-bezier(.2,.8,.2,1),transform .45s cubic-bezier(.2,.8,.2,1),opacity .35s,width .45s cubic-bezier(.2,.8,.2,1);}
.bubble:nth-child(odd){border-radius:47% 53% 55% 45%/44% 58% 42% 56%;}
.bubble:hover,.bubble:focus-visible{transform:translate(-50%,-50%) scale(calc(var(--s,1) * 1.06));outline:none;}
.bubble:focus-visible{box-shadow:0 0 0 4px #fff,0 0 0 6.5px #1a1c1c;}
.bubble[hidden]{display:none;}
.bubble.is-centre{--w:30%;font-size:18px;box-shadow:0 10px 26px -10px rgba(0,0,0,.35);}
.bubble.is-dim{opacity:.35;}
.bubble.is-on{background:#1a1c1c;color:#fff;}
.nav-crumb{display:none;flex-wrap:wrap;gap:8px;justify-content:center;}
.nav-crumb button{font:600 14px/1 inherit;font-family:inherit;padding:8px 14px;border-radius:999px;border:1.5px solid #e8e6df;background:#fff;color:#1a1c1c;cursor:pointer;}
.nav-crumb button:hover{border-color:#1a1c1c;}
.nav-crumb button[aria-current="true"]{background:#1a1c1c;color:#fff;border-color:#1a1c1c;}
.js .nav-list{display:none;}
.no-js .nav-stage,.no-js .nav-crumb,.no-js .nav-results{display:none;}
.nav-results[hidden]{display:none;}
@media (max-width:520px){.bubble{font-size:13px;padding:6%;}.bubble.is-centre{font-size:15px;}}
@media (prefers-reduced-motion:reduce){.bubble{transition:none;}}
</style>'''

SCRIPT = r'''<script>
(function(){
  var stage=document.getElementById('nav-stage'),lines=document.getElementById('nav-lines'),crumb=document.getElementById('nav-crumb'),results=document.getElementById('nav-results'),intro=document.getElementById('nav-intro');
  if(!stage)return;
  var TREE=JSON.parse(document.getElementById('nav-tree').textContent);
  var state={domain:null,aspect:null};
  function bubble(id){return stage.querySelector('[data-bubble="'+id+'"]');}
  function place(el,x,y,w,s){el.style.setProperty('--x',x+'%');el.style.setProperty('--y',y+'%');if(w)el.style.setProperty('--w',w+'%');el.style.setProperty('--s',s||1);}
  function ring(n,r){var out=[];for(var i=0;i<n;i++){var a=-Math.PI/2+i*2*Math.PI/n;out.push([50+r*Math.cos(a),50+r*Math.sin(a)]);}return out;}
  // A slightly wobbly ink line from the centre to each bubble, seeded by index so it never jitters.
  function line(x1,y1,x2,y2,seed){var mx=(x1+x2)/2,my=(y1+y2)/2,dx=x2-x1,dy=y2-y1,len=Math.sqrt(dx*dx+dy*dy)||1,k=(((seed*7919)%13)-6)/6*Math.min(4,len/6);return 'M'+x1+' '+y1+' Q'+(mx-dy/len*k)+' '+(my+dx/len*k)+' '+x2+' '+y2;}
  function draw(pts,dot){lines.innerHTML=(dot?'<circle cx="50" cy="50" r="1.6" fill="#1a1c1c"/>':'')+pts.map(function(p,i){var vis=[50,50,p[0],p[1]];var d=vis[2]-vis[0],e=vis[3]-vis[1],l=Math.sqrt(d*d+e*e)||1;return '<path d="'+line(50+d/l*15,50+e/l*15,p[0]-d/l*11,p[1]-e/l*11,i+1)+'"/>';}).join('');}
  function render(){
    var domains=TREE.map(function(d){return d.key;});
    stage.querySelectorAll('.bubble').forEach(function(b){b.hidden=true;b.classList.remove('is-centre','is-dim','is-on');b.setAttribute('aria-pressed','false');});
    if(!state.domain){
      var pts=ring(domains.length,37);
      domains.forEach(function(k,i){var b=bubble('d:'+k);b.hidden=false;place(b,pts[i][0],pts[i][1],24,1);});
      draw(pts,true);crumb.style.display='none';results.hidden=true;intro.hidden=false;
    }else{
      var d=TREE.filter(function(x){return x.key===state.domain;})[0],c=bubble('d:'+d.key);
      c.hidden=false;c.classList.add('is-centre');c.setAttribute('aria-pressed','true');place(c,50,50,30,1);
      var pts=ring(4,36);
      d.aspects.forEach(function(a,i){var b=bubble('a:'+d.key+':'+a.key);b.hidden=false;place(b,pts[i][0],pts[i][1],26,1);
        if(state.aspect){if(a.key===state.aspect){b.classList.add('is-on');b.setAttribute('aria-pressed','true');}else b.classList.add('is-dim');}});
      draw(pts);
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
    c = BY_ID[cid]
    return (f'<li class="flex flex-col gap-2">{profiles.also_link(c, profiles.portrait_size(c))}'
            f'<span class="ml-[116px] inline-flex self-start px-3 py-1 rounded-full text-[13px] font-semibold text-[#1a1c1c] bg-[#f6f4ee] border border-[#e8e6df]">{esc(why)}</span></li>')


def build():
    shell = SHELL.read_text(encoding='utf-8')
    head = head_for(shell[:shell.index('<body')])
    header = header_for(shell[shell.index('<body'):shell.index('<main')])
    footer = shell[shell.index('<footer'):]
    footer = footer.replace('<script src="analytics-config.js" defer></script>', SCRIPT + '\n<script src="analytics-config.js" defer></script>', 1)

    bubbles, crumbs, panels, listing = [], ['<button type="button" data-domain="">Start again</button>'], [], []
    for d in DOMAINS:
        bubbles.append(f'<button type="button" class="bubble" data-bubble="d:{d["key"]}" style="--tint:{d["tint"]}" aria-pressed="false" hidden>{esc(d["label"])}</button>')
        crumbs.append(f'<button type="button" data-domain="{d["key"]}">{esc(d["label"])}</button>')
        items = []
        for asp in d['aspects']:
            bubbles.append(f'<button type="button" class="bubble" data-bubble="a:{d["key"]}:{asp["key"]}" style="--tint:{d["tint"]}" aria-pressed="false" hidden>{esc(asp["label"])}</button>')
            cards = ''.join(who_card(cid, why) for cid, why in asp['who'])
            panels.append(f'<div data-panel="{d["key"]}:{asp["key"]}" hidden><h2 class="text-[24px] font-extrabold tracking-tight text-[#1a1c1c]">{esc(d["label"])} <span aria-hidden="true">›</span> {esc(asp["label"])}</h2>'
                          f'<p class="mt-2 text-[15px] text-[#5f5e59]">Clinicians whose profiles say they work on this. The reason is in their own words.</p>'
                          f'<ul class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-8 list-none p-0 m-0">{cards}</ul></div>')
            items.append(f'<li class="py-4"><h3 class="text-[17px] font-bold text-[#1a1c1c]">{esc(asp["label"])}</h3><ul class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6 list-none p-0 m-0">{cards}</ul></li>')
        listing.append(f'<section class="pt-10 border-t border-[#e8e6df]"><h2 class="text-[24px] font-extrabold tracking-tight text-[#1a1c1c]">{esc(d["label"])}</h2><ul class="list-none p-0 m-0 divide-y divide-[#e8e6df]">{"".join(items)}</ul></section>')

    tree = [dict(key=d['key'], aspects=[dict(key=a['key']) for a in d['aspects']]) for d in DOMAINS]
    url = f'{SITE}/{SLUG}.html'
    ld = {'@context': 'https://schema.org', '@type': 'WebPage', '@id': url, 'url': url, 'name': SEO, 'description': DESCRIPTION, 'inLanguage': 'en-AU'}
    return f'''{head}{header}<main id="main" class="w-full bg-[#FAFAF7]">
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pt-10 pb-6 text-center">
<h1 class="hero-in text-[36px] sm:text-[44px] lg:text-[52px] leading-[1.05] font-extrabold tracking-tight text-[#1a1c1c] max-w-[18ch] mx-auto">Where does ADHD get in the way?</h1>
<p id="nav-intro" class="hero-in hero-in-2 mt-5 text-[19px] leading-[1.6] text-[#5f5e59] max-w-[52ch] mx-auto">Pick a place, then the part of it. The clinicians whose profiles say they work on exactly that appear underneath.</p>
<div id="nav-crumb" class="nav-crumb mt-6" aria-label="Change domain">{''.join(crumbs)}</div>
</div>
<div class="max-w-[1200px] mx-auto w-full px-5 md:px-8 lg:px-12 pb-10">
<div id="nav-stage" class="nav-stage hero-in hero-in-3" role="group" aria-label="Care navigator"><svg id="nav-lines" class="nav-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"></svg>{''.join(bubbles)}</div>
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
