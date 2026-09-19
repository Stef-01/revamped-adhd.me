#!/usr/bin/env python3
"""Inject the discipline tracks into academy.html (idempotent).
Edit scripts/academy_tracks_content.py, then run: python3 scripts/build-academy-tracks.py"""
import html, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from academy_tracks_content import TRACKS
from sketchy_scenes import SCENES, SHARED

LESSON_MIN = 2   # minutes per lesson
CHECK_MIN = 1    # minutes per knowledge check
LEARN_CAP, TOTAL_CAP = 6, 10
def e(s): return html.escape(s, quote=False)
def ic(name, cls=''): return f'<iconify-icon icon="{name}"' + (f' class="{cls}"' if cls else '') + '></iconify-icon>'

def question(qid, stem, opts, ans, fb):
    lis = ''.join(f'<li class="q__opt" data-opt="{k}"><label><input type="radio" name="{qid}" value="{k}" data-k="{qid}"><span class="q__k">{k}</span><span>{e(o)}</span></label></li>' for k, o in zip('ABCD', opts))
    return (f'<div class="q" id="{qid}" data-a="{ans}" data-mode="instant"><p class="q__kick">{ic("ph:check-square-duotone")}Knowledge check</p>'
            f'<p class="q__stem">{e(stem)}</p><ul class="q__opts">{lis}</ul><p class="q__fb"><b>Answer {ans}.</b> {e(fb)}</p></div>')

def lesson(tk, li, L):
    title, paras, keys, stem, opts, ans, fb = L
    slug = tk.replace('-', '')
    return (f'<div class="lesson" id="{slug}l{li}"><h3 class="lesson__h"><span class="lesson__num">{li}</span>{e(title)}'
            f'<span class="lesson__min">{ic("ph:clock-duotone")}{LESSON_MIN} min</span></h3>'
            f'<div class="prose">{"".join(f"<p>{e(p)}</p>" for p in paras)}</div>'
            f'<div class="box box--key"><p class="box__t">{ic("ph:hash-duotone", "box__i")}What to hold on to</p><ul>{"".join(f"<li>{e(k)}</li>" for k in keys)}</ul></div>'
            + question(f'{tk}-chk{li}', stem, opts, ans, fb) + '</div>')

def budget(t):
    scene = SCENES[t['key']]['minutes'] if t['key'] in SCENES else 0
    learn = scene + LESSON_MIN * len(t['lessons'])
    checks = CHECK_MIN * (len(t['lessons']) + len(t['final']))
    assert learn <= LEARN_CAP, (t['title'], 'learning minutes', learn)
    assert learn + checks <= TOTAL_CAP, (t['title'], 'total minutes', learn + checks)
    return learn, checks


# ------------------------------------------------------------------ Sketchy-method layer
def sk_defs():
    """Every symbol is defined ONCE here and <use>d by the scenes and the explorers."""
    out = ['<svg class="sk-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs>',
           '<!-- SHARED VOCABULARY: recurs in every discipline scene. Replace art here; ids must not change. -->']
    for sid, (title, art) in SHARED.items():
        out.append(f'<!-- SYMBOL: {title} -->\n<symbol id="{sid}" viewBox="0 0 100 100">{art}</symbol>')
    for key, sc in SCENES.items():
        out.append(f'<!-- SCENE {key}: {sc["world"]} -->')
        for sy in sc['symbols']:
            if sy['shared']: continue
            out.append(f'<!-- SYMBOL: {sy["encodes"]} -->\n<symbol id="sk-{sy["id"]}" viewBox="0 0 100 100">{sy["art"]}</symbol>')
    out.append('</defs></svg>')
    return '\n'.join(out)

