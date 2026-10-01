// Pictures and checks of pages in one headless Chrome, driven over the DevTools protocol (Node 22+).
//   node site/qa.mjs jobs.json
// jobs.json: [{"url": "http://127.0.0.1:8781/tr/", "out": "a.png", "w": 1440, "h": 900, "dpr": 2, "mobile": false,
//              "lang": "tr-TR,tr", "scheme": "dark", "reduce": false, "wait": 900,
//              "scrollTo": 1200 | ".selector" | {"sel": ".hero", "p": 0.5} (pinned section progress),
//              "steps": 30 (scroll there frame by frame, like a person),
//              "js": "optional async code; a returned value is printed",
//              "full": false (whole page), "check": true (overflow, broken images, errors), "pdf": "out.pdf"}]
// Page errors and console errors are printed with the job they belong to.
import { spawn } from "node:child_process";
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";

const jobs = JSON.parse(readFileSync(process.argv[2], "utf8"));
const port = 9400 + Math.floor(Math.random() * 400);
const chrome = spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "spendry-qa-"))}`,
   "--hide-scrollbars", "--no-first-run", "--allow-file-access-from-files", "--enable-webgl", "--ignore-gpu-blocklist",
   ...(process.env.CHROME_ARGS || "").split(" ").filter(Boolean), "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
process.on("exit", () => chrome.kill("SIGKILL"));

let target;
for (let i = 0; i < 150 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page"); } catch {}
}
if (!target) { console.error("Chrome did not start"); process.exit(1); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let id = 0;
const pending = new Map(), waiters = [];
let current = "";
ws.addEventListener("message", (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  for (const w of waiters.filter((w) => w.method === msg.method)) { w.resolve(msg); waiters.splice(waiters.indexOf(w), 1); }
  if (msg.method === "Runtime.exceptionThrown") {
    const d = msg.params.exceptionDetails;
    console.log(current, "PAGE ERROR:", d.exception?.description?.split("\n")[0] || d.text, d.url || "", d.lineNumber ?? "");
  }
  if (msg.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(msg.params.type)) {
    console.log(current, `console.${msg.params.type}:`, msg.params.args.map((a) => a.value ?? a.description).join(" ").slice(0, 300));
  }
  if (msg.method === "Network.loadingFailed" && !msg.params.canceled) console.log(current, "LOAD FAILED:", msg.params.errorText);
  if (msg.method === "Network.responseReceived" && msg.params.response.status >= 400) {
    console.log(current, "HTTP", msg.params.response.status, msg.params.response.url);
  }
});
const send = (method, params = {}) => new Promise((resolve) => {
  const n = ++id; pending.set(n, resolve); ws.send(JSON.stringify({ id: n, method, params }));
});
const once = (method) => new Promise((resolve) => waiters.push({ method, resolve }));
const evaluate = async (code) => {
  const r = await send("Runtime.evaluate", { expression: `(async () => { ${code} })()`, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) return { error: r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text };
  return { value: r.result?.result?.value };
};

// Where to scroll: a number, a selector's top, or a pinned section at progress p (0 to 1).
const scrollCode = (to, steps) => `
  const target = (() => {
    const to = ${JSON.stringify(to)};
    if (typeof to === "number") return to;
    if (typeof to === "string") { const el = document.querySelector(to); return el ? el.getBoundingClientRect().top + scrollY : 0; }
    const el = document.querySelector(to.sel);
    if (!el) return 0;
    const top = el.getBoundingClientRect().top + scrollY;
    return top + to.p * Math.max(0, el.offsetHeight - innerHeight);
  })();
  const lenis = window.__lenis;
  const go = (y) => { if (lenis) lenis.scrollTo(y, { immediate: true, force: true }); else scrollTo(0, y); };
  const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const start = scrollY, steps = ${steps || 0};
  if (steps > 0) { for (let i = 1; i <= steps; i++) { go(start + (target - start) * i / steps); await frame(); } }
  else { go(target); await frame(); }
  if (window.ScrollTrigger) window.ScrollTrigger.update();
  await new Promise((r) => setTimeout(r, 400));
  return Math.round(scrollY);`;

const checkCode = `
  const out = {};
  out.overflowX = document.documentElement.scrollWidth - innerWidth;
  out.brokenImages = [...document.images].filter((i) => i.complete && i.naturalWidth === 0 && i.loading !== "lazy" && !i.dataset.src).map((i) => i.src.split("/").slice(-2).join("/")).slice(0, 8);
  const wide = [];
  document.querySelectorAll("body *").forEach((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    if (cs.position === "fixed" || cs.visibility === "hidden" || cs.display === "none") return;
    if (r.width > 0 && (r.right > innerWidth + 2 || r.left < -2) && !e.closest("[data-qa-ok]")) wide.push(e.tagName + "." + String(e.className).split(" ")[0] + " " + Math.round(r.left) + ".." + Math.round(r.right));
  });
  out.outside = wide.slice(0, 6);
  out.height = document.documentElement.scrollHeight;
  return out;`;

await send("Page.enable");
await send("Runtime.enable");
await send("Network.enable");
const { result: version } = await send("Browser.getVersion");
let last = {}, applied = "";
for (const raw of jobs) {
  // Viewport settings carry over from the job before, so a follow-up step never resizes the page by accident.
  const job = { ...last, ...raw };
  for (const k of ["w", "h", "dpr", "mobile", "lang", "scheme", "reduce"]) if (k in raw) last[k] = raw[k];
  current = job.out || job.url;
  const emu = JSON.stringify([job.w, job.h, job.dpr, job.mobile, job.lang, job.scheme, job.reduce]);
  if (emu !== applied) {
    applied = emu;
    await send("Emulation.setUserAgentOverride", {
      userAgent: job.mobile ? "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1" : version.userAgent,
      acceptLanguage: job.lang || "en-US,en",
    });
    await send("Emulation.setDeviceMetricsOverride", { width: job.w || 1440, height: job.h || 900, deviceScaleFactor: job.dpr || 2, mobile: !!job.mobile });
    await send("Emulation.setTouchEmulationEnabled", { enabled: !!job.mobile, maxTouchPoints: job.mobile ? 5 : 0 });
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: job.scheme || "light" },
                                                         { name: "prefers-reduced-motion", value: job.reduce ? "reduce" : "no-preference" }] });
  }
  if (raw.url) {
    const loaded = once("Page.loadEventFired");
    await send("Page.navigate", { url: raw.url });
    await Promise.race([loaded, sleep(20000)]);
    await sleep(job.settle ?? 700);
  }
  if (raw.scrollTo !== undefined) {
    const r = await evaluate(scrollCode(raw.scrollTo, raw.steps));
    if (r.error) console.log(current, "scroll error:", r.error);
  }
  if (raw.js) {
    const r = await evaluate(raw.js);
    if (r.error) console.log(current, "script error:", r.error);
    else if (r.value !== undefined) console.log(current, JSON.stringify(r.value));
  }
  await sleep(raw.wait ?? 600);
  if (raw.check) {
    const r = await evaluate(checkCode);
    console.log(current, "CHECK", JSON.stringify(r.value || r.error));
  }
  if (raw.pdf) {
    mkdirSync(dirname(raw.pdf), { recursive: true });
    const r = await send("Page.printToPDF", { printBackground: true, preferCSSPageSize: true, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 });
    if (r.result?.data) writeFileSync(raw.pdf, Buffer.from(r.result.data, "base64"));
    else console.log(current, "pdf failed", JSON.stringify(r.error || {}));
  }
  if (raw.out) {
    mkdirSync(dirname(raw.out), { recursive: true });
    const params = { format: raw.out.endsWith(".jpg") ? "jpeg" : "png", quality: raw.out.endsWith(".jpg") ? 88 : undefined };
    if (raw.full) params.captureBeyondViewport = true;
    if (raw.full) {
      const { result } = await send("Page.getLayoutMetrics");
      params.clip = { x: 0, y: 0, width: result.cssContentSize.width, height: Math.min(result.cssContentSize.height, 16000), scale: 1 };
    }
    const shot = await send("Page.captureScreenshot", params);
    if (shot.result?.data) writeFileSync(raw.out, Buffer.from(shot.result.data, "base64"));
    else console.log(current, "screenshot failed", JSON.stringify(shot.error || {}));
  }
}
ws.close();
chrome.kill();
