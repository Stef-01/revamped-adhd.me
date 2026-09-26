#!/usr/bin/env node
// Social share images for the blog: each cover in assets/blog/*.svg, centred on a 1200x630 PNG in
// assets/blog/og/. Social platforms do not accept SVG for og:image, and 1200x630 is the size they crop to.
//
//   node scripts/build-og-images.cjs
//
// Re-run after build-blog.py changes a cover. Needs Playwright: `npm i -D playwright && npx playwright
// install chromium`, or point PLAYWRIGHT_PATH at an existing install and CHROME_PATH at a Chromium binary.
const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const ROOT = path.resolve(__dirname, '..');
const COVERS = path.join(ROOT, 'assets/blog');
const OUT = path.join(COVERS, 'og');
const GROUND = '#f6ecce';   // the covers' own background, so the padding either side is invisible

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
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
  await browser.close();
})();
