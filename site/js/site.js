/* spendryapp.com motion. Everything here is an extra: without it (no script, reduced motion, an old browser)
   every section shows in its final state and the numbers are still filled in.
   Rules kept throughout: pictures are never scaled past their own pixels and never put in 3D, so they stay sharp;
   a parent and its children are never both faded with autoAlpha (the children would stay hidden). */
(() => {
  "use strict";
  const d = document;
  const root = d.documentElement;
  const motion = root.classList.contains("motion");
  const rtl = root.dir === "rtl";
  const dir = rtl ? -1 : 1;
  const locale = root.dataset.locale || root.lang || "en-US";
  const currency = root.dataset.currency || "USD";
  const q = (s, el = d) => el.querySelector(s);
  const qa = (s, el = d) => [...el.querySelectorAll(s)];
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
  const G = window.gsap;
  const ST = window.ScrollTrigger;

  // ---------------------------------------------------------------- numbers and dates in the page's language
  const nf = (o) => { try { return new Intl.NumberFormat(locale, o); } catch (err) { return new Intl.NumberFormat("en-US", o); } };
  const money0 = nf({ style: "currency", currency, maximumFractionDigits: 0, minimumFractionDigits: 0 });
  const moneyN = nf({ style: "currency", currency });
  const plainN = nf({});
  const pctN = nf({ style: "percent", maximumFractionDigits: 2 });
  const money = (v) => money0.format(Math.round(v));
  const monthYear = (offset) => {
    const t = new Date(); t.setDate(1); t.setMonth(t.getMonth() + offset);
    return new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(t);
  };
  const duration = (months) => {
    const y = Math.floor(months / 12), m = months % 12;
    try {
      if (Intl.DurationFormat) {
        const parts = {}; if (y) parts.years = y; if (m || !y) parts.months = m;
        return new Intl.DurationFormat(locale, { style: "long" }).format(parts);
      }
    } catch (err) { /* falls through */ }
    const unit = (n, u) => nf({ style: "unit", unit: u, unitDisplay: "long" }).format(n);
    const list = [];
    if (y) list.push(unit(y, "year"));
    if (m || !y) list.push(unit(m, "month"));
    try { return new Intl.ListFormat(locale, { style: "long", type: "unit" }).format(list); } catch (err) { return list.join(" "); }
  };
  window.__spendryFormat = { money, moneyN, duration, monthYear, locale, currency, pctN, nf };

  // ---------------------------------------------------------------- language menu, remembered for the next visit
  const langBtn = q(".lang-btn"), langPanel = q("#langs");
  if (langBtn && langPanel) {
    const open = (yes) => {
      if (yes) {
        langPanel.hidden = false;
        requestAnimationFrame(() => langPanel.classList.add("open"));
        if (window.__lenis) window.__lenis.stop();
        setTimeout(() => (q("[aria-current]", langPanel) || q("a", langPanel)).focus({ preventScroll: true }), 250);
      } else {
        langPanel.classList.remove("open");
        if (window.__lenis) window.__lenis.start();
        setTimeout(() => { if (!langPanel.classList.contains("open")) langPanel.hidden = true; }, 450);
        langBtn.focus({ preventScroll: true });
      }
      langBtn.setAttribute("aria-expanded", String(yes));
    };
    langBtn.addEventListener("click", () => open(langBtn.getAttribute("aria-expanded") !== "true"));
    q(".lang-close", langPanel).addEventListener("click", () => open(false));
    langPanel.addEventListener("click", (ev) => { if (ev.target === langPanel) open(false); });
    d.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && langBtn.getAttribute("aria-expanded") === "true") open(false); });
  }
  qa("a[data-lang]").forEach((a) => a.addEventListener("click", () => {
    try { localStorage.setItem("spendry-lang", a.dataset.lang); } catch (err) { /* storage off */ }
  }));

  // ---------------------------------------------------------------- FAQ: open and close smoothly
  qa(".qa").forEach((item) => {
    const sum = q("summary", item), body = q(".qa-a", item);
    sum.addEventListener("click", (ev) => {
      if (!G || !motion) return;
      ev.preventDefault();
      if (item.open) {
        G.to(body, { height: 0, duration: .45, ease: "expo.out", onComplete: () => { item.open = false; body.style.height = ""; ST && ST.refresh(); } });
      } else {
        item.open = true;
        G.fromTo(body, { height: 0 }, { height: "auto", duration: .6, ease: "expo.out", onComplete: () => ST && ST.refresh() });
      }
    });
  });

  // ---------------------------------------------------------------- debt payoff lab
  const simulate = (debts, extra, method, rollover = true) => {
    const ds = debts.map((x, i) => ({ i, bal: x.bal, rate: x.r, min: x.min, paid: 0 })).filter((x) => x.bal > 0);
    const order = ds.slice().sort(method === "snowball" ? (a, b) => a.bal - b.bal || b.rate - a.rate : (a, b) => b.rate - a.rate || a.bal - b.bal);
    const budget = ds.reduce((s, x) => s + x.min, 0) + extra;
    let month = 0, interest = 0;
    const totals = [ds.reduce((s, x) => s + x.bal, 0)];
    while (ds.some((x) => x.bal > 0.005) && month < 600) {
      month++;
      ds.forEach((x) => { if (x.bal > 0) { const i = x.bal * x.rate; x.bal += i; interest += i; } });
      let pool = rollover ? budget : Infinity;
      ds.forEach((x) => { if (x.bal > 0) { const p = Math.min(x.min, x.bal, pool); x.bal -= p; if (rollover) pool -= p; } });
      if (rollover) order.forEach((x) => { if (x.bal > 0 && pool > 0) { const p = Math.min(pool, x.bal); x.bal -= p; pool -= p; } });
      ds.forEach((x) => { if (x.bal <= 0.005 && !x.paid) { x.bal = 0; x.paid = month; } });
      totals.push(ds.reduce((s, x) => s + Math.max(0, x.bal), 0));
    }
    return { months: month, interest, totals, paid: ds.map((x) => ({ i: x.i, month: x.paid })), stuck: month >= 600 };
  };
  window.__spendrySimulate = simulate;

  const lab = q("[data-lab]");
  let labIntro = null;
  if (lab) {
    const data = JSON.parse(lab.dataset.lab);
    const perMonth = data.period === "month";
    const debts = data.debts.map((x) => ({ ...x, r: (perMonth ? x.rate : x.rate / 12) / 100 }));
    qa("[data-bal]", lab).forEach((el, i) => { el.textContent = money(debts[i].bal); });
    qa("[data-rate]", lab).forEach((el, i) => { el.textContent = pctN.format(debts[i].rate / 100); });
    const range = q("input[type=range]", lab);
    const out = (k) => q(`[data-o="${k}"]`, lab);
    const segBtns = qa(".seg button", lab), thumb = q(".seg-thumb", lab), hint = q(".m-hint", lab);
    const month = q(".g-month", lab), dur = q(".g-dur", lab);
    const cLine = q(".c-line", lab), cArea = q(".c-area", lab), cMin = q(".c-min", lab), marks = q(".c-marks", lab);
    const rows = qa(".debts li", lab);
    const base = simulate(debts, 0, "avalanche", false);
    const W = 600, H = 200, N = 72;
    const X = (m) => (m / base.months) * W;
    const Y = (v) => H - 12 - (v / base.totals[0]) * (H - 30);
    const sample = (totals) => Array.from({ length: N + 1 }, (_, k) => {
      const m = (k / N) * base.months;
      const a = Math.floor(m), b = Math.min(a + 1, totals.length - 1);
      const va = totals[Math.min(a, totals.length - 1)] ?? 0, vb = totals[b] ?? 0;
      return a >= totals.length - 1 ? 0 : va + (vb - va) * (m - a);
    });
    const path = (pts) => pts.map((v, k) => `${k ? "L" : "M"}${((k / N) * W).toFixed(1)},${Y(v).toFixed(1)}`).join("");
    cMin.setAttribute("d", path(sample(base.totals)));
    let method = "avalanche", shown = null, shownVals = { interest: 0, saved: 0, sooner: 0, months: 0 };
    const state = { k: 1 };
    const render = (res, animate) => {
      const target = sample(res.totals);
      const from = shown || target.map(() => base.totals[0]);
      const draw = (k) => {
        const pts = target.map((v, i) => from[i] + (v - from[i]) * k);
        const line = path(pts);
        cLine.setAttribute("d", line);
        cArea.setAttribute("d", `${line}L${W},${H}L0,${H}Z`);
        shown = pts;
      };
      const vals = { interest: res.interest, saved: Math.max(0, base.interest - res.interest), sooner: Math.max(0, base.months - res.months), months: res.months };
      const write = (v) => {
        out("interest").textContent = money(v.interest);
        out("saved").textContent = money(v.saved);
        out("sooner").textContent = duration(Math.round(v.sooner));
        month.textContent = monthYear(Math.round(v.months));
        dur.textContent = duration(Math.round(v.months));
      };
      marks.innerHTML = "";
      res.paid.slice().sort((a, b) => a.month - b.month).forEach((p) => {
        const m = document.createElement("span");
        const v = res.totals[p.month] ?? 0;
        m.style.left = `${(X(p.month) / W) * 100}%`;
        m.style.top = `${(Y(v) / H) * 100}%`;
        m.style.setProperty("--c", getComputedStyle(rows[p.i]).getPropertyValue("--c"));
        m.title = `${data.debts[p.i].name} · ${monthYear(p.month)}`;
        marks.appendChild(m);
      });
      if (animate && G && motion) {
        const tw = { ...shownVals };
        G.to(state, { k: 1, duration: .8, ease: "expo.out", startAt: { k: 0 }, onUpdate: () => draw(state.k) });
        G.to(tw, { ...vals, duration: .8, ease: "expo.out", onUpdate: () => write(tw) });
      } else {
        draw(1);
        write(vals);
      }
      shownVals = vals;
    };
    const run = (animate = true) => {
      const extra = Number(range.value);
      const pct = ((extra - Number(range.min)) / (Number(range.max) - Number(range.min))) * 100;
      range.style.setProperty("--p", `${pct}%`);
      out("extra").textContent = money(extra);
      render(simulate(debts, extra, method), animate);
    };
    const setMethod = (m, animate = true) => {
      method = m;
      segBtns.forEach((b, i) => {
        const on = b.dataset.m === m;
        b.setAttribute("aria-checked", String(on));
        if (on) thumb.style.transform = `translateX(${dir * i * 100}%)`;
      });
      hint.textContent = data.labels[`hint_${m}`];
      run(animate);
    };
    segBtns.forEach((b) => b.addEventListener("click", () => setMethod(b.dataset.m)));
    let raf = 0;
    range.addEventListener("input", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => run(true)); });
    setMethod("avalanche", false);
    labIntro = () => { shown = null; shownVals = { interest: 0, saved: 0, sooner: 0, months: 0 }; run(true); };
  }

  // ---------------------------------------------------------------- reminders: the lock screen fills in
  const lock = q("[data-rem]");
  let playNotes = null;
  if (lock) {
    const data = JSON.parse(lock.dataset.rem);
    const list = q(".notes", lock);
    const fmt = (tpl, args) => {
      let n = 0;
      return tpl.replace(/%%|%(\d+\$)?(?:\.\d+)?(lld|ld|d|@|f|s)/g, (m, pos) => {
        if (m === "%%") return "%";
        const i = pos ? parseInt(pos, 10) - 1 : n++;
        return args[i] ?? "";
      });
    };
    const day = (offset) => { const t = new Date(); t.setDate(t.getDate() + offset); return new Intl.DateTimeFormat(locale, { day: "numeric", month: "long" }).format(t); };
    const rel = (() => { try { return new Intl.RelativeTimeFormat(locale, { numeric: "auto", style: "short" }); } catch (err) { return null; } })();
    const ago = (v, u) => (rel ? rel.format(v, u) : "");
    const A = data.amounts, Nm = data.names, T = data.tpl;
    const notes = [
      { b: fmt(T.notif_milestone_halfway_body, [Nm.loan]), title: T.notif_milestone_halfway_title, when: ago(-1, "day") },
      { b: fmt(T.notif_debt_1day_body, [Nm.loan, moneyN.format(A.loan)]), when: ago(-3, "hour") },
      { b: fmt(T.notif_cc_early_body, [Nm.card, moneyN.format(A.card), day(2)]), when: ago(-1, "hour") },
      { b: fmt(T.notif_budget_body, [76, Nm.budget, money(A.used), money(A.limit)]), title: T.notif_budget_warning_title, when: ago(-12, "minute") },
      { b: fmt(T.notif_celebration_debt_body, [Nm.store, plainN.format(142), money(A.saved)]), title: T.notif_celebration_debt_title, when: ago(0, "second") },
    ];
    const make = (n) => {
      const li = document.createElement("li");
      li.className = "note-card";
      li.innerHTML = `<img src="/assets/brand/icon-96.webp" alt="" width="40" height="40"><div><div class="nt"><b></b><time></time></div><p></p></div>`;
      q("b", li).textContent = n.title || "Spendry";
      q("time", li).textContent = n.when;
      q("p", li).textContent = n.b;
      return li;
    };
    window.__spendryNotes = { notes, make };
    q(".lock-date", lock).textContent = new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long" }).format(new Date());
    if (!motion || !G) {
      notes.slice().reverse().forEach((n) => list.appendChild(make(n)));
    } else {
      playNotes = () => {
        list.innerHTML = "";
        notes.forEach((n, i) => G.delayedCall(i * .5, () => {
          const li = make(n);
          list.prepend(li);
          G.fromTo(li, { height: 0, marginBottom: -10, opacity: 0, scale: .9, y: -24 },
            { height: "auto", marginBottom: 0, opacity: 1, scale: 1, y: 0, duration: .8, ease: "expo.out" });
        }));
      };
    }
  }

  // ---------------------------------------------------------------- the money row: one amount, many currencies
  const moneyRow = q("[data-money]");
  if (moneyRow) {
    const rates = { USD: 1, EUR: .92, JPY: 150, GBP: .79, TRY: 41, BRL: 5.4, INR: 84, KRW: 1380, CAD: 1.37, SAR: 3.75, CNY: 7.2, PLN: 4, SEK: 10.5, MXN: 18, IDR: 16000, THB: 35, ILS: 3.7, VND: 25000, UAH: 41.5, CHF: .88 };
    const list = [[locale, currency], ["en-US", "USD"], ["de-DE", "EUR"], ["ja-JP", "JPY"], ["en-GB", "GBP"], ["tr-TR", "TRY"], ["pt-BR", "BRL"],
      ["hi-IN", "INR"], ["ko-KR", "KRW"], ["fr-CA", "CAD"], ["ar-SA", "SAR"], ["zh-CN", "CNY"], ["pl-PL", "PLN"], ["sv-SE", "SEK"], ["es-MX", "MXN"],
      ["id-ID", "IDR"], ["th-TH", "THB"], ["he-IL", "ILS"], ["de-CH", "CHF"], ["uk-UA", "UAH"]];
    const seen = new Set();
    const html = list.filter(([, c]) => !seen.has(c) && seen.add(c)).map(([l, c]) => {
      const v = 3612.29 * (rates[c] || 1);
      let s;
      try { s = new Intl.NumberFormat(l, { style: "currency", currency: c, maximumFractionDigits: v > 9999 ? 0 : 2 }).format(v); } catch (err) { s = `${c} ${Math.round(v)}`; }
      return `<span>${s}</span><i></i>`;
    }).join("");
    moneyRow.innerHTML = html + html;
  }

  // ---------------------------------------------------------------- back to top, and the download dock on phones
  const toTop = q(".to-top"), dock = q(".dock"), stageEl = q(".stage"), finalSec = q(".final");
  const updateTop = () => {
    const after = stageEl ? stageEl.offsetTop + stageEl.offsetHeight - innerHeight * .5 : innerHeight;
    if (dock) dock.classList.toggle("show", scrollY > after && scrollY < (finalSec ? finalSec.offsetTop - innerHeight * .9 : Infinity));
    if (toTop) toTop.classList.toggle("show", scrollY > after + innerHeight * .5);
  };
  addEventListener("scroll", updateTop, { passive: true });
  if (toTop) toTop.addEventListener("click", (ev) => { ev.preventDefault(); if (window.__lenis) window.__lenis.scrollTo(0, { duration: 1.6 }); else scrollTo({ top: 0, behavior: motion ? "smooth" : "auto" }); });

  if (!motion || !G) {
    qa("[data-count]").forEach((el) => { el.textContent = plainN.format(Number(el.dataset.count)); });
  }
  if (!G || !ST) { root.classList.add("ready"); return; }
  G.registerPlugin(ST);
  if (window.SplitText) G.registerPlugin(window.SplitText);
  if (window.CustomEase) G.registerPlugin(window.CustomEase);
  const ease = window.CustomEase ? window.CustomEase.create("spendry", "M0,0 C0.16,1 0.3,1 1,1") : "expo.out";

  if (!motion) {
    qa("[data-rise], .hero-copy [data-hero], .phones").forEach((el) => { el.style.opacity = 1; el.style.transform = "none"; });
    qa(".hero-title .ln-in").forEach((el) => { el.style.transform = "none"; });
    root.classList.add("ready");
    return;
  }

  // ---------------------------------------------------------------- smooth scrolling
  let lenis = null;
  if (window.Lenis) {
    lenis = new window.Lenis({ lerp: .09, smoothWheel: true, wheelMultiplier: 1, touchMultiplier: 1.4, syncTouch: false });
    window.__lenis = lenis;
    lenis.on("scroll", ST.update);
    G.ticker.add((time) => lenis.raf(time * 1000));
    G.ticker.lagSmoothing(0);
    qa('a[href^="#"], a[href*="/#"]').forEach((a) => a.addEventListener("click", (ev) => {
      if (a.hasAttribute("data-story")) return;
      const url = new URL(a.href, location.href);
      if (url.pathname !== location.pathname || !url.hash) return;
      const target = url.hash === "#main" ? 0 : q(url.hash);
      if (target === null) return;
      ev.preventDefault();
      lenis.scrollTo(target, { offset: 0, duration: 1.6 });
    }));
  }
  ST.config({ ignoreMobileResize: true });

  // ---------------------------------------------------------------- nav: hides going down, comes back going up; dark or light
  const nav = q("[data-nav]");
  let lastY = scrollY;
  const setNav = (theme) => nav.classList.toggle("light", theme === "light");
  addEventListener("scroll", () => {
    const y = scrollY;
    const langOpen = langBtn && langBtn.getAttribute("aria-expanded") === "true";
    if (!langOpen) nav.classList.toggle("away", y > 160 && y > lastY + 2);
    if (y < lastY - 2 || y < 160) nav.classList.remove("away");
    lastY = y;
  }, { passive: true });

  // ---------------------------------------------------------------- the flowing ribbons (WebGL), paused when out of sight
  const auroras = qa("canvas.aurora").map((canvas) => ribbons(canvas)).filter(Boolean);
  function ribbons(canvas) {
    const gl = canvas.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power", preserveDrawingBuffer: false });
    if (!gl) return null;
    const small = innerWidth < 900;
    const LINES = small ? 16 : 26;
    const vs = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    const fs = `precision mediump float;uniform vec2 R;uniform float T;uniform vec2 M;
      vec3 pal(float t){t=abs(fract(t*.5)*2.-1.);
        return t<.5?mix(vec3(.22,.8,1.),vec3(.2,.45,1.),t*2.):mix(vec3(.2,.45,1.),vec3(.58,.42,1.),(t-.5)*2.);}
      float band(vec2 p,float k,float t,out float glow){
        float c=.13*sin(p.x*1.1+t*.3+k*2.4)+.05*sin(p.x*2.3-t*.41+k*1.3)+p.x*.3-.06-k*.3;
        float th=p.x*1.35-t*.36+k*2.2;
        float w=.2+.04*sin(p.x*.9+t*.21+k);
        float acc=0.;
        for(int j=0;j<${LINES};j++){
          float f=float(j)/${LINES - 1}.;
          float o=(f-.5)*2.*w;
          float y=c+o*cos(th);
          float dz=(f-.5)*2.*sin(th);
          float dd=abs(p.y-y);
          acc+=(smoothstep(.003,0.,dd)*.6+.0011/(dd+.003))*(.55+.45*dz);
        }
        glow=exp(-pow((p.y-c)/((w*abs(cos(th))+.02)*1.6),2.));
        return acc;
      }
      void main(){
        vec2 p=(gl_FragCoord.xy-.5*R)/R.y;
        p+=M*.03;
        float t=T;
        vec3 col=vec3(.016,.024,.07);
        col+=vec3(.03,.06,.2)*smoothstep(1.4,0.,length(p-vec2(.55,.35)));
        col+=vec3(.12,.04,.22)*.55*smoothstep(1.2,0.,length(p-vec2(-.8,-.45)));
        float ga,gb;
        float a=band(p,0.,t,ga);
        col+=pal(.1+p.x*.25+t*.02)*(a*.17+ga*.06);
        float b=band(p,1.,t*.85+4.,gb);
        col+=pal(.9+p.x*.2-t*.015)*(b*.09+gb*.03);
        col=1.-exp(-col*1.6);
        col*=smoothstep(1.9,.4,length(p*vec2(.7,1.)));
        gl_FragColor=vec4(col,1.);
      }`;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null; };
    const v = sh(gl.VERTEX_SHADER, vs), f = sh(gl.FRAGMENT_SHADER, fs);
    if (!v || !f) return null;
    const pr = gl.createProgram();
    gl.attachShader(pr, v); gl.attachShader(pr, f); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return null;
    gl.useProgram(pr);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(pr, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const uR = gl.getUniformLocation(pr, "R"), uT = gl.getUniformLocation(pr, "T"), uM = gl.getUniformLocation(pr, "M");
    const scale = small ? .5 : .62;
    const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
    let visible = false, running = false, last = 0;
    const t0 = performance.now();
    const size = () => {
      const w = Math.max(1, Math.round(canvas.clientWidth * scale)), h = Math.max(1, Math.round(canvas.clientHeight * scale));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; gl.viewport(0, 0, w, h); }
    };
    const frame = (now) => {
      if (!visible || d.hidden) { running = false; return; }
      running = true;
      if (small && now - last < 30) { requestAnimationFrame(frame); return; }
      last = now;
      size();
      mouse.x += (mouse.tx - mouse.x) * .05; mouse.y += (mouse.ty - mouse.y) * .05;
      gl.uniform2f(uR, canvas.width, canvas.height);
      gl.uniform1f(uT, (now - t0) / 1000);
      gl.uniform2f(uM, mouse.x, mouse.y);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      requestAnimationFrame(frame);
    };
    const start = () => { if (!running && visible) requestAnimationFrame(frame); };
    new IntersectionObserver(([en]) => { visible = en.isIntersecting; start(); }).observe(canvas);
    d.addEventListener("visibilitychange", start);
    if (fine) addEventListener("pointermove", (ev) => { mouse.tx = ev.clientX / innerWidth - .5; mouse.ty = .5 - ev.clientY / innerHeight; }, { passive: true });
    canvas.classList.add("on");
    canvas.parentElement.classList.add("webgl-on");
    return { canvas };
  }

  // ---------------------------------------------------------------- shared reveals: titles line by line, the rest rises
  const splitReady = window.SplitText && !root.classList.contains("no-split");
  qa("[data-split]").forEach((el) => {
    if (el.closest(".stage")) return;
    if (splitReady) {
      window.SplitText.create(el, {
        type: "lines", mask: "lines", linesClass: "split-line", autoSplit: true,
        onSplit: (self) => G.from(self.lines, { yPercent: 105, duration: 1.1, ease, stagger: .08,
          scrollTrigger: { trigger: el, start: "top 88%", once: true } }),
      });
    } else {
      G.from(el, { y: 40, opacity: 0, duration: 1.1, ease, scrollTrigger: { trigger: el, start: "top 88%", once: true } });
    }
  });
  ST.batch("[data-rise]", {
    start: "top 90%", once: true,
    onEnter: (els) => G.to(els, { opacity: 1, y: 0, duration: 1, ease, stagger: .07, overwrite: true }),
  });

  // ---------------------------------------------------------------- hero and story
  const stage = q(".stage");
  if (stage) {
    const pin = q(".stage-pin", stage);
    const phones = q(".phones", stage), pc = q(".pw-c", stage), pl = q(".pw-l", stage), pr = q(".pw-r", stage);
    const inC = q(".ph-c", stage), inL = q(".ph-l", stage), inR = q(".ph-r", stage);
    const floats = qa(".fw", stage), floatPar = qa(".fp", stage), floatImg = qa(".float", stage);
    const copy = q(".hero-copy", stage), caps = qa(".cap", stage);
    const scr = qa(".scr", stage), lifts = qa(".lift", stage), slots = qa(".slot", stage);
    G.set(pl, { xPercent: -60, yPercent: 5, scale: .84, force3D: false });
    G.set(pr, { xPercent: 60, yPercent: 5, scale: .84, force3D: false });
    G.set(floats[0], { xPercent: -96, yPercent: 70, rotation: -6 });
    G.set(floats[1], { xPercent: 30, yPercent: -150, rotation: 5 });
    G.set(lifts, { autoAlpha: 0 });
    G.set(scr.slice(1), { xPercent: 100 * dir });

    // Arrival: the headline rises line by line, the phones come up and the two cards settle beside them.
    G.timeline({ defaults: { ease } })
      .to(qa(".hero-title .ln-in", stage), { y: 0, duration: 1.3, stagger: .1 }, .1)
      .to(qa("[data-hero]", copy), { opacity: 1, duration: 1, stagger: .08 }, .35)
      .fromTo(qa("[data-hero]", copy), { y: 20 }, { y: 0, duration: 1, stagger: .08 }, .35)
      .to(phones, { opacity: 1, duration: .8 }, .15)
      .from(inC, { yPercent: 16, duration: 1.5, force3D: false }, .15)
      .from(inL, { xPercent: 45, opacity: 0, duration: 1.5, force3D: false }, .4)
      .from(inR, { xPercent: -45, opacity: 0, duration: 1.5, force3D: false }, .4)
      .from(floatImg, { y: 46, opacity: 0, duration: 1.2, stagger: .15 }, .85);
    G.to(floatImg, { yPercent: -5, duration: 3.2, ease: "sine.inOut", yoyo: true, repeat: -1, stagger: 1.1, delay: 2 });
    if (fine) {
      const fx = floatPar.map((f) => G.quickTo(f, "x", { duration: 1.4, ease: "power3.out" }));
      const fy = floatPar.map((f) => G.quickTo(f, "y", { duration: 1.4, ease: "power3.out" }));
      stage.addEventListener("pointermove", (ev) => {
        if (scrollY > innerHeight * .3) return;
        const x = ev.clientX / innerWidth - .5, y = ev.clientY / innerHeight - .5;
        fx.forEach((f, i) => f(x * (i ? -26 : 32))); fy.forEach((f, i) => f(y * (i ? -20 : 26)));
      });
    }

    // Now and then one of the app's own notifications drops in over the phone.
    const N = window.__spendryNotes;
    let toast = null;
    if (N && N.notes.length) {
      toast = d.createElement("div");
      toast.className = "toast";
      toast.setAttribute("aria-hidden", "true");
      phones.appendChild(toast);
      const order = [2, 3, 1, 4];
      let k = 0;
      const show = () => {
        if (scrollY > innerHeight * .15 || d.hidden) return;
        toast.innerHTML = "";
        const cardEl = N.make(N.notes[order[k++ % order.length]]);
        toast.appendChild(cardEl);
        G.timeline()
          .fromTo(cardEl, { y: -40, scale: .9, opacity: 0 }, { y: 0, scale: 1, opacity: 1, duration: .8, ease: "back.out(1.3)" })
          .to(cardEl, { y: -20, opacity: 0, duration: .5, ease: "power2.in" }, "+=3.4");
      };
      G.delayedCall(3.2, function loop() { show(); G.delayedCall(7.5, loop); });
    }

    const mm = G.matchMedia();
    mm.add({ wide: "(min-width: 900px)", narrow: "(max-width: 899px)" }, (ctx) => {
      const { wide } = ctx.conditions;
      const tl = G.timeline({
        defaults: { ease: "power2.inOut" },
        scrollTrigger: { trigger: stage, pin, start: "top top", end: () => `+=${Math.round(innerHeight * (wide ? 3.2 : 3))}`, scrub: .8, invalidateOnRefresh: true, anticipatePin: 1 },
      });
      if (toast) tl.to(toast, { opacity: 0, y: -30, duration: .4 }, 0);
      tl.to(copy, { y: -80, opacity: 0, duration: 1, ease: "power2.in" }, 0)
        .to(pl, { xPercent: -140, opacity: 0, duration: 1.2, ease: "power2.in", force3D: false }, 0)
        .to(pr, { xPercent: 140, opacity: 0, duration: 1.2, ease: "power2.in", force3D: false }, 0)
        .to(floats[0], { x: "-=240", y: "+=160", opacity: 0, duration: 1, ease: "power2.in" }, 0)
        .to(floats[1], { x: "+=240", y: "-=160", opacity: 0, duration: 1, ease: "power2.in" }, 0);
      if (!wide) {
        tl.to(phones, { y: () => innerHeight * .35 - (phones.offsetTop + phones.offsetHeight / 2), duration: 1.3 }, .1)
          .to(pc, { scale: () => Math.min(.8, (innerHeight * .56) / (pc.offsetHeight || 1)), duration: 1.3, force3D: false }, .1);
      }
      const capIn = (i, at) => tl.fromTo(caps[i], { opacity: 0, y: 40, visibility: "visible" }, { opacity: 1, y: 0, duration: .8, ease: "power3.out", immediateRender: false }, at);
      const capOut = (i, at) => tl.to(caps[i], { opacity: 0, y: -40, duration: .6, ease: "power2.in" }, at);
      // The step's main card comes forward out of the phone, towards the words, and goes back.
      const pop = (i, at) => {
        tl.set(lifts[i], { autoAlpha: 1 }, at)
          .fromTo(slots[i], { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: false }, at + .15)
          .to(slots[i], { opacity: 0, duration: .4 }, at + 1.75)
          .fromTo(lifts[i], { scale: 1, xPercent: 0, yPercent: 0, boxShadow: "0 0 0 0 rgba(0,0,0,0)" },
            { scale: wide ? 1.22 : 1.1, xPercent: wide ? -26 * dir : 0, yPercent: wide ? -4 : -8,
              boxShadow: "0 50px 80px -30px rgba(0,0,0,.8)", duration: .9, ease: "power3.out", immediateRender: false, force3D: false }, at)
          .to(lifts[i], { scale: 1, xPercent: 0, yPercent: 0, boxShadow: "0 0 0 0 rgba(0,0,0,0)", duration: .7, force3D: false }, at + 1.5)
          .set(lifts[i], { autoAlpha: 0 }, at + 2.25);
      };
      // Moving to the next step: the screens slide inside the phone, like swiping between tabs.
      const push = (a, b, at) => {
        tl.to(scr[a], { xPercent: -100 * dir, duration: 1, ease: "power3.inOut" }, at)
          .fromTo(scr[b], { xPercent: 100 * dir }, { xPercent: 0, duration: 1, ease: "power3.inOut", immediateRender: false }, at);
      };
      capIn(0, 1);
      pop(0, 1.7);
      capOut(0, 4.1); push(0, 1, 4.1); capIn(1, 4.7);
      pop(1, 5.3);
      capOut(1, 7.7); push(1, 2, 7.7); capIn(2, 8.3);
      pop(2, 8.9);
      tl.to({}, { duration: .6 }, 11.1);
      return () => { G.set(caps, { clearProps: "all" }); };
    });
  }

  // ---------------------------------------------------------------- the money row drifts slowly, a little faster while scrolling
  const tracks = qa(".mq-track");
  if (tracks.length) {
    const pos = tracks.map(() => 0);
    let vel = 0, visible = false;
    ST.create({ trigger: ".marquee", start: "top bottom", end: "bottom top", onToggle: (s) => { visible = s.isActive; }, onUpdate: (s) => { vel = s.getVelocity(); } });
    const setters = tracks.map((t) => G.quickSetter(t, "xPercent"));
    G.ticker.add((time, dt) => {
      if (!visible) return;
      vel *= .9;
      tracks.forEach((t, i) => {
        const way = (i ? -1 : 1) * dir;
        const speed = (.0005 + Math.min(Math.abs(vel) / 1500000, .0015)) * dt;
        pos[i] = (pos[i] - speed * way) % 50;
        if (pos[i] > 0) pos[i] -= 50;
        setters[i](pos[i]);
      });
    });
  }

  // ---------------------------------------------------------------- statement: words light up with the scroll
  const words = q(".words");
  if (words) {
    const ws = qa(".w", words);
    let lit = -1;
    ST.create({
      trigger: words, start: "top 82%", end: "bottom 50%", scrub: true,
      onUpdate: (s) => {
        const n = Math.round(s.progress * ws.length);
        if (n === lit) return;
        lit = n;
        ws.forEach((w, i) => w.classList.toggle("on", i < n));
      },
    });
  }

  // ---------------------------------------------------------------- the wall of screens and the wall of widgets: from one to all
  const zoomOut = (section, pinSel, wallSel, focusSel, copySel, othersSel, opts) => {
    const wall = q(wallSel);
    if (!wall) return;
    const focus = q(focusSel, wall), box = wall.parentElement, copyW = q(copySel);
    const others = qa(othersSel, wall).filter((w) => !w.contains(focus) && w !== focus && getComputedStyle(w).display !== "none");
    let dx = 0, dy = 0, s0 = 2, sf = 1, y0 = 0;
    // Centred by GSAP itself (xPercent and yPercent), so measuring never loses the centring.
    const measure = () => {
      G.set(wall, { x: 0, y: 0, scale: 1, xPercent: -50, yPercent: -50, force3D: false });
      const a = wall.getBoundingClientRect(), b = focus.getBoundingClientRect(), c = box.getBoundingClientRect(), head = copyW.getBoundingClientRect();
      const fx = b.left + b.width / 2, fy = b.top + b.height * opts.focusY;
      dx = (a.left + a.width / 2) - fx;
      dy = (a.top + a.height / 2) - fy;
      sf = Math.min(1, (c.height - opts.margin) / a.height, (innerWidth - 32) / a.width);
      const room = c.bottom - head.bottom - 30;
      const img = q("img", focus) || focus;
      const sharp = ((img.naturalWidth || opts.natural) * 1.15) / (b.width * Math.max(1, devicePixelRatio || 1));
      s0 = Math.max(1.05, Math.min(sharp, opts.max, (innerWidth * opts.wide) / b.width, (room * .9) / (b.height * opts.tall)));
      y0 = (head.bottom + room / 2) - (c.top + c.height / 2);
    };
    measure();
    const tl = G.timeline({
      scrollTrigger: { trigger: section, pin: pinSel, start: "top top", end: () => `+=${Math.round(innerHeight * opts.length)}`, scrub: .8,
        invalidateOnRefresh: true, onRefreshInit: measure },
    });
    tl.fromTo(wall, { scale: () => s0, x: () => dx * s0, y: () => dy * s0 + y0 }, { scale: () => sf, x: 0, y: 0, duration: 1, ease: "power2.inOut", force3D: false }, 0)
      .to(copyW, { opacity: 0, y: -50, duration: .22, ease: "power2.in" }, .12)
      .fromTo(others, { opacity: 0, scale: .8 }, { opacity: 1, scale: 1, duration: .5, stagger: { each: .03, from: "random" }, ease: "power2.out", force3D: false }, .22)
      .to({}, { duration: .2 });
  };
  zoomOut(".showcase", ".sc-pin", ".sc-wall", ".scp-focus .scp-screen", ".sc-copy", ".scp",
    { focusY: .24, margin: 70, natural: 1206, max: 3, wide: .62, tall: .5, length: 1.7 });
  zoomOut(".wid", ".wid-pin", ".wall", ".wp", ".wid-copy", ".w",
    { focusY: .5, margin: 70, natural: 1092, max: 2.3, wide: .86, tall: 1, length: 1.6 });

  // ---------------------------------------------------------------- lab: numbers and the line draw when it comes into view
  if (lab) ST.create({ trigger: lab, start: "top 78%", once: true, onEnter: () => labIntro && labIntro() });

  // ---------------------------------------------------------------- reminders: notifications arrive one by one
  if (lock) {
    G.timeline({ scrollTrigger: { trigger: lock, start: "top 72%", once: true } })
      .from(lock, { y: 80, opacity: 0, duration: 1.3, ease })
      .add(() => playNotes && playNotes(), .5);
  }

  // ---------------------------------------------------------------- automations: each step lights the next
  qa(".flow").forEach((flow) => {
    const wideFlow = matchMedia("(min-width: 900px)").matches;
    G.timeline({ scrollTrigger: { trigger: flow, start: "top 88%", once: true } })
      .from(qa(".step", flow), { opacity: 0, y: 14, duration: .7, stagger: .3, ease })
      .from(qa(".wire", flow), { [wideFlow ? "scaleX" : "scaleY"]: 0, duration: .5, stagger: .3, ease: "power2.inOut" }, .25);
  });

  // ---------------------------------------------------------------- numbers count up
  const st = q(".st");
  if (st) {
    const els = qa("[data-count]", st);
    els.forEach((el) => { const end = Number(el.dataset.count); el.textContent = plainN.format(end > 0 ? 0 : 1024); });
    ST.create({
      trigger: st, start: "top 85%", once: true,
      onEnter: () => els.forEach((el) => {
        const end = Number(el.dataset.count), c = { v: end > 0 ? 0 : 1024 };
        G.to(c, { v: end, duration: 1.8, ease: "power3.out", onUpdate: () => { el.textContent = plainN.format(Math.round(c.v)); } });
      }),
    });
  }

  // ---------------------------------------------------------------- finale and footer
  const finalIcon = q(".final-icon");
  if (finalIcon) G.from(finalIcon, { scale: .8, opacity: 0, duration: 1.2, ease, scrollTrigger: { trigger: ".final", start: "top 70%", once: true } });
  const mark = q(".foot-mark");
  if (mark) G.from(mark, { yPercent: 50, opacity: 0, ease: "none", scrollTrigger: { trigger: ".foot", start: "top 85%", end: "bottom bottom", scrub: true } });
  qa(".tool-hero, .nf").forEach((hero) => G.from(qa(".crumbs, .nf-code", hero), { y: 20, opacity: 0, duration: 1, ease }));

  // ---------------------------------------------------------------- nav colour follows the section under it
  qa("[data-theme]").forEach((sec) => {
    ST.create({ trigger: sec, start: "top 36px", end: "bottom 36px", onToggle: (self) => { if (self.isActive) setNav(sec.dataset.theme); } });
  });
  if (d.body.classList.contains("page-tool") || d.body.classList.contains("page-nf")) setNav("dark");

  // "See how it works" goes to the first step of the story, not past it.
  qa("[data-story]").forEach((a) => a.addEventListener("click", (ev) => {
    const s = stage && ST.getAll().find((t) => t.pin && t.trigger === stage);
    if (!s) return;
    ev.preventDefault();
    const y = s.start + (s.end - s.start) * .18;
    if (lenis) lenis.scrollTo(y, { duration: 2 }); else scrollTo({ top: y, behavior: "smooth" });
  }));

  // Arriving at /#lab and the like: pinned sections add height above, so go there again once they are set up.
  const goHash = () => {
    if (!location.hash || location.hash.length < 2) return;
    let t = null;
    try { t = q(location.hash); } catch (err) { return; }
    if (!t) return;
    if (lenis) lenis.scrollTo(t, { immediate: true, force: true }); else t.scrollIntoView();
  };
  // Triggers were made section by section, not in page order: sort them so every pinned section's extra height
  // is counted for the ones below it, then measure again.
  const settle = () => { ST.sort(); ST.refresh(); };
  settle();
  root.classList.add("ready");
  addEventListener("load", () => { settle(); goHash(); });
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(settle);
})();
