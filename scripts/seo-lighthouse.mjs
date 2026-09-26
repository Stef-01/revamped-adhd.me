#!/usr/bin/env node
// Lighthouse scores for a spread of page types, against a running copy of the site.
//
//   npm start                      # serves the site on http://localhost:5173
//   npm run seo:lighthouse         # scores the default pages
//   npm run seo:lighthouse -- how-it-works kate-row   # or just these
//
// BASE_URL points it somewhere else (a preview, or the live site). CHROME_PATH is passed through to
// Lighthouse when Chrome is not where it expects. Full JSON reports go to seo-reports/ (git-ignored).
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync } from 'node:fs';

const LIGHTHOUSE = 'lighthouse@13.5.0';
const BASE = (process.env.BASE_URL || 'http://localhost:5173').replace(/\/$/, '');
const DEFAULT_PAGES = ['index', 'how-it-works', 'the-doctors', 'care-navigator', 'our-story', 'learn',
  'kate-row', 'adhd-psychologist', 'blog-adhd-and-exercise'];
const pages = process.argv.slice(2).length ? process.argv.slice(2) : DEFAULT_PAGES;
const categories = ['performance', 'accessibility', 'best-practices', 'seo'];
mkdirSync('seo-reports', { recursive: true });

const rows = [];
for (const page of pages) {
  const url = `${BASE}/${page === 'index' ? '' : page + '.html'}`;
  const out = `seo-reports/${page}.json`;
  const run = spawnSync('npx', ['-y', LIGHTHOUSE, url, '--quiet', '--output=json', `--output-path=${out}`,
    `--only-categories=${categories.join(',')}`, '--chrome-flags=--headless=new --no-sandbox'],
    { stdio: ['ignore', 'ignore', 'pipe'], encoding: 'utf8' });
  if (run.status !== 0) {
    rows.push({ page, error: (run.stderr || '').trim().split('\n').pop() });
    continue;
  }
  const lhr = JSON.parse(readFileSync(out, 'utf8'));
  const failing = Object.values(lhr.audits)
    .filter(a => a.score !== null && a.score < 0.9 && a.scoreDisplayMode !== 'informative' && a.scoreDisplayMode !== 'manual')
    .map(a => a.id);
  rows.push({ page, ...Object.fromEntries(categories.map(c => [c, Math.round(lhr.categories[c].score * 100)])),
    lcp: lhr.audits['largest-contentful-paint'].displayValue, cls: lhr.audits['cumulative-layout-shift'].displayValue, failing });
}

const pad = (s, n) => String(s).padEnd(n);
console.log(pad('page', 26) + categories.map(c => pad(c.replace('best-practices', 'practices'), 13)).join('') + pad('LCP', 9) + 'CLS');
for (const r of rows) {
  if (r.error) { console.log(pad(r.page, 26) + 'error: ' + r.error); continue; }
  console.log(pad(r.page, 26) + categories.map(c => pad(r[c], 13)).join('') + pad(r.lcp, 9) + r.cls);
}
const failures = {};
for (const r of rows) for (const id of r.failing || []) (failures[id] = failures[id] || []).push(r.page);
if (Object.keys(failures).length) {
  console.log('\nAudits below 90 on at least one page:');
  for (const [id, where] of Object.entries(failures).sort((a, b) => b[1].length - a[1].length)) console.log(`  ${id}: ${where.join(', ')}`);
}
