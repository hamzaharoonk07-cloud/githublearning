// Renders index.html frame by frame with headless Chromium.
//   node render.mjs                 → frames/00000.jpg … + cues.json
//   node render.mjs --stills 1,5.8  → stills/t1.png, stills/t5.8.png (for checking layout)
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const dir = path.dirname(fileURLToPath(import.meta.url));
// the globally installed Playwright (ESM imports ignore NODE_PATH)
const { chromium } = createRequire(import.meta.url)('playwright');
const url = 'file://' + path.join(dir, 'index.html') + '?render';
const stillsArg = process.argv.indexOf('--stills');
const WORKERS = 4;

const browser = await chromium.launch();
async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto(url);
  await page.evaluate(async () => {
    await Promise.all(['800 100px "Bricolage Grotesque"', '700 40px "Plus Jakarta Sans"', '500 30px "JetBrains Mono"',
      '400 40px "Noto Nastaliq Urdu"'].map(f => document.fonts.load(f, 'abcاردو')));
    await document.fonts.ready;
  });
  return page;
}

if (stillsArg > 0) {
  mkdirSync(path.join(dir, 'stills'), { recursive: true });
  const page = await openPage();
  for (const t of process.argv[stillsArg + 1].split(',').map(Number)) {
    await page.evaluate(t => window.render(t), t);
    await page.screenshot({ path: path.join(dir, 'stills', `t${t}.png`) });
  }
} else {
  mkdirSync(path.join(dir, 'frames'), { recursive: true });
  const first = await openPage();
  const { fps, duration, cues } = await first.evaluate(() => ({ fps: window.FPS, duration: window.DURATION, cues: window.CUES }));
  writeFileSync(path.join(dir, 'cues.json'), JSON.stringify({ fps, duration, cues }, null, 1));
  const total = Math.round(fps * duration);
  const pages = [first, ...await Promise.all(Array.from({ length: WORKERS - 1 }, openPage))];
  let done = 0;
  await Promise.all(pages.map(async (page, w) => {
    for (let f = w; f < total; f += WORKERS) {
      await page.evaluate(t => window.render(t), f / fps);
      await page.screenshot({ path: path.join(dir, 'frames', String(f).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 94 });
      if (++done % 60 === 0) console.log(`${done}/${total}`);
    }
  }));
}
await browser.close();
