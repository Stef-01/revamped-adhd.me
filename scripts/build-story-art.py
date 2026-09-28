#!/usr/bin/env python3
"""Cut-paper collage illustrations for the journey on our-story.html.

Writes assets/story/01..05-*.svg. Every piece is paper: torn edges, a little grain, a soft lift
shadow, and the site's mascots. Colours are the site's own. Deterministic: same drawing every run.

    python3 scripts/build-story-art.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'story'
OUT.mkdir(parents=True, exist_ok=True)

INK, PAPER, PAGE = '#1a1c1c', '#fdfbf7', '#FAFAF7'
GOLD, BLUE, BLUE_D, GREEN, GREEN_D, PEACH, LILAC, CORAL = (
    '#f1bc31', '#cfe4f6', '#8fbde3', '#dbe9d3', '#9cc58f', '#fbd8cf', '#dad9eb', '#ff4d2e')
MASCOT_RED, MASCOT_GOLD, MASCOT_MINT, MASCOT_LILAC = '#d96b52', '#f1bc31', '#9be5b5', '#b9b3e6'
FONT = "'Plus Jakarta Sans', 'Helvetica Neue', Arial, sans-serif"

W, H = 640, 480


def defs(seed):
    return f'''<defs>
<filter id="torn" x="-6%" y="-6%" width="112%" height="112%"><feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="3" seed="{seed}"/><feDisplacementMap in="SourceGraphic" scale="8" xChannelSelector="R" yChannelSelector="G"/></filter>
<filter id="lift" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="5" stdDeviation="4" flood-color="{INK}" flood-opacity=".18"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="{seed}" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .1  0 0 0 0 .1  0 0 0 0 .1  0 0 0 .10 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<pattern id="half" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="1.7" fill="{INK}" opacity=".13"/></pattern>
</defs>'''


def svg(label, body, seed):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">'
            f'{defs(seed)}{body}</svg>')


def paper(shape, fill, rot=0, cx=W / 2, cy=H / 2, grain=True, half=False):
    """A torn piece of paper: the shape, torn, lifted, with grain and optional halftone."""
    extra = ''
    if half:
        extra += shape.replace('FILL', 'url(#half)')
    if grain:
        extra += shape.replace('FILL', '#fff').replace('<', '<', 1).replace('/>', ' filter="url(#grain)"/>', 1)
    return (f'<g filter="url(#lift)" transform="rotate({rot} {cx} {cy})"><g filter="url(#torn)">'
            f'{shape.replace("FILL", fill)}{extra}</g></g>')


def rect(x, y, w, h, r=10):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="FILL"/>'


def circle(cx, cy, r):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="FILL"/>'


def path(d):
    return f'<path d="{d}" fill="FILL"/>'


BLOB = 'M50 16 C68 16, 78 28, 76 50 C74 64, 82 78, 76 90 C68 98, 32 98, 24 90 C18 78, 26 64, 24 50 C22 28, 32 16, 50 16 Z'


def mascot(x, y, s, fill, mouth='smile', coat=False, look=0):
    face = (f'<circle cx="{43 + look}" cy="46" r="3.5" fill="{INK}"/><circle cx="{57 + look}" cy="46" r="3.5" fill="{INK}"/>'
            f'<circle cx="{44 + look}" cy="44.5" r="1.3" fill="#fff"/><circle cx="{58 + look}" cy="44.5" r="1.3" fill="#fff"/>')
    face += {
        'smile': f'<path d="M{45 + look} 56 Q{50 + look} 62 {55 + look} 56" fill="none" stroke="{INK}" stroke-linecap="round" stroke-width="3"/>',
        'open': f'<path d="M{44 + look} 55 Q{50 + look} 65 {56 + look} 55 Z" fill="{INK}"/>',
        'o': f'<ellipse cx="{50 + look}" cy="58" rx="3.2" ry="4" fill="{INK}"/>',
        'flat': f'<path d="M{45 + look} 58 H{55 + look}" stroke="{INK}" stroke-linecap="round" stroke-width="3"/>',
    }[mouth]
    wear = ''
    if coat:
        wear = (f'<path d="M26 62 C30 58 36 56 40 56 L50 72 L60 56 C64 56 70 58 74 62 C76 74 80 84 76 90 C68 98 32 98 24 90 C20 84 24 74 26 62 Z" '
                f'fill="#fff" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
                f'<path d="M50 72 V95" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>'
                f'<path d="M41 58 C38 70 43 80 50 80 C57 80 62 70 59 58" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
                f'<circle cx="50" cy="83" r="3.4" fill="#cfd3d6" stroke="{INK}" stroke-width="2"/>')
    return (f'<g transform="translate({x} {y}) scale({s})"><ellipse cx="50" cy="97" rx="30" ry="4.5" fill="#000" opacity=".12"/>'
            f'<path d="{BLOB}" fill="{fill}" stroke="{INK}" stroke-width="4.5" stroke-linejoin="round"/>{wear}{face}</g>')


def star(x, y, s, fill):
    return (f'<path transform="translate({x} {y}) scale({s})" d="M0 -14 L3 -3 L14 0 L3 3 L0 14 L-3 3 L-14 0 L-3 -3 Z" '
            f'fill="{fill}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')


def text(x, y, s, size, weight=800, fill=INK, anchor='middle', rot=0, spacing=0):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}" transform="rotate({rot} {x} {y})">{s}</text>')


def tape(x, y, w, rot):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="22" fill="#fff" opacity=".62" '
            f'transform="rotate({rot} {x + w / 2} {y + 11})" filter="url(#torn)"/>')


# ------------------------------------------------------------------ 01 two trainees
b = paper(rect(70, 60, 500, 330, 18), BLUE, rot=-2.5)
b += paper(circle(470, 140, 52), GOLD, half=True)
b += paper(path('M60 330 C160 280 260 300 330 320 C420 345 500 300 590 320 L590 420 L60 420 Z'), GREEN, rot=1)
b += paper(path('M120 360 C200 330 300 350 380 365 L380 420 L120 420 Z'), GREEN_D, grain=False)
b += mascot(160, 170, 2.2, MASCOT_RED, 'smile', coat=True, look=2)
b += mascot(330, 180, 2.1, MASCOT_GOLD, 'open', coat=True, look=-2)
b += tape(250, 44, 120, -4)
b += star(110, 110, 1.3, GOLD) + star(560, 250, 1, '#f2a7c8') + star(420, 70, .8, '#fff')
(OUT / '01-trainees.svg').write_text(svg('Two cheerful characters in white coats with stethoscopes', b, 3))

# ------------------------------------------------------------------ 02 two routes
b = paper(rect(60, 70, 520, 320, 22), PAPER, rot=1.5)
# the fork: one road splitting in two
b += (f'<path d="M320 420 C320 360 318 330 316 300 C300 250 220 230 170 190" fill="none" stroke="{CORAL}" stroke-width="16" stroke-linecap="round" opacity=".9"/>'
      f'<path d="M316 300 C340 250 420 230 470 190" fill="none" stroke="{CORAL}" stroke-width="16" stroke-linecap="round" opacity=".9"/>'
      f'<path d="M320 420 C320 360 318 330 316 300 C300 250 220 230 170 190 M316 300 C340 250 420 230 470 190" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="10 12" stroke-linecap="round"/>')
# left: without medication — exercise, a dumbbell
b += paper(circle(150, 150, 70), GREEN, half=True)
b += (f'<g transform="rotate(-20 150 150)">'
      f'<rect x="112" y="143" width="76" height="14" rx="6" fill="#cfd3d6" stroke="{INK}" stroke-width="3.5"/>'
      f'<rect x="96" y="118" width="20" height="64" rx="6" fill="{CORAL}" stroke="{INK}" stroke-width="4"/>'
      f'<rect x="184" y="118" width="20" height="64" rx="6" fill="{CORAL}" stroke="{INK}" stroke-width="4"/>'
      f'<rect x="82" y="128" width="16" height="44" rx="5" fill="{GOLD}" stroke="{INK}" stroke-width="4"/>'
      f'<rect x="202" y="128" width="16" height="44" rx="5" fill="{GOLD}" stroke="{INK}" stroke-width="4"/>'
      f'</g>'
      f'<path d="M92 92 l-10 -8 M104 84 l-4 -12 M80 106 l-13 -3" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
# right: medication — a pill bottle
b += paper(circle(490, 150, 70), LILAC, half=True)
b += (f'<rect x="462" y="104" width="56" height="80" rx="10" fill="#fff" stroke="{INK}" stroke-width="4"/>'
      f'<rect x="456" y="90" width="68" height="20" rx="6" fill="{CORAL}" stroke="{INK}" stroke-width="4"/>'
      f'<rect x="470" y="128" width="40" height="30" rx="4" fill="{PEACH}" stroke="{INK}" stroke-width="2.5"/>'
      + text(490, 150, 'Rx', 16) +
      f'<rect x="530" y="160" width="26" height="12" rx="6" fill="{GOLD}" stroke="{INK}" stroke-width="3" transform="rotate(-25 543 166)"/>')
b += mascot(265, 300, 1.1, MASCOT_MINT, 'o', look=0)
b += tape(90, 58, 100, -12) + tape(470, 372, 100, 10)
b += star(300, 110, 1.1, GOLD)
(OUT / '02-two-routes.svg').write_text(svg('A road splitting two ways: a dumbbell on one side, a pill bottle on the other', b, 7))

# ------------------------------------------------------------------ 03 script, no plan
b = paper(rect(90, 90, 460, 300, 16), PEACH, rot=-1.5)
# the prescription slip
slip = (rect(150, 60, 230, 300, 8))
b += paper(slip, '#fff', rot=-6, cx=265, cy=210, grain=True)
b += (f'<g transform="rotate(-6 265 210)"><rect x="150" y="60" width="230" height="44" fill="{BLUE_D}"/>'
      + text(265, 90, 'PRESCRIPTION', 15, 800, '#fff', spacing=3) +
      text(186, 150, 'Rx', 38, 800) +
      ''.join(f'<rect x="178" y="{176 + i * 26}" width="{170 - i * 22}" height="9" rx="4.5" fill="#e6dfd1"/>' for i in range(5)) +
      f'<path d="M190 330 C215 318 235 338 260 322 S300 330 320 318" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/></g>')
# the plan: an empty checklist
b += paper(rect(390, 150, 150, 170, 8), GOLD, rot=5, cx=465, cy=235)
b += (f'<g transform="rotate(5 465 235)">' + text(465, 185, 'The plan', 17) +
      ''.join(f'<rect x="410" y="{205 + i * 32}" width="18" height="18" rx="4" fill="#fff" stroke="{INK}" stroke-width="3"/>'
              f'<rect x="438" y="{210 + i * 32}" width="80" height="8" rx="4" fill="{INK}" opacity=".12"/>' for i in range(3)) + '</g>')
b += mascot(470, 318, 1.15, MASCOT_LILAC, 'flat', look=-3)
b += (f'<g transform="translate(560 300)"><circle r="24" fill="#fff" stroke="{INK}" stroke-width="3.5"/>' + text(0, 11, '?', 32, 800) + '</g>')
(OUT / '03-script-no-plan.svg').write_text(svg('A prescription slip, and beside it an empty checklist called the plan', b, 11))

# ------------------------------------------------------------------ 04 there has to be more
b = paper(circle(320, 230, 190), LILAC, half=True)
rays = ''.join(
    f'<path d="M{320 + 95 * c:.1f} {180 + 95 * s:.1f} L{320 + 135 * c:.1f} {180 + 135 * s:.1f}" stroke="{GOLD}" stroke-width="9" stroke-linecap="round"/>'
    for c, s in [(-1, 0), (-.7, -.7), (0, -1), (.7, -.7), (1, 0), (-.87, .5), (.87, .5)])
b += rays
b += (f'<g filter="url(#lift)"><path d="M320 100 C270 100 238 138 240 182 C242 214 262 232 276 250 C284 262 286 274 286 286 H354 C354 274 356 262 364 250 C378 232 398 214 400 182 C402 138 370 100 320 100 Z" fill="{GOLD}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
      f'<path d="M320 100 C270 100 238 138 240 182 C242 214 262 232 276 250 C284 262 286 274 286 286 H354 C354 274 356 262 364 250 C378 232 398 214 400 182 C402 138 370 100 320 100 Z" fill="url(#half)"/>'
      f'<rect x="290" y="286" width="60" height="16" rx="5" fill="#fff" stroke="{INK}" stroke-width="4"/>'
      f'<rect x="294" y="302" width="52" height="16" rx="5" fill="#cfd3d6" stroke="{INK}" stroke-width="4"/>'
      f'<path d="M300 318 H340 L332 332 H308 Z" fill="{INK}"/>'
      f'<path d="M296 196 C300 176 312 166 320 186 C328 166 340 176 344 196" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/></g>')
b += mascot(120, 290, 1.2, MASCOT_RED, 'open', look=3)
b += f'<path d="M205 330 C230 300 240 280 262 262" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
b += star(470, 110, 1.4, '#fff') + star(520, 330, 1, GOLD) + star(150, 130, .9, '#f2a7c8')
(OUT / '04-more-to-it.svg').write_text(svg('A character pointing up at a glowing lightbulb', b, 5))

# ------------------------------------------------------------------ 05 the team
b = paper(path('M60 250 C140 120 500 110 590 250 L600 420 L50 420 Z'), GREEN, rot=0, half=False)
b += paper(path('M60 250 C140 120 500 110 590 250'), GREEN, grain=False)
# a gold ribbon joining them
b += f'<path d="M80 330 C180 300 240 360 320 330 S460 300 560 330" fill="none" stroke="{GOLD}" stroke-width="14" stroke-linecap="round"/>'
members = [
    (70, 250, MASCOT_RED, 'stethoscope'),
    (175, 225, MASCOT_GOLD, 'bubble'),
    (280, 215, MASCOT_MINT, 'calendar'),
    (385, 225, MASCOT_LILAC, 'apple'),
    (490, 250, '#f2a7c8', 'watch'),
]
props = {
    'stethoscope': f'<path d="M-12 -14 C-14 4 -6 12 0 12 C6 12 14 4 12 -14" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/><circle cx="0" cy="16" r="5" fill="#cfd3d6" stroke="{INK}" stroke-width="2.5"/>',
    'bubble': f'<path d="M-18 -14 H18 A6 6 0 0 1 24 -8 V6 A6 6 0 0 1 18 12 H-2 L-10 20 V12 H-18 A6 6 0 0 1 -24 6 V-8 A6 6 0 0 1 -18 -14 Z" fill="#fff" stroke="{INK}" stroke-width="3"/><circle cx="-8" cy="-1" r="2.5" fill="{INK}"/><circle cx="0" cy="-1" r="2.5" fill="{INK}"/><circle cx="8" cy="-1" r="2.5" fill="{INK}"/>',
    'calendar': f'<rect x="-18" y="-14" width="36" height="32" rx="5" fill="#fff" stroke="{INK}" stroke-width="3"/><rect x="-18" y="-14" width="36" height="10" rx="4" fill="{CORAL}" stroke="{INK}" stroke-width="3"/><path d="M-8 6 L-2 12 L10 0" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>',
    'apple': f'<path d="M0 -6 C-18 -16 -26 4 -16 16 C-10 22 -4 20 0 18 C4 20 10 22 16 16 C26 4 18 -16 0 -6 Z" fill="{CORAL}" stroke="{INK}" stroke-width="3"/><path d="M0 -6 C0 -12 4 -16 8 -18" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>',
    'watch': f'<circle cx="0" cy="2" r="17" fill="#fff" stroke="{INK}" stroke-width="3"/><rect x="-5" y="-22" width="10" height="7" rx="2" fill="{INK}"/><path d="M0 2 V-8 M0 2 L7 6" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>',
}
for x, y, fill, prop in members:
    b += mascot(x, y, 0.95, fill, 'smile')
    b += f'<g transform="translate({x + 48} {y - 18})">{props[prop]}</g>'
b += star(320, 120, 1.4, GOLD) + star(150, 150, .9, '#fff') + star(500, 150, 1, '#fff')
(OUT / '05-the-team.svg').write_text(svg('Five characters in a row, each holding a tool: a stethoscope, a speech bubble, a calendar, an apple and a stopwatch', b, 9))

print('\n'.join(f'{p.name} {p.stat().st_size}' for p in sorted(OUT.glob('*.svg'))))
