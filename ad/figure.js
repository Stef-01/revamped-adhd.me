'use strict';
// One woman, drawn whole for every exposed pose.
//
// A pose is a small authored skeleton: hip, neck, skull centre, elbows, wrists,
// knees, ankles, toes, plus four shape scalars (torso bow, chin tuck, gaze,
// finger curl). figureParts() redraws the entire contour from that skeleton
// every time, so a bent elbow is one continuous tapered outline with a crease on
// the inside, not two rotated capsules with grain on top. Nothing here rotates a
// finished limb; the limb is drawn again.
//
// The skeleton exists to hold contacts and proportions. What reaches the screen
// is the contour, the creases, the fabric folds and the shading, all rebuilt per
// pose. Marks are seeded from the drawing id, so a held drawing holds its marks.
//
// Local units: y increases downward, the floor is y = 0, the figure faces +x and
// stands 562 units tall (about seven heads).

const FIG = {
  // clothing and skin, every colour taken from tailwind.config.js
  trouser: '#24487a', trouserShade: '#1c385e',
  shirt: '#FEF1C9', shirtShade: '#f0dda6',
  skin: '#e9c9a6', skinShade: '#d2ab86',
  hair: '#2b241d', shoe: '#1f2a33',
  line: '#1a1c1c',
  // build
  shoulderNear: [-4, 19], shoulderFar: [-22, 28],
  armR: [27, 15, 11], foreR: [14, 11, 9],
  thighR: [30, 21, 13], shinR: [20, 14, 10],
  torsoFront: [44, 36, 43, 17], torsoBack: [48, 43, 50, 19],
  neckR: [22, 16, 13],
};

// ------------------------------------------------------------------ geometry
const vlerp = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
const vadd = (a, b) => [a[0] + b[0], a[1] + b[1]];
const vang = (a, b) => Math.atan2(b[1] - a[1], b[0] - a[0]);

function radiusAt(u, radii) {
  const n = radii.length - 1, x = clamp(u, 0, 1) * n, i = Math.min(n - 1, Math.floor(x));
  return lerp(radii[i], radii[i + 1], x - i);
}

// A single continuous outline around a bent limb. The offset is limited by the
// local radius of curvature on the inside of a bend, so the contour creases at
// the elbow or the knee instead of crossing itself. Point count depends only on
// the input length, so any two poses of the same limb correspond.
function limbOutline(pts, radiiFront, radiiBack = radiiFront, per = 7) {
  const path = motionPath(pts, {smooth: true});
  const N = (pts.length - 1) * per, ds = path.length / N;
  const S = [];
  for (let i = 0; i <= N; i++) { const u = i / N, a = path.at(u); S.push({p: a.p, t: a.tangent, u}); }
  const turnAt = i => {
    const a = S[Math.max(0, i - 1)].t, b = S[Math.min(N, i + 1)].t;
    const d = Math.atan2(b[1], b[0]) - Math.atan2(a[1], a[0]);
    return Math.atan2(Math.sin(d), Math.cos(d));
  };
  const flank = (sgn, radii) => S.map((s, i) => {
    const k = turnAt(i), inner = Math.sign(k) === sgn && Math.abs(k) > 1e-6;
    const want = radiusAt(s.u, radii);
    const r = inner ? Math.min(want, (2 * ds / Math.abs(k)) * 0.78) : want;
    return [s.p[0] - sgn * s.t[1] * r, s.p[1] + sgn * s.t[0] * r];
  });
  return [...flank(1, radiiFront), ...flank(-1, radiiBack).reverse()];
}

// Place a shape authored in local space (x forward, y down) at p, turned by a.
const placed = (shape, p, a, s = 1, flipY = 1) => {
  const ca = Math.cos(a), sa = Math.sin(a);
  return shape.map(([x, y]) => { const X = x * s, Y = y * s * flipY; return [p[0] + X * ca - Y * sa, p[1] + X * sa + Y * ca]; });
};

