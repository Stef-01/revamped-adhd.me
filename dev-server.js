#!/usr/bin/env node
// Zero-dependency dev server for the ADHDme site.
// - Serves the site folder as static files
// - Live-reloads open browser tabs when any file changes (unless --no-reload)
// Usage: npm run dev   (PORT=3000 npm run dev to change the port)
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const PORT = Number(process.env.PORT) || 5173;
const LIVE = !process.argv.includes('--no-reload');

const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.gif': 'image/gif', '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2', '.txt': 'text/plain',
};

const RELOAD_SNIPPET = `\n<script>(function(){var es=new EventSource('/__reload');es.onmessage=function(e){if(e.data==='reload')location.reload();};})();</script>\n`;
const clients = new Set();

const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);

  if (LIVE && url === '/__reload') {
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
    res.write('retry: 500\n\n');
    clients.add(res);
    req.on('close', () => clients.delete(res));
    return;
  }

  let filePath = path.normalize(path.join(ROOT, url === '/' ? 'index.html' : url));
  if (!filePath.startsWith(ROOT)) { res.writeHead(403); return res.end('Forbidden'); }
  if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) filePath = path.join(filePath, 'index.html');
  if (!fs.existsSync(filePath) && !path.extname(filePath)) filePath += '.html'; // /learn -> learn.html

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end('<h1 style="font-family:system-ui">404 — not found</h1><p><a href="/">Back to home</a></p>');
    }
    const ext = path.extname(filePath).toLowerCase();
    const type = MIME[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
    if (LIVE && ext === '.html') {
      const html = data.toString('utf8');
      return res.end(html.includes('</body>') ? html.replace('</body>', RELOAD_SNIPPET + '</body>') : html + RELOAD_SNIPPET);
    }
    res.end(data);
  });
});

if (LIVE) {
  let timer = null;
  const notify = () => { clearTimeout(timer); timer = setTimeout(() => { for (const c of clients) c.write('data: reload\n\n'); }, 120); };
  try { fs.watch(ROOT, { recursive: true }, (evt, file) => { if (file && !file.startsWith('node_modules') && !file.startsWith('.')) notify(); }); }
  catch (e) { console.warn('File watching unavailable on this platform:', e.message); }
}

server.listen(PORT, () => {
  console.log(`\n  ADHDme dev server running at http://localhost:${PORT}${LIVE ? '  (live reload on)' : ''}\n  Root: ${ROOT}\n  Press Ctrl+C to stop.\n`);
});
