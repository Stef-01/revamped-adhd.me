// node --test tests/matching.test.js — the pure parts of matching.js: what the flags allow, what the one-field
// form accepts, the mail-app route, and that an endpoint request goes out once and is confirmed only when the
// server says so.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const m = require('../matching.js');

const MAILTO = { pilotEnabled: true, intakeOpen: true, contactEmail: 'info@adhdme.au', requestEndpoint: '', copyVersion: 'pilot-test' };
const ENDPOINT = { ...MAILTO, requestEndpoint: '/api/matching', collectionNoticeApproved: true, approvedCollectionNoticeVersion: 'v1', retentionPolicyText: 'Deleted 90 days after close.' };
const GOOD = { email: 'testy@example.com', consent: true };

function committedConfig() {
  const src = fs.readFileSync(path.join(__dirname, '..', 'matching-config.js'), 'utf8');
  const w = {}; new Function('window', src)(w); return w.ADHDME_MATCHING;
}

test('the committed configuration opens only the mail-app route, which stores nothing', () => {
  const cfg = committedConfig();
  const d = m.decide(cfg);
  assert.equal(cfg.requestEndpoint, '');
  assert.equal(cfg.collectionNoticeApproved, false);
  assert.equal(d.route === 'mailto' || d.enabled === false, true);
  if (d.enabled) assert.equal(d.route, 'mailto');
});

test('decide: the appointment schedule is preferred when set, and needs no site-side approvals', () => {
  assert.deepEqual(m.decide({ ...MAILTO, appointmentUrl: 'https://calendar.google.com/calendar/appointments/schedules/x?gv=true' }),
                   { enabled: true, open: true, route: 'appointment', reason: '' });
  assert.equal(m.decide({ ...ENDPOINT, appointmentUrl: 'https://calendar.google.com/x?gv=true' }).route, 'appointment');
});

test('decide: off, no route, paused, and the endpoint route’s approvals', () => {
  assert.deepEqual(m.decide({}), { enabled: false, open: false, route: '', reason: 'disabled' });
  assert.equal(m.decide({ pilotEnabled: true, intakeOpen: true }).reason, 'no-route');
  assert.equal(m.decide({ ...MAILTO, intakeOpen: false }).reason, 'paused');
  assert.deepEqual(m.decide(MAILTO), { enabled: true, open: true, route: 'mailto', reason: '' });
  assert.equal(m.decide({ ...ENDPOINT, collectionNoticeApproved: false }).reason, 'notice-unapproved');
  assert.equal(m.decide({ ...ENDPOINT, retentionPolicyText: '' }).reason, 'no-retention');
  assert.deepEqual(m.decide(ENDPOINT), { enabled: true, open: true, route: 'endpoint', reason: '' });
});

test('validate: an email and the ticked box pass', () => {
  assert.deepEqual(m.validate(GOOD), { ok: true, errors: {} });
});

test('validate: missing consent alone blocks', () => {
  assert.deepEqual(Object.keys(m.validate({ ...GOOD, consent: false }).errors), ['consent']);
});

test('validate: a bad email is named and nothing else is', () => {
  assert.deepEqual(Object.keys(m.validate({ email: 'nope', consent: true }).errors), ['email']);
  assert.deepEqual(Object.keys(m.validate({}).errors).sort(), ['consent', 'email']);
});

test('mailto: addressed to the team with a fixed message, carrying nothing the person typed', () => {
  const href = m.mailtoHref(MAILTO);
  assert.ok(href.startsWith('mailto:info@adhdme.au?subject='));
  assert.ok(decodeURIComponent(href).includes('help finding the right clinician'));
  assert.ok(!href.includes('testy'));
});

test('payload: only the email, consent and labels', () => {
  const p = m.payload({ email: ' testy@example.com ', consent: true }, ENDPOINT);
  assert.deepEqual(p, { email: 'testy@example.com', consent: true, collection_notice_version: 'v1', copy_version: 'pilot-test' });
});

test('submit: success only when the server accepts', async () => {
  const calls = [];
  const r = await m.createSubmitter(async (url, init) => { calls.push([url, init]); return { ok: true, status: 202 }; }, ENDPOINT)(GOOD);
  assert.deepEqual(r, { accepted: true });
  assert.equal(calls.length, 1);
  assert.equal(calls[0][1].method, 'POST');
  assert.equal(JSON.parse(calls[0][1].body).email, 'testy@example.com');
});

test('submit: a server error or a network failure asks for a retry', async () => {
  const r1 = await m.createSubmitter(async () => ({ ok: false, status: 500 }), ENDPOINT)(GOOD);
  assert.equal(r1.accepted, false); assert.equal(r1.retry, true);
  const r2 = await m.createSubmitter(async () => { throw new Error('offline'); }, ENDPOINT)(GOOD);
  assert.equal(r2.accepted, false); assert.equal(r2.retry, true);
});

test('submit: a second press while one request is in flight does not send again', async () => {
  let resolve; let calls = 0;
  const submit = m.createSubmitter(() => { calls++; return new Promise(res => { resolve = res; }); }, ENDPOINT);
  const first = submit(GOOD);
  assert.deepEqual(await submit(GOOD), { accepted: false, busy: true });
  resolve({ ok: true, status: 202 });
  assert.deepEqual(await first, { accepted: true });
  assert.equal(calls, 1);
});

test('submit: a request that never answers times out into the retry state', async () => {
  const never = (url, init) => new Promise((res, rej) => { init.signal && init.signal.addEventListener('abort', () => rej(new Error('aborted'))); });
  const r = await m.createSubmitter(never, ENDPOINT, 20)(GOOD);
  assert.equal(r.accepted, false); assert.equal(r.retry, true);
});