// ------------------------------------------------------- authored components
// A profile head, drawn twice: chin tucked down onto the chest, and chin lifted
// clear of it. The jaw, the throat line and the cheek all change between them;
// `chin` reads across the two drawings. Local origin is the skull centre, x is
// the direction the face looks.
const HEAD_DOWN = [
  [-6, -41], [16, -37], [29, -23], [33, -6], [36, 3], [42, 9], [35, 13],
  [33, 22], [26, 31], [12, 38], [-4, 39], [-20, 33], [-31, 20], [-35, 1], [-30, -21], [-19, -35],
];
const HEAD_UP = [
  [-7, -41], [15, -38], [29, -25], [34, -9], [38, 0], [44, 5], [36, 10],
  [35, 19], [30, 29], [16, 35], [-2, 34], [-19, 28], [-31, 16], [-35, -2], [-30, -23], [-20, -36],
];
const headShape = chin => HEAD_DOWN.map((p, i) => vlerp(p, HEAD_UP[i], chin));

const HAIR_DOWN = [
  [-7, -44], [14, -42], [29, -29], [26, -34], [10, -46], [-14, -44], [-31, -29],
  [-40, -6], [-44, 14], [-48, 30], [-41, 36], [-31, 26], [-28, 8], [-24, -12],
];
const HAIR_UP = [
  [-8, -45], [13, -43], [29, -31], [26, -36], [9, -47], [-15, -44], [-32, -30],
  [-41, -8], [-46, 11], [-52, 27], [-45, 34], [-34, 24], [-29, 6], [-25, -14],
];
const hairShape = chin => HAIR_DOWN.map((p, i) => vlerp(p, HAIR_UP[i], chin));

// A hand, wrist at the origin, fingers along +x. Open in the lap, closed on the
// knee: two drawings, not one shape squeezed.
const HAND_OPEN = [[0, -10], [14, -13], [27, -11], [33, -4], [32, 6], [24, 13], [10, 14], [-1, 11]];
const HAND_SHUT = [[0, -10], [12, -13], [21, -9], [23, -1], [21, 7], [14, 12], [4, 13], [-2, 10]];
const handShape = curl => HAND_OPEN.map((p, i) => vlerp(p, HAND_SHUT[i], curl));

// A shoe, ankle at the origin, toe along +x.
const SHOE = [[-13, -14], [6, -16], [24, -13], [38, -5], [42, 3], [36, 9], [4, 11], [-14, 8], [-18, -3]];

const EYE = [[-7, 0], [-3, -4], [3, -4], [7, 0], [2, 4], [-3, 4]];

