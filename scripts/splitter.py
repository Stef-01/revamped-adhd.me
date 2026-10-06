#!/usr/bin/env python3
"""Question-splitting intake prototype on the real ADHD.me provider data. Read-only on the site.

    python3 scripts/splitter.py            # print the report to stdout
    python3 scripts/splitter.py --write    # write SPLITTER-PROTOTYPE.md at the repo root

Deterministic, no LLM calls, no patient data. Providers come from scripts/build-profiles.py (CLINICIANS)
and the aspect/domain membership from scripts/build-navigator.py (DOMAINS), both imported, never copied.
Every question is a yes/no over one structured field. A provider whose profile does not declare the field
is "undeclared": it survives BOTH answers (we never exclude on a silence). "Probably" is routed as yes.
"""
import importlib.util
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(name, fname):
    s = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / fname)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


profiles = load('profiles', 'build-profiles.py')
navigator = load('navigator', 'build-navigator.py')
P = profiles.CLINICIANS
IDS = [c['id'] for c in P]
BY = {c['id']: c for c in P}
Y, N, U = 'y', 'n', 'u'


def detail(c, key):
    return next((v for k, v in c['details'] if k == key), None)


def region(c):
    pl = c['place']
    for key, label in (('Brisbane', 'Brisbane'), ('Perth', 'Perth'), ('Bundall', 'Gold Coast'),
                       ('Double Bay', 'Sydney'), ('Beecroft', 'Sydney'), ('Jindabyne', 'Snowy Mountains')):
        if key in pl:
            return label
    return 'other'


# ---------------------------------------------------------------- the question bank
# name -> (question text, source field, {id: y|n|u})
Q = {}
for d in navigator.DOMAINS:
    members = {cid for a in d['aspects'] for cid, _ in a['who']}
    Q['domain:' + d['key']] = (f'Is this about {d["label"].lower()}?', 'navigator domain',
                              {i: (Y if i in members else N) for i in IDS})
    for a in d['aspects']:
        m = {cid for cid, _ in a['who']}
        Q[f'aspect:{d["key"]}:{a["key"]}'] = (f'Is it mainly "{a["label"]}"?', 'navigator aspect',
                                              {i: (Y if i in m else N) for i in IDS})
for cat in sorted({c['category'] for c in P}):
    Q['category:' + cat] = (f'Do you want a {cat.replace("-", " ")}?', 'category',
                            {c['id']: (Y if c['category'] == cat else N) for c in P})
Q['telehealth'] = ('Is video / phone care fine?', 'telehealth', {c['id']: (Y if c['telehealth'] else N) for c in P})
for r in sorted({region(c) for c in P}):
    Q['region:' + r] = (f'Are you in {r}?', 'place', {c['id']: (Y if region(c) == r else N) for c in P})
Q['wheelchair'] = ('Do you need a step-free clinic?', 'details > Wheelchair access',
                   {c['id']: (Y if (detail(c, 'Wheelchair access') or '').startswith('Yes') else
                              U if (detail(c, 'Wheelchair access') or '').startswith('Not declared') else N) for c in P})
Q['lang:other'] = ('Do you want care in a language other than English?', 'languages',
                   {c['id']: (Y if [x for x in c['languages'] if x != 'English'] else (U if not c['languages'] else N)) for c in P})
Q['pronouns:she'] = ('Do you want a she/her clinician?', 'pronouns', {c['id']: (Y if c['pronouns'] == 'she/her' else N) for c in P})
Q['provisional'] = ('Is a provisional (supervised) psychologist okay?', 'role',
                    {c['id']: (Y if 'Provisional' in c['role'] else N) for c in P})
# only keep questions that actually split something
Q = {k: v for k, v in Q.items() if len({x for x in v[2].values() if x != U}) > 1}


def keep(vals, ans, ids):
    return [i for i in ids if vals[i] in (ans, U)]


def cost(vals, ids):
    """Expected candidates left after asking, answer weighted by how many providers fall on each side."""
    y, n = keep(vals, Y, ids), keep(vals, N, ids)
    if len(y) == len(ids) or len(n) == len(ids):
        return None
    return (len(y) ** 2 + len(n) ** 2) / len(ids)


def best(ids):
    scored = [(cost(v[2], ids), k) for k, v in Q.items()]
    scored = [(c, k) for c, k in scored if c is not None]
    return min(scored)[1] if scored else None


def build(ids, depth=0):
    if len(ids) == 1:
        return dict(ids=ids, depth=depth)
    q = best(ids)
    if q is None:
        return dict(ids=ids, depth=depth, stuck=True)
    vals = Q[q][2]
    return dict(ids=ids, depth=depth, q=q,
                yes=build(keep(vals, Y, ids), depth + 1), no=build(keep(vals, N, ids), depth + 1))


