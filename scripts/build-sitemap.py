#!/usr/bin/env python3
"""Write sitemap.xml and llms.txt from the pages sitemap.xml already lists.

The <loc> list in sitemap.xml stays the source of truth (add a page there by hand, as README says for
clinicians). This script keeps that list and its order, and adds what search engines can use:
  - <lastmod>: a blog post's publish date; for any other page, the date of the last commit that changed
    its file (today, if the file has uncommitted changes).
  - <image:image>: a clinician's portrait on their profile, and a post's share image on the post.
llms.txt (https://llmstxt.org) is a plain Markdown index of the same pages, grouped for a reader, with
each page's own title and description. It is a proposal that some AI tools read; search engines do not
rank on it.

  python3 scripts/build-sitemap.py            # write both files
  python3 scripts/build-sitemap.py --check    # exit 1 if either is out of date
"""
import datetime
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.adhdme.au'
SITEMAP = ROOT / 'sitemap.xml'
LLMS = ROOT / 'llms.txt'


def page_file(loc):
    name = loc[len(SITE) + 1:] if loc.startswith(SITE + '/') else ''
    return ROOT / (name or 'index.html')


def head_meta(text, pattern):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)).strip() if m else ''


def last_changed(path):
    rel = str(path.relative_to(ROOT))
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:
        return datetime.date.today().isoformat()
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out or datetime.date.today().isoformat()


def pages():
    locs = re.findall(r'<loc>([^<]+)</loc>', SITEMAP.read_text(encoding='utf-8'))
    out = []
    for loc in dict.fromkeys(locs):          # each URL once, in the order listed
        path = page_file(loc)
        text = path.read_text(encoding='utf-8')
        slug = path.stem
        published = head_meta(text, r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"')
        portrait = head_meta(text, r'<meta property="og:image" content="(' + re.escape(SITE) + r'/assets/clinicians/[^"]+)"')
        share = head_meta(text, r'<meta property="og:image" content="(' + re.escape(SITE) + r'/assets/blog/og/[^"]+)"')
        out.append(dict(
            loc=loc, slug=slug, path=path,
            title=head_meta(text, r'<title>(.*?)</title>').replace(' · ADHDme', ''),
            description=head_meta(text, r'<meta name="description" content="([^"]*)"'),
            lastmod=published or last_changed(path),
            images=[i for i in (portrait, share) if i],
            kind=('post' if slug.startswith('blog-') else 'profile' if portrait else
                  'guide' if slug.startswith('adhd-') else 'page'),
        ))
    return out


def sitemap(ps):
    rows = []
    for p in ps:
        images = ''.join(f'<image:image><image:loc>{i}</image:loc></image:image>' for i in p['images'])
        rows.append(f"  <url><loc>{p['loc']}</loc><lastmod>{p['lastmod']}</lastmod>{images}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + '\n'.join(rows) + '\n</urlset>\n')


SECTIONS = [
    ('Find care', lambda p: p['kind'] == 'page' and p['slug'] in ('index', 'the-doctors', 'care-navigator', 'how-it-works')),
    ('Clinicians', lambda p: p['kind'] == 'profile'),
    ('ADHD care by place and profession', lambda p: p['kind'] == 'guide'),
    ('Guides', lambda p: p['kind'] == 'post'),
    ('About', lambda p: p['kind'] == 'page' and p['slug'] in ('our-story', 'learn')),
    ('Optional', lambda p: p['kind'] == 'page' and p['slug'] in ('privacy', 'terms', 'automated-decisions')),
]


def llms(ps):
    lines = ['# ADHDme', '',
             '> A directory of ADHD clinicians in Australia: GPs, psychologists, allied health clinicians and coaches. '
             'Each profile says how the clinician works, where they practise and what they charge, and you book with '
             'the practice directly. ADHDme does not provide health care and takes no commission.', '',
             'Clinician profiles are written from each clinician\'s own description of their work. Fees and Medicare '
             'details are as each practice publishes them; the practice confirms them when you book.', '']
    placed = set()
    for heading, keep in SECTIONS:
        chosen = [p for p in ps if keep(p) and p['loc'] not in placed]
        if not chosen:
            continue
        lines += [f'## {heading}', '']
        for p in chosen:
            placed.add(p['loc'])
            lines.append(f"- [{p['title']}]({p['loc']}): {p['description']}")
        lines.append('')
    missing = [p['loc'] for p in ps if p['loc'] not in placed]
    if missing:
        raise SystemExit('build-sitemap: no llms.txt section for ' + ', '.join(missing))
    return '\n'.join(lines).rstrip() + '\n'


def main(argv):
    ps = pages()
    outputs = {SITEMAP: sitemap(ps), LLMS: llms(ps)}
    stale = [path.name for path, text in outputs.items() if not path.exists() or path.read_text(encoding='utf-8') != text]
    if '--check' in argv:
        print('out of date: ' + ', '.join(stale) + '; run python3 scripts/build-sitemap.py' if stale else 'sitemap.xml and llms.txt are up to date')
        return 1 if stale else 0
    for path, text in outputs.items():
        path.write_text(text, encoding='utf-8', newline='')
        print(('wrote  ' if path.name in stale else 'same   ') + path.name)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