// ---------------------------------------------------------------- the drawing
// Returns ordered groups. Each group is filled, then its contours are drawn on
// top, so the near leg covers the far one and the shirt falls over both hips.
function figureParts(pose) {
  const P = pose;
  const shN = vadd(P.neck, [FIG.shoulderNear[0], FIG.shoulderNear[1] - P.shrug]);
  const shF = vadd(P.neck, [FIG.shoulderFar[0], FIG.shoulderFar[1] - P.shrug]);

  // Torso: a bowed centreline from the hip to the neck. `curve` pushes the
  // midpoint forward, which is what rounds the back and closes the chest.
  const axis = vang(P.hip, P.neck), nx = -Math.sin(axis), ny = Math.cos(axis);
  const mid = vlerp(P.hip, P.neck, .52);
  const waist = [mid[0] + nx * P.curve, mid[1] + ny * P.curve];
  const chest = vlerp(waist, P.neck, .62);
  const torso = limbOutline([P.hip, waist, chest, P.neck], FIG.torsoFront, FIG.torsoBack, 7);

  const arm = (sh, el, wr) => limbOutline([sh, el, wr], [...FIG.armR.slice(0, 2), FIG.foreR[1], FIG.foreR[2]], undefined, 7);
  const leg = (hip, kn, an) => limbOutline([hip, kn, an], [...FIG.thighR.slice(0, 2), FIG.shinR[1], FIG.shinR[2]], undefined, 7);

  const hipF = vadd(P.hip, [-16, 6]), hipN = vadd(P.hip, [6, 8]);
  const legF = leg(hipF, P.knF, P.anF), legN = leg(hipN, P.knN, P.anN);
  const armF = arm(shF, P.elF, P.wrF), armN = arm(shN, P.elN, P.wrN);
  const handF = placed(handShape(P.curlF), P.wrF, vang(P.elF, P.wrF));
  const handN = placed(handShape(P.curlN), P.wrN, vang(P.elN, P.wrN));
  const shoeF = placed(SHOE, P.anF, vang(P.anF, P.toF));
  const shoeN = placed(SHOE, P.anN, vang(P.anN, P.toN));

  const head = placed(headShape(P.chin), P.head, P.face);
  const hair = placed(hairShape(P.chin), P.head, P.face);
  const hp = (x, y) => placed([[x, y]], P.head, P.face)[0];
  // The neck is a column from the collar to the base of the skull. It widens
  // into the shoulders at the bottom, and the chin tuck shortens what shows.
  const neckTop = hp(-4, 26), neckBase = vadd(chest, [2, -4]);
  const neckTube = limbOutline([neckBase, vlerp(neckBase, neckTop, .55), neckTop], FIG.neckR, undefined, 5);
  // The throat: one short mark from under the jaw, no more. It lengthens as the
  // chin lifts, which is the whole point of the beat.
  const neckLine = [hp(12, 27), hp(6, 36), hp(-1, 44)];

  const rows = [];   // stroke rows, in draw order inside their group
  const add = (g, id, points, o = {}) => rows.push({group: g, id, points, width: o.w ?? 2.6, opacity: o.a ?? 1, close: o.close ?? false, corner: o.corner ?? Math.PI, color: o.color});

  // shading: short strokes along the shadow side of a form, fixed grid so they
  // hold their identity from pose to pose
  const shadeAlong = (g, id, pts, n, off, len, w) => {
    const path = motionPath(pts, {smooth: true});
    for (let i = 0; i < n; i++) {
      const u = (i + .5) / n, {p, tangent: t} = path.at(u);
      const nxv = -t[1], nyv = t[0], d = off * (.7 + .3 * Math.sin(u * Math.PI));
      add(g, `${id}/${i}`, [[p[0] - nxv * d, p[1] - nyv * d], [p[0] - nxv * (d - len), p[1] - nyv * (d - len)]], {w, a: .38});
    }
  };

  add('legFar', 'leg-far', legF, {close: true, w: 2.3, a: .95});
  add('legFar', 'shoe-far', shoeF, {close: true, w: 2.3, a: .95});
  add('armFar', 'arm-far', armF, {close: true, w: 2.2, a: .9});
  add('armFar', 'hand-far', handF, {close: true, w: 1.9, a: .9});
  add('legNear', 'leg-near', legN, {close: true, w: 2.9});
  // knee crease: the inside of the bend, drawn as its own mark
  const kneeIn = (kn, hip, an) => {
    const a = vang(kn, hip), b = vang(kn, an), m = (Math.atan2(Math.sin(a) + Math.sin(b), Math.cos(a) + Math.cos(b)));
    return [0, 1, 2].map(i => [kn[0] + Math.cos(m) * (13 + i * 3) + Math.cos(m + 1.57) * (i - 1) * 9, kn[1] + Math.sin(m) * (13 + i * 3) + Math.sin(m + 1.57) * (i - 1) * 9]);
  };
  add('legNear', 'knee-near', kneeIn(P.knN, hipN, P.anN), {w: 1.4, a: .5});
  add('legNear', 'shoe-near', shoeN, {close: true, w: 2.8});
  add('legNear', 'shoe-near/sole', [vlerp(shoeN[7], shoeN[6], .1), vlerp(shoeN[7], shoeN[6], .55), vlerp(shoeN[7], shoeN[6], .95)], {w: 1.5, a: .6});
  shadeAlong('legNear', 'shade/shin', [P.knN, P.anN], 4, -15, 8, 1.2);

  add('torso', 'torso', torso, {close: true, w: 3});
  add('torso', 'collar', [vadd(shF, [10, -10]), vadd(neckBase, [-10, -6]), vadd(neckBase, [12, -2]), vadd(shN, [20, 8])], {w: 1.9, a: .8});
  // the hem falls across both hips, so it is drawn after the legs
  const hemA = vadd(P.hip, [-52, 16]), hemB = vadd(P.hip, [0, 30]), hemC = vadd(P.hip, [48, 18]);
  add('torso', 'hem', [hemA, hemB, hemC], {w: 2, a: .75});
  for (let i = 0; i < 3; i++) {
    const u = .3 + i * .22, a = vlerp(vadd(waist, [nx * -14, ny * -14]), hemB, u);
    add('torso', `fold/${i}`, [[a[0] - 16 + i * 5, a[1] - 34], [a[0] - 6 + i * 4, a[1] - 8], [a[0] - 12 + i * 6, a[1] + 14]], {w: 1.3, a: .42});
  }
  shadeAlong('torso', 'shade/back', [P.hip, waist, chest], 6, -44, 13, 1.3);

  add('armNear', 'arm-near', armN, {close: true, w: 2.9});
  add('armNear', 'elbow-near', [[P.elN[0] - 6, P.elN[1] - 13], [P.elN[0] - 11, P.elN[1] - 2], [P.elN[0] - 6, P.elN[1] + 10]], {w: 1.3, a: .45});
  add('armNear', 'hand-near', handN, {close: true, w: 2.4});
  for (let i = 0; i < 3; i++) {
    const t = .34 + i * .2, base = vlerp(P.wrN, vadd(P.wrN, [Math.cos(vang(P.elN, P.wrN)) * 26, Math.sin(vang(P.elN, P.wrN)) * 26]), 1);
    add('armNear', `finger/${i}`, [vlerp(P.wrN, base, .45 + i * .05), vlerp(P.wrN, base, .8), vadd(vlerp(P.wrN, base, .95), [0, (i - 1) * 6])], {w: 1.2, a: .45 - i * .06});
  }

  add('neck', 'neck', neckTube, {close: true, w: 2.2, a: .9});
  add('head', 'throat', neckLine, {w: 1.5, a: .5});
  add('head', 'head', head, {close: true, w: 3});
  add('head', 'ear', placed([[-16, -2], [-9, -6], [-5, 1], [-8, 10], [-15, 11]], P.head, P.face), {close: true, w: 1.6, a: .7});
  add('head', 'ear/inner', placed([[-13, 1], [-10, 4], [-12, 8]], P.head, P.face), {w: 1.1, a: .5});
  add('head', 'hair', hair, {close: true, w: 2.6});
  for (let i = 0; i < 4; i++) {
    const y = -26 + i * 17;
    add('head', `hair/strand/${i}`, placed([[-24, y], [-33, y + 8], [-31, y + 22]], P.head, P.face), {w: 1.2, a: .45});
  }
  add('head', 'brow', placed([[12, -13], [22, -15], [29, -11]], P.head, P.face), {w: 2, a: .85});
  add('head', 'eye', placed(EYE.map(([x, y]) => [x + 20, y - 4]), P.head, P.face), {close: true, w: 1.7, a: .9});
  add('head', 'pupil', placed(EYE.map(([x, y]) => [x * .42 + 21, y * .42 - 4]), P.head, P.face), {close: true, w: 2.4, a: 1});
  add('head', 'mouth', placed([[26, 16], [31, 18], [34, 15]], P.head, P.face), {w: 1.6, a: .7});
  add('head', 'cheek', placed([[18, 6], [22, 12], [20, 18]], P.head, P.face), {w: 1.1, a: .3});

  const fills = [
    {group: 'legFar', paths: [[legF, FIG.trouserShade], [shoeF, '#17202a']]},
    {group: 'armFar', paths: [[armF, FIG.shirtShade], [handF, FIG.skinShade]]},
    {group: 'legNear', paths: [[legN, FIG.trouser], [shoeN, FIG.shoe]]},
    {group: 'neck', paths: [[neckTube, FIG.skinShade]]},
    {group: 'torso', paths: [[torso, FIG.shirt]]},
    {group: 'armNear', paths: [[armN, FIG.shirt], [handN, FIG.skin]]},
    {group: 'head', paths: [[head, FIG.skin], [hair, FIG.hair]]},
  ];
  return {rows, fills, anchors: {head: P.head, chest, hipN, shN}};
}

