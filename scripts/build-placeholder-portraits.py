#!/usr/bin/env python3
"""Make the six portrait files for a clinician who has not yet supplied a photograph.

    python3 scripts/build-placeholder-portraits.py <id> [<id> ...]

Writes assets/clinicians/<id>.jpg, -640.jpg, -320.jpg and the WebP equivalents: a square illustration
in the blog covers' style (a character on a tinted, dotted ground), so build-profiles.py can run and
the profile is honest about what it is. Replace the six files with the real portrait when it arrives;
nothing else changes. Needs Pillow and the Playwright Chromium the repo's screenshots use.
"""
import importlib.util
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'clinicians'
spec = importlib.util.spec_from_file_location('blog', ROOT / 'scripts' / 'build-blog.py')
blog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blog)

TINTS = ['#f6ecce', '#d0e4de', '#dad9eb', '#fbd8cf', '#dcedfa', '#f3f1ea']
FILLS = ['#d96b52', '#f5cf6d', '#8fbfe3', '#9be5b5', '#f2a7c8']
SIZES = [('', 1000), ('-640', 640), ('-320', 320)]


def svg(i):
    tint, fill = TINTS[i % len(TINTS)], FILLS[i % len(FILLS)]
    body = (blog.blob(500, 560, 6.2, fill=fill, face='calm')
            + blog.sparkle(190, 210, 2.2) + blog.sparkle(800, 260, 1.6, '#f2a7c8') + blog.sparkle(770, 800, 1.4, '#9be5b5'))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="1000" height="1000">'
            f'<defs><pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="2.5" cy="2.5" r="2.5" fill="{blog.INK}" opacity=".08"/></pattern></defs>'
            f'<rect width="1000" height="1000" fill="{tint}"/><rect width="1000" height="1000" fill="url(#dots)"/>{body}</svg>')


RASTER = """
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const [svgPath, pngPath] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }).catch(async () => chromium.launch());
  const p = await b.newPage({ viewport: { width: 1000, height: 1000 } });
  await p.setContent('<html><body style="margin:0">' + require('fs').readFileSync(svgPath, 'utf8') + '</body></html>');
  await p.screenshot({ path: pngPath, clip: { x: 0, y: 0, width: 1000, height: 1000 } });
  await b.close();
})();
"""


def main(ids):
    if not ids:
        raise SystemExit(__doc__)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / 'raster.js').write_text(RASTER)
        for i, cid in enumerate(ids):
            (tmp / f'{cid}.svg').write_text(svg(i))
            subprocess.run(['node', str(tmp / 'raster.js'), str(tmp / f'{cid}.svg'), str(tmp / f'{cid}.png')], check=True)
            full = Image.open(tmp / f'{cid}.png').convert('RGB')
            for suffix, px in SIZES:
                im = full.resize((px, px), Image.LANCZOS)
                im.save(OUT / f'{cid}{suffix}.jpg', 'JPEG', quality=86, optimize=True, progressive=True)
                im.save(OUT / f'{cid}{suffix}.webp', 'WEBP', quality=84, method=6)
            print('wrote', cid)


if __name__ == '__main__':
    main(sys.argv[1:])
