import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import { join, extname, normalize } from "node:path";
const root = process.argv[2], port = Number(process.argv[3] || 8781);
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".json": "application/json", ".xml": "application/xml", ".txt": "text/plain", ".csv": "text/csv" };
http.createServer(async (req, res) => {
  try {
    let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let f = normalize(join(root, p));
    if (!f.startsWith(root)) { res.writeHead(403); return res.end(); }
    let s = await stat(f).catch(() => null);
    if (s && s.isDirectory()) { f = join(f, "index.html"); s = await stat(f).catch(() => null); }
    if (!s) { const nf = await readFile(join(root, "404.html")).catch(() => ""); res.writeHead(404, { "content-type": types[".html"] }); return res.end(nf); }
    const body = await readFile(f);
    res.writeHead(200, { "content-type": types[extname(f)] || "application/octet-stream", "cache-control": "no-cache" });
    res.end(body);
  } catch (e) { res.writeHead(500); res.end(String(e)); }
}).listen(port, "127.0.0.1");