const FIG_GROUPS = ['legFar', 'armFar', 'legNear', 'neck', 'torso', 'armNear', 'head'];

// One compiled drawing per exposed pose. The id seeds every mark, so holding a
// drawing holds its ink; a new drawing is a new set of marks, never a reseed of
// the same one on the next output frame.
const _figCache = new Map();
function figureDrawing(pose, id) {
  const hit = _figCache.get(id); if (hit) return hit;
  const {rows, fills} = figureParts(pose);
  const cels = FIG_GROUPS.map(g => {
    const strokes = rows.filter(r => r.group === g).map(r => ({
      id: r.id, points: r.points, width: r.width, opacity: r.opacity,
      close: r.close, corner: r.corner, color: r.color,
    }));
    return {group: g, cel: strokes.length ? compileCel({strokes}, {id: `${id}/${g}`}) : null,
      fills: (fills.find(f => f.group === g) || {paths: []}).paths};
  });
  // The drawing's own extent. Everything this figure paints happens inside it,
  // so the figure is clipped to it: a stroke or a fill can never leave a mark
  // somewhere else in the frame, whatever the renderer does with a long run of
  // short segments over a filled path.
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const see = ([px, py]) => { if (px < x0) x0 = px; if (px > x1) x1 = px; if (py < y0) y0 = py; if (py > y1) y1 = py; };
  for (const {cel, fills} of cels) {
    for (const [pts] of fills) pts.forEach(see);
    if (cel) for (const st of cel.strokes) for (const sm of st.samples) see(sm.p);
  }
  const pad = 14;
  const out = {cels, box: [x0 - pad, y0 - pad, (x1 - x0) + pad * 2, (y1 - y0) + pad * 2]};
  if (_figCache.size > 8) _figCache.delete(_figCache.keys().next().value);
  _figCache.set(id, out);
  return out;
}

