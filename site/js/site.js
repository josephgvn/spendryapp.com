/* spendryapp.com motion. Everything here is an extra: without it (no script, reduced motion, an old browser)
   every section shows in its final state and the numbers are still filled in. */
(() => {
  "use strict";
  const d = document;
  const root = d.documentElement;
  const motion = root.classList.contains("motion");
  const rtl = root.dir === "rtl";
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
        const r = langBtn.getBoundingClientRect();
        langPanel.style.setProperty("--lx", `${r.left + r.width / 2}px`);
        langPanel.style.setProperty("--ly", `${r.top + r.height / 2}px`);
        langPanel.hidden = false;
        requestAnimationFrame(() => langPanel.classList.add("open"));
        if (window.__lenis) window.__lenis.stop();
        setTimeout(() => (q("[aria-current]", langPanel) || q("a", langPanel)).focus({ preventScroll: true }), 300);
        if (G && motion) G.fromTo(qa(".lang-grid a", langPanel), { y: 16, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .6, stagger: .012, ease: "expo.out", delay: .15 });
      } else {
        langPanel.classList.remove("open");
        if (window.__lenis) window.__lenis.start();
        setTimeout(() => { if (!langPanel.classList.contains("open")) langPanel.hidden = true; }, 800);
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
        G.to(body, { height: 0, duration: .5, ease: "expo.out", onComplete: () => { item.open = false; body.style.height = ""; ST && ST.refresh(); } });
        item.classList.remove("on");
      } else {
        item.open = true;
        G.fromTo(body, { height: 0 }, { height: "auto", duration: .7, ease: "expo.out", onComplete: () => ST && ST.refresh() });
        G.fromTo(q("p", body), { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: .7, ease: "expo.out", delay: .05 });
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
    const seg = q(".seg", lab), segBtns = qa(".seg button", lab), thumb = q(".seg-thumb", lab), hint = q(".m-hint", lab);
    const gBar = q(".g-bar", lab), month = q(".g-month", lab), dur = q(".g-dur", lab);
    const cLine = q(".c-line", lab), cArea = q(".c-area", lab), cMin = q(".c-min", lab), marks = q(".c-marks", lab);
    const rows = qa(".debts li", lab);
    const base = simulate(debts, 0, "avalanche", false);
    const W = 600, H = 180, N = 72;
    const X = (m) => (m / base.months) * W;
    const Y = (v) => H - 14 - (v / base.totals[0]) * (H - 34);
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
        gBar.style.strokeDashoffset = (326.7 * (1 - clamp(v.months / base.months))).toFixed(1);
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
      if (animate && G) {
        const tw = { ...shownVals };
        G.to(state, { k: 1, duration: .9, ease: "expo.out", startAt: { k: 0 }, onUpdate: () => draw(state.k) });
        G.to(tw, { ...vals, duration: .9, ease: "expo.out", onUpdate: () => write(tw) });
        G.fromTo(qa("span", marks), { scale: 0 }, { scale: 1, duration: .6, ease: "back.out(3)", stagger: .06, delay: .25 });
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
      const res = simulate(debts, extra, method);
      render(res, animate);
    };
    const setMethod = (m) => {
      method = m;
      segBtns.forEach((b, i) => {
        const on = b.dataset.m === m;
        b.setAttribute("aria-checked", String(on));
        if (on) thumb.style.transform = `translateX(${(rtl ? -1 : 1) * i * 100}%)`;
      });
      hint.textContent = data.labels[`hint_${m}`];
      run(true);
    };
    segBtns.forEach((b) => b.addEventListener("click", () => setMethod(b.dataset.m)));
    let raf = 0;
    range.addEventListener("input", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => run(true)); });
    // A first draw without animation, so the numbers are there even before the section is reached.
    setMethod("avalanche");
    labIntro = () => {
      shown = null;
      shownVals = { interest: 0, saved: 0, sooner: 0, months: 0 };
      run(true);
    };
    if (!motion || !G) run(false);
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
      { t: "", b: fmt(T.notif_milestone_halfway_body, [Nm.loan]), title: T.notif_milestone_halfway_title, when: ago(-1, "day") },
      { t: "", b: fmt(T.notif_debt_1day_body, [Nm.loan, moneyN.format(A.loan)]), when: ago(-3, "hour") },
      { t: "", b: fmt(T.notif_cc_early_body, [Nm.card, moneyN.format(A.card), day(2)]), when: ago(-1, "hour") },
      { t: "", b: fmt(T.notif_budget_body, [76, Nm.budget, money(A.used), money(A.limit)]), title: T.notif_budget_warning_title, when: ago(-12, "minute") },
      { t: "", b: fmt(T.notif_celebration_debt_body, [Nm.store, plainN.format(142), money(A.saved)]), title: T.notif_celebration_debt_title, when: ago(0, "second") },
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
    const date = q(".lock-date", lock);
    date.textContent = new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long" }).format(new Date());
    if (!motion || !G) {
      notes.slice().reverse().forEach((n) => list.appendChild(make(n)));
    } else {
      playNotes = () => {
        list.innerHTML = "";
        const tl = G.timeline();
        notes.forEach((n, i) => {
          tl.add(() => {
            const li = make(n);
            list.prepend(li);
            G.fromTo(li, { height: 0, marginBottom: -10, autoAlpha: 0, scale: .86, y: -30 },
              { height: "auto", marginBottom: 0, autoAlpha: 1, scale: 1, y: 0, duration: .9, ease: "expo.out" });
          }, i * .55);
        });
        return tl;
      };
    }
  }

  // ---------------------------------------------------------------- marquee money: one amount, many currencies
  const moneyRow = q("[data-money]");
  if (moneyRow) {
    const rates = { USD: 1, EUR: .92, JPY: 150, GBP: .79, TRY: 41, BRL: 5.4, INR: 84, KRW: 1380, CAD: 1.37, SAR: 3.75, CNY: 7.2, PLN: 4, SEK: 10.5, MXN: 18, IDR: 16000, THB: 35, ILS: 3.7, VND: 25000, UAH: 41.5, CHF: .88 };
    const list = [[locale, currency], ["en-US", "USD"], ["de-DE", "EUR"], ["ja-JP", "JPY"], ["en-GB", "GBP"], ["tr-TR", "TRY"], ["pt-BR", "BRL"],
      ["hi-IN", "INR"], ["ko-KR", "KRW"], ["fr-CA", "CAD"], ["ar-SA", "SAR"], ["zh-CN", "CNY"], ["pl-PL", "PLN"], ["sv-SE", "SEK"], ["es-MX", "MXN"],
      ["id-ID", "IDR"], ["th-TH", "THB"], ["he-IL", "ILS"], ["de-CH", "CHF"], ["uk-UA", "UAH"]];
    const seen = new Set();
    const html = list.filter(([, c]) => !seen.has(c) && seen.add(c)).map(([l, c], k) => {
      const v = 3612.29 * (rates[c] || 1);
      let s;
      try { s = new Intl.NumberFormat(l, { style: "currency", currency: c, maximumFractionDigits: v > 9999 ? 0 : 2 }).format(v); } catch (err) { s = `${c} ${Math.round(v)}`; }
      return `<span>${s}</span><i></i>`;
    }).join("");
    moneyRow.innerHTML = html + html;
  }

  // ---------------------------------------------------------------- to top
  const toTop = q(".to-top");
  const stageEl = q(".stage");
  const updateTop = () => {
    if (!toTop) return;
    const max = d.documentElement.scrollHeight - innerHeight;
    const after = stageEl ? stageEl.offsetTop + stageEl.offsetHeight : innerHeight * 1.2;
    toTop.classList.toggle("show", scrollY > after);
    toTop.style.setProperty("--p", (max > 0 ? scrollY / max : 0).toFixed(3));
  };
  addEventListener("scroll", updateTop, { passive: true });
  if (toTop) toTop.addEventListener("click", (ev) => { ev.preventDefault(); if (window.__lenis) window.__lenis.scrollTo(0, { duration: 1.6 }); else scrollTo({ top: 0, behavior: motion ? "smooth" : "auto" }); });

  // ---------------------------------------------------------------- counters without motion
  if (!motion || !G) {
    qa("[data-count]").forEach((el) => { el.textContent = plainN.format(Number(el.dataset.count)); });
  }

  if (!G || !ST) { root.classList.add("ready"); return; }
  G.registerPlugin(ST);
  if (window.SplitText) G.registerPlugin(window.SplitText);
  if (window.DrawSVGPlugin) G.registerPlugin(window.DrawSVGPlugin);
  if (window.CustomEase) G.registerPlugin(window.CustomEase);
  const ease = window.CustomEase ? window.CustomEase.create("spendry", "M0,0 C0.16,1 0.3,1 1,1") : "expo.out";

  if (!motion) {
    // Reduced motion: final states, and the lab drawn once.
    qa("[data-rise], .hero-copy [data-hero], .phones").forEach((el) => { el.style.opacity = 1; el.style.transform = "none"; });
    qa(".hero-title .ln-in").forEach((el) => { el.style.transform = "none"; });
    root.classList.add("ready");
    return;
  }

  // ---------------------------------------------------------------- smooth scrolling
  let lenis = null;
  if (window.Lenis) {
    lenis = new window.Lenis({ lerp: .085, smoothWheel: true, wheelMultiplier: 1, touchMultiplier: 1.4, syncTouch: false });
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
      lenis.scrollTo(target, { offset: 0, duration: 1.8 });
    }));
  }
  ST.config({ ignoreMobileResize: true });

  // ---------------------------------------------------------------- nav: hides going down, comes back going up; dark or light
  const nav = q("[data-nav]");
  let lastY = scrollY, navTheme = "dark";
  const setNav = (theme) => { if (theme !== navTheme) { navTheme = theme; nav.classList.toggle("light", theme === "light"); } };
  const onScrollNav = () => {
    const y = scrollY;
    const langOpen = langBtn && langBtn.getAttribute("aria-expanded") === "true";
    if (!langOpen) nav.classList.toggle("away", y > 160 && y > lastY + 2);
    if (y < lastY - 2 || y < 160) nav.classList.remove("away");
    lastY = y;
  };
  addEventListener("scroll", onScrollNav, { passive: true });
  qa("[data-theme]").forEach((sec) => {
    if (sec.classList.contains("stage")) return;
    ST.create({ trigger: sec, start: "top 36px", end: "bottom 36px", onToggle: (self) => { if (self.isActive) setNav(sec.dataset.theme); } });
  });
  if (d.body.classList.contains("page-tool") || d.body.classList.contains("page-nf")) setNav("dark");

  // ---------------------------------------------------------------- pointer: a soft ring that follows and grows over what can be pressed
  if (fine) {
    const cur = d.createElement("div");
    cur.className = "cursor";
    cur.setAttribute("aria-hidden", "true");
    cur.innerHTML = "<i></i><b></b>";
    d.body.appendChild(cur);
    const ring = q("i", cur), dot = q("b", cur);
    const rx = G.quickTo(ring, "x", { duration: .5, ease: "power3.out" }), ry = G.quickTo(ring, "y", { duration: .5, ease: "power3.out" });
    const dx = G.quickTo(dot, "x", { duration: .12, ease: "power3.out" }), dy = G.quickTo(dot, "y", { duration: .12, ease: "power3.out" });
    addEventListener("pointermove", (ev) => {
      if (ev.pointerType !== "mouse") return;
      rx(ev.clientX); ry(ev.clientY); dx(ev.clientX); dy(ev.clientY);
      cur.classList.add("on");
    }, { passive: true });
    d.addEventListener("pointerover", (ev) => {
      const t = ev.target.closest && ev.target.closest("a, button, input, summary, [data-tilt], .ring-stage");
      cur.classList.toggle("drag", !!t && t.classList.contains("ring-stage"));
      cur.classList.toggle("hover", !!t && !t.classList.contains("ring-stage"));
    });
    d.addEventListener("pointerdown", () => cur.classList.add("down"));
    d.addEventListener("pointerup", () => cur.classList.remove("down"));
    d.documentElement.addEventListener("pointerleave", () => cur.classList.remove("on"));
  }

  // ---------------------------------------------------------------- the flowing ribbons (WebGL), paused when out of sight
  const auroras = qa("canvas.aurora").map((canvas) => ribbons(canvas)).filter(Boolean);
  function ribbons(canvas) {
    const gl = canvas.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power", preserveDrawingBuffer: false });
    if (!gl) return null;
    const small = innerWidth < 900;
    const LINES = small ? 16 : 26;
    const vs = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    const fs = `precision mediump float;uniform vec2 R;uniform float T;uniform vec2 M;uniform float K;
      vec3 pal(float t){t=abs(fract(t*.5)*2.-1.);
        return t<.5?mix(vec3(.22,.8,1.),vec3(.2,.45,1.),t*2.):mix(vec3(.2,.45,1.),vec3(.62,.4,1.),(t-.5)*2.);}
      float band(vec2 p,float k,float t,out float glow){
        float c=.13*sin(p.x*1.1+t*.3+k*2.4)+.05*sin(p.x*2.3-t*.41+k*1.3)+p.x*.3-.06-k*.3+K*.0;
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
        p+=M*.035;
        float t=T;
        vec3 col=vec3(.016,.024,.07);
        col+=vec3(.03,.06,.22)*smoothstep(1.4,0.,length(p-vec2(.55,.35)));
        col+=vec3(.13,.04,.24)*.6*smoothstep(1.2,0.,length(p-vec2(-.8,-.45)));
        float ga,gb;
        float a=band(p,0.,t,ga);
        col+=pal(.1+p.x*.25+t*.02)*(a*.2+ga*.08);
        float b=band(p,1.,t*.85+4.,gb);
        col+=pal(.9+p.x*.2-t*.015)*(b*.11+gb*.04);
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
    const uR = gl.getUniformLocation(pr, "R"), uT = gl.getUniformLocation(pr, "T"), uM = gl.getUniformLocation(pr, "M"), uK = gl.getUniformLocation(pr, "K");
    const scale = small ? .5 : .62;
    const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
    let visible = false, running = false, t0 = performance.now(), last = 0, spread = 1;
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
      gl.uniform1f(uK, spread);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      requestAnimationFrame(frame);
    };
    const start = () => { if (!running && visible) requestAnimationFrame(frame); };
    new IntersectionObserver(([en]) => { visible = en.isIntersecting; start(); }).observe(canvas);
    d.addEventListener("visibilitychange", start);
    if (fine) addEventListener("pointermove", (ev) => { mouse.tx = ev.clientX / innerWidth - .5; mouse.ty = .5 - ev.clientY / innerHeight; }, { passive: true });
    canvas.classList.add("on");
    return { canvas, setVisible: (yes) => { visible = yes; start(); }, setSpread: (s) => { spread = s; } };
  }

  // ---------------------------------------------------------------- shared reveals
  const splitReady = window.SplitText && !root.classList.contains("no-split");
  qa("[data-split]").forEach((el) => {
    if (el.closest(".stage")) return;
    if (splitReady) {
      window.SplitText.create(el, {
        type: "lines", mask: "lines", linesClass: "split-line", autoSplit: true,
        onSplit: (self) => G.from(self.lines, { yPercent: 110, rotate: rtl ? -2 : 2, duration: 1.3, ease, stagger: .09,
          scrollTrigger: { trigger: el, start: "top 88%", once: true } }),
      });
    } else {
      G.from(el, { y: 50, autoAlpha: 0, duration: 1.3, ease, scrollTrigger: { trigger: el, start: "top 88%", once: true } });
    }
  });
  ST.batch("[data-rise]", {
    start: "top 90%", once: true,
    onEnter: (els) => G.to(els, { opacity: 1, y: 0, duration: 1.1, ease, stagger: .08, overwrite: true }),
  });

  // Dark sections open as a circle growing from their top edge.
  qa(".bgc").forEach((bg) => {
    const sec = bg.parentElement;
    if (sec.classList.contains("ring")) return;   // follows the widgets, which are dark already
    G.fromTo(bg, { clipPath: "circle(0% at 50% 0%)" }, { clipPath: "circle(142% at 50% 0%)", ease: "none",
      scrollTrigger: { trigger: sec, start: "top 96%", end: "top 18%", scrub: true } });
  });

  // ---------------------------------------------------------------- hero and story
  const stage = q(".stage");
  if (stage) {
    const pin = q(".stage-pin", stage);
    const phones = q(".phones", stage), pc = q(".pw-c", stage), pl = q(".pw-l", stage), pr = q(".pw-r", stage);
    const inC = q(".ph-c", stage), inL = q(".ph-l", stage), inR = q(".ph-r", stage);
    const floats = qa(".fw", stage), floatPar = qa(".fp", stage), floatImg = qa(".float", stage);
    const copy = q(".hero-copy", stage), caps = qa(".cap", stage);
    const wash = q(".wash", stage), cue = q(".scroll-cue", stage), ring = q(".story-ring", stage), ringBar = q(".story-ring .bar", stage);
    const dots = qa(".story-ring .dot", stage), scr = qa(".scr", stage), lifts = qa(".lift", stage), dim = q(".dim", stage);
    const aurora = auroras.find((a) => stage.contains(a.canvas));
    const cardCenter = (el) => {
      const s = el.dataset.card.match(/left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:([\d.]+)%/);
      return s ? [Number(s[1]) + Number(s[3]) / 2, Number(s[2]) + Number(s[4]) / 2] : [50, 30];
    };
    const centers = scr.map(cardCenter);
    scr.forEach((el, i) => { if (i) G.set(el, { clipPath: `circle(0% at ${centers[i][0]}% ${centers[i][1]}%)` }); });
    G.set(pl, { xPercent: -58, yPercent: 4, z: -240, rotationY: rtl ? -24 : 24, scale: .84 });
    G.set(pr, { xPercent: 58, yPercent: 4, z: -240, rotationY: rtl ? 24 : -24, scale: .84 });
    G.set(floats[0], { xPercent: -96, yPercent: 70, rotation: -6 });
    G.set(floats[1], { xPercent: 30, yPercent: -150, rotation: 5 });
    G.set(lifts, { autoAlpha: 0 });

    // Arrival: the page opens as a circle, the headline rises line by line and the phones fan out.
    const intro = G.timeline({ defaults: { ease } });
    intro.fromTo(pin, { clipPath: "circle(0% at 50% 55%)" }, { clipPath: "circle(120% at 50% 55%)", duration: 1.6, ease: "expo.inOut", clearProps: "clipPath" })
      .to(qa(".hero-title .ln-in", stage), { y: 0, duration: 1.4, stagger: .12 }, .5)
      .to(qa("[data-hero]", copy), { opacity: 1, duration: 1.2, stagger: .09 }, .75)
      .fromTo(qa("[data-hero]", copy), { y: 26 }, { y: 0, duration: 1.2, stagger: .09 }, .75)
      .to(phones, { opacity: 1, duration: .8 }, .45)
      .from(inC, { yPercent: 36, rotationX: 28, scale: .78, duration: 1.8 }, .45)
      .from(inL, { xPercent: 64, rotationY: rtl ? 26 : -26, scale: .8, opacity: 0, duration: 1.8 }, .7)
      .from(inR, { xPercent: -64, rotationY: rtl ? -26 : 26, scale: .8, opacity: 0, duration: 1.8 }, .7)
      .from(floatImg, { scale: .5, autoAlpha: 0, y: 60, duration: 1.4, stagger: .18 }, 1.1)
      .from(cue, { autoAlpha: 0, scale: .5, duration: 1.2 }, 1.3);

    // A gentle float and tilt that follows the pointer while the hero is on screen.
    if (fine) {
      const rx = G.quickTo(phones, "rotationX", { duration: 1.2, ease: "power3.out" });
      const ry = G.quickTo(phones, "rotationY", { duration: 1.2, ease: "power3.out" });
      const fx = floatPar.map((f) => G.quickTo(f, "x", { duration: 1.4, ease: "power3.out" }));
      const fy = floatPar.map((f) => G.quickTo(f, "y", { duration: 1.4, ease: "power3.out" }));
      stage.addEventListener("pointermove", (ev) => {
        if (scrollY > innerHeight * .3) return;
        const x = ev.clientX / innerWidth - .5, y = ev.clientY / innerHeight - .5;
        rx(-y * 8); ry(x * 10);
        fx.forEach((f, i) => f(x * (i ? -34 : 44))); fy.forEach((f, i) => f(y * (i ? -26 : 34)));
      });
    }
    G.to(floatImg, { yPercent: -6, duration: 3.2, ease: "sine.inOut", yoyo: true, repeat: -1, stagger: 1.1 });

    // Now and then one of the app's own notifications drops in above the phone, as it would on a Lock Screen.
    const N = window.__spendryNotes;
    if (N && N.notes.length) {
      const toast = d.createElement("div");
      toast.className = "toast";
      toast.setAttribute("aria-hidden", "true");
      phones.appendChild(toast);
      const order = [2, 3, 1, 4];
      let k = 0;
      const show = () => {
        if (scrollY > innerHeight * .15 || d.hidden) return;
        toast.innerHTML = "";
        const card = N.make(N.notes[order[k++ % order.length]]);
        toast.appendChild(card);
        G.timeline()
          .fromTo(card, { y: -46, scale: .86, autoAlpha: 0, filter: "blur(8px)" }, { y: 0, scale: 1, autoAlpha: 1, filter: "blur(0px)", duration: .9, ease: "back.out(1.4)" })
          .to(card, { y: -24, scale: .94, autoAlpha: 0, duration: .6, ease: "power2.in" }, "+=3.4");
      };
      G.delayedCall(3.4, function loop() { show(); G.delayedCall(7.5, loop); });
    }

    const mm = G.matchMedia();
    mm.add({ wide: "(min-width: 900px)", narrow: "(max-width: 899px)" }, (ctx) => {
      const { wide } = ctx.conditions;
      let washAt = "72% 50%";
      const measure = () => {
        const a = pin.getBoundingClientRect(), b = pc.getBoundingClientRect();
        washAt = `${(((b.left + b.width / 2) - a.left) / a.width * 100).toFixed(1)}% ${(((b.top + b.height / 2) - a.top) / a.height * 100).toFixed(1)}%`;
      };
      measure();
      const tl = G.timeline({
        defaults: { ease: "power2.inOut" },
        scrollTrigger: {
          trigger: stage, pin, start: "top top", end: () => `+=${Math.round(innerHeight * (wide ? 3.4 : 3.1))}`, scrub: .8,
          invalidateOnRefresh: true, anticipatePin: 1, onRefreshInit: measure,
          onUpdate: (self) => {
            setNav(self.progress > .11 ? "light" : "dark");
            if (aurora) aurora.setVisible(self.progress < .2 && self.isActive || self.progress < .05);
            const step = self.progress < .41 ? 0 : self.progress < .71 ? 1 : 2;
            dots.forEach((dot, i) => dot.classList.toggle("on", i <= step));
          },
        },
      });
      // Each step: the camera moves in on the screen's main card, the card lifts off the screen, then all settles back.
      const zoom = wide ? 1.38 : 1.24;
      const lift = (i, at) => {
        tl.set(inC, { transformOrigin: `${centers[i][0]}% ${centers[i][1]}%` }, at)
          .fromTo(inC, { scale: 1 }, { scale: zoom, duration: 1, ease: "power3.inOut", immediateRender: false }, at)
          .to(lifts[i], { autoAlpha: 1, duration: .01 }, at + .35)
          .fromTo(lifts[i], { scale: 1, yPercent: 0, boxShadow: "0 0 0 rgba(10,15,40,0)" },
            { scale: 1.06, yPercent: -6, boxShadow: "0 40px 80px -20px rgba(10,15,40,.45), 0 0 0 1px rgba(10,15,40,.06)", duration: .8, ease: "power3.out", immediateRender: false }, at + .35)
          .to(dim, { opacity: 1, duration: .8 }, at + .35)
          .to(lifts[i], { scale: 1, yPercent: 0, boxShadow: "0 0 0 rgba(10,15,40,0)", duration: .6, ease: "power2.inOut" }, at + 1.45)
          .to(dim, { opacity: 0, duration: .6 }, at + 1.45)
          .to(inC, { scale: 1, duration: .8, ease: "power3.inOut" }, at + 1.45)
          .to(lifts[i], { autoAlpha: 0, duration: .01 }, at + 2.05);
      };
      const toast = q(".toast", stage);
      if (toast) tl.to(toast, { autoAlpha: 0, y: -30, duration: .4 }, 0);
      tl.to(copy, { y: -90, autoAlpha: 0, duration: 1.1, ease: "power2.in" }, 0)
        .to(cue, { autoAlpha: 0, scale: .6, duration: .5 }, 0)
        .to(pl, { xPercent: -150, z: -700, rotationY: rtl ? -60 : 60, autoAlpha: 0, duration: 1.4, ease: "power2.in" }, 0)
        .to(pr, { xPercent: 150, z: -700, rotationY: rtl ? 60 : -60, autoAlpha: 0, duration: 1.4, ease: "power2.in" }, 0)
        .to(floats[0], { x: "-=260", y: "+=220", rotation: -24, autoAlpha: 0, duration: 1.2, ease: "power2.in" }, 0)
        .to(floats[1], { x: "+=260", y: "-=240", rotation: 22, autoAlpha: 0, duration: 1.2, ease: "power2.in" }, 0)
        .to(phones, { rotationX: 0, rotationY: 0, duration: 1 }, 0)
        .fromTo(wash, { clipPath: () => `circle(0% at ${washAt})` }, { clipPath: () => `circle(175% at ${washAt})`, duration: 1.6, ease: "power2.in" }, .25);
      if (wide) {
        tl.to(pc, { scale: 1.06, duration: 1.4 }, .2);
      } else {
        tl.to(phones, { y: () => -innerHeight * .64, duration: 1.4 }, .1).to(pc, { scale: .8, duration: 1.4 }, .1);
      }
      tl.to(ring, { opacity: 1, duration: .6 }, 1.3)
        .fromTo(caps[0], { autoAlpha: 0, y: 50 }, { autoAlpha: 1, y: 0, duration: .8, ease: "power3.out" }, 1.4)
        .to(ringBar, { strokeDashoffset: 163.4 * (2 / 3), duration: .8 }, 1.4);
      lift(0, 2.1);
      tl.to(caps[0], { autoAlpha: 0, y: -50, duration: .6, ease: "power2.in" }, 4.4)
        .to(scr[1], { clipPath: `circle(150% at ${centers[1][0]}% ${centers[1][1]}%)`, duration: 1.1, ease: "power2.inOut" }, 4.5)
        .fromTo(caps[1], { autoAlpha: 0, y: 50 }, { autoAlpha: 1, y: 0, duration: .8, ease: "power3.out" }, 5)
        .to(ringBar, { strokeDashoffset: 163.4 / 3, duration: .8 }, 5);
      lift(1, 5.8);
      tl.to(caps[1], { autoAlpha: 0, y: -50, duration: .6, ease: "power2.in" }, 8.1)
        .to(scr[2], { clipPath: `circle(150% at ${centers[2][0]}% ${centers[2][1]}%)`, duration: 1.1, ease: "power2.inOut" }, 8.2)
        .fromTo(caps[2], { autoAlpha: 0, y: 50 }, { autoAlpha: 1, y: 0, duration: .8, ease: "power3.out" }, 8.7)
        .to(ringBar, { strokeDashoffset: 0, duration: .8 }, 8.7);
      lift(2, 9.5);
      tl.to({}, { duration: .8 }, 11.6);
      return () => { setNav("dark"); };
    });
  }

  // ---------------------------------------------------------------- marquee: drifts on its own, faster and leaning while scrolling
  const tracks = qa(".mq-track");
  if (tracks.length) {
    const pos = tracks.map(() => 0);
    let vel = 0, skew = 0, visible = false;
    ST.create({ trigger: ".marquee", start: "top bottom", end: "bottom top", onToggle: (s) => { visible = s.isActive; },
      onUpdate: (s) => { vel = s.getVelocity(); } });
    const setters = tracks.map((t) => G.quickSetter(t, "css"));
    G.ticker.add((time, dt) => {
      if (!visible) return;
      vel *= .92;
      skew += (clamp(vel / 180, -9, 9) - skew) * .1;
      tracks.forEach((t, i) => {
        const dir = (i ? -1 : 1) * (rtl ? -1 : 1);
        const speed = (.012 + Math.min(Math.abs(vel) / 26000, .12)) * dt;
        pos[i] = (pos[i] - speed * dir) % 50;
        if (pos[i] > 0) pos[i] -= 50;
        setters[i]({ xPercent: pos[i], skewX: -skew * (i ? -1 : 1) });
      });
    });
  }

  // ---------------------------------------------------------------- statement: words light up with the scroll
  const words = q(".words");
  if (words) {
    const ws = qa(".w", words), hls = qa(".hl", words);
    let lit = -1;
    ST.create({
      trigger: words, start: "top 82%", end: "bottom 48%", scrub: true,
      onUpdate: (s) => {
        const n = Math.round(s.progress * ws.length);
        if (n === lit) return;
        lit = n;
        ws.forEach((w, i) => w.classList.toggle("on", i < n));
        hls.forEach((h) => h.classList.toggle("on", qa(".w", h).every((w) => w.classList.contains("on"))));
      },
    });
    G.from(words, { scale: .94, transformOrigin: rtl ? "100% 50%" : "0% 50%", ease: "none", scrollTrigger: { trigger: words, start: "top bottom", end: "top 40%", scrub: true } });
  }

  // ---------------------------------------------------------------- orbit: every part of the money picture circles the app
  const orbit = q(".orbit-stage");
  if (orbit) {
    const pillsIn = qa(".ring-in .pill", orbit), pillsOut = qa(".ring-out .pill", orbit);  // inner spans; the li around each one circles
    const lines = qa(".orbit-lines circle", orbit);
    const tl = G.timeline({ scrollTrigger: { trigger: orbit, start: "top 78%", once: true } });
    tl.from(orbit, { scale: .55, rotate: -40, autoAlpha: 0, duration: 1.8, ease })
      .from(lines, { drawSVG: window.DrawSVGPlugin ? "0%" : undefined, autoAlpha: 0, duration: 1.6, stagger: .15, ease }, .1)
      .from(q(".orbit-core", orbit), { scale: 0, duration: 1.4, ease: "back.out(1.8)" }, .3)
      .from(pillsIn, { autoAlpha: 0, scale: .3, duration: .9, stagger: .07, ease: "back.out(2)" }, .6)
      .from(pillsOut, { autoAlpha: 0, scale: .3, duration: .9, stagger: .05, ease: "back.out(2)" }, .8);
    let p = 0, active = false;
    ST.create({ trigger: ".orbit", start: "top bottom", end: "bottom top", onToggle: (s) => { active = s.isActive; }, onUpdate: (s) => { p = s.progress; } });
    let a = 0;
    G.ticker.add((time, dt) => {
      if (!active) return;
      a += dt * .004;
      orbit.style.setProperty("--rot", `${(a + p * 140).toFixed(2)}deg`);
      orbit.style.setProperty("--rot2", `${(-a * .7 - p * 100).toFixed(2)}deg`);
    });
  }

  // ---------------------------------------------------------------- features: tiles open up, the screens settle, and tilt under the pointer
  qa(".tile").forEach((tile, i) => {
    const shot = q(".tile-shot", tile);
    const tl = G.timeline({ scrollTrigger: { trigger: tile, start: "top 88%", once: true } });
    tl.from(tile, { y: 90, autoAlpha: 0, scale: .94, duration: 1.4, ease, delay: (i % 3) * .08 })
      .fromTo(tile, { clipPath: "inset(14% 8% 0% 8% round 30px)" }, { clipPath: "inset(0% 0% 0% 0% round 30px)", duration: 1.4, ease, clearProps: "clipPath" }, "<")
      .from(shot, { yPercent: 40, rotate: rtl ? 14 : -14, scale: 1.25, duration: 1.8, ease }, "<.1")
      .from(qa(".tile-copy > *", tile), { y: 24, autoAlpha: 0, duration: 1, stagger: .07, ease }, "<.2");
    G.to(shot, { yPercent: -10, ease: "none", scrollTrigger: { trigger: tile, start: "top bottom", end: "bottom top", scrub: true } });
  });
  if (fine) {
    qa("[data-tilt]").forEach((el) => {
      const rx = G.quickTo(el, "rotationX", { duration: .7, ease: "power3.out" });
      const ry = G.quickTo(el, "rotationY", { duration: .7, ease: "power3.out" });
      G.set(el, { transformPerspective: 1100 });
      el.addEventListener("pointermove", (ev) => {
        const r = el.getBoundingClientRect();
        const x = (ev.clientX - r.left) / r.width, y = (ev.clientY - r.top) / r.height;
        rx((.5 - y) * 7); ry((x - .5) * 9);
        el.style.setProperty("--gx", `${x * 100}%`); el.style.setProperty("--gy", `${y * 100}%`);
      });
      el.addEventListener("pointerleave", () => { rx(0); ry(0); });
    });
    qa("[data-magnetic]").forEach((el) => {
      const mx = G.quickTo(el, "x", { duration: .6, ease: "power3.out" }), my = G.quickTo(el, "y", { duration: .6, ease: "power3.out" });
      el.addEventListener("pointermove", (ev) => {
        const r = el.getBoundingClientRect();
        mx((ev.clientX - r.left - r.width / 2) * .22); my((ev.clientY - r.top - r.height / 2) * .3);
      });
      el.addEventListener("pointerleave", () => { mx(0); my(0); });
    });
  }

  // ---------------------------------------------------------------- lab: the panel rises, the ring and the line draw
  if (lab) {
    const tl = G.timeline({ scrollTrigger: { trigger: lab, start: "top 75%", once: true } });
    tl.from(lab, { y: 80, autoAlpha: 0, scale: .96, duration: 1.4, ease })
      .add(() => labIntro && labIntro(), .2)
      .from(qa(".debts li", lab), { x: rtl ? -30 : 30, autoAlpha: 0, duration: .9, stagger: .07, ease }, .4)
      .from(q(".gauge", lab), { rotate: -120, scale: .7, autoAlpha: 0, duration: 1.4, ease }, .2);
  }

  // ---------------------------------------------------------------- reminders: notifications arrive, the countdown ticks
  if (lock) {
    const count = q(".count"), num = q(".c-num"), bar = q(".c-bar");
    const tl = G.timeline({ scrollTrigger: { trigger: lock, start: "top 70%", once: true } });
    tl.from(lock, { y: 100, rotate: rtl ? -4 : 4, scale: .92, autoAlpha: 0, duration: 1.6, ease })
      .from(q(".lock-time", lock), { y: -30, autoAlpha: 0, duration: 1.2, ease }, .3)
      .add(() => playNotes && playNotes(), .7);
    if (count) {
      const c = { v: 7 };
      G.timeline({ scrollTrigger: { trigger: count, start: "top 85%", once: true } })
        .fromTo(bar, { strokeDashoffset: 326.7 }, { strokeDashoffset: 326.7 * (1 - 4 / 7) * .9 + 20, duration: 2.2, ease: "power2.inOut" })
        .to(c, { v: 3, duration: 2.2, ease: "power2.inOut", onUpdate: () => { num.textContent = plainN.format(Math.round(c.v)); } }, 0);
    }
  }

  // ---------------------------------------------------------------- widgets: from one widget to the whole Home Screen
  const wall = q(".wall");
  if (wall) {
    const focus = q(".wp", wall);
    const others = qa(".w", wall).filter((w) => w !== focus && getComputedStyle(w).display !== "none");
    const box = q(".wall-box");
    let dx = 0, dy = 0, s0 = 2.2, sf = 1;
    const measure = () => {
      G.set(wall, { clearProps: "transform" });
      const a = wall.getBoundingClientRect(), b = focus.getBoundingClientRect(), c = box.getBoundingClientRect();
      dx = (a.left + a.width / 2) - (b.left + b.width / 2);
      dy = (a.top + a.height / 2) - (b.top + b.height / 2);
      sf = Math.min(1, (c.height - 44) / a.height, (innerWidth - 32) / a.width);
      s0 = Math.min(2.3, (innerWidth * .86) / b.width, (c.height * .9) / b.height);
    };
    measure();
    const tl = G.timeline({
      scrollTrigger: { trigger: ".wid", pin: ".wid-pin", start: "top top", end: () => `+=${Math.round(innerHeight * 1.5)}`, scrub: .8,
        invalidateOnRefresh: true, onRefreshInit: measure },
    });
    tl.fromTo(wall, { scale: () => s0, x: () => dx * s0, y: () => dy * s0 }, { scale: () => sf, x: 0, y: 0, duration: 1, ease: "power2.inOut" }, 0)
      .fromTo(others, { autoAlpha: 0, scale: .7 }, { autoAlpha: 1, scale: 1, duration: .5, stagger: { each: .03, from: "random" }, ease: "power2.out" }, .25)
      .from(".wid-bg img", { scale: 1.4, rotate: 10, duration: 1, ease: "none" }, 0)
      .to({}, { duration: .2 });
  }

  // ---------------------------------------------------------------- the ring of screens: turns with the scroll, and by hand
  const ringStage = q(".ring-stage");
  if (ringStage) {
    const rot = q(".ring-rot", ringStage), items = qa(".rs", ringStage), name = q(".ring-name");
    const state = { scroll: 0, drag: 0 };
    let front = -1, active = false;
    const renderRing = () => {
      const ry = state.scroll + state.drag;
      rot.style.setProperty("--ry", `${ry.toFixed(2)}deg`);
      items.forEach((it, i) => {
        let a = ((i * 36 + ry) % 360 + 540) % 360 - 180;
        const facing = Math.cos(a * Math.PI / 180);
        it.style.setProperty("--sh", clamp((1 - facing) * .55, 0, .8).toFixed(3));
      });
      const f = ((Math.round(-ry / 36) % 10) + 10) % 10;
      if (f !== front) {
        front = f;
        const label = items[f].dataset.name;
        G.to(name, { autoAlpha: 0, y: -8, duration: .15, onComplete: () => { name.textContent = label; G.to(name, { autoAlpha: 1, y: 0, duration: .35, ease }); } });
      }
    };
    ST.create({
      trigger: ".ring", pin: ".ring-pin", start: "top top", end: () => `+=${Math.round(innerHeight * 1.6)}`, scrub: .6,
      onToggle: (s) => { active = s.isActive; },
      onUpdate: (s) => { state.scroll = -s.progress * 324; renderRing(); },
    });
    G.from(ringStage, { y: 120, scale: .72, autoAlpha: 0, duration: 1.8, ease, scrollTrigger: { trigger: ".ring", start: "top 60%", once: true } });
    let down = false, sx = 0, sd = 0, v = 0, lx = 0, lt = 0;
    ringStage.addEventListener("pointerdown", (ev) => { down = true; sx = lx = ev.clientX; sd = state.drag; lt = performance.now(); v = 0; G.killTweensOf(state, "drag"); ringStage.setPointerCapture(ev.pointerId); });
    ringStage.addEventListener("pointermove", (ev) => {
      if (!down) return;
      const now = performance.now();
      v = (ev.clientX - lx) / Math.max(1, now - lt);
      lx = ev.clientX; lt = now;
      state.drag = sd + (ev.clientX - sx) * .28;
      renderRing();
    });
    const up = () => {
      if (!down) return;
      down = false;
      const target = Math.round((state.drag + v * 220) / 36) * 36 + (Math.round(state.scroll / 36) * 36 - state.scroll);
      G.to(state, { drag: target, duration: 1.4, ease: "expo.out", onUpdate: renderRing });
    };
    ringStage.addEventListener("pointerup", up);
    ringStage.addEventListener("pointercancel", up);
    renderRing();
  }

  // ---------------------------------------------------------------- automations: each step lights the next
  qa(".flow").forEach((flow, i) => {
    const wide = matchMedia("(min-width: 900px)").matches;
    G.timeline({ scrollTrigger: { trigger: flow, start: "top 85%", once: true } })
      .from(flow, { y: 60, autoAlpha: 0, duration: 1.2, ease })
      .from(qa(".node", flow), { scale: .7, autoAlpha: 0, duration: .8, stagger: .35, ease: "back.out(2)" }, .2)
      .from(qa(".wire", flow), { [wide ? "scaleX" : "scaleY"]: 0, duration: .5, stagger: .35, ease: "power2.inOut" }, .45);
  });

  // ---------------------------------------------------------------- privacy: the shield and its rings
  const privHero = q(".priv-hero");
  if (privHero) {
    G.from(privHero, { scale: .3, autoAlpha: 0, duration: 1.6, ease: "back.out(1.6)", scrollTrigger: { trigger: privHero, start: "top 80%", once: true } });
    G.to(privHero, { scale: 1.25, ease: "none", scrollTrigger: { trigger: ".priv", start: "top bottom", end: "bottom top", scrub: true } });
    G.from(".dnc", { scale: .6, autoAlpha: 0, duration: 1.2, ease: "back.out(2)", scrollTrigger: { trigger: ".dnc", start: "top 88%", once: true } });
  }

  // ---------------------------------------------------------------- numbers count up inside their rings
  qa(".st li").forEach((li) => {
    const bar = q(".s-bar", li), el = q("[data-count]", li);
    const end = Number(el.dataset.count);
    const c = { v: end > 0 ? 0 : 1024 };
    el.textContent = plainN.format(c.v);
    G.timeline({ scrollTrigger: { trigger: li, start: "top 85%", once: true } })
      .fromTo(bar, { strokeDashoffset: 339.3 }, { strokeDashoffset: 339.3 * (1 - Number(bar.dataset.f || 1)), duration: 2, ease }, 0)
      .to(c, { v: end, duration: 2, ease: "power3.out", onUpdate: () => { el.textContent = plainN.format(Math.round(c.v)); } }, 0)
      .from(li, { y: 40, autoAlpha: 0, duration: 1.2, ease }, 0);
  });

  // ---------------------------------------------------------------- finale: a circle of colour opens, the icon lands
  const final = q(".final");
  if (final) {
    G.fromTo(q(".final-bg", final), { clipPath: "circle(12% at 50% 70%)" }, { clipPath: "circle(120% at 50% 70%)", ease: "none",
      scrollTrigger: { trigger: final, start: "top 95%", end: "top 15%", scrub: true } });
    G.timeline({ scrollTrigger: { trigger: final, start: "top 55%", once: true } })
      .from(q(".final-icon", final), { scale: .2, rotate: -30, autoAlpha: 0, duration: 1.6, ease: "elastic.out(1, .55)" })
      .from(q(".spin-wrap", final), { scale: .6, rotate: -90, autoAlpha: 0, duration: 1.6, ease }, .5)
      .from(q(".qr", final), { x: rtl ? -40 : 40, autoAlpha: 0, duration: 1.2, ease }, .7);
  }

  // The big name in the footer rises into place.
  const mark = q(".foot-mark");
  if (mark) G.from(mark, { yPercent: 55, opacity: 0, ease: "none", scrollTrigger: { trigger: ".foot", start: "top 85%", end: "bottom bottom", scrub: true } });

  // Tool pages: the hero ribbons, the panels.
  qa(".tool-hero, .nf").forEach((hero) => {
    G.from(qa(".crumbs, .nf-code", hero), { y: 20, autoAlpha: 0, duration: 1, ease });
  });

  // "See how it works" and the scroll cue go to the first step of the story, not past it.
  qa("[data-story]").forEach((a) => a.addEventListener("click", (ev) => {
    const st = stage && ST.getAll().find((t) => t.pin && t.trigger === stage);
    if (!st) return;
    ev.preventDefault();
    const y = st.start + (st.end - st.start) * .2;
    if (lenis) lenis.scrollTo(y, { duration: 2.2 }); else scrollTo({ top: y, behavior: "smooth" });
  }));

  // Arriving at /#lab and the like: the pinned sections add height above, so go there again once they are set up.
  const goHash = () => {
    if (!location.hash || location.hash.length < 2) return;
    let t = null;
    try { t = q(location.hash); } catch (err) { return; }
    if (!t) return;
    if (lenis) lenis.scrollTo(t, { immediate: true, force: true }); else t.scrollIntoView();
  };
  root.classList.add("ready");
  addEventListener("load", () => { ST.refresh(); goHash(); });
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(() => ST.refresh());
})();
