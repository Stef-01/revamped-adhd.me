# Sketchy-method visual layer: illustration brief

The discipline tracks in `academy.html` carry a visual-mnemonic layer modelled on the Sketchy method: one persistent illustrated world per discipline, facts encoded as symbols placed inside it, revealed one at a time, then revisited in a symbol explorer before the knowledge checks.

**All artwork in the build is placeholder geometry.** The interaction is finished and tested. An illustrator, or an image tool, replaces the art without touching any logic.

## Files

| File | Role |
| --- | --- |
| `scripts/sketchy_scenes.py` | Single source of truth: the shared icon vocabulary and the four scenes (symbol art, position, fact, recap, encoding cues). |
| `scripts/build-academy-tracks.py` | Renders scenes and explorers into `academy.html`. Run it after any change. |
| `assets/academy/sketchy.js` | Progressive reveal, keyboard control, reduce-motion toggle, explorer. Never references artwork. |
| `assets/academy/sketchy.css` | Styles, using the workbook’s own design tokens. |

```bash
python3 scripts/build-academy-tracks.py
```

## How to drop in final art

1. Each symbol is an SVG `<symbol>` with a `0 0 100 100` viewBox. In `sketchy_scenes.py`, replace the `art` string of a symbol with the final vector markup drawn to that viewBox. Keep the `id`.
2. Each world backdrop is drawn at `800 x 450`. Replace the scene’s `backdrop` string. Symbol positions (`x`, `y`, `size`) are in that same coordinate space; adjust them if the furniture moves.
3. Use `currentColor` for ink and `var(--sk-accent)` for the scene’s one accent colour, so the palette cap holds. `var(--sk-b1)` and `var(--sk-b2)` are the two other base colours.
4. Rebuild. Every symbol is defined once in a hidden sprite and referenced with `<use>` by both the scene and the explorer, so one edit updates both.
5. In the generated HTML each symbol is preceded by a `<!-- SYMBOL: … -->` comment stating the fact it encodes.

## Rules the art must keep

- **One world per discipline.** Everything nests in the same scene. No new image per fact.
- **At most 8 symbols per scene.** The builder refuses more. If a track needs more, add a second sub-scene in the same world.
- **At least two encoding cues per symbol** (colour, position, sound-alike pun, an action that shows the mechanism, or proximity to a related symbol). The cues are listed below; final art must still deliver them. The builder enforces the minimum.
- **Three base colours plus one accent per scene.** The shared vocabulary below keeps its own fixed colours in every scene; that is deliberate, so learners recognise it anywhere.
- **No decoration that does not encode a fact.**

## Shared vocabulary (draw once, identical in every scene)

| Symbol id | Means | Placeholder |
| --- | --- | --- |
| `sk-stamp-strong` | Guideline: strong recommendation | Solid dark stamp with a tick |
| `sk-stamp-weak` | Guideline: conditional recommendation | Dashed outline stamp with a dashed tick |
| `sk-shield-high` | Evidence certainty: high | Gold shield, letter H |
| `sk-shield-mod` | Evidence certainty: moderate | Silver shield, letter M |
| `sk-shield-low` | Evidence certainty: low | Bronze shield, letter L |
| `sk-shield-vlow` | Evidence certainty: very low | Grey dashed shield, letters VL |
| `sk-myth` | Myth-buster | The coral mascot, frowning, holding up a red “no” sign |
| `sk-signpost` | Referral pathway | Two-armed signpost with an arrow |

The myth-buster is the same mascot used across the Learn page illustrations, so it is already familiar to learners.

## Occupational therapy: The adaptation workshop

Scene: A room being modified for someone with ADHD: a workbench at the left, a wall with a schedule and a clock, a door with a hook at the right.

Palette: base `#f6ecce`, `#d9c9a3`, `#1c1917`; accent `#2f8f6b`. Runtime: about 5 minutes including the explorer.

| # | Symbol id | Must encode | Encoding cues to preserve | Badge | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | `sk-ot1` | A police cap resting on a tape measure marked plus two: the COPM, where a change of two or more points is clinically meaningful. | sound-alike pun (COP + Measure); position: on the workbench, where work starts | none | Module 1, lesson 1 |
| 2 | `sk-ot2` | A wall schedule where the gaps between blocks glow: breakdowns cluster at transitions between activities. | colour: accent marks the gaps, not the blocks; position: on the wall, the overview of the day | none | Module 1, lesson 2 |
| 3 | `sk-ot3` | An analogue clock with a shaded wedge of remaining time: make time visible where it is lost. | action: the wedge visibly shrinks; position: high on the wall, always in sight | none | Module 2, lesson 1 |
| 4 | `sk-ot4` | Keys hanging on a hook right beside the door: the cue lives at the point of performance, and each item has one home. | position: beside the door, the point of performance; proximity: next to the referral signpost, both are about leaving | none | Module 2, lesson 2 |
| 5 | `sk-ot5` | A chicken coop holding four eggs lettered G, P, D and C: the CO-OP approach, Goal, Plan, Do, Check, where the person hatches their own strategy. | sound-alike pun (coop = CO-OP); action: the person hatches the plan, not the therapist | Evidence certainty: low | Module 2, lesson 3 |
| 6 | `sk-ot6` | A single pair of headphones on the bench beside a tally mark: trial one sensory adjustment at a time and measure it. | action: one item, one tally, a single trial; badge: grey shield for very thin evidence | Evidence certainty: very low | Module 3, lesson 1 |
| 7 | `sk-signpost` | The referral signpost standing at the doorway: mood, risk, sleep and eating concerns leave this room for the GP, a psychologist or a dietitian. | recurring symbol: referral signpost; position: at the exit | none | Module 4, lesson 3 |
| 8 | `sk-myth` | The myth-buster crossing out the word lazy: a missed routine is an executive-function problem, not a motivation problem. | recurring symbol: myth-buster; position: on the workbench, where the blame usually lands | none | Pitfall |

