# ADHDme — Landing Site Design System

Extracted from the current ADHDme landing page (adhdme-landing-reference.html). Warm, high-contrast editorial style: "built by ADHDers, for ADHDers" — validating, calm, momentum-focused. Single yellow accent on cream/white with deep-charcoal anchors.

## Colors
| Token | Hex | Use |
|---|---|---|
| brand-yellow | #F5BA13 (header bar renders #F1BC31, header border #E2AC24) | Primary accent: CTA fills, headline highlight line, underline decorations, verified badges |
| brand-yellowLight | #FFF8E6 | Feature icon tiles |
| brand-yellowMuted | #FEF1C9 | Soft highlight surfaces |
| brand-dark | #141414 | Primary text, dark CTA block, header button |
| brand-charcoal | #222222 | Dark hover state |
| brand-red | #E03616 (hover #C72F12) | Accent dot in wordmark, "Designed for Divergence" tag, blurred glow orb |
| brand-cream | #FAFAF7 | Page background |
| brand-border | #E8E6DF | Hairline borders on cards/sections/footer |
| white | #FFFFFF | Cards, footer |
| gray-600 / gray-700 | Tailwind defaults | Body copy |
| gray-400 | Tailwind default | Legal / mono footer tag |
| membership-card gradient | linear-gradient(135deg, #1C1A17 0%, #111111 60%, #28241D 100%) + 1px ring rgba(245,186,19,0.25) | Dark member card |

Legacy purple (#8C52FF) is overridden everywhere by yellow — do not reintroduce purple/blue accents.

## Typography
- Family: **Plus Jakarta Sans** (400/500/600/700/800) for headlines and body. **Space Grotesk** (500/700) for mono-style eyebrows, tags and chips.
- Headlines: extrabold (800), letter-spacing -0.035em, line-height 1.05.
  - Hero h1: 72px desktop / 60px tablet / 36px mobile, white on photo, second line in brand-yellow.
  - Section h2: 48px desktop / 36px mobile, brand-dark.
  - Card h4: 20px bold.
- Body: 16px / 1.65, gray-600. Large body 18px. Small 14px.
- Eyebrow tag: 12px, bold, uppercase, tracking-widest, inside a pill (emerald-100/emerald-800, red-50/brand-red, or white/10 on dark).

## Shape
- Buttons, inputs, tags, chips: fully rounded (9999px pills).
- Section cards / photo frames / CTA block: 24px radius (rounded-3xl).
- Inner media, icon tiles, member card: 16px radius (rounded-2xl).

## Elevation
- shadow-subtle: 0 4px 20px -2px rgba(0,0,0,0.05) — feature cards at rest
- shadow-card: 0 20px 40px -15px rgba(20,20,20,0.15) — hero, photo cards, CTA block
- glow-yellow: 0 0 25px rgba(245,186,19,0.45) — optional focus/hover glow
- Blurred decorative orbs (288px, blur-3xl) in yellow/20 and red/20 inside the dark CTA block.

## Spacing & Layout
- Container max-width 1280px, horizontal padding 24px.
- Section vertical padding 64px (mobile) → 96px (desktop). Grid gaps 32px.
- Editorial 12-column split for section headers: 7 cols headline / 5 cols copy + CTA (right-aligned on desktop).

## Components
- **Header**: full-width yellow bar (#F1BC31), logo left (56px tall), 4 bold 14px nav links centered (How it works · The Doctors · Learn · Our Story), dark pill CTA "Join waitlist" with yellow arrow icon.
- **Hero**: full-bleed photograph, min-height 760px desktop / 640px mobile, editorial headline bottom-left: "Not just focus. / Life back." (second line yellow), drop shadow on text.
- **Value proposition**: split header ("For everything you navigate every single day, this is for you." with yellow underline) + yellow pill "Join Us"; below it a rounded-3xl vivid abstract painted banner (red/yellow/pink fluid) with a floating dark **membership card**: "adhdme" wordmark + red dot, "FOUNDING MEMBER" mono tag, avatar with yellow border + check badge, "Verified ADHD Member", name, tier line, 3 stat chips (Daily Streak · Body Double · Dopamine Log).
- **Our story**: emerald eyebrow "Our story", h2 "The people behind ADHDme", three tilted polaroid photo cards (-3.5°, 0° elevated with yellow 2px border, +3°), white 14px frames, 4:5 photos, caption pill bottom-left; centered caption paragraph.
- **Feature pillars**: red eyebrow "Designed for Divergence", h3 "Tools that flow with your brain, never against it.", 3 white cards (emoji tile 48px in yellowLight, h4, 14px body): Zero-Friction Momentum ⚡ · Silent Body Doubling 🤝 · Dopamine Rewards Bank 🎯.
- **CTA block**: dark rounded-3xl, centered, "🚀 Founding Cohort Access Open" pill, h2 "Ready to swap overwhelm for clarity?", email input pill + yellow "Join waitlist →" button, "No spam ever. Early access invites distributed weekly."
- **Footer**: white, hairline top, logo + "© 2026 ADHDme Inc.", links (Privacy Policy · Terms of Care · Accessibility · Contact), mono tag "CRAFTED FOR NEURODIVERSITY".

## Motion
- Transitions 200–300ms ease. Photo cards: hover un-tilt, lift -4px, scale 1.02. Header CTA: hover shadow + translate-x 2px. Member card: hover lift -4px.

## Do / Don't
- Do keep yellow as the single accent; generous whitespace; warm, validating copy; big editorial headlines.
- Don't add purple/blue accents, dense UI, harsh shadows, or clinical/medical stock imagery.