def sk_scene(key, track_title):
    sc = SCENES[key]; b1, b2, ink, acc = sc['palette']; n = len(sc['symbols'])
    style = f'--sk-b1:{b1};--sk-b2:{b2};--sk-ink:{ink};--sk-accent:{acc}'
    groups = []
    for i, sy in enumerate(sc['symbols'], 1):
        ref = sy['shared'] or f'sk-{sy["id"]}'; z = sy['size']
        badge = (f'<use href="#{sy["badge"]}" x="{z*0.60:.0f}" y="{-z*0.10:.0f}" width="{z*0.42:.0f}" height="{z*0.42:.0f}"/>' if sy['badge'] else '')
        label = e(f'{sy["title"]}. {sy["encodes"]}' + (f' {SHARED[sy["badge"]][0]}.' if sy['badge'] else ''))
        groups.append(f'<!-- SYMBOL: {sy["encodes"]} -->\n<g class="sk__sym" data-step="{i}" tabindex="-1" role="button" aria-label="{label}" '
                      f'data-title="{e(sy["title"])}" data-recap="{e(sy["recap"])}" data-cues="{e("; ".join(sy["cues"]))}" data-lesson="{e(sy["lesson"])}" transform="translate({sy["x"]} {sy["y"]})">'
                      f'<g class="sk__pop"><rect class="sk__ring" x="-6" y="-6" width="{z+12}" height="{z+12}" rx="14"/><use href="#{ref}" width="{z}" height="{z}"/>{badge}'
                      f'<circle class="sk__nbg" cx="4" cy="4" r="12"/><text class="sk__n" x="4" y="9" text-anchor="middle">{i}</text></g></g>')
    used = ['sk-stamp-strong', 'sk-stamp-weak', 'sk-shield-high', 'sk-shield-mod', 'sk-shield-low', 'sk-shield-vlow', 'sk-myth', 'sk-signpost']
    legend = ''.join(f'<span><svg viewBox="0 0 100 100" aria-hidden="true"><use href="#{u}"/></svg>{e(SHARED[u][0])}</span>' for u in used)
    scene = (f'<figure class="sk" id="sk-{key}" style="{style}" data-world="{e(sc["world"])}" data-desc="{e(sc["desc"])}">'
             f'<div class="sk__head"><div><span class="sk__kick">Visual map of this track</span><h3 class="sk__title">{e(sc["world"])}</h3></div>'
             f'<span class="lesson__min">{ic("ph:clock-duotone")}{sc["minutes"]} min</span></div>'
             f'<div class="sk__stage"><svg class="sk__svg" viewBox="0 0 800 450" role="group" aria-labelledby="sk-{key}-t sk-{key}-d">'
             f'<title id="sk-{key}-t">{e(sc["world"])}: a visual map of the {e(track_title)} track</title><desc id="sk-{key}-d">{e(sc["desc"])} It holds {n} symbols, each encoding one point from the lessons.</desc>'
             f'<!-- WORLD BACKDROP: {sc["world"]}. Placeholder geometry; replace with final scene art at the same 800x450 size. -->\n<g aria-hidden="true">{sc["backdrop"]}</g>\n'
             + '\n'.join(groups) + '</svg></div>'
             '<div class="sk__cap" data-sk-cap="" aria-live="polite"></div>'
             '<div class="sk__bar"><span class="sk__count" data-sk-count=""></span>'
             '<button type="button" class="btn btn--ghost" data-sk-prev="">Back</button>'
             '<button type="button" class="btn" data-sk-next="">Start the scene <span aria-hidden="true">→</span></button>'
             '<button type="button" class="btn btn--ghost" data-sk-all="">Show the whole scene</button>'
             '<label class="sk__still"><input type="checkbox" data-sk-motion="">Reduce motion: show the finished scene</label></div>'
             f'<div class="sk__legend" aria-label="Symbols that mean the same thing in every track">{legend}</div>'
             '<p class="sk__note">Stamps and shields summarise how this track describes the evidence. Confirm each against the tables in the Australian ADHD guideline before relying on it.</p></figure>')
    cards = []
    for i, sy in enumerate(sc['symbols'], 1):
        ref = sy['shared'] or f'sk-{sy["id"]}'
        badge = (f'<svg class="skx__badge" viewBox="0 0 100 100" aria-hidden="true"><use href="#{sy["badge"]}"/></svg>' if sy['badge'] else '')
        extra = f' {SHARED[sy["badge"]][0]}.' if sy['badge'] else ''
        cards.append(f'<button type="button" class="skx__b" aria-expanded="false">{badge}<svg class="skx__art" viewBox="0 0 100 100" role="img" aria-label="{e(sy["encodes"])}"><use href="#{ref}"/></svg>'
                     f'<span class="skx__t">{i}. {e(sy["title"])}</span><span class="skx__r">{e(sy["recap"])}{e(extra)}</span></button>')
    explorer = (f'<div class="skx" style="{style}"><h2 class="h2">{ic("ph:squares-four-duotone", "h2__i")}Symbol explorer</h2>'
                '<p class="prose">The same symbols, out of the scene. Before you open one, try to recall what it stands for; then tap, hover or focus it to check.</p>'
                f'<div class="skx__grid">{"".join(cards)}</div></div>')
    return scene + explorer + '\n<!-- QUIZ INTEGRATION POINT: the existing lessons and their .q knowledge checks follow, unchanged. -->\n'