// Each exposed drawing is rendered once into its own canvas and then blitted.
// This is the caching pattern from the skill's sketchbook-bird study: on twos or
// threes a held drawing is rasterised once and reused for its whole exposure,
// which is both faster and the only way the ink stays bit-identical through a
// hold. It also keeps every mark inside a surface the size of the drawing.
const SPRITE_OVERSAMPLE = 1.08;   // >= the film's largest camera zoom, so the blit only ever scales down
const _spriteCache = new Map();
function figureSprite(pose, id, ink) {
  const key = id + '|' + S.toFixed(3) + '|' + ink;
  const hit = _spriteCache.get(key); if (hit) return hit;
  const {cels, box} = figureDrawing(pose, id);
  const k = S * SPRITE_OVERSAMPLE;
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.ceil(box[2] * k));
  canvas.height = Math.max(1, Math.ceil(box[3] * k));
  const g = canvas.getContext('2d');
  g.setTransform(k, 0, 0, k, 0, 0);
  g.translate(-box[0], -box[1]);
  for (const {cel, fills} of cels) {
    for (const [pts, col] of fills) { g.fillStyle = col; g.fill(curvePath(pts, true, Math.PI)); }
    if (cel) drawCel(g, cel, {material: 'ink', color: ink});
  }
  const sprite = {canvas, box};
  if (_spriteCache.size > 6) _spriteCache.delete(_spriteCache.keys().next().value);
  _spriteCache.set(key, sprite);
  return sprite;
}

