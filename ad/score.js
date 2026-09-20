'use strict';
// Twenty seconds, written for the cut. A clock ticks over the queue and stops
// the instant the knot lets go; the chords open from a suspended second into a
// plain major as she stands; two bells mark the two doors; the last note lands
// on the dot. Original, synthesised through Web Audio - no samples, nothing
// licensed from anywhere.

function score(ac, t0, destination) {
  const master = ac.createGain();
  master.gain.setValueAtTime(.72, t0);
  master.gain.setValueAtTime(.72, t0 + 19.1);
  master.gain.linearRampToValueAtTime(0, t0 + 20);
  const comp = ac.createDynamicsCompressor();
  comp.threshold.value = -17; comp.knee.value = 16; comp.ratio.value = 2.6; comp.attack.value = .02; comp.release.value = .26;
  master.connect(comp); comp.connect(destination);

  const dry = ac.createGain(); dry.gain.value = .86; dry.connect(master);
  const verb = ac.createConvolver(), ir = ac.createBuffer(2, Math.floor(ac.sampleRate * 2.2), ac.sampleRate), rr = rng(509);
  for (let s = 0; s < 2; s++) { const d = ir.getChannelData(s); for (let i = 0; i < d.length; i++) d[i] = (rr() * 2 - 1) * Math.exp(-i / ac.sampleRate * 3.1) * (i > ac.sampleRate * .014 ? 1 : 0); }
  verb.buffer = ir;
  const wet = ac.createGain(); wet.gain.value = .23; verb.connect(wet); wet.connect(master);
  const send = (node, amt = .3, pan = 0) => { const p = ac.createStereoPanner(); p.pan.value = pan; node.connect(p); p.connect(dry); const s = ac.createGain(); s.gain.value = amt; p.connect(s); s.connect(verb); };
  const hz = n => 440 * 2 ** ((n - 69) / 12);

  // felt piano: a few inharmonic partials under a fast decay
  function key(n, t, d = 2.4, v = .2, pan = 0) {
    if (t >= 19.6) return;
    const g = ac.createGain(), f = ac.createBiquadFilter();
    f.type = 'lowpass'; f.frequency.value = 2900; g.connect(f); send(f, .6, pan);
    g.gain.setValueAtTime(0, t0 + t); g.gain.linearRampToValueAtTime(v, t0 + t + .008);
    g.gain.exponentialRampToValueAtTime(v * .24, t0 + t + .28); g.gain.exponentialRampToValueAtTime(.0001, t0 + t + d);
    for (const [ratio, amt] of [[1, 1], [2.003, .28], [3.01, .09], [4.02, .04]]) {
      const o = ac.createOscillator(), a = ac.createGain();
      o.type = 'sine'; o.frequency.value = hz(n) * ratio; a.gain.value = amt;
      o.connect(a); a.connect(g); o.start(t0 + t); o.stop(t0 + t + d + .05);
    }
  }
  // bowed pad
  function pad(notes, t, d, v = .03) {
    for (let j = 0; j < notes.length; j++) {
      const e = ac.createGain(), f = ac.createBiquadFilter();
      f.type = 'lowpass'; f.frequency.setValueAtTime(520, t0 + t); f.frequency.linearRampToValueAtTime(1280, t0 + t + d * .75);
      e.connect(f); send(f, .7, (j / (notes.length - 1 || 1) - .5) * .7);
      e.gain.setValueAtTime(0, t0 + t); e.gain.linearRampToValueAtTime(v, t0 + t + Math.min(.9, d * .28));
      e.gain.setValueAtTime(v * .9, t0 + t + d * .7); e.gain.exponentialRampToValueAtTime(.0001, t0 + t + d + 1);
      for (const det of [-5, 5]) { const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = hz(notes[j]); o.detune.value = det; o.connect(e); o.start(t0 + t); o.stop(t0 + t + d + 1.05); }
    }
  }
  function bell(n, t, v = .1) {
    const e = ac.createGain(); send(e, .9, .3);
    e.gain.setValueAtTime(v, t0 + t); e.gain.exponentialRampToValueAtTime(.0001, t0 + t + 3.2);
    for (const [r, k] of [[1, .7], [2, .18], [3.98, .06]]) { const o = ac.createOscillator(), g = ac.createGain(); o.frequency.value = hz(n) * r; g.gain.value = k; o.connect(g); g.connect(e); o.start(t0 + t); o.stop(t0 + t + 3.25); }
  }
  // the clock in the waiting room
  function tick(t, v = .05, seed = 1) {
    const buf = ac.createBuffer(1, Math.ceil(ac.sampleRate * .05), ac.sampleRate), d = buf.getChannelData(0), r = rng(seed);
    for (let i = 0; i < d.length; i++) d[i] = (r() * 2 - 1) * Math.pow(1 - i / d.length, 7);
    const s = ac.createBufferSource(); s.buffer = buf;
    const f = ac.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = 2400; f.Q.value = 1.6;
    const g = ac.createGain(); g.gain.value = v;
    s.connect(f); f.connect(g); send(g, .2, -.25); s.start(t0 + t);
  }
  function air(t, d, v, seed = 1, freq = 900) {
    const buf = ac.createBuffer(1, Math.ceil(ac.sampleRate * d), ac.sampleRate), data = buf.getChannelData(0), r = rng(seed);
    for (let i = 0; i < data.length; i++) data[i] = (r() * 2 - 1) * Math.sin(Math.PI * i / data.length) ** 2;
    const s = ac.createBufferSource(); s.buffer = buf;
    const f = ac.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = freq; f.Q.value = .6;
    const g = ac.createGain(); g.gain.value = v;
    s.connect(f); f.connect(g); send(g, .5, .1); s.start(t0 + t);
  }

  // 0.0-4.75  the queue: one held chord, a clock, nothing moving
  pad([45, 52, 57], 0, 4.4, .028);
  key(69, .2, 3.2, .1, -.2); key(64, 2.1, 3.0, .085, .18);
  for (let i = 0; i < 9; i++) tick(.45 + i * .52, .045 + (i % 2) * .012, 3 + i);

  // 4.75-8.5  the knot lets go: the tick stops, the line takes the room with it
  air(4.6, 1.5, .10, 71, 1500);
  pad([45, 52, 59, 64], 4.8, 3.4, .034);
  key(76, 4.9, 2.6, .17, .06); key(71, 5.5, 2.2, .12, -.14); key(69, 6.4, 2.6, .12, .2);
  key(64, 7.3, 3.0, .11, -.1);

  // 8.5-13.25  two ways in, and the weight coming off the chair
  pad([45, 52, 57, 64], 8.6, 4.4, .04);
  bell(81, 8.7, .085);          // the yellow rule
  bell(76, 9.9, .075);          // the blue rule
  key(72, 8.6, 2.4, .14, -.18); key(76, 10.4, 2.4, .13, .2);
  air(11.2, .9, .05, 77, 700);  // the push out of the seat
  key(79, 11.5, 2.8, .16, .04); key(81, 12.4, 2.6, .15, -.12);

  // 13.25-17.25  walking: a plain major, a step on every other beat
  pad([50, 57, 62, 66], 13.3, 4.2, .042);
  const walk = [[13.4, 74], [13.9, 78], [14.4, 81], [14.9, 78], [15.4, 83], [15.9, 81], [16.4, 86], [16.9, 83]];
  walk.forEach(([t, n], i) => key(n, t, 2.2, .105 + (i % 2) * .028, (i % 2 ? 1 : -1) * .22));
  key(50, 13.3, 3.4, .12, 0); key(57, 15.4, 3.0, .095, 0);

  // 17.25-20  the card: the mark, then the dot
  pad([50, 57, 62, 69], 17.3, 2.3, .05);
  key(62, 17.3, 3.2, .2, -.1); key(69, 17.55, 3.0, .15, .12);
  bell(86, 17.9, .12);          // the logo settles
  key(74, 18.5, 2.6, .17, .04);
  bell(93, 18.55, .05);         // the dot lands
}
