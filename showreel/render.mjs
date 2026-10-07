// Renders reel.html frame-by-frame in headless Chromium and pipes PNGs to ffmpeg.
//   node render.mjs                 → showreel_video.mp4 (no audio)
//   node render.mjs --frames 0,60   → preview PNGs in ./preview
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const dir = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const framesArg = args.includes('--frames') ? args[args.indexOf('--frames') + 1] : null;
const out = args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(dir, 'showreel_video.mp4');

const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => { console.error('[pageerror]', e); process.exit(1); });
await page.goto('file://' + path.join(dir, 'reel.html') + '?render=1');
await page.evaluate(() => window.ready);
const clip = { x: 0, y: 0, width: 1920, height: 1080 };

if (framesArg) {
  mkdirSync(path.join(dir, 'preview'), { recursive: true });
  for (const f of framesArg.split(',').map(Number)) {
    await page.evaluate(f => window.renderFrame(f), f);
    writeFileSync(path.join(dir, 'preview', `f${String(f).padStart(4, '0')}.png`), await page.screenshot({ type: 'png', clip }));
  }
} else {
  const total = 900;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '60', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = 0; f < total; f++) {
    await page.evaluate(f => window.renderFrame(f), f);
    const buf = await page.screenshot({ type: 'png', clip });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 60 === 0) console.log(`frame ${f}/${total}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
