'use strict';
// The ADHDme brand, read off the site in this repository, not invented here.
//   yellow  #f1bc31  header bar, the "Get assessed by a GP" rule, the marked hero phrase
//   coral   #ff4d2e  the dot after "me" in the logo
//   blue    #2c80c6  the "Work with a psychologist" rule
//   ink     #1a1c1c  every heading
//   cream   #FAFAF7  the page
// Type is Plus Jakarta Sans at the site's own hero setting: weight 800,
// letter-spacing -0.035em, line-height 1.05 (index.html, .font-brand-headline).

const BRAND = {
  yellow: '#f1bc31', yellowSoft: '#FEF1C9', yellowHover: '#e5b026',
  coral: '#ff4d2e', blue: '#2c80c6', blueLight: '#5fb0ec',
  ink: '#1a1c1c', body: '#4a453a', muted: '#6b6455',
  cream: '#FAFAF7', card: '#ffffff', border: '#E8E6DF', rule: '#d2c5ad',
  skin: '#f6e2cf', skinShade: '#e3c3a5', shirt: '#ffffff', jeans: '#dfe6ee',
};

const AD_PALETTE = {
  paper: BRAND.cream, paperBand: null, ink: BRAND.ink,
  night: BRAND.ink, chalk: BRAND.yellow, chalkDim: '#8a8578',
  guide: 'rgba(44,128,198,.45)',
  fills: [BRAND.yellow, BRAND.blue, BRAND.card, BRAND.yellowSoft, BRAND.border],
  shade: BRAND.body, light: '#ffffff', blush: BRAND.yellowSoft,
  accents: [BRAND.coral, BRAND.yellow, BRAND.blue, BRAND.blueLight],
  inks: [BRAND.blue, BRAND.coral, BRAND.yellow],
  finish: 'ink',
};

// ---------------------------------------------------------------- type
// Crisp brand type against a drawn frame: the site's headings are set, not
// lettered, and pretending otherwise would misrepresent the brand. The hand
// belongs to the drawing.
function brandFont(size, weight = 800) { return `${weight} ${size}px "${BRAND_FONT}", "Plus Jakarta Sans", system-ui, sans-serif`; }

function setType(c, size, {weight = 800, track = -0.035, align = 'left', baseline = 'alphabetic'} = {}) {
  c.font = brandFont(size, weight);
  c.textAlign = align; c.textBaseline = baseline;
  if ('letterSpacing' in c) c.letterSpacing = `${(track * size).toFixed(2)}px`;
}

const typeWidth = (c, text) => c.measureText(text).width;

// A line of type that wipes up behind a moving edge, the way the landing page's
// hero lines arrive (.hero-in in motion.css). progress 0..1; 1 is fully up.
function riseLine(c, text, x, y, size, o = {}) {
  const {weight = 800, track = -0.035, color = BRAND.ink, align = 'left', progress = 1, rise = 0.5} = o;
  const p = clamp(progress, 0, 1); if (p <= 0) return;
  c.save();
  setType(c, size, {weight, track, align});
  const pad = size * 0.42, band = size * 1.28;
  c.beginPath(); c.rect(x - W, y - band, W * 2, band + pad); c.clip();
  c.globalAlpha *= easeOut(clamp(p * 1.35, 0, 1));
  c.fillStyle = color;
  c.fillText(text, x, y + (1 - easeOut(p)) * size * rise);
  c.restore();
}

// Two words in two colours on one baseline, for "Not just focus. / Life
// returned to you." The second half is the marked phrase, in brand yellow.
function riseSplit(c, a, b, x, y, size, o = {}) {
  const {colorA = '#ffffff', colorB = BRAND.yellow, progress = 1, gapFactor = 0.28} = o;
  c.save(); setType(c, size);
  const wa = typeWidth(c, a); c.restore();
  riseLine(c, a, x, y, size, {...o, color: colorA, progress});
  riseLine(c, b, x + wa + size * gapFactor, y, size, {...o, color: colorB, progress: clamp(progress * 1.6 - 0.6, 0, 1)});
}

// ---------------------------------------------------------------- the mark
// The header lockup from index.html: "ADHD" letter-spaced over "me", with the
// coral dot on the baseline beside it. size is the cap height of "me".
function logoMetrics(c, size) {
  c.save();
  setType(c, size * 0.39, {track: 0.62});
  const topW = typeWidth(c, 'ADHD');
  setType(c, size, {track: -0.03});
  const meW = typeWidth(c, 'me');
  c.restore();
  return {topW, meW, dotR: size * 0.175, gap: size * 0.075, stack: size * 0.80};
}

// The dot is drawn by the caller when it has to travel; pass dot:false then.
function adhdmeMark(c, x, y, size, o = {}) {
  const {ink = BRAND.ink, dotColor = BRAND.coral, dot = true, progress = 1} = o;
  const m = logoMetrics(c, size), p = clamp(progress, 0, 1);
  c.save();
  c.fillStyle = ink;
  c.globalAlpha *= easeOut(clamp(p * 2, 0, 1));
  setType(c, size * 0.39, {track: 0.62, align: 'left'});
  c.fillText('ADHD', x, y - m.stack);
  c.globalAlpha = c.globalAlpha * easeOut(clamp(p * 2 - 0.6, 0, 1));
  setType(c, size, {track: -0.03, align: 'left'});
  c.fillText('me', x, y);
  c.restore();
  if (dot) { c.save(); c.globalAlpha *= easeOut(clamp(p * 2 - 1.2, 0, 1)); c.fillStyle = dotColor; c.beginPath(); c.arc(x + m.meW + m.gap + m.dotR, y - m.dotR * 0.62, m.dotR, 0, TAU); c.fill(); c.restore(); }
  return m;
}

// Where the dot sits for a mark drawn at (x, y): the film flies the real dot
// into this point, so the logo is completed by the line the film has followed.
function markDot(c, x, y, size) {
  const m = logoMetrics(c, size);
  return [x + m.meW + m.gap + m.dotR, y - m.dotR * 0.62, m.dotR];
}

// ---------------------------------------------------------------- the rules
// The landing page puts a 3px rule above each door: yellow over "Get assessed
// by a GP", blue over "Work with a psychologist". Those two rules are the film's
// through-line, so they are drawn as ink, with a little pressure.
function brandRule(c, x0, x1, y, color, o = {}) {
  const {weight = 9, seed = 4, amp = 1.1} = o;
  if (x1 - x0 <= 0.5) return;
  c.save(); c.strokeStyle = color; c.lineWidth = weight; c.lineCap = 'round';
  wob(c, [[x0, y], [lerp(x0, x1, .5), y], [x1, y]], amp, seed, false, {pressure: .35, freq: .7});
  c.restore();
}