def branch(t):
    learn, checks = budget(t)
    n_checks = len(t['lessons']) + len(t['final'])
    finals = ''.join(question(f'{t["key"]}-fin{i}', *c) for i, c in enumerate(t['final'], 1))
    return (f'<div class="branch" data-branch="{t["key"]}" style="--mh:{t["hue"]}" hidden="">'
            f'<div class="branch__head">{ic(t["icon"], "branch__i")}<div><span class="kick">{t["label"]}</span><h3 class="branch__t">{e(t["title"])}</h3>'
            f'<p class="branch__d">{e(t["blurb"])} {learn + checks} minutes: {learn} of learning, {checks} of checks.</p></div></div>'
            f'<div class="box box--objectives"><p class="box__t">{ic("ph:target-duotone", "box__i")}Before you start</p><ul>{"".join(f"<li>{e(s)}</li>" for s in t["scope"])}</ul></div>'
            + (sk_scene(t['key'], t['title']) if t['key'] in SCENES else '')
            + f'<h2 class="h2">{ic("ph:book-open-text-duotone", "h2__i")}Lessons</h2>'
            + ''.join(lesson(t['key'], li, L) for li, L in enumerate(t['lessons'], 1))
            + f'<h2 class="h2">{ic("ph:check-square-duotone", "h2__i")}Check yourself</h2>' + finals
            + f'<div class="box box--refresh"><p class="box__t">{ic("ph:books-duotone", "box__i")}Sources</p><ul>{"".join(f"<li>{e(s)}</li>" for s in t["sources"])}</ul></div>'
            + '<p class="branch__next"><button type="button" class="btn btn--ghost" data-journey-back="">Choose another discipline</button></p></div>'), n_checks

def section():
    cards, branches = [], []
    for t in TRACKS:
        b, n = branch(t); branches.append(b)
        cards.append(f'<button type="button" class="journey__card" data-journey="{t["key"]}" style="--ph:{t["hue"]}" aria-pressed="false">{ic(t["icon"], "journey__i")}'
                     f'<span class="journey__n">{t["label"]}</span><span class="journey__t">{e(t["title"])}</span><span class="journey__d">{e(t["blurb"])}</span>'
                     f'<span class="journey__prog" data-jprog="{t["key"]}"><i style="width:0%"></i><b>0</b> of {n}</span></button>')
    return ('<!-- TRACKS -->\n<section class="sec" id="tracks">\n'
            f'  <h2 class="h2">{ic("ph:identification-card-duotone", "h2__i")}Training by discipline</h2>\n'
            '  <p class="prose">One ten-minute module for each discipline: six minutes of learning, four of knowledge checks that mark as you answer. Only the points you would act on. The eleven modules that follow are the full course and are open to everyone.</p>\n'
            f'  <div class="box box--refresh"><p class="box__t">{ic("ph:shield-warning-duotone", "box__i")}How to read these tracks</p>'
            '<p>These are practice-level summaries consistent with the Australian ADHD guideline. Where trial evidence is thin, the lesson says so. '
            'They do not replace your profession’s scope of practice, your registration standards or local prescribing law.</p></div>\n'
            '  ' + sk_defs() + '\n'
            '  <div class="journey" data-journey-root="tracks">\n'
            f'    <div class="journey__grid">{"".join(cards)}</div>\n  </div>\n'
            + '\n'.join(branches) + '\n</section>\n<!-- /TRACKS -->\n')

