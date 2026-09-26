#!/usr/bin/env python3
"""Download each app's App Store icon for the Apps section on Learn, as a 128px PNG in assets/learn/apps/.

    python3 scripts/fetch-app-icons.py      # needs internet access and Pillow

Each app is looked up in the Australian App Store by its id or name; an app in SITE_ONLY (whose App Store name
is shared with an unrelated app) gives the icon its own website publishes. Re-run when an app changes its icon.
"""
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'learn' / 'apps'
SIZE = 128

# slug: (App Store id or None, website)
APPS = {
    'focusmate': (None, 'https://www.focusmate.com/'),
    'goblin-tools': ('6449003064', 'https://goblin.tools/'),
    'tiimo': (None, 'https://www.tiimoapp.com/'),
    'structured': ('1499198946', 'https://structured.app/'),
    'inflow': ('1528183849', 'https://www.getinflow.io/'),
    'finch': (None, 'https://finchcare.com/'),
    'forest': (None, 'https://www.forestapp.cc/'),
    'brainfm': (None, 'https://www.brain.fm/'),
    'routinery': ('1450486923', 'https://www.routinery.app/'),
    'due': (None, 'https://www.dueapp.com/'),
    'habitica': (None, 'https://habitica.com/'),
    'todoist': (None, 'https://todoist.com/'),
}
# Search terms for apps whose id is not pinned above; the first result whose name starts with the term wins.
TERMS = {'focusmate': 'Focusmate', 'tiimo': 'Tiimo', 'finch': 'Finch', 'forest': 'Forest',
         'brainfm': 'Brain.fm', 'due': 'Due', 'habitica': 'Habitica', 'todoist': 'Todoist'}
SITE_ONLY = {'focusmate'}   # "Focusmate" in the App Store is a different developer's app blocker
UA = {'User-Agent': 'Mozilla/5.0 (ADHDme icon fetch)'}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def app_store(slug, app_id):
    if app_id:
        results = json.loads(get(f'https://itunes.apple.com/lookup?id={app_id}&country=au'))['results']
    else:
        q = urllib.parse.urlencode({'term': TERMS[slug], 'entity': 'software', 'country': 'au', 'limit': 10})
        results = [r for r in json.loads(get(f'https://itunes.apple.com/search?{q}'))['results']
                   if r['trackName'].lower().startswith(TERMS[slug].lower())]
    if not results:
        return None
    r = results[0]
    print(f'{slug}: App Store "{r["trackName"]}" by {r.get("sellerName")} ({r["trackViewUrl"]})')
    return get(r['artworkUrl512'])


def website(slug, site):
    html = get(site).decode('utf-8', 'replace')
    for rel in ('apple-touch-icon', 'icon'):
        m = re.search(r'<link[^>]+rel="[^"]*' + rel + r'[^"]*"[^>]*href="([^"]+)"', html) or \
            re.search(r'<link[^>]+href="([^"]+)"[^>]+rel="[^"]*' + rel, html)
        if m:
            url = urllib.parse.urljoin(site, m.group(1))
            print(f'{slug}: website icon {url}')
            return get(url)
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    missing = []
    for slug, (app_id, site) in APPS.items():
        data = None
        try:
            data = None if slug in SITE_ONLY else app_store(slug, app_id)
        except Exception as e:
            print(f'{slug}: App Store lookup failed: {e}')
        if data is None:
            try:
                data = website(slug, site)
            except Exception as e:
                print(f'{slug}: website fetch failed: {e}')
        if data is None:
            missing.append(slug)
            continue
        im = Image.open(io.BytesIO(data)).convert('RGBA')
        im.thumbnail((SIZE, SIZE), Image.LANCZOS)
        im.save(OUT / f'{slug}.png', optimize=True)
        print(f'{slug}: wrote {im.size[0]}x{im.size[1]}')
    if missing:
        print('no icon for: ' + ', '.join(missing))
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
