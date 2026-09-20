#!/usr/bin/env python3
"""Generate the newsletter cover image, assets/brand/newsletter-cover.png.

    python3 scripts/build-newsletter-cover.py

Why this exists rather than reusing assets/brand/og.png: beehiiv treats a post cover very
differently from a link preview. It darkens the image with a scrim, centre-crops it from
1200x630 to whatever the surface needs (the feed card is about 1.25:1), and lays its own
date, title and author over the lower left. og.png is a good social card and survives none
of that — the scrim turns brand amber to olive, the crop cuts "AD" off "ADHD", and its
headline ends up fighting beehiiv's title for the same space.

So this cover is built for those three facts:

  * Ink ground, not amber. The scrim is what muddied the amber; starting dark means the
    scrim barely changes the image and beehiiv's white text has something to sit on.
  * No words of its own. beehiiv supplies the title. Anything written here competes with it.
  * Everything inside the centre, nothing below the midline. Content survives a square crop
    (x 285-915) and stays clear of the overlay.

The wordmark is lifted from og.png rather than re-typeset, the same trick masthead.png uses:
it guarantees the real lockup, letterspacing and coral dot without needing the font file.
"""
import pathlib

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'assets' / 'brand' / 'og.png'
OUT = ROOT / 'assets' / 'brand' / 'newsletter-cover.png'

W, H = 1200, 630
INK = (26, 28, 28)        # #1a1c1c  the site's ink
AMBER = (241, 188, 49)    # #f1bc31  brand amber
CREAM = (250, 250, 247)   # #FAFAF7  the site's page ground
CORAL = (253, 93, 46)     # #fd5d2e  the dot in the wordmark

WORDMARK_BOX = (72, 75, 190, 149)   # where the lockup sits in og.png
SCALE = 2.6                          # 118px wide there -> ~307px here
MARK_CENTRE_Y = 210                  # upper-middle, clear of beehiiv's overlay
RULE_W, RULE_H, RULE_Y = 168, 7, 340


def wordmark_layers(src):
    """(glyph alpha, dot alpha) for the lockup, pulled off og.png's amber ground.

    Coverage rather than a hard threshold, so the edges stay smooth when recoloured: how far
    each pixel travelled from amber towards ink gives the glyph alpha directly.
    """
    a = np.asarray(src.crop(WORDMARK_BOX).convert('RGB'), dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    amber_l = 0.2126 * AMBER[0] + 0.7152 * AMBER[1] + 0.0722 * AMBER[2]
    ink_l = 0.2126 * INK[0] + 0.7152 * INK[1] + 0.0722 * INK[2]

    dot = np.clip((r - g - 60) / 90, 0, 1) * (b < 160)        # the one warm-red mark
    glyph = np.clip((amber_l - luma) / (amber_l - ink_l), 0, 1)
    glyph = np.clip(glyph - dot, 0, 1)                         # the dot is not a letter
    return glyph, dot


def paste(canvas, alpha, colour, box):
    layer = Image.new('RGBA', canvas.size, colour + (0,))
    mask = Image.fromarray((alpha * 255).astype(np.uint8), 'L').resize(
        (box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
    full = Image.new('L', canvas.size, 0)
    full.paste(mask, box[:2])
    layer.putalpha(full)
    return Image.alpha_composite(canvas, layer)


def build():
    glyph, dot = wordmark_layers(Image.open(SOURCE))
    h, w = glyph.shape
    mw, mh = round(w * SCALE), round(h * SCALE)
    box = ((W - mw) // 2, MARK_CENTRE_Y - mh // 2)
    box = (box[0], box[1], box[0] + mw, box[1] + mh)

    canvas = Image.new('RGBA', (W, H), INK + (255,))
    canvas = paste(canvas, glyph, CREAM, box)
    canvas = paste(canvas, dot, CORAL, box)

    # One amber mark, so the brand colour is present without the scrim having anything to muddy.
    rule = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    Image.Image.paste(rule, Image.new('RGBA', (RULE_W, RULE_H), AMBER + (255,)),
                      ((W - RULE_W) // 2, RULE_Y))
    canvas = Image.alpha_composite(canvas, rule)

    canvas.convert('RGB').save(OUT, 'PNG', optimize=True)
    print(f'wrote {OUT.relative_to(ROOT)}  {W}x{H}  {OUT.stat().st_size // 1024} KB')


if __name__ == '__main__':
    build()