def leaves(t):
    if 'q' not in t:
        yield t
    else:
        yield from leaves(t['yes'])
        yield from leaves(t['no'])


def render(t, ind=0):
    pad = '  ' * ind
    if 'q' not in t:
        names = ', '.join(BY[i]['name'] for i in t['ids'])
        return [f'{pad}-> {names}' + ('  (indistinguishable on declared fields)' if t.get('stuck') else '')]
    out = [f'{pad}{Q[t["q"]][0]}  [{t["q"]}, {len(t["ids"])} left]']
    out += [f'{pad}  yes/probably:'] + render(t['yes'], ind + 2)
    out += [f'{pad}  no:'] + render(t['no'], ind + 2)
    return out


def depths(tree):
    """id -> (worst depth to a leaf containing it, size of that leaf)."""
    d = {}
    for lf in leaves(tree):
        for i in lf['ids']:
            if i not in d or lf['depth'] > d[i][0]:
                d[i] = (lf['depth'], len(lf['ids']))
    return d


def walk(tree, acceptable):
    """Follow a case through the tree. The person is modelled by the set of providers they would accept:
    they answer yes when anyone acceptable sits on the yes side (a question that does not matter to them is
    a "no preference", answered yes), otherwise no. Returns (asked list, final ids)."""
    asked, t = [], tree
    while 'q' in t:
        yes = any(i in acceptable for i in t['yes']['ids'])
        asked.append((Q[t['q']][0], 'yes' if yes else 'no'))
        t = t['yes'] if yes else t['no']
    return asked, t['ids']


def acceptable_for(*needs):
    """Providers who satisfy every need (a Q key whose answer is yes)."""
    return {i for i in IDS if all(Q[n][2][i] in (Y, U) for n in needs)}


def aspects_of():
    asp = {i: [] for i in IDS}
    for d in navigator.DOMAINS:
        for a in d['aspects']:
            for cid, _ in a['who']:
                asp[cid].append(f'{d["key"]}:{a["key"]}')
    return asp


def fieldtable():
    rows = ['| id | category | role | place | tele | wheelchair | languages | pronouns | aspects it sits under |', '|' + '---|' * 9]
    asp = aspects_of()
    for c in P:
        w = detail(c, 'Wheelchair access') or ''
        rows.append(f'| {c["id"]} | {c["category"]} | {c["role"]} | {c["place"]} | {"Y" if c["telehealth"] else "N"} | '
                    f'{w.split(":")[0][:14] or "EMPTY"} | {", ".join(c["languages"]) or "EMPTY"} | {c["pronouns"] or "EMPTY"} | '
                    f'{", ".join(asp[c["id"]]) or "none (empty)"} |')
    return '\n'.join(rows)


def split_table(ids):
    rows = ['| question | source | yes | no | undeclared | expected left |', '|---|---|---|---|---|---|']
    scored = []
    for k, (txt, src, vals) in Q.items():
        c = cost(vals, ids)
        scored.append((c if c is not None else 99, k, txt, src, vals))
    for c, k, txt, src, vals in sorted(scored):
        cnt = Counter(vals[i] for i in ids)
        rows.append(f'| {txt} `{k}` | {src} | {cnt[Y]} | {cnt[N]} | {cnt[U]} | {c:.1f} |')
    return '\n'.join(rows)


def empty_fields():
    out = []
    for key in ('languages', 'experience', 'chips', 'qualifications', 'description', 'fees'):
        e = [c['id'] for c in P if not c.get(key)]
        out.append(f'- `{key}`: empty on {len(e)}/{len(P)}' + (f' ({", ".join(e)})' if e and len(e) <= 8 else ''))
    wc = [c['id'] for c in P if (detail(c, 'Wheelchair access') or '').startswith('Not declared')]
    out.append(f'- `Wheelchair access`: "Not declared" on {len(wc)}/{len(P)}')
    unplaced = [i for i, v in aspects_of().items() if not v]
    out.append(f'- navigator aspects: {len(unplaced)}/{len(P)} providers sit under none ({", ".join(unplaced)})')
    return '\n'.join(out)


# Bart's case (23 Sep 2026): 'marriage breakdown'. Needs assumed (stated in the report): the partner relationship,
# rejection hurts as much as the arguments, in Brisbane.
BART = ('aspect:relationships:partner', 'aspect:relationships:rejection', 'region:Brisbane')


def missing_fields(tree):
    return [f'- {", ".join(BY[i]["name"] for i in lf["ids"])} ({len(lf["ids"])}): identical on every declared field; one '
            f'declared specialty, age band or approach that splits them removes {len(lf["ids"]) - 1} narrowing step(s) for anyone routed here.'
            for lf in sorted(leaves(tree), key=lambda l: -len(l['ids'])) if lf.get('stuck')]


