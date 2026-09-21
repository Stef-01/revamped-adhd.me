#!/usr/bin/env python3
"""Checks that keep the UX evaluation fixes fixed. Plain assertions, no framework.

    python3 scripts/check-site.py      # exit 1 and a list if anything is wrong

What it looks for, and the mistake each one came from (see UX-EVALUATION-UPGRADE-PLAN.md):
  - text stranded outside an attribute, e.g. class names after a closed style="…"   (X-03)
  - an internal link to a page or asset that is not in the repo
  - a second typeface: font-serif on any page                                       (LRN-01)
  - a cost figure on How it works that the generator no longer holds                (HIW-03)
  - a card or profile whose button says Book when the link is an enquiry form, or
    an enquiry listed above a bookable diary on The Network                         (X-01)
"""
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
ONLINE_DIARIES = ('healthengine.com.au', 'halaxy.com/book')  # keep in step with build-profiles.py
problems = []


class Page(HTMLParser):
    def __init__(self, name):
        super().__init__(convert_charrefs=True)
        self.name, self.links, self.in_svg = name, [], 0

    def handle_starttag(self, tag, attrs):
        self.in_svg += tag == 'svg'
        for key, value in attrs:
            if not self.in_svg and (re.search(r'["\[\]]', key) or (':' in key and not key.startswith(('xmlns', 'xlink', 'xml')))):
                problems.append(f'{self.name}:{self.getpos()[0]}: <{tag}> has stray text "{key}" outside any attribute')
            if key in ('href', 'src') and value:
                self.links.append((self.getpos()[0], value))

    def handle_endtag(self, tag):
        self.in_svg -= tag == 'svg' and self.in_svg > 0


for path in sorted(ROOT.glob('*.html')):
    text = path.read_text(encoding='utf-8')
    page = Page(path.name)
    page.feed(text)
    for line, link in page.links:
        target = link.split('#')[0].split('?')[0]
        if target and not re.match(r'[a-z]+:|//', target) and not (ROOT / target).exists():
            problems.append(f'{path.name}:{line}: links to {target}, which does not exist')
    if re.search(r'class="[^"]*\bfont-serif\b', text):
        problems.append(f'{path.name}: uses font-serif; headings are extrabold Plus Jakarta Sans everywhere')
    cta = re.search(r'href="([^"]+)" target="_blank" rel="noopener noreferrer">(Book|Enquire) with ', text)
    if cta and (cta.group(2) == 'Book') != any(h in cta.group(1) for h in ONLINE_DIARIES):
        problems.append(f'{path.name}: button says {cta.group(2)} but the link is {cta.group(1)}')

deck = (ROOT / 'the-doctors.html').read_text(encoding='utf-8')
for panel in re.findall(r'<div role="tabpanel"[^>]*id="panel-([\w-]+)"[^>]*><ul[^>]*>(.*?)</ul>', deck, re.S):
    verbs = re.findall(r'aria-label="(Book|Enquire) with ', panel[1])
    if verbs != sorted(verbs):  # 'Book' sorts before 'Enquire'
        problems.append(f'the-doctors.html: panel "{panel[0]}" lists an enquiry above a bookable diary')

# Cost figures on How it works are hand-written; every one must still be a figure the generator holds.
profiles = (ROOT / 'scripts' / 'build-profiles.py').read_text(encoding='utf-8')
hiw = (ROOT / 'how-it-works.html').read_text(encoding='utf-8')
for figure in ('$299', '$199', '$498', '$253', '$149', '$104', '$149.05', '$101.55'):
    if figure not in hiw or figure not in profiles:
        problems.append(f'how-it-works.html and build-profiles.py disagree about {figure}')

if problems:
    print('\n'.join(problems))
    sys.exit(1)
print('site checks pass')
