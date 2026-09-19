# The ADHDme ad

A twenty-second hand-drawn film, 16:9, 1920×1080, 24 fps, with its own score.
Everything is drawn in JavaScript on a Canvas 2D context; there are no photos,
no video, no stock assets and no external fonts.

Watch it at `out/adhdme-ad-final.mp4`. Open `adhdme-ad.html` in a browser to
scrub it frame by frame, or to hear the score (press play, then sound).

## What it says

One woman has been waiting for an ADHD assessment. The wait is drawn as a knot
of line above her head. The knot lets go, pulls straight, and divides into the
two coloured rules the landing page puts above *Get assessed by a GP.* and
*Work with a psychologist.* She stands up and walks. The far end of that line
is the coral dot from the logo, so the last thing the line does is finish the
mark on the end card.

Every word is the site's own copy, not new claims:

| In the film | From |
| --- | --- |
| "A year in a queue." / "A bill you could not plan for." | `index.html`, *The wait was never the care* |
| "The wait was never the care." | `index.html`, same section heading |
| "Get assessed by a GP." · "$299 initial · no referral needed" | `index.html`, *Two ways in* |
| "Work with a psychologist." · "Medicare rebates may apply" | `index.html`, *Two ways in* |
| "Not just focus." / "Life returned to you." | `index.html`, the hero, with the same yellow on the second line |

`adhdme.au` on the end card is the brand's domain, taken from the site's
contact address (`info@adhdme.au`). Point it somewhere else if the campaign
should land on a different URL — it is one string in `adhdme-ad.html`.

## The look

The palette in `brand.js` is read off `index.html` and `tailwind.config.js`,
not invented: yellow `#f1bc31` is the GP door, blue `#2c80c6` the psychology
door, coral `#ff4d2e` the logo dot, ink `#1a1c1c`, cream `#FAFAF7`.

Type is set, not lettered, in the site's own Plus Jakarta Sans at the hero's
setting (weight 800, letter-spacing −0.035em). The typeface is the brand; the
hand belongs to the drawing. The font is inlined as a data URL in `fonts.js`
so the film renders identically anywhere and the canvas is never tainted.

## Files

```
adhdme-ad.html   brief, beat sheet, performance and exposure tracks, timeline
figure.js        the woman: eleven authored keys and the drawing that rebuilds
                 her whole contour from each one
scenes.js        the room, the knot, the two rules, the end card's ground
brand.js         palette, type, the ADHDme lockup
score.js         twenty seconds of original Web Audio
fonts.js         Plus Jakarta Sans, inlined (SIL OFL 1.1)
study-poses.html every authored key on one sheet — look here first after a
                 change to a pose
core.js studio.js cels.js materials.js   copied from the skill, never edited
render.mjs package.json                  copied from the skill
```

## How the figure works

A pose is a small authored skeleton — hip, neck, skull centre, elbows, wrists,
knees, ankles, toes, plus four shape scalars for the torso bow, the chin tuck,
the gaze and the finger curl. `figureParts()` rebuilds the entire contour from
that skeleton every time, so a bent elbow is one continuous tapered outline with
a crease on the inside rather than two rotated capsules with grain laid over
them. The skeleton holds proportion and contact; the contour is what reaches the
screen, and it is drawn again for every exposed pose.

Poses are exposed through `exposureTrack`, so only a finite set of drawings is
ever produced: sixes while she is still, ones for the head lift and for leaving
the chair, twos elsewhere. Each exposed drawing is rasterised once into its own
canvas and reused for its whole hold, which keeps the ink identical through a
hold and makes the render fast.

Root travel during the walk is a separate linear track whose keys sit at the
same times as the pose keys, so the planted ankle moves backwards through the
pose by exactly as much as the root moves forward and the contact foot does not
slide.

## Rendering

Needs Node 22+, a Chrome or Chromium binary and `ffmpeg` on `PATH`.

```bash
npm i --no-audit --no-fund
node render.mjs adhdme-ad.html --grid 24          # the whole film on one sheet
node render.mjs adhdme-ad.html --strip 330,18     # consecutive frames over a contact
node render.mjs adhdme-ad.html --only 400         # one frame, full size
node render.mjs adhdme-ad.html                    # frames, score.wav, mp4, contact sheet
node render.mjs study-poses.html --only 0         # the pose sheet
```

Set `CHROME=/path/to/chrome` if it is not on `PATH`. Running as root needs a
launcher that adds `--no-sandbox`:

```sh
#!/bin/sh
exec /path/to/chromium --no-sandbox --disable-dev-shm-usage "$@"
```

`--grid`, `--strip` and `--only` are preview modes; only a full render writes
the MP4.

## Two things worth knowing before you edit

**The figure is drawn through a sprite, on purpose.** Drawing the character's
fills and then its thousands of short ink segments straight onto the main canvas
made Chromium rasterise a second copy of the head about 1100 units to the left
of the figure. The geometry, the transform and even a clip around the figure
were all verified correct — the stray pixels landed outside the clip, so they
came from the rasteriser, not from a draw. Rendering each drawing into its own
canvas and blitting it (the pattern `examples/sketchbook-bird.html` uses in the
skill) avoids it, and is faster besides. If you go back to drawing direct, check
the empty part of the frame during the walk.

**Aspect ratio is a composition decision, not a flag.** `--ar 9:16` will render,
but the staging — a figure on the right, a headline column on the left, two
rules running off the right edge — is built for 16:9. A vertical cut needs the
beats restaged, not just a different canvas.
