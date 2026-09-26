#!/usr/bin/env python3
"""Tell the IndexNow search engines which pages changed, so they recrawl them soon rather than on their own
schedule. Bing is one, and ChatGPT search and Copilot answer from Bing's index. Google does not use IndexNow;
it reads sitemap.xml.

    python3 scripts/indexnow.py BEFORE AFTER    # send the pages that changed between two commits
    python3 scripts/indexnow.py --all           # send every page in sitemap.xml

Only pages listed in sitemap.xml are sent, so nothing noindex goes out. The engines check the request against
the key file at the site root, KEY.txt. .github/workflows/indexnow.yml runs this after each push to main.
"""
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.adhdme.au'
KEY = '1e12d7c3d4abf54cd5f4374a443befd2'
ENDPOINT = 'https://api.indexnow.org/indexnow'


def url(name):
    return SITE + '/' + ('' if name == 'index.html' else name)


def main(argv):
    if not (ROOT / f'{KEY}.txt').is_file():
        raise SystemExit(f'indexnow: the key file {KEY}.txt is missing from the site root')
    listed = set(re.findall(r'<loc>([^<]+)</loc>', (ROOT / 'sitemap.xml').read_text(encoding='utf-8')))
    if argv == ['--all']:
        urls = sorted(listed)
    elif len(argv) == 2:
        changed = subprocess.run(['git', 'diff', '--name-only', argv[0], argv[1], '--', '*.html'], cwd=ROOT,
                                 capture_output=True, text=True, check=True).stdout.split()
        urls = sorted(u for u in (url(name) for name in changed if '/' not in name) if u in listed)
    else:
        raise SystemExit(__doc__)
    if not urls:
        print('indexnow: no listed page changed, nothing to send')
        return 0
    body = json.dumps({'host': 'www.adhdme.au', 'key': KEY, 'keyLocation': f'{SITE}/{KEY}.txt', 'urlList': urls})
    request = urllib.request.Request(ENDPOINT, data=body.encode(), headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
    except urllib.error.HTTPError as e:
        raise SystemExit(f'indexnow: {e.code} {e.reason} for {len(urls)} page(s): {e.read().decode(errors="replace")[:300]}')
    print(f'indexnow: {status} for {len(urls)} page(s)')
    for u in urls:
        print('  ' + u)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