def report():
    tree = build(IDS)
    dep = depths(tree)
    ds = [v[0] for v in dep.values()]
    iso = [k for k, v in dep.items() if v[1] == 1]
    stuck_ids = {i for lf in leaves(tree) if lf.get('stuck') for i in lf['ids']}
    asked, final = walk(tree, acceptable_for(*BART))
    L = ['# Question-splitting intake prototype (ADHD.me provider data)', '',
         f'Generated by `scripts/splitter.py` from `scripts/build-profiles.py` ({len(P)} providers) and `scripts/build-navigator.py`. '
         'Read-only on the site; no LLM calls; no patient data. Rerun: `python scripts/splitter.py --write`.', '',
         '## Headline', '',
         f'- Providers: {len(P)}. Questions in the bank: {len(Q)}.',
         f'- Depth to the leaf containing each provider: average **{sum(ds)/len(ds):.2f}**, worst case **{max(ds)}**.',
         f'- Providers isolated to exactly one name: {len(iso)}/{len(P)}. '
         f'Providers indistinguishable from a sibling on every declared field: {len(stuck_ids)}.',
         f"- Bart's case ends at **{len(final)} provider(s)** after **{len(asked)} questions**: "
         f'{", ".join(BY[i]["name"] for i in final)}.', '',
         'Answer semantics: yes, no, or "probably" (routed as yes). A provider whose profile is silent on a field survives both answers.', '',
         '## 1. Field table (one row per provider)', '', fieldtable(), '',
         '### Empty / undeclared fields', '', empty_fields(), '',
         '## 2. Split ratio per question (over all providers)', '', split_table(IDS), '',
         '## 3. Greedy question tree', '', '```', *render(tree), '```', '',
         '### Depth to reach each provider', '',
         '| provider | depth | candidates left at that leaf |', '|---|---|---|']
    for i in sorted(dep, key=lambda k: (dep[k][0], k)):
        L.append(f'| {BY[i]["name"]} | {dep[i][0]} | {dep[i][1]} |')
    L += ['', "## 4. Bart's case, walked by hand", '',
          "Case (23 Sep 2026): the navigator returned 151 results for 'marriage breakdown' and Bart gave up typing. "
          'Assumed needs (stated, not guessed silently): it is about the partner; rejection hurts as much as the arguments; '
          'they are in Brisbane. The walk answers yes whenever an acceptable provider sits on the yes side ("no preference" counts as yes), otherwise no.', '']
    L += [f'{n}. {qt} -> **{a}**' for n, (qt, a) in enumerate(asked, 1)]
    L += ['', 'Caveat: the greedy tree asks whichever question splits best, not the one Bart would volunteer. Question 2 (anxiety and low mood) and 4 (confidence) are answered yes only because the acceptable provider sits on that side; a real person might answer no and be routed to a sibling. The count is the tree depth, not a measure of how natural the questions feel.', '', f'**Ends at:** {", ".join(BY[i]["name"] + " (" + BY[i]["role"] + ", " + BY[i]["place"] + ")" for i in final)}.', '',
          'Variants (same tree, other answers):']
    for note, needs in (('partner + rejection, telehealth anywhere (Brisbane not required)', BART[:2]),
                        ('arguments and conflict, in Brisbane', ('aspect:relationships:conflict', 'region:Brisbane')),
                        ('partner, in Brisbane', ('aspect:relationships:partner', 'region:Brisbane'))):
        acc = acceptable_for(*needs)
        a2, f2 = walk(tree, acc)
        L.append(f'- {note}: {len(acc)} acceptable ({", ".join(BY[i]["name"] for i in sorted(acc))}); '
                 f'{len(a2)} questions -> {", ".join(BY[i]["name"] for i in f2)}')
    L += ['', '## 5. Fields a one-hour provider interview should fill', '',
          'Groups the tree cannot split today:', '', *(missing_fields(tree) or ['- none']), '',
          'Fields empty or undeclared for most providers, each of which would turn "survives both answers" into a real split: '
          '`Wheelchair access` (undeclared for most coaches and GPs), `languages` (empty for most), age band seen '
          '(child / teen / adult), taking new patients this month, and a named approach (couples work vs individual). '
          'None exist as structured fields today; each is one yes/no for the tree.', '']
    return '\n'.join(L), dict(avg=sum(ds) / len(ds), worst=max(ds), bart=(len(asked), final))


if __name__ == '__main__':
    text, stats = report()
    if '--write' in sys.argv:
        (ROOT / 'SPLITTER-PROTOTYPE.md').write_text(text, encoding='utf-8')
        print('wrote SPLITTER-PROTOTYPE.md')
    else:
        print(text)
    print(f'avg depth {stats["avg"]:.2f}, worst {stats["worst"]}, bart {stats["bart"][0]} questions -> '
          f'{[BY[i]["name"] for i in stats["bart"][1]]}', file=sys.stderr)
