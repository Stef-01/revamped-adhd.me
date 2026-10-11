#!/usr/bin/env python3
"""Static checks for the matching pilot: the things a tester reads off the files rather than the browser.

    python3 scripts/check-matching.py        # exit 1 on any failure

What it holds the pilot to:
  - the committed flags are off, and there is no endpoint to send to;
  - every form control on matching-help.html has a visible label or legend, errors are tied to their fields,
    and the consent box starts unticked;
  - matching.js keeps answers out of browser storage, URLs and analytics (the only storage key is the
    "seen this call-to-action" flag, and the only analytics properties are a placement and a copy label);
  - the request page is marked private to analytics, so autocapture and session replay are off there;
  - the three calls-to-action exist, are hidden by default, and carry the approved copy;
  - no sensitive wording slipped in (free pilot, turnaround promise, "perfect match", "AI-powered", and the
    site's general "No referral needed" line, which is not this feature's promise to make).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fails = []

def fail(msg):
    fails.append(msg)

cfg = (ROOT / 'matching-config.js').read_text(encoding='utf-8')
for flag in ('pilotEnabled', 'intakeOpen', 'collectionNoticeApproved'):
    if not re.search(rf'\b{flag}:\s*false\b', cfg):
        fail(f'matching-config.js: {flag} must be committed as false')
if not re.search(r"requestEndpoint:\s*''", cfg):
    fail('matching-config.js: requestEndpoint must be committed empty')

js = (ROOT / 'matching.js').read_text(encoding='utf-8')
storage = re.findall(r'(localStorage|sessionStorage)\.(setItem|getItem)\(([^)]*)\)', js)
for kind, op, arg in storage:
    if 'seenKey(' not in arg:
        fail(f'matching.js: {kind}.{op}({arg}) stores something other than the seen-flag')
if re.search(r'\blocalStorage\s*\.', js):
    fail('matching.js: must not use localStorage at all')
for name, props in re.findall(r"track\('([a-z-]+)',\s*\{([^}]*)\}", js):
    keys = set(re.findall(r'(\w+):', props))
    if keys - {'placement', 'copy_version'}:
        fail(f'matching.js: {name} sends properties beyond placement and copy_version: {sorted(keys)}')
if re.search(r'console\.(log|info|warn|error)', js):
    fail('matching.js: must not log (answers could end up in a recording or a report)')
if re.search(r'location\.(search|hash|href)\s*=|history\.(push|replace)State', js):
    fail('matching.js: must not write answers into the URL')

page = (ROOT / 'matching-help.html').read_text(encoding='utf-8')
if '<html lang="en-AU" class="no-js" data-private-page>' not in page:
    fail('matching-help.html: the html element must carry data-private-page')
if '<meta name="robots" content="noindex">' not in page:
    fail('matching-help.html: must be noindex while the pilot is off')
if re.search(r'<input[^>]*name="consent"[^>]*\bchecked\b', page):
    fail('matching-help.html: the consent box must start unticked')
if 'matching-config.js' not in page or 'matching.js' not in page:
    fail('matching-help.html: must load matching-config.js and matching.js')
for name in ('locality', 'first_name', 'email', 'state', 'budget'):
    if not re.search(rf'<label[^>]*for="{name}"', page):
        fail(f'matching-help.html: no visible <label for="{name}">')
for name in ('scope', 'service', 'mode', 'priorities'):
    if not re.search(rf'<fieldset[^>]*data-field="{name}"[^>]*>\s*<legend', page):
        fail(f'matching-help.html: the {name} group needs a <fieldset> with a <legend>')
for m in re.finditer(r'<(input|select)[^>]*name="([a-z_]+)"[^>]*>', page):
    tag = m.group(0)
    if 'aria-describedby="' not in tag:
        fail(f'matching-help.html: {m.group(2)} control is not tied to its error message')
if '<textarea' in page or 'type="file"' in page:
    fail('matching-help.html: no free text areas or uploads')
body = page[page.index('<main'):page.index('</main>')]   # the shared share-image alt in <head> is not this page's copy
for bad in ('perfect match', 'AI-powered', 'best clinician', 'clinically approved', 'No referral needed', 'free of charge', 'within 48 hours', 'within 24 hours'):
    if bad.lower() in body.lower():
        fail(f'matching-help.html: contains "{bad}"')

analytics = (ROOT / 'analytics.js').read_text(encoding='utf-8')
for ev in ('matching-cta-viewed', 'matching-cta-clicked', 'matching-form-started', 'matching-request-submitted'):
    if f"'{ev}': MATCHING" not in analytics:
        fail(f'analytics.js: {ev} is not declared')
if "autocapture: !privatePage &&" not in analytics or "disable_session_recording: privatePage ||" not in analytics:
    fail('analytics.js: a private page must switch autocapture and replay off')

for file, placements in (('index.html', ['homepage']), ('the-doctors.html', ['directory', 'no_results'])):
    html = (ROOT / file).read_text(encoding='utf-8')
    for p in placements:
        tags = re.findall(rf'<(?:div|a)[^>]*data-matching-cta="{p}"[^>]*>', html)
        if len(tags) != 1:
            fail(f'{file}: expected one data-matching-cta="{p}", found {len(tags)}')
        elif ' hidden' not in tags[0]:
            fail(f'{file}: the {p} call-to-action must be hidden by default')
    if 'Request matching help' not in html:
        fail(f'{file}: the call-to-action button copy is missing')
    if 'matching.js' not in html:
        fail(f'{file}: must load matching.js')

for f in fails:
    print('FAIL', f)
print('matching pilot checks pass' if not fails else f'{len(fails)} problem(s)')
sys.exit(1 if fails else 0)
