#!/usr/bin/env node
// Social share images, 1200x630 (the size platforms crop to):
//   - the blog: each cover in assets/blog/*.svg, centred on a PNG in assets/blog/og/. Social platforms do not
//     accept SVG for og:image.
//   - clinicians: the whole square portrait beside the name and role, as a JPEG in assets/clinicians/og/.
//     A square portrait cropped to 1.91:1 by a platform loses the top of the head.
//
//   node scripts/build-og-images.cjs
//
// Re-run after build-blog.py changes a cover, or after build-profiles.py writes a new or renamed clinician
// (the cards read each profile's structured data), then run build-profiles.py again so the profile uses its
// card. Needs Playwright: `npm i -D playwright && npx playwright install chromium`, or point PLAYWRIGHT_PATH
// at an existing install and CHROME_PATH at a Chromium binary.
const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const ROOT = path.resolve(__dirname, '..');
const SITE = 'https://www.adhdme.au';
const COVERS = path.join(ROOT, 'assets/blog');
const OUT = path.join(COVERS, 'og');
const GROUND = '#f6ecce';   // the covers' own background, so the padding either side is invisible
const CARDS = path.join(ROOT, 'assets/clinicians/og');

const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const dataUri = (file, type) => `data:${type};base64,${fs.readFileSync(file).toString('base64')}`;

// Each profile's name, role and portrait, from the ProfilePage structured data build-profiles.py writes.
function clinicians() {
  const out = [];
  for (const file of fs.readdirSync(ROOT).filter(f => f.endsWith('.html')).sort()) {
    const text = fs.readFileSync(path.join(ROOT, file), 'utf8');
    const graph = [...text.matchAll(/<script type="application\/ld\+json">(.*?)<\/script>/gs)]
      .flatMap(m => JSON.parse(m[1])['@graph'] || []);
    const page = graph.find(n => n['@type'] === 'ProfilePage');
    if (!page) continue;
    const person = graph.find(n => n['@id'] === page.mainEntity['@id']);
    if (!page.name.startsWith(person.name + ', ')) throw new Error(`${file}: page name does not start with "${person.name}, "`);
    const portrait = person.image.replace(SITE + '/', '');
    out.push({ id: path.basename(portrait, '.jpg'), name: person.name, role: page.name.slice(person.name.length + 2), portrait });
  }
  return out;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  fs.mkdirSync(CARDS, { recursive: true });
  const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  const covers = fs.readdirSync(COVERS).filter(f => f.endsWith('.svg')).sort();
  for (const file of covers) {
    const svg = fs.readFileSync(path.join(COVERS, file), 'utf8').replace('<svg ', '<svg width="1120" height="630" ');
    await page.setContent(`<!doctype html><body style="margin:0;width:1200px;height:630px;background:${GROUND};`
      + `display:flex;align-items:center;justify-content:center">${svg}</body>`);
    await page.screenshot({ path: path.join(OUT, file.replace(/\.svg$/, '.png')) });
    console.log('wrote  assets/blog/og/' + file.replace(/\.svg$/, '.png'));
  }

  // The wordmark is lifted from the site's own share card (its top left), so every card carries the same lockup.
  const font = dataUri(path.join(ROOT, 'assets/fonts/plus-jakarta-sans-latin.woff2'), 'font/woff2');
  const brand = dataUri(path.join(ROOT, 'assets/brand/og.png'), 'image/png');
  for (const c of clinicians()) {
    await page.setContent(`<!doctype html><html><head><style>
@font-face{font-family:'Plus Jakarta Sans';font-weight:200 800;src:url(${font}) format('woff2')}
body{margin:0;width:1200px;height:630px;position:relative;background:#f1bc31;font-family:'Plus Jakarta Sans';-webkit-font-smoothing:antialiased}
.mark{position:absolute;left:60px;top:60px;width:150px;height:100px;background:url(${brand}) -60px -60px no-repeat}
img{position:absolute;left:642px;top:72px;width:486px;height:486px;border-radius:24px;object-fit:cover;object-position:center 30%}
.text{position:absolute;left:72px;bottom:72px;width:520px;color:#1a1c1c}
h1{margin:0;font-size:64px;line-height:1.05;font-weight:800;letter-spacing:-2px}
p{margin:20px 0 0;font-size:28px;line-height:1.3;font-weight:600;color:rgba(26,28,28,.85)}
</style></head><body><div class="mark"></div><img src="${dataUri(path.join(ROOT, c.portrait), 'image/jpeg')}" alt="">
<div class="text"><h1>${esc(c.name)}</h1><p>${esc(c.role)}</p></div></body></html>`);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(CARDS, c.id + '.jpg'), type: 'jpeg', quality: 85 });
    console.log(`wrote  assets/clinicians/og/${c.id}.jpg`);
  }
  await browser.close();
})();