OLD_JS_START = "  /* ---------- module 11: choose your pathway ---------- */"
NEW_JS = r"""  /* ---------- pathway pickers: module 11, and training by discipline ----------
     Each [data-journey-root] owns the branches inside its own section, so two
     pickers on one page never hide each other's content. */
  [].slice.call(document.querySelectorAll('[data-journey-root]')).forEach(function (root) {
    var name = root.getAttribute('data-journey-root');
    var storeKey = name ? 'journey.' + name : 'journey';
    var scope = root.closest('section') || document;
    var cards = [].slice.call(root.querySelectorAll('[data-journey]'));
    var branches = [].slice.call(scope.querySelectorAll('.branch[data-branch]'));
    function show(key, scroll) {
      cards.forEach(function (c) { c.setAttribute('aria-pressed', c.getAttribute('data-journey') === key ? 'true' : 'false'); });
      branches.forEach(function (b) { if (b.getAttribute('data-branch') === key) b.removeAttribute('hidden'); else b.setAttribute('hidden', ''); });
      if (key) set(storeKey, key); else del(storeKey);
      if (scroll) { var b = scope.querySelector('.branch[data-branch="' + key + '"]'); if (b) window.scrollTo({ top: b.getBoundingClientRect().top + window.pageYOffset - 72, behavior: 'smooth' }); }
    }
    function progressAll() {
      branches.forEach(function (b) {
        var key = b.getAttribute('data-branch');
        var all = b.querySelectorAll('.q[data-mode="instant"]');
        var done = b.querySelectorAll('.q[data-mode="instant"][data-done]');
        var out = root.querySelector('[data-jprog="' + key + '"]');
        if (!out || !all.length) return;
        out.querySelector('b').textContent = done.length;
        out.lastChild.textContent = ' of ' + all.length;
        out.querySelector('i').style.setProperty('--pct', Math.round(done.length / all.length * 100) + '%');
        var card = root.querySelector('[data-journey="' + key + '"]');
        if (card) card.setAttribute('data-complete', done.length === all.length ? '1' : '0');
      });
    }
    cards.forEach(function (c) { c.addEventListener('click', function () { show(c.getAttribute('data-journey'), true); }); });
    scope.querySelectorAll('[data-journey-back]').forEach(function (b) {
      b.addEventListener('click', function () { window.scrollTo({ top: root.getBoundingClientRect().top + window.pageYOffset - 72, behavior: 'smooth' }); });
    });
    scope.addEventListener('change', function (ev) { if (ev.target.closest && ev.target.closest('.branch')) setTimeout(progressAll, 0); });
    var savedJ = get(storeKey);
    if (savedJ) show(savedJ, false);
    progressAll();
  });
"""

def main():
    p = ROOT / 'academy.html'; s = p.read_text()
    # 1. section
    if '<!-- TRACKS -->' in s:
        s = re.sub(r'<!-- TRACKS -->.*?<!-- /TRACKS -->\n', lambda m: section(), s, count=1, flags=re.S)
    else:
        anchor = '\n<section class="sec sec--module" id="m1"'
        assert anchor in s
        s = s.replace(anchor, '\n' + section() + anchor.lstrip('\n'), 1) if False else s.replace(anchor, '\n' + section().rstrip('\n') + anchor, 1)
    # 2. sidebar entry
    if 'href="#tracks"' not in s:
        nav_anchor = '<p class="nav__sec">Modules</p>'
        assert nav_anchor in s
        s = s.replace(nav_anchor, '<p class="nav__sec">By discipline</p><a class="nav__item" href="#tracks"><span class="nav__n"><iconify-icon icon="ph:identification-card-duotone"></iconify-icon></span><span class="nav__t">Training by discipline</span></a>' + nav_anchor, 1)
    # 3. script: one picker -> any number of pickers
    if OLD_JS_START in s:
        a = s.index(OLD_JS_START); b = s.index("  /* ---------- motion: reveal on scroll, reading bar ---------- */", a)
        s = s[:a] + NEW_JS + '\n\n' + s[b:]
    assert 'pathway pickers: module 11, and training by discipline' in s
    if 'assets/academy/sketchy.css' not in s:
        s = s.replace('<link rel="stylesheet" href="academy-skin.css">', '<link rel="stylesheet" href="academy-skin.css">\n<link rel="stylesheet" href="assets/academy/sketchy.css">', 1)
    if 'assets/academy/sketchy.js' not in s:
        s = s.replace('</body>', '<script src="assets/academy/sketchy.js" defer></script>\n</body>', 1)
    p.write_text(s)
    # 4. login page blurb
    lp = ROOT / 'academy-login.html'; l = lp.read_text()
    old = 'The ADHDme Clinical Academy: an eleven-module, self-directed clinician workbook.'
    if old in l:
        lp.write_text(l.replace(old, 'The ADHDme Clinical Academy: short training tracks by discipline, plus an eleven-module, self-directed clinician workbook.'))
    print('tracks:', len(TRACKS), '| academy.html bytes:', len(s))

if __name__ == '__main__':
    main()
