#!/usr/bin/env node
// Overwhelm check: word rules for every page, measured in a browser the way a reader sees the page.
// Too much text on one screen is hard going for anyone with ADHD, so these limits are strict. The benchmark
// is Lyra Health (lyrahealth.com): a short headline, a one-line subhead, blocks of about 15 words.
//
//   npm start                    # serves the site on http://localhost:5173
//   npm run check:overwhelm      # exit 1 if any page breaks a rule
//
// What is counted: visible words inside <main> at 1280x900, with motion reduced so the page is settled.
// Text inside a closed <details> is not on screen, so it is not counted (its <summary> is). "First screen"
// is the reading text in the top 900px: words outside links and buttons, since a row of clinician cards
// or a button is scanned, not read. "Longest block" is the longest paragraph or list item. The lede is the
// paragraph under the headline; two lines at most. Rules per page type are in RULES.
//
// It also saves a first-screen screenshot of each page, desktop and phone, to seo-reports/overwhelm/, with
// Lyra's home page alongside when the network allows it, and lists every page that gained words since the
// previous run (seo-reports/overwhelm.json). SHOTS=0 skips the screenshots. BASE_URL points it at another
// copy of the site; PLAYWRIGHT_PATH and CHROME_PATH work as in build-og-images.cjs.
const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const ROOT = path.resolve(__dirname, '..');
const BASE = (process.env.BASE_URL || 'http://localhost:5173').replace(/\/$/, '');
const OUT = path.join(ROOT, 'seo-reports');
const SHOTS = process.env.SHOTS !== '0';
const LYRA = 'https://www.lyrahealth.com/';

// words: visible words on the page. fold: reading words on the first screen. block: longest paragraph or
// list item. h1: words in the headline. lede: words in the paragraph under it.
const RULES = {
  core:    { words: 200, fold: 60,  block: 30, h1: 8,  lede: 25 },   // home, how it works, network, story
  hub:     { words: 500, fold: 60,  block: 30, h1: 8,  lede: 25 },   // lists of links: Learn, ADHD care
  search:  { words: 300, fold: 60,  block: 30, h1: 8,  lede: 25 },   // ADHD care by place and profession
  profile: { words: 300, fold: 70,  block: 40, h1: 8,  lede: 25 },   // one clinician: a header card, then a list
  article: { words: 800, fold: 200, block: 60, h1: 12, lede: 40 },   // blog posts
  legal:   { words: 800, fold: 200, block: 60, h1: 8,  lede: 40 },   // privacy, terms and the like
};
const LEGAL = ['privacy', 'terms', 'automated-decisions', 'measurement'];
const HUBS = ['learn', 'adhd-services'];

function kind(slug, html) {
  if (LEGAL.includes(slug)) return 'legal';
  if (HUBS.includes(slug)) return 'hub';
  if (slug.startsWith('blog-')) return 'article';
  if (/<meta property="og:image" content="[^"]*\/assets\/clinicians\//.test(html)) return 'profile';
  if (slug.startsWith('adhd-')) return 'search';
  return 'core';
}

// Runs in the page.
function measure() {
  const main = document.querySelector('main');
  const shown = el => {
    if (el.closest('details:not([open])') && !el.closest('summary')) return false;
    if (el.closest('script,style,svg,[hidden],.sr-only')) return false;
    const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden' && el.getClientRects().length > 0;
  };
  const count = t => (t.match(/[A-Za-z0-9$’'][\w$’'.,%-]*/g) || []).length;
  let words = 0, fold = 0;
  const walk = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  while (walk.nextNode()) {
    const el = walk.currentNode.parentElement;
    const n = el && shown(el) ? count(walk.currentNode.textContent) : 0;
    if (!n) continue;
    words += n;
    if (el.getBoundingClientRect().top + window.scrollY < 880 && !el.closest('a, button')) fold += n;   // 20px of it showing
  }
  const blocks = [...main.querySelectorAll('p, li, dd, blockquote')]
    .filter(el => shown(el) && !el.querySelector('p, li'))
    .map(el => ({ n: count(el.textContent), text: el.textContent.trim().replace(/\s+/g, ' ') }))
    .sort((a, b) => b.n - a.n);
  // The lede is the first paragraph after the headline, before the next section's heading. A hero with no
  // paragraph under its headline has no lede.
  const h1 = main.querySelector('h1');
  const after = el => h1 && (h1.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING);
  const nextHeading = [...main.querySelectorAll('h2')].find(after);
  const lede = h1 && [...main.querySelectorAll('p')].find(p => after(p) && shown(p) && count(p.textContent) >= 3 &&
    !(nextHeading && (nextHeading.compareDocumentPosition(p) & Node.DOCUMENT_POSITION_FOLLOWING)));
  return {
    words, fold,
    block: blocks.length ? blocks[0].n : 0,
    blockText: blocks.length ? blocks[0].text.slice(0, 70) : '',
    h1: h1 ? count(h1.textContent) : 0,
    lede: lede ? count(lede.textContent) : 0,
  };
}

