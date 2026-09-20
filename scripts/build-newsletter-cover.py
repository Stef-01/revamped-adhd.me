#!/usr/bin/env python3
"""Generate the newsletter cover image, assets/brand/newsletter-cover.png.

    python3 scripts/build-newsletter-cover.py

Why this exists rather than reusing assets/brand/og.png: beehiiv treats a post cover very
differently from a link preview. It lays a scrim over the image, centre-crops it from
1200x630 to whatever the surface needs (the feed card is about 1.25:1), and writes its own
date, title and author over the lower left. og.png is a good social card and survives none
of that — the crop cuts "AD" off "ADHD", and its headline ends up fighting beehiiv's title
for the same space.

The scrim is the part worth knowing, because it is stronger than it looks. Measured off a
rendered card: brand amber #f1bc31 comes back as #443817, which is a 65% black blend. That
is a hard ceiling on the whole image — nothing in a cover can render brighter than about
35% of its own value, so cream #FAFAF7 arrives as mid-grey #575757 and amber as a dull
bronze. A logo on a flat ground therefore cannot be made to look crisp here by picking
better colours; it will always read as washed out. beehiiv's own title is drawn on top of
the scrim, so it stays pure white and is the only bright thing on the card.

A 65% scrim is the standard treatment for photography, so that is what this uses: the
clinic photograph already on the site, warm and on-brand, graded slightly towards the
palette's amber. The lower left is kept quiet for the overlay, and there is no text in the
image at all, because beehiiv supplies the only words the card needs.
"""
import pathlib

from PIL import Image, ImageEnhance

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'assets' / 'clinic-bg.jpg'
OUT = ROOT / 'assets' / 'brand' / 'newsletter-cover.jpg'  # a photograph; JPEG, not PNG

W, H = 1200, 630
# Framing: hold the group and the window light, and leave the lower left — where beehiiv
# writes the date, title and author — on the quiet floor and planter rather than on a face.
FOCUS_X = 0.54
WARMTH = 1.06      # a nudge towards the palette's amber; the photo is already warm
CONTRAST = 1.04    # the scrim flattens, so give it a little back first


def build():
    src = Image.open(SOURCE).convert('RGB')
    sw, sh = src.size

    scale = max(W / sw, H / sh)
    rw, rh = round(sw * scale), round(sh * scale)
    img = src.resize((rw, rh), Image.LANCZOS)

    left = min(max(0, round(rw * FOCUS_X - W / 2)), rw - W)
    top = min(max(0, round((rh - H) * 0.5)), rh - H)
    img = img.crop((left, top, left + W, top + H))

    img = ImageEnhance.Color(img).enhance(WARMTH)
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)

    img.save(OUT, 'JPEG', quality=86, optimize=True, progressive=True)
    print(f'wrote {OUT.relative_to(ROOT)}  {W}x{H}  {OUT.stat().st_size // 1024} KB'
          f'   (from {SOURCE.name} {sw}x{sh})')


if __name__ == '__main__':
    build()