## Exercise physiology: The evidence gym

Scene: A gym floor with an entrance desk at the left, then three stations left to right: a running track, a yoga mat and a boxing bag, each with a gauge above it.

Palette: base `#e8eef3`, `#b9c7d3`, `#1c1917`; accent `#d96b52`. Runtime: about 5 minutes including the explorer.

| # | Symbol id | Must encode | Encoding cues to preserve | Badge | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | `sk-ep1` | A clipboard at the entrance with a pill ticked and an energy can crossed out: screen every client, list their medicines, and drop the pre-workout. | position: at the entrance, before any station; colour: accent cross on the can | none | Module 1, lesson 1 |
| 2 | `sk-ep2` | A runner beneath a gauge pointing to the middle, beside an hourglass: twenty to thirty minutes of aerobic work gives a small to moderate lift that lasts about an hour. | action: the gauge needle shows effect size; proximity: hourglass beside it shows the effect is short | Evidence certainty: low | Module 2, lesson 1 |
| 3 | `sk-ep3` | A seated figure on a mat under a gauge pointing low: mind-body exercise helps a little, no more than other active programmes. | action: gauge needle points low; position: middle station, middling support | Evidence certainty: low | Module 2, lesson 2 |
| 4 | `sk-ep4` | A hanging bag under a gauge with a question mark instead of a needle: coordinative exercise has too few studies to call. | colour: gauge has no accent, because there is no reading; position: far station, furthest from evidence | Evidence certainty: very low | Module 2, lesson 2 |
| 5 | `sk-ep5` | A speech bubble sitting on top of a crossed-out heart-rate reading: on a stimulant, prescribe intensity by talk test and perceived exertion, not heart rate alone. | action: the bubble literally overrides the number; colour: accent strike through the reading | none | Module 1, lesson 2 |
| 6 | `sk-ep6` | A pair of sneakers beside a calendar showing one cross and never two in a row: train with a partner at a fixed time, and never miss twice. | proximity: two shoes means two people; action: a single cross, never a second | none | Module 3, lessons 2 and 3 |
| 7 | `sk-signpost` | The referral signpost with a heart on it: chest pain, fainting or sustained palpitations mean stop the session and refer for medical review. | recurring symbol: referral signpost; position: by the exit, the way out of the session | none | Module 1, lesson 3 |
| 8 | `sk-myth` | The myth-buster crossing out a pill swapped for a dumbbell: exercise is a modest, short-acting addition, not a replacement for medication. | recurring symbol: myth-buster; position: at the front desk, where the question gets asked | none | Pitfall |

## Psychology: The clinic reception and triage desk

Scene: A clinic reception: a desk at the left, filing drawers behind it, a floor timeline running across the room, and a branching signpost at the right leading to treatment.

Palette: base `#ecebf5`, `#c9c6e0`, `#1c1917`; accent `#5b54c7`. Runtime: about 5 minutes including the explorer.

| # | Symbol id | Must encode | Encoding cues to preserve | Badge | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | `sk-psy1` | A stage microphone on the reception desk with a speech bubble of examples: the DIVA-5 structured interview, where every criterion needs a real example. | sound-alike pun (diva = DIVA-5); position: on the desk, the first thing a client meets | none | Module 1, lesson 1 |
| 2 | `sk-psy2` | A filing cabinet with a school report poking out of one drawer and another drawer empty but still labelled: seek collateral, and know that missing records do not rule ADHD out. | proximity: the full and the empty drawer sit together; colour: accent on the report that exists | none | Module 1, lesson 2 |
| 3 | `sk-psy3` | Two lines on the floor: one solid and continuous, one in separate humps. ADHD is lifelong and trait-like; mood disorders come in episodes. | action: one line runs unbroken, the other rises and falls; position: along the floor, the path through a life | none | Module 1, lesson 3 |
| 4 | `sk-psy4` | A signpost with three arms for adults, teens and children, each carrying a recommendation stamp: ADHD-specific cognitive behavioural therapy adds benefit for adults on top of medication, and the recommendation differs by age group. | position: the fork between assessment and treatment; badge: recommendation stamp on each arm | Guideline: conditional recommendation | Module 2, lesson 1 |
| 5 | `sk-psy5` | A single calendar clipped to a single list: the core skill is one calendar and one task list, checked at the same time each day. | proximity: the two are clipped together as one system; colour: accent on the single shared clip | none | Module 2, lesson 2 |
| 6 | `sk-psy6` | A small storm cloud raining on a heart that holds an umbrella: emotional dysregulation is common in adult ADHD though absent from the criteria, and it can be worked on. | action: the storm passes quickly; the umbrella is the skill; colour: accent umbrella | Evidence certainty: moderate | Module 3, lesson 1 |
| 7 | `sk-signpost` | The referral signpost pointing out of the clinic: medication questions go to the prescriber, and any risk goes through your risk pathway and the GP. | recurring symbol: referral signpost; position: at the way out of the clinic | none | Module 4, lessons 1 and 3 |
| 8 | `sk-myth` | The myth-buster crossing out a questionnaire score: a high rating-scale score means assess properly, not that the diagnosis is made. | recurring symbol: myth-buster; position: at reception, where the score arrives first | none | Pitfall |

