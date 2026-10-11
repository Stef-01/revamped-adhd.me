// node --test tests/ — the pure parts of matching.js: what the flags allow, what the form accepts, and that a
// request goes out once, is confirmed only when the server says so, and keeps its answers out of everything else.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const m = require('../matching.js');

const OPEN = { pilotEnabled: true, intakeOpen: true, requestEndpoint: '/api/matching', collectionNoticeApproved: true,
               approvedCollectionNoticeVersion: 'v1', retentionPolicyText: 'Deleted 90 days after close.', copyVersion: 'pilot-test' };
const GOOD = { scope: 'self-adult', service: 'psychology', state: 'QLD', locality: '4000', mode: 'either', budget: 'not-sure',
               priorities: ['availability', 'cost'], firstName: 'Testy', email: 'testy@example.com', consent: true };

test('the committed configuration keeps everything off', () => {
  const fs = require('node:fs');
  const src = fs.readFileSync(require('node:path').join(__dirname, '..', 'matching-config.js'), 'utf8');
  const sandbox = { window: {} };
  new Function('window', src)(sandbox.window);
  const d = m.decide(sandbox.window.ADHDME_MATCHING);
  assert.equal(d.enabled, false);
  assert.equal(d.open, false);
  assert.equal(sandbox.window.ADHDME_MATCHING.requestEndpoint, '');
});

test('decide: each missing approval keeps intake closed, with a reason', () => {
  assert.deepEqual(m.decide({}), { enabled: false, open: false, reason: 'disabled' });
  assert.equal(m.decide({ ...OPEN, intakeOpen: false }).reason, 'paused');
  assert.equal(m.decide({ ...OPEN, requestEndpoint: '' }).reason, 'no-endpoint');
  assert.equal(m.decide({ ...OPEN, collectionNoticeApproved: false }).reason, 'notice-unapproved');
  assert.equal(m.decide({ ...OPEN, approvedCollectionNoticeVersion: '' }).reason, 'notice-unapproved');
  assert.equal(m.decide({ ...OPEN, retentionPolicyText: '' }).reason, 'no-retention');
  assert.deepEqual(m.decide(OPEN), { enabled: true, open: true, reason: '' });
});

test('validate: a complete in-scope request passes', () => {
  assert.deepEqual(m.validate(GOOD), { ok: true, outOfScope: false, errors: {} });
});

test('validate: outside the pilot scope is explained, not treated as an error', () => {
  const v = m.validate({ ...GOOD, scope: 'other' });
  assert.equal(v.ok, false);
  assert.equal(v.outOfScope, true);
  assert.deepEqual(v.errors, {});
  assert.equal(m.validate({ ...GOOD, scope: '' }).errors.scope, 'Choose who the care is for.');
});

test('validate: every required field is named, and the rest of the answers are untouched', () => {
  const v = m.validate({ scope: 'self-adult', priorities: [], consent: false });
  assert.deepEqual(Object.keys(v.errors).sort(), ['consent', 'email', 'firstName', 'locality', 'mode', 'service', 'state']);
});

test('validate: missing consent alone blocks the request', () => {
  const v = m.validate({ ...GOOD, consent: false });
  assert.deepEqual(Object.keys(v.errors), ['consent']);
});

test('validate: priorities are capped at two and must come from the list', () => {
  assert.equal(m.validate({ ...GOOD, priorities: ['availability', 'cost', 'location'] }).errors.priorities, 'Choose up to two.');
  assert.equal(m.validate({ ...GOOD, priorities: ['speed'] }).errors.priorities, 'Choose from the options listed.');
  assert.equal(m.validate({ ...GOOD, priorities: [] }).ok, true);
});

test('validate: budget has no invented price bands', () => {
  assert.equal(m.validate({ ...GOOD, budget: '' }).ok, true);
  assert.equal(m.validate({ ...GOOD, budget: 'prefer-not-to-say' }).ok, true);
  assert.equal(m.validate({ ...GOOD, budget: '$100-200' }).ok, false);
});

test('validate: free text is short and plain, so it cannot carry a medical history', () => {
  assert.equal(m.validate({ ...GOOD, locality: 'x'.repeat(41) }).ok, false);
  assert.equal(m.validate({ ...GOOD, locality: 'Diagnosed 2019; on dex 20mg' }).ok, false);
  assert.equal(m.validate({ ...GOOD, firstName: 'A'.repeat(41) }).ok, false);
  assert.equal(m.validate({ ...GOOD, email: 'not-an-email' }).ok, false);
});

test('payload: only the collected fields, trimmed, plus the notice version agreed to', () => {
  const p = m.payload({ ...GOOD, locality: ' 4000 ', firstName: ' Testy ' }, OPEN);
  assert.deepEqual(Object.keys(p).sort(), ['budget', 'collection_notice_version', 'consent', 'copy_version', 'email', 'first_name', 'locality', 'mode', 'priorities', 'service', 'state']);
  assert.equal(p.locality, '4000');
  assert.equal(p.first_name, 'Testy');
  assert.equal(p.collection_notice_version, 'v1');
});

test('submit: success only when the server accepts', async () => {
  const calls = [];
  const fetchOk = async (url, init) => { calls.push([url, init]); return { ok: true, status: 202 }; };
  const r = await m.createSubmitter(fetchOk, OPEN)(GOOD);
  assert.deepEqual(r, { accepted: true });
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], '/api/matching');
  assert.equal(calls[0][1].method, 'POST');
  assert.equal(JSON.parse(calls[0][1].body).email, 'testy@example.com');
});

test('submit: a server error or a network failure asks for a retry and keeps nothing', async () => {
  const r1 = await m.createSubmitter(async () => ({ ok: false, status: 500 }), OPEN)(GOOD);
  assert.equal(r1.accepted, false); assert.equal(r1.retry, true); assert.equal(r1.status, 500);
  const r2 = await m.createSubmitter(async () => { throw new Error('offline'); }, OPEN)(GOOD);
  assert.equal(r2.accepted, false); assert.equal(r2.retry, true);
});

test('submit: a second press while one request is in flight does not send again', async () => {
  let resolve; let calls = 0;
  const slow = () => { calls++; return new Promise(res => { resolve = res; }); };
  const submit = m.createSubmitter(slow, OPEN);
  const first = submit(GOOD);
  const second = await submit(GOOD);
  assert.deepEqual(second, { accepted: false, busy: true });
  resolve({ ok: true, status: 202 });
  assert.deepEqual(await first, { accepted: true });
  assert.equal(calls, 1);
  // and once it has settled, a genuine retry is allowed
  assert.deepEqual(await m.createSubmitter(async () => ({ ok: true }), OPEN)(GOOD), { accepted: true });
});

test('submit: a request that never answers times out into the retry state', async () => {
  const never = (url, init) => new Promise((res, rej) => { init.signal && init.signal.addEventListener('abort', () => rej(new Error('aborted'))); });
  const r = await m.createSubmitter(never, OPEN, 20)(GOOD);
  assert.equal(r.accepted, false); assert.equal(r.retry, true);
});
