'use strict';
// The room, the knot, and the two rules the knot turns into.
//
// One line carries the whole film. It starts wound into a ball above her head -
// the year in the queue - then pulls straight, then divides into the two
// coloured rules the landing page puts above "Get assessed by a GP." and
// "Work with a psychologist.". Its leading end is the coral dot from the logo,
// so the last thing the line does is finish the mark.

const FLOOR = 940, SEAT = 795, LINE_Y = 652;
const RULE_X0 = 1120, RULE_X1 = 1868, RULE_TOP = 238, RULE_BOT = 762;
const FIG_X = 980, FIG_SCALE = 1;

// ------------------------------------------------------------------ the room
function floorLine(c, fade = 1) {
  if (fade <= 0) return;
  c.save(); c.globalAlpha *= fade;
  c.strokeStyle = alpha(BRAND.ink, .34); c.lineWidth = 2.6; c.lineCap = 'round';
  wob(c, [[-400, FLOOR], [640, FLOOR - 1], [1400, FLOOR + 1], [2400, FLOOR]], 1.2, 12, false, {corner: 3, pressure: .3});
  c.strokeStyle = alpha(BRAND.rule, .75); c.lineWidth = 1.2;
  wob(c, [[-400, FLOOR + 11], [900, FLOOR + 13], [2400, FLOOR + 11]], 1, 13, false, {corner: 3});
  c.restore();
}

// A waiting-room chair, side on. Plain, because the point of it is that nothing
// about the wait was ever the care.
function chair(c, x, o = {}) {
  const {a = 1, fill = '#f2efe6', ink = BRAND.ink, seed = 3} = o;
  if (a <= 0) return;
  const seatL = x - 118, seatR = x + 96, back = x - 122;
  const shape = [
    [seatL, SEAT], [seatR, SEAT - 3], [seatR + 6, SEAT + 13], [seatL - 4, SEAT + 16],
  ];
  const backRest = [[back - 4, SEAT + 6], [back - 20, SEAT - 176], [back + 2, SEAT - 180], [back + 16, SEAT + 4]];
  const legF = [[x + 66, SEAT + 12], [x + 74, FLOOR], [x + 88, FLOOR], [x + 82, SEAT + 12]];
  const legB = [[seatL + 6, SEAT + 14], [seatL - 4, FLOOR], [seatL + 10, FLOOR], [seatL + 20, SEAT + 14]];
  c.save(); c.globalAlpha *= a;
  for (const [pts, col] of [[legB, '#efece4'], [backRest, fill], [shape, fill], [legF, '#efece4']]) {
    c.fillStyle = col; c.fill(curvePath(pts, true, .9));
  }
  c.strokeStyle = ink; c.lineWidth = 2.4; c.lineCap = 'round'; c.lineJoin = 'round';
  for (const pts of [legB, backRest, shape, legF]) wob(c, pts, .9, seed, true, {corner: .9, pressure: .3});
  c.strokeStyle = alpha(ink, .3); c.lineWidth = 1.2;
  wob(c, [[back + 4, SEAT - 150], [x + 10, SEAT - 154]], .8, seed + 4, false);
  c.restore();
}

// The rest of the queue, receding. It is the only thing in the frame that has a
// perspective to it, and it leaves when the wait does.
function queueChairs(c, fade = 1) {
  if (fade <= 0) return;
  const rows = [[650, .5], [380, .32], [110, .19]];
  for (const [x, a] of rows) chair(c, x, {a: a * fade, fill: '#f7f5ef', ink: alpha(BRAND.ink, .75), seed: 3 + x});
}

// ------------------------------------------------------------------ the line
// One wandering line, wound into a knot, with every point's straightened
// position worked out once. Straightening is a lerp between the two, run from
// the leading end backwards, so the knot pulls tight rather than fading out.
const THREAD = (() => {
  const r = rng(47), knot = [];
  const cx = 1420, cy = 330, rx = 252, ry = 150;
  let x = cx, y = cy, ang = .6;
  for (let i = 0; i < 210; i++) {
    ang += noise1(i * .17, 5) * 1.15 + (r() - .5) * .3;
    const dx = (x - cx) / rx, dy = (y - cy) / ry;
    if (Math.hypot(dx, dy) > 1) ang = Math.atan2(cy - y, cx - x) + (r() - .5) * 1.25;
    x += Math.cos(ang) * 31; y += Math.sin(ang) * 31;
    knot.push([x, y]);
  }
  // it leaves the knot and heads for the right edge
  const last = knot[knot.length - 1];
  for (let i = 1; i <= 30; i++) {
    const u = i / 30, land = clamp(u / .52, 0, 1);
    knot.push([lerp(last[0], 1980, easeIO(u)), lerp(last[1], LINE_Y, easeIO(land)) - Math.sin(land * Math.PI) * 40]);
  }
  const pts = smoothPts(knot, false, 7, 2.6);
  const N = pts.length - 1;
  const straight = pts.map((_, i) => [lerp(-260, 1980, i / N), LINE_Y]);
  return {pts, straight, N};
})();

