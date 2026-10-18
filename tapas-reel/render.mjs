// Usage: node render.mjs <A|B>[:orange] <out.mp4> [fps]   |   node render.mjs <A|B> --stills t1,t2,...
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const [spec = 'A', out = 'out.mp4', arg3] = process.argv.slice(2);
const [version, bg = ''] = spec.split(':');
const root = path.dirname(new URL(import.meta.url).pathname);
const server = http.createServer((req, res) => {
  const f = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  const type = { '.html': 'text/html', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png' }[path.extname(f)] || 'application/octet-stream';
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end(); } else { res.writeHead(200, { 'content-type': type }); res.end(d); } });
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('pageerror', e));
await page.goto(`http://localhost:${port}/index.html?render&v=${version}&bg=${bg}`);
await page.evaluate(() => window.ready);

if (out === '--stills') {
  for (const t of arg3.split(',').map(Number)) {
    await page.evaluate(t => window.renderFrame(t), t);
    await page.screenshot({ path: path.join(root, 'out', `still_${version}${bg}_${t.toFixed(1)}.png`) });
    console.log('still', t);
  }
} else {
  const fps = Number(arg3 || 30), frames = Math.round(25 * fps);
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-tune', 'grain', '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.renderFrame(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 97 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`${version} frame ${i}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
server.close();
