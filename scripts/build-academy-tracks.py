#!/usr/bin/env python3
"""Inject the discipline tracks into academy.html (idempotent).
Edit scripts/academy_tracks_content.py, then run: python3 scripts/build-academy-tracks.py"""
import html, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from academy_tracks_content import TRACKS

LESSON_MIN = 4
def e(s): return html.escape(s, quote=False)
def ic(name, cls=''): return f'<iconify-icon icon="{name}"' + (f' class="{cls}"' if cls else '') + '></iconify-icon>'

def question(qid, stem, opts, ans, fb):
    lis = ''.join(f'<li class="q__opt" data-opt="{k}"><label><input type="radio" name="{qid}" value="{k}" data-k="{qid}"><span class="q__k">{k}</span><span>{e(o)}</span></label></li>' for k, o in zip('ABCD', opts))
    return (f'<div class="q" id="{qid}" data-a="{ans}" data-mode="instant"><p class="q__kick">{ic("ph:check-square-duotone")}Knowledge check</p>'
            f'<p class="q__stem">{e(stem)}</p><ul class="q__opts">{lis}</ul><p class="q__fb"><b>Answer {ans}.</b> {e(fb)}</p></div>')

def lesson(tk, mi, li, L):
    title, paras, keys, stem, opts, ans, fb = L
    slug = tk.replace('-', '')
    return (f'<div class="lesson" id="{slug}m{mi}l{li}"><h3 class="lesson__h"><span class="lesson__num">{li}</span>{e(title)}'
            f'<span class="lesson__min">{ic("ph:clock-duotone")}{LESSON_MIN} min</span></h3>'
            f'<div class="prose">{"".join(f"<p>{e(p)}</p>" for p in paras)}</div>'
            f'<div class="box box--key"><p class="box__t">{ic("ph:hash-duotone", "box__i")}What to hold on to</p><ul>{"".join(f"<li>{e(k)}</li>" for k in keys)}</ul></div>'
            + question(f'{tk}-m{mi}-chk{li}', stem, opts, ans, fb) + '</div>')

def module(tk, mi, m):
    total = LESSON_MIN * len(m['lessons'])
    assert total <= 12, (tk, mi, total)
    return (f'<h2 class="h2">{ic("ph:book-open-text-duotone", "h2__i")}Module {mi}: {e(m["title"])}'
            f'<span class="lesson__min">{ic("ph:clock-duotone")}{total} min</span></h2>'
            f'<p class="prose">{e(m["lede"])}</p>'
            + ''.join(lesson(tk, mi, li, L) for li, L in enumerate(m['lessons'], 1)))

def branch(t):
    n_checks = sum(len(m['lessons']) for m in t['modules'])
    mins = sum(LESSON_MIN * len(m['lessons']) for m in t['modules'])
    return (f'<div class="branch" data-branch="{t["key"]}" style="--mh:{t["hue"]}" hidden="">'
            f'<div class="branch__head">{ic(t["icon"], "branch__i")}<div><span class="kick">{t["label"]}</span><h3 class="branch__t">{e(t["title"])}</h3>'
            f'<p class="branch__d">{e(t["blurb"])} {len(t["modules"])} modules, {mins} minutes in total, no module longer than 12 minutes.</p></div></div>'
            f'<div class="box box--objectives"><p class="box__t">{ic("ph:target-duotone", "box__i")}Scope of this track</p><ul>{"".join(f"<li>{e(s)}</li>" for s in t["scope"])}</ul></div>'
            + ''.join(module(t['key'], mi, m) for mi, m in enumerate(t['modules'], 1))
            + f'<div class="box box--refresh"><p class="box__t">{ic("ph:books-duotone", "box__i")}Sources for this track</p><ul>{"".join(f"<li>{e(s)}</li>" for s in t["sources"])}</ul></div>'
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
            '  <p class="prose">Short tracks written for the work you actually do. Choose your discipline: each track has four modules, and no module takes longer than 12 minutes. '
            'Every lesson ends with a knowledge check that marks as you answer. The eleven modules that follow are the full course and are open to everyone.</p>\n'
            f'  <div class="box box--refresh"><p class="box__t">{ic("ph:shield-warning-duotone", "box__i")}How to read these tracks</p>'
            '<p>These are practice-level summaries consistent with the Australian ADHD guideline. Where trial evidence is thin, the lesson says so. '
            'They do not replace your profession’s scope of practice, your registration standards or local prescribing law.</p></div>\n'
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
    p.write_text(s)
    # 4. login page blurb
    lp = ROOT / 'academy-login.html'; l = lp.read_text()
    old = 'The ADHDme Clinical Academy: an eleven-module, self-directed clinician workbook.'
    if old in l:
        lp.write_text(l.replace(old, 'The ADHDme Clinical Academy: short training tracks by discipline, plus an eleven-module, self-directed clinician workbook.'))
    print('tracks:', len(TRACKS), '| academy.html bytes:', len(s))

if __name__ == '__main__':
    main()
