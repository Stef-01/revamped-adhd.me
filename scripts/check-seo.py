#!/usr/bin/env python3
"""On-page SEO rules for every page, checked from the committed HTML. Exit 1 on any failure.

Indexable pages (no robots noindex) must:
  - be listed in sitemap.xml, and every sitemap URL must be an indexable page;
  - have a title of 30 to 60 characters including " · ADHDme" (legal pages may be shorter, and a profile whose
    name and role run over may exceed it, whole, rather than cut a word), unique across the site;
  - have a meta description of 110 to 160 characters, unique across the site;
  - have a canonical URL pointing at the page itself, and og:url, og:title and og:image to match;
  - have exactly one <h1>, and no heading that skips a level on the way down (h2 straight to h4);
  - give every <img> an alt attribute (empty is fine for decoration);
  - carry JSON-LD that parses.
Pages with noindex must not be in sitemap.xml.

  python3 scripts/check-seo.py
"""
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.adhdme.au'
SKIP = {'academy.html', 'academy-login.html'}   # login-gated and noindex; kept out of every SEO check
LEGAL = {'privacy.html', 'terms.html', 'automated-decisions.html'}   # a short plain title is the convention


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings, self.imgs_without_alt, self.ld = [], 0, []
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if re.fullmatch(r'h[1-6]', tag):
            self.headings.append(int(tag[1]))
        elif tag == 'img' and 'alt' not in a:
            self.imgs_without_alt += 1
        elif tag == 'script' and a.get('type') == 'application/ld+json':
            self._in_ld = True
            self.ld.append('')

    def handle_endtag(self, tag):
        if tag == 'script':
            self._in_ld = False

    def handle_data(self, data):
        if self._in_ld:
            self.ld[-1] += data


def meta(text, pattern):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)).strip() if m else None


def main():
    problems = []
    sitemap = set(re.findall(r'<loc>([^<]+)</loc>', (ROOT / 'sitemap.xml').read_text(encoding='utf-8')))
    titles, descriptions = {}, {}
    for path in sorted(ROOT.glob('*.html')):
        if path.name in SKIP:
            continue
        text = path.read_text(encoding='utf-8')
        url = SITE + '/' + ('' if path.name == 'index.html' else path.name)
        noindex = bool(re.search(r'<meta name="robots" content="[^"]*noindex', text))
        say = lambda msg: problems.append(f'{path.name}: {msg}')
        if noindex:
            if url in sitemap:
                say('noindex, but listed in sitemap.xml')
            continue
        if url not in sitemap:
            say('indexable, but missing from sitemap.xml')

        title = meta(text, r'<title>(.*?)</title>')
        if not title:
            say('no <title>')
        else:
            titles.setdefault(title, []).append(path.name)
            profile = '/assets/clinicians/' in (meta(text, r'<meta property="og:image" content="([^"]+)"') or '')
            if (len(title) < 30 and path.name not in LEGAL) or (len(title) > 60 and not profile):
                say(f'title is {len(title)} characters: {title!r}')
        desc = meta(text, r'<meta name="description" content="([^"]*)"')
        if not desc:
            say('no meta description')
        else:
            descriptions.setdefault(desc, []).append(path.name)
            if not 110 <= len(desc) <= 160:
                say(f'meta description is {len(desc)} characters')

        canonical = meta(text, r'<link rel="canonical" href="([^"]+)"')
        if canonical != url:
            say(f'canonical is {canonical!r}, expected {url!r}')
        if meta(text, r'<meta property="og:url" content="([^"]+)"') != url:
            say('og:url does not match the canonical URL')
        for tag in ('og:title', 'og:image'):
            if not meta(text, rf'<meta property="{tag}" content="([^"]+)"'):
                say(f'no {tag}')

        page = Page()
        page.feed(text)
        if page.headings.count(1) != 1:
            say(f'{page.headings.count(1)} <h1> elements')
        for before, after in zip(page.headings, page.headings[1:]):
            if after > before + 1:
                say(f'heading skips from h{before} to h{after}')
                break
        if page.imgs_without_alt:
            say(f'{page.imgs_without_alt} <img> without alt')
        for block in page.ld:
            try:
                json.loads(block)
            except ValueError as e:
                say(f'JSON-LD does not parse: {e}')

    for loc in sitemap:
        name = loc[len(SITE) + 1:] or 'index.html'
        if not (ROOT / name).exists():
            problems.append(f'sitemap.xml lists {loc}, which has no file')
    for label, seen in (('title', titles), ('meta description', descriptions)):
        for value, pages in seen.items():
            if len(pages) > 1:
                problems.append(f'same {label} on {", ".join(pages)}: {value!r}')

    for p in problems:
        print(p)
    print(f'check-seo: {len(problems)} problem(s)' if problems else 'check-seo: all pages pass')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