// Draw the figure at world position (x, y) with the floor at y.
function drawFigure(c, pose, id, {x = 0, y = 0, scale = 1, opacity = 1, ink = FIG.line} = {}) {
  const {canvas, box} = figureSprite(pose, id, ink);
  c.save(); c.translate(x, y); c.scale(scale, scale); c.globalAlpha *= opacity;
  c.drawImage(canvas, box[0], box[1], box[2], box[3]);
  c.restore();
}

// A shadow under the planted feet: an ellipse that tightens as weight lands.
function contactShadow(c, x, y, w, k = 1, color = 'rgba(26,28,28,.13)') {
  if (k <= 0) return;
  c.save(); c.fillStyle = color; c.globalAlpha *= clamp(k, 0, 1);
  c.beginPath(); c.ellipse(x, y, w, w * .17, 0, 0, TAU); c.fill(); c.restore();
}

// ---------------------------------------------------------------- the poses
// Eleven authored keys. Every value is in the figure's local frame with the
// floor at y = 0. The chair seat is at y = -145; while she is on it the hip
// stays on the seat and both feet stay on the floor, so the contacts are in the
// drawings rather than in a solver.
const KEY = {
  // slumped: shoulders up and rolled forward, chin down, hands dead in the lap
  slump: {
    hip: [0, -152], neck: [40, -318], head: [66, -362], chin: .06, face: .46, curve: -26, shrug: 9,
    elF: [44, -238], wrF: [86, -190], curlF: .5, elN: [58, -236], wrN: [98, -186], curlN: .45,
    knF: [110, -143], anF: [124, -28], toF: [152, -12], knN: [150, -148], anN: [166, -28], toN: [198, -12],
  },
  // the same drawing an exhalation later: the ribs drop, the head settles
  slumpB: {
    hip: [0, -151], neck: [41, -314], head: [68, -357], chin: .03, face: .5, curve: -29, shrug: 6,
    elF: [45, -235], wrF: [87, -188], curlF: .52, elN: [59, -233], wrN: [99, -184], curlN: .47,
    knF: [110, -143], anF: [124, -28], toF: [152, -12], knN: [150, -148], anN: [166, -28], toN: [198, -12],
  },
  // the head comes up: chin clears the chest, the back is still round
  lift: {
    hip: [0, -152], neck: [34, -324], head: [52, -376], chin: .82, face: -.06, curve: -20, shrug: 4,
    elF: [40, -240], wrF: [84, -192], curlF: .45, elN: [54, -238], wrN: [96, -188], curlN: .4,
    knF: [110, -143], anF: [124, -28], toF: [152, -12], knN: [150, -148], anN: [166, -28], toN: [198, -12],
  },
  // she follows the line out to the right: spine lengthens, shoulders drop
  look: {
    hip: [0, -153], neck: [26, -336], head: [44, -390], chin: .95, face: -.13, curve: -9, shrug: -2,
    elF: [32, -248], wrF: [76, -198], curlF: .38, elN: [46, -246], wrN: [90, -194], curlN: .3,
    knF: [110, -143], anF: [124, -28], toF: [152, -12], knN: [150, -148], anN: [166, -28], toN: [198, -12],
  },
  // hands to the knees, feet drawn back under the body: the decision to move
  gather: {
    hip: [4, -150], neck: [48, -326], head: [74, -376], chin: .68, face: .12, curve: -14, shrug: 2,
    elF: [56, -250], wrF: [92, -184], curlF: .8, elN: [70, -248], wrN: [106, -180], curlN: .85,
    knF: [ 92, -147], anF: [ 78, -28], toF: [106, -12], knN: [124, -152], anN: [116, -28], toN: [150, -12],
  },
  // weight over the feet, hips leaving the seat, head furthest forward
  rise: {
    hip: [44, -196], neck: [86, -352], head: [110, -400], chin: .55, face: .16, curve: -20, shrug: 6,
    elF: [86, -276], wrF: [104, -206], curlF: .7, elN: [100, -272], wrN: [118, -202], curlN: .75,
    knF: [108, -178], anF: [ 78, -28], toF: [106, -12], knN: [130, -181], anN: [116, -28], toN: [150, -12],
  },
  // pushing up through both legs, arms trailing behind the torso
  push: {
    hip: [58, -262], neck: [80, -426], head: [98, -476], chin: .7, face: .06, curve: -12, shrug: 3,
    elF: [66, -338], wrF: [58, -268], curlF: .55, elN: [80, -334], wrN: [72, -264], curlN: .6,
    knF: [ 88, -196], anF: [ 78, -28], toF: [106, -12], knN: [106, -200], anN: [116, -28], toN: [150, -12],
  },
  // standing, still settling; the site's whole promise is that this is possible
  stand: {
    hip: [62, -300], neck: [70, -470], head: [84, -520], chin: .86, face: -.02, curve: -5, shrug: -3,
    elF: [44, -386], wrF: [34, -304], curlF: .4, elN: [70, -384], wrN: [64, -302], curlN: .42,
    knF: [44, -160], anF: [40, -28], toF: [70, -12], knN: [74, -160], anN: [80, -28], toN: [112, -12],
  },
  // walk, contact: near heel down in front, far toe still behind
  stepA: {
    hip: [62, -296], neck: [70, -466], head: [86, -516], chin: .88, face: -.03, curve: -4, shrug: -2,
    elF: [76, -382], wrF: [96, -306], curlF: .5, elN: [56, -380], wrN: [30, -308], curlN: .5,
    knF: [22, -166], anF: [-6, -30], toF: [22, -6], knN: [104, -170], anN: [136, -34], toN: [168, -28],
  },
  // passing: the trailing leg comes through, the body is at its highest
  pass: {
    hip: [62, -306], neck: [70, -476], head: [86, -526], chin: .88, face: -.02, curve: -4, shrug: -3,
    elF: [66, -390], wrF: [66, -310], curlF: .45, elN: [66, -388], wrN: [62, -310], curlN: .45,
    knF: [70, -170], anF: [56, -40], toF: [88, -22], knN: [64, -166], anN: [70, -28], toN: [102, -12],
  },
  // the other passing position: far foot flat, near foot swinging through
  passB: {
    hip: [62, -306], neck: [70, -476], head: [86, -526], chin: .88, face: -.02, curve: -4, shrug: -3,
    elF: [66, -390], wrF: [66, -310], curlF: .45, elN: [66, -388], wrN: [62, -310], curlN: .45,
    knF: [64, -166], anF: [70, -28], toF: [102, -12], knN: [70, -170], anN: [56, -40], toN: [88, -22],
  },
  // walk, the opposite contact
  stepB: {
    hip: [62, -296], neck: [70, -466], head: [86, -516], chin: .88, face: -.03, curve: -4, shrug: -2,
    elF: [48, -382], wrF: [26, -306], curlF: .5, elN: [84, -380], wrN: [110, -308], curlN: .5,
    knF: [104, -168], anF: [134, -32], toF: [166, -26], knN: [24, -168], anN: [-2, -30], toN: [28, -6],
  },
};

const POSE_FIELDS = Object.keys(KEY.slump);
function lerpPose(a, b, t) {
  const out = {};
  for (const k of POSE_FIELDS) out[k] = Array.isArray(a[k]) ? vlerp(a[k], b[k], t) : lerp(a[k], b[k], t);
  return out;
}

// An authored performance track: [time, key] with the spacing written down, not
// eased into every key. poseAt() is sampled through an exposure track, so only a
// finite set of drawings is ever produced.
function performanceTrack(rows) {
  return t => {
    if (t <= rows[0][0]) return KEY[rows[0][1]];
    for (let i = 1; i < rows.length; i++) {
      if (t < rows[i][0]) {
        const [t0, a, ease] = rows[i - 1], [t1, b] = rows[i];
        const u = (t - t0) / (t1 - t0);
        return lerpPose(KEY[a], KEY[b], (ease || easeIO)(u));
      }
    }
    return KEY[rows[rows.length - 1][1]];
  };
}