// pull: 0 knotted, 1 straight, run from the leading end backwards so the knot
// tightens rather than fades. settle: 0 lying across the frame, 1 gathered into
// the rule that sits at (x0..x1, y). Returns the leading end, which is where the
// coral dot rides all film.
function threadShape(pull, settle, y, x0, x1) {
  const {pts, straight, N} = THREAD, s = clamp(settle, 0, 1), out = [];
  for (let i = 0; i <= N; i++) {
    const t = easeInOutSine(clamp(pull * 1.62 - (1 - i / N) * .62, 0, 1));
    const gx = lerp(straight[i][0], lerp(x0, x1, i / N), s), gy = lerp(straight[i][1], y, s);
    out.push([lerp(pts[i][0], gx, t), lerp(pts[i][1], gy, t)]);
  }
  return out;
}

function drawThread(c, shape, o = {}) {
  const {width = 3.4, color = BRAND.ink, alpha: al = 1, seed = 8} = o;
  if (al <= 0 || shape.length < 3) return shape[shape.length - 1];
  c.save(); c.globalAlpha *= al; c.strokeStyle = color; c.lineWidth = width;
  c.lineCap = 'round'; c.lineJoin = 'round';
  wob(c, shape, 1.1, seed, false, {smooth: false, pressure: .32, freq: .5});
  c.restore();
  return shape[shape.length - 1];
}

// The dot that ends the line is the dot that ends the logo.
function coralDot(c, p, r = 13, o = {}) {
  const {color = BRAND.coral, a = 1} = o;
  if (a <= 0 || r <= 0) return;
  c.save(); c.globalAlpha *= a; c.fillStyle = color;
  c.beginPath(); c.arc(p[0], p[1], r, 0, TAU); c.fill(); c.restore();
}

// ----------------------------------------------------------------- the doors
// The landing page's two blocks: a coloured rule, a heading, and the one number
// or fact that decides whether somebody can act on it today.
const DOORS = [
  {y: RULE_TOP, color: BRAND.yellow, title: 'Get assessed by a GP.', note: '$299 initial · no referral needed'},
  {y: RULE_BOT, color: BRAND.blue, title: 'Work with a psychologist.', note: 'Medicare rebates may apply'},
];

function doorLabels(c, progress) {
  const p = clamp(progress, 0, 1);
  DOORS.forEach((d, i) => {
    const q = clamp(p * 1.7 - i * .32, 0, 1);
    riseLine(c, d.title, RULE_X0, d.y + 74, 50, {color: BRAND.ink, progress: q, rise: .7});
    riseLine(c, d.note, RULE_X0, d.y + 126, 31, {weight: 600, track: -.005, color: BRAND.muted, progress: clamp(q * 1.5 - .5, 0, 1), rise: .7});
  });
}

// The blue rule is the other half of the same line. It starts exactly where the
// first one is and peels away downward, so what the eye sees is one line
// dividing into two, not a second line arriving.
function blueRule(c, split, fromY, fromX0) {
  const s = clamp(split, 0, 1); if (s <= 0) return;
  const e = easeInOutQuint(s);
  brandRule(c, lerp(fromX0, RULE_X0, e), RULE_X1, lerp(fromY, RULE_BOT, e),
    mix(BRAND.ink, BRAND.blue, easeIO(clamp(s * 1.8, 0, 1))),
    {weight: lerp(3.4, 9, e), seed: 21, amp: lerp(1.1, .8, e)});
}

// ------------------------------------------------------------------ the card
function cardGround(c) {
  resetT(c);
  c.fillStyle = BRAND.ink; c.fillRect(0, 0, W, H);
  grain(c, rectPath(0, 0, W, H), [0, 0, W, H], 1200, '#ffffff', .035, 31, 1.5);
}