## Nutrition: The kitchen and pantry

Scene: A kitchen: a bench along the back with a balance scale at its centre, two plates as separate stations on the bench, a wall clock, and a bathroom scale by the door at the right.

Palette: base `#eef3e6`, `#c7d3b3`, `#1c1917`; accent `#e0a915`. Runtime: about 5 minutes including the explorer.

| # | Symbol id | Must encode | Encoding cues to preserve | Badge | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | `sk-nut1` | A balance scale with a small fish rising on one side and a large pill weighing down the other: omega-3 has at best a small effect, far below medication. | action: the scale physically tips, showing the size difference; position: centre of the bench, the centre of the argument | Evidence certainty: low | Module 3, lesson 1 |
| 2 | `sk-nut2` | A breakfast plate placed to the left of a pill bottle under a rising sun: eat a proper breakfast before the morning dose takes effect. | position: the plate comes before the bottle, left to right; colour: accent sunrise marks the time of day | none | Module 2, lesson 1 |
| 3 | `sk-nut3` | A wall clock whose hand is a fork, with an alarm bell on top: when hunger cues are absent, eat by the clock. | wordplay made visual: the fork is the clock hand; position: on the wall above the bench | none | Module 2, lesson 2 |
| 4 | `sk-nut4` | A plate divided into several different foods, sitting at its own station: regular, varied, adequate eating is the priority, and any link between eating pattern and ADHD is observational. | position: its own station on the left of the bench; colour: accent segments show variety | Evidence certainty: very low | Module 2, lesson 3 |
| 5 | `sk-nut5` | A plain single-colour plate with a sugar cube on it, at the opposite station: a less varied pattern is only an observational association, and sugar has not been shown to cause ADHD. | position: the opposite station from the varied plate; colour: one flat colour, no accent | Evidence certainty: very low | Module 3, lesson 2 |
| 6 | `sk-nut6` | A bathroom scale by the door flying a small flag marked minus five per cent: unintended loss of about five per cent in three months means tell the GP. | colour: accent warning flag; proximity: beside the door and the referral signpost | none | Module 1, lesson 2 |
| 7 | `sk-signpost` | The referral signpost at the door: two or more positive SCOFF answers, or anything beyond general advice, goes to an Accredited Practising Dietitian and the GP. | recurring symbol: referral signpost; position: at the door, the way out of your scope | none | Module 1, lesson 3 |
| 8 | `sk-myth` | The myth-buster crossing out a sugar cube: sugar does not cause ADHD, and no diet or supplement reverses it. | recurring symbol: myth-buster; position: in the pantry, where the claims are stored | none | Pitfall |

## Accessibility that is already built

- Every symbol has an accessible name describing the fact it encodes, not its appearance, plus the meaning of any badge.
- The scene is fully keyboard operable: Back and Next buttons, left and right arrow keys, and each revealed symbol is a focusable button. Unrevealed symbols are removed from the tab order.
- The caption is a polite live region, so screen readers hear each fact as it is revealed.
- “Reduce motion” shows the finished scene at once with no animation. It defaults to the operating-system setting, is remembered, and applies to every scene.
- Print shows every symbol and every recap.

## Before clinical release

The stamps and shields currently reflect how each track’s own text describes the evidence (for example “small effect”, “evidence is thin”). **They have not been checked line by line against the recommendation-strength and GRADE certainty tables in the Australian ADHD guideline.** Each scene says so on screen. A clinician should confirm every badge in `sketchy_scenes.py` against the guideline, and correct any that differ, before this is used for training.

Two symbols carry content beyond the lesson text and deserve particular review: the two plates in the nutrition scene (diet-pattern associations, described as observational only), and the mind-body and coordinative stations in the exercise scene.

## Scope notes

- Scenes exist for occupational therapy, exercise physiology, psychology and nutrition. General practice and naturopathy have no scene yet; add an entry to `SCENES` keyed `t-gp` or `t-nat` and rebuild.
- Lesson text and all 72 knowledge checks are unchanged. Each scene ends with a `QUIZ INTEGRATION POINT` comment, after which the existing lessons and checks follow as before.
- On phones the scene is small; the symbol explorer beneath it is the main reading surface there.
