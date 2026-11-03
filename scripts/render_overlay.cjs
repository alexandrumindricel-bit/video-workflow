#!/usr/bin/env node
/* Step 6: render captions + motion graphics as a transparent 1080x1920 ProRes 4444 layer.
   Usage: node render_overlay.cjs WORKDIR [--workers 3]
   Reads WORKDIR/{storyboard.json, words.json, layout.json, segments.json}; writes WORKDIR/overlay.mov
   Frames whose visual state did not change are reused (no new screenshot), so holds are cheap. */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const FPS = 30;
const work = path.resolve(process.argv[2]);
const wi = process.argv.indexOf('--workers');
const WORKERS = wi > 0 ? parseInt(process.argv[wi + 1]) : 3;
const read = f => JSON.parse(fs.readFileSync(path.join(work, f), 'utf8'));

async function renderRange(browser, data, f0, f1, outFile, layer) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
  page.on('pageerror', e => { console.error('[page error]', e.message); process.exitCode = 1; });
  await page.goto('file://' + path.join(__dirname, '..', 'renderer', 'overlay.html'));
  await page.evaluate(d => window.init(d), { ...data, layer });
  const ff = spawn('ffmpeg', ['-nostdin', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0', outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
  const write = buf => new Promise(r => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', r); else r(); });
  let lastSig = null, lastBuf = null, shots = 0;
  for (let f = f0; f < f1; f++) {
    const sig = await page.evaluate(t => window.renderAt(t), f / FPS);
    if (sig !== lastSig || !lastBuf) {
      lastBuf = await page.screenshot({ omitBackground: true, type: 'png' });
      lastSig = sig; shots++;
    }
    await write(lastBuf);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c))));
  await page.close();
  return shots;
}

(async () => {
  const sb = read('storyboard.json');
  // flash / light-leak transitions are drawn in the overlay layer (glitch + punch are done in compose.py)
  const extra = (sb.transitions || []).filter(t => t.kind === 'flash' || t.kind === 'leak').map(t => ({
    type: t.kind, start: t.at - (t.kind === 'leak' ? 0.25 : 0), end: t.at + (t.dur || (t.kind === 'leak' ? 0.35 : 0.2)),
    peak: t.peak, color: t.color, sfx: null }));
  sb.elements = [...(sb.elements || []), ...extra];
  const data = { storyboard: sb, words: read('words.json'), layout: read('layout.json') };
  const duration = read('segments.json').duration;
  const total = Math.round(duration * FPS);
  const BACK_TYPES = new Set(['backdrop', 'glass', 'cover', 'wall']);
  const layerOf = el => el.type === 'orbit' ? 'both' : (el.layer || (BACK_TYPES.has(el.type) ? 'back' : 'front'));
  const layers = ['front'];
  if (sb.elements.some(el => layerOf(el) !== 'front')) layers.push('back');
  const backFile = path.join(work, 'overlay_back.mov');
  if (!layers.includes('back') && fs.existsSync(backFile)) fs.unlinkSync(backFile);
  const browser = await chromium.launch();
  const t0 = Date.now();
  for (const layer of layers) {
    const per = Math.ceil(total / WORKERS);
    const parts = [];
    for (let w = 0; w < WORKERS; w++) {
      const a = w * per, b = Math.min(total, (w + 1) * per);
      if (a < b) parts.push({ a, b, file: path.join(work, `overlay_${layer}_part${w}.mov`) });
    }
    const shots = await Promise.all(parts.map(p => renderRange(browser, data, p.a, p.b, p.file, layer)));
    const list = path.join(work, `overlay_${layer}_parts.txt`);
    fs.writeFileSync(list, parts.map(p => `file '${p.file}'`).join('\n'));
    const outName = layer === 'front' ? 'overlay.mov' : 'overlay_back.mov';
    await new Promise((res, rej) => spawn('ffmpeg', ['-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy',
      path.join(work, outName)], { stdio: 'inherit' }).on('close', c => c === 0 ? res() : rej(new Error('concat ' + c))));
    parts.forEach(p => fs.unlinkSync(p.file));
    console.log(`${outName}: ${total} frames (${shots.reduce((a, b) => a + b, 0)} unique) in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