async function open(browser, url, width, height) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
  await page.route(/posthog|google-analytics|googletagmanager|beehiiv/, r => r.abort());
  await page.addInitScript(() => { try { localStorage.setItem('adhdme-privacy-ack', '1'); } catch (e) {} });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.addStyleTag({ content: '.consent-bar{display:none!important}' });
  await page.evaluate(() => document.querySelectorAll('[data-reveal]').forEach(e => e.classList.add('is-visible')));
  await page.waitForTimeout(400);
  return page;
}

(async () => {
  const slugs = fs.readdirSync(ROOT).filter(f => f.endsWith('.html') && !f.startsWith('academy'))
    .map(f => f.replace(/\.html$/, '')).sort();
  const shots = path.join(OUT, 'overwhelm');
  fs.mkdirSync(shots, { recursive: true });
  const previousFile = path.join(OUT, 'overwhelm.json');
  const previous = fs.existsSync(previousFile) ? JSON.parse(fs.readFileSync(previousFile, 'utf8')) : {};

  const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
  const rows = [];
  for (const slug of slugs) {
    const type = kind(slug, fs.readFileSync(path.join(ROOT, slug + '.html'), 'utf8'));
    const url = `${BASE}/${slug === 'index' ? '' : slug + '.html'}`;
    const page = await open(browser, url, 1280, 900);
    const m = await page.evaluate(measure);
    if (SHOTS) await page.screenshot({ path: path.join(shots, `${slug}-desktop.png`) });
    await page.close();
    if (SHOTS) {
      const phone = await open(browser, url, 390, 844);
      await phone.screenshot({ path: path.join(shots, `${slug}-phone.png`) });
      await phone.close();
    }
    const rule = RULES[type];
    const broken = Object.keys(rule).filter(k => m[k] > rule[k]);
    rows.push({ slug, type, ...m, broken });
  }

  // Lyra, for a side-by-side look. The environment's network policy may block it; the rules above stand either way.
  let lyra = 'not reachable from this network, so compare against the pattern in the header comment';
  if (SHOTS) {
    try {
      const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
      await page.goto(LYRA, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(1500);
      await page.screenshot({ path: path.join(shots, 'lyra-desktop.png') });
      await page.close();
      lyra = 'saved as seo-reports/overwhelm/lyra-desktop.png';
    } catch (e) { /* blocked or offline */ }
  }
  await browser.close();

  const pad = (s, n) => String(s).padEnd(n);
  console.log(pad('page', 38) + pad('type', 9) + pad('words', 8) + pad('first', 8) + pad('block', 8) + pad('h1', 5) + pad('lede', 6) + 'breaks');
  for (const r of rows) {
    const grew = previous[r.slug] && r.words > previous[r.slug].words ? ` (+${r.words - previous[r.slug].words})` : '';
    console.log(pad(r.slug, 38) + pad(r.type, 9) + pad(r.words + grew, 8) + pad(r.fold, 8) + pad(r.block, 8) +
      pad(r.h1, 5) + pad(r.lede, 6) + r.broken.join(', '));
  }
  console.log('\nLimits (words, first screen, longest block, h1, lede):');
  for (const [type, r] of Object.entries(RULES)) console.log(`  ${pad(type, 8)} ${r.words}, ${r.fold}, ${r.block}, ${r.h1}, ${r.lede}`);
  const grown = rows.filter(r => previous[r.slug] && r.words > previous[r.slug].words);
  if (Object.keys(previous).length) {
    console.log(grown.length ? `\nGained words since the last run: ${grown.map(r => `${r.slug} +${r.words - previous[r.slug].words}`).join(', ')}`
      : '\nNo page gained words since the last run.');
  }
  const failing = rows.filter(r => r.broken.length);
  for (const r of failing.filter(r => r.broken.includes('block'))) console.log(`  longest block on ${r.slug}: "${r.blockText}…"`);
  if (SHOTS) console.log(`\nFirst-screen screenshots: seo-reports/overwhelm/. Lyra: ${lyra}.`);
  fs.writeFileSync(previousFile, JSON.stringify(Object.fromEntries(rows.map(r => [r.slug, r])), null, 1));
  console.log(failing.length ? `\noverwhelm check: ${failing.length} page(s) over the limits` : '\noverwhelm check: every page within the limits');
  process.exit(failing.length ? 1 : 0);
})();
