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

  // First-screen pictures that start hidden wait in data-src (see build.py screen(later)); the script arrives after
  // the page has loaded, so now they can come.
  const swapIn = (img) => {
    if (img.dataset.srcset) { img.srcset = img.dataset.srcset; img.removeAttribute("data-srcset"); }
    img.src = img.dataset.src;
    img.removeAttribute("data-src");
  };
  qa("img[data-src]:not([data-near])").forEach(swapIn);
  // The wall of screens loads when the reader is getting close: before the story is pinned it sits so near the top
  // that the browser's own lazy loading would fetch it with the first screen.
  const nearImgs = qa("img[data-src][data-near]");
  if (nearImgs.length) {
    if (window.IntersectionObserver) {
      const io = new IntersectionObserver((entries) => entries.forEach((en) => { if (en.isIntersecting) { io.unobserve(en.target); swapIn(en.target); } }), { rootMargin: "1400px 0px 1400px 0px" });
      requestAnimationFrame(() => setTimeout(() => nearImgs.forEach((img) => io.observe(img)), 1200));
    } else nearImgs.forEach(swapIn);
  }

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
  // Filled in only when it comes near the screen: laying out twenty scripts' digits is the costliest text on the page.
  const moneyRow = q("[data-money]");
  const moneyText = () => {
    const rates = { USD: 1, EUR: .92, JPY: 150, GBP: .79, TRY: 41, BRL: 5.4, INR: 84, KRW: 1380, CAD: 1.37, SAR: 3.75, CNY: 7.2, PLN: 4, SEK: 10.5, MXN: 18, IDR: 16000, THB: 35, ILS: 3.7, VND: 25000, UAH: 41.5, CHF: .88 };
    const list = [[locale, currency], ["en-US", "USD"], ["de-DE", "EUR"], ["ja-JP", "JPY"], ["en-GB", "GBP"], ["tr-TR", "TRY"], ["pt-BR", "BRL"],
      ["hi-IN", "INR"], ["ko-KR", "KRW"], ["fr-CA", "CAD"], ["ar-SA", "SAR"], ["zh-CN", "CNY"], ["pl-PL", "PLN"], ["sv-SE", "SEK"], ["es-MX", "MXN"],
      ["id-ID", "IDR"], ["th-TH", "THB"], ["he-IL", "ILS"], ["de-CH", "CHF"], ["uk-UA", "UAH"]];
    const seen = new Set();
    return list.filter(([, c]) => !seen.has(c) && seen.add(c)).map(([l, c]) => {
      const v = 3612.29 * (rates[c] || 1);
      try { return new Intl.NumberFormat(l, { style: "currency", currency: c, maximumFractionDigits: v > 9999 ? 0 : 2 }).format(v); } catch (err) { return `${c} ${Math.round(v)}`; }
    });
  };
  if (moneyRow) {
    const html = moneyText().map((s) => `<span>${s}</span><i></i>`).join("");
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
    qa("[data-rise]").forEach((el) => el.classList.add("in", "done"));
    root.classList.add("ready");
    return;
  }

  /* Start-up is kept small on purpose: the first screen animates with CSS, things further down are watched with
     IntersectionObservers (no layout reads), and the scroll-linked parts are built one by one when the page is idle,
     then measured once. Slow phones and page-speed tests count every long task at load. */
  ST.config({ ignoreMobileResize: true, autoRefreshEvents: "visibilitychange,resize" });
  const jobs = [];
  const later = (fn) => jobs.push(fn);
  // Calls fn once for each element when it comes within `margin` of the screen.
  const when = (els, margin, fn) => {
    const list = els.filter(Boolean);
    if (!list.length) return null;
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (!en.isIntersecting) return;
      io.unobserve(en.target);
      fn(en.target, en);
    }), { rootMargin: margin });
    list.forEach((el) => io.observe(el));
    return io;
  };
  const AHEAD = "0px 0px 35% 0px";       // get ready a little before it shows
  const AT = (pct) => `0px 0px -${pct}% 0px`; // play when its top passes this far up the screen

  // ---------------------------------------------------------------- nav: hides going down, comes back going up; dark or light
  const nav = q("[data-nav]");
  let lastY = scrollY;
  const setNav = (theme) => nav.classList.toggle("light", theme === "light");
  const themed = qa("[data-theme]");
  let bands = [];
  const measureThemes = () => {
    bands = themed.map((sec) => { const r = sec.getBoundingClientRect(); return { a: r.top + scrollY, b: r.bottom + scrollY, t: sec.dataset.theme }; });
  };
  const navTheme = () => {
    const y = scrollY + 36;
    for (const band of bands) if (y >= band.a && y < band.b) { setNav(band.t); return; }
  };
  addEventListener("scroll", () => {
    const y = scrollY;
    const langOpen = langBtn && langBtn.getAttribute("aria-expanded") === "true";
    if (!langOpen) nav.classList.toggle("away", y > 160 && y > lastY + 2);
    if (y < lastY - 2 || y < 160) nav.classList.remove("away");
    lastY = y;
    navTheme();
  }, { passive: true });
  if (d.body.classList.contains("page-tool") || d.body.classList.contains("page-nf")) setNav("dark");

  // ---------------------------------------------------------------- shared reveals: titles line by line, the rest rises
  let riseK = 0, riseFrame = 0;
  when(qa('[data-rise]:not([data-rise="now"])'), AT(10), (el) => {
    // the ones that arrive together go one after another
    if (!riseFrame) riseFrame = requestAnimationFrame(() => { riseK = 0; riseFrame = 0; });
    el.style.setProperty("--d", `${(riseK++ * .07).toFixed(2)}s`);
    el.classList.add("in");
    setTimeout(() => el.classList.add("done"), 1100 + riseK * 70);
  });
  const splitReady = window.SplitText && !root.classList.contains("no-split");
  const titles = qa("[data-split]").filter((el) => !el.closest(".stage"));
  const splits = new Map();
  const prepTitle = (el) => {
    if (splits.has(el)) return;
    if (!splitReady) { splits.set(el, null); G.set(el, { y: 40, opacity: 0 }); return; }
    splits.set(el, window.SplitText.create(el, {
      type: "lines", mask: "lines", linesClass: "split-line", autoSplit: true,
      onSplit: (self) => (el.dataset.played ? null : G.set(self.lines, { yPercent: 105 })),
    }));
  };
  const playTitle = (el) => {
    prepTitle(el);
    el.dataset.played = "1";
    const sp = splits.get(el);
    if (sp) G.to(sp.lines, { yPercent: 0, duration: 1.1, ease, stagger: .08 });
    else G.to(el, { y: 0, opacity: 1, duration: 1.1, ease });
  };
  // A title that is already on screen when the page opens is left as it is (it was drawn in the first frame).
  const openingTitles = new Set();
  if (titles.length) {
    const first = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) openingTitles.add(en.target); });
      first.disconnect();
      const rest = titles.filter((el) => !openingTitles.has(el));
      when(rest, AHEAD, prepTitle);
      when(rest, AT(12), playTitle);
    });
    titles.forEach((el) => first.observe(el));
  }

  // ---------------------------------------------------------------- hero and story
  const stage = q(".stage");
  if (stage) {
    const pin = q(".stage-pin", stage);
    const phones = q(".phones", stage), pc = q(".pw-c", stage), pl = q(".pw-l", stage), pr = q(".pw-r", stage);
    const floats = qa(".fw", stage), floatPar = qa(".fp", stage), floatImg = qa(".float", stage);
    const copy = q(".hero-copy", stage), caps = qa(".cap", stage);
    const scr = qa(".scr", stage), lifts = qa(".lift", stage), slots = qa(".slot", stage);
    G.set(pl, { xPercent: -60, yPercent: 5, scale: .84, force3D: false });
    G.set(pr, { xPercent: 60, yPercent: 5, scale: .84, force3D: false });
    G.set(floats[0], { xPercent: -96, yPercent: 70, rotation: -6 });
    G.set(floats[1], { xPercent: 30, yPercent: -150, rotation: 5 });
    G.set(lifts, { autoAlpha: 0 });
    G.set(scr.slice(1), { xPercent: 100 * dir });
    stage.classList.add("set");
    // The headline, the words and the middle phone came in with CSS; the two cards settle beside the phone.
    const since = performance.now() / 1000;
    G.fromTo(floatImg, { y: 46, opacity: 0 }, { y: 0, opacity: 1, duration: 1.2, ease, stagger: .15, delay: Math.max(.2, .85 - since) });
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

    later(() => {
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
        const capIn = (i, at) => tl.fromTo(caps[i], { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: .8, ease: "power3.out", immediateRender: false }, at);
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
    });
  }

  // ---------------------------------------------------------------- the money row drifts slowly, a little faster while scrolling
  const tracks = qa(".mq-track");
  if (tracks.length) {
    const pos = tracks.map(() => 0);
    let vel = 0, visible = false, lastS = scrollY;
    const io = new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; });
    io.observe(q(".marquee"));
    // Plain style writes: GSAP would read each row's transform first, and reading anything inside a row that is
    // still left out of layout makes the browser lay it out (with all its fonts) on the spot.
    const setters = tracks.map((t) => (v) => { t.style.transform = `translate3d(${v.toFixed(3)}%,0,0)`; });
    G.ticker.add((time, dt) => {
      const y = scrollY;
      if (!visible) { lastS = y; return; }
      vel = Math.max(Math.abs(y - lastS) / Math.max(dt, 1) * 1000, vel * .9);
      lastS = y;
      tracks.forEach((t, i) => {
        const way = (i ? -1 : 1) * dir;
        const speed = (.0005 + Math.min(vel / 1500000, .0015)) * dt;
        pos[i] = (pos[i] - speed * way) % 50;
        if (pos[i] > 0) pos[i] -= 50;
        setters[i](pos[i]);
      });
    });
  }

  // ---------------------------------------------------------------- statement: words light up with the scroll
  const words = q(".words");
  if (words) later(() => {
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
  });

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
  const walls = G.matchMedia();
  // The two walls are pinned scenes further down: they are built when the reader comes near them (or after the page
  // has been quiet for a while), so opening the page doesn't pay for them.
  const scenes = [];
  const scene = (sel, build) => { const el = q(sel); if (el) scenes.push({ el, build }); };
  scene(".showcase", () => walls.add("(min-width: 761px)", () => {
    zoomOut(".showcase", ".sc-pin", ".sc-wall", ".scp-focus .scp-screen", ".sc-copy", ".scp",
      { focusY: .24, margin: 70, natural: 1206, max: 3, wide: .62, tall: .5, length: 1.7 });
  }));
  scene(".wid", () => walls.add("(min-width: 761px)", () => {
    zoomOut(".wid", ".wid-pin", ".wall", ".wp", ".wid-copy", ".w",
      { focusY: .5, margin: 70, natural: 1092, max: 2.3, wide: .86, tall: 1, length: 1.6 });
  }));
  // Builds every scene down to this one, in page order, then measures once.
  const buildTo = (target) => {
    if (!scenes.includes(target)) return;
    let sc;
    do { sc = scenes.shift(); sc.build(); } while (sc !== target);
    ST.sort();
    ST.refresh();
  };
  const buildAll = () => { if (scenes.length) buildTo(scenes[scenes.length - 1]); };
  // Going to a part of the page through a link: every pin above it has to exist first, or the place moves on the way.
  d.addEventListener("click", (ev) => {
    const a = ev.target.closest ? ev.target.closest('a[href*="#"]') : null;
    if (!a || a.hasAttribute("data-story")) return;
    const url = new URL(a.href, location.href);
    if (url.pathname === location.pathname && url.hash.length > 1 && url.hash !== "#main") buildAll();
  }, true);
  walls.add("(max-width: 760px)", () => {
    [[".sc-wall", ".scp"], [".wall", ".w"]].forEach(([wallSel, itemSel]) => {
      const wall = q(wallSel);
      if (!wall) return;
      const items = qa(itemSel, wall).filter((w) => getComputedStyle(w).display !== "none");
      when([wall], AHEAD, () => G.set(items, { y: 40, opacity: 0 }));
      when([wall], AT(15), () => G.to(items, { y: 0, opacity: 1, duration: 1, ease, stagger: .06 }));
    });
  });

  // ---------------------------------------------------------------- lab: numbers and the line draw when it comes into view
  if (lab) when([lab], AT(22), () => labIntro && labIntro());

  // ---------------------------------------------------------------- reminders: notifications arrive one by one
  if (lock) {
    when([lock], AHEAD, () => G.set(lock, { y: 80, opacity: 0 }));
    when([lock], AT(28), () => {
      G.timeline().fromTo(lock, { y: 80, opacity: 0 }, { y: 0, opacity: 1, duration: 1.3, ease })
        .add(() => playNotes && playNotes(), .5);
    });
  }

  // ---------------------------------------------------------------- automations: each step lights the next
  qa(".flow").forEach((flow) => {
    const prop = matchMedia("(min-width: 900px)").matches ? "scaleX" : "scaleY";
    when([flow], AHEAD, () => { G.set(qa(".step", flow), { opacity: 0, y: 14 }); G.set(qa(".wire", flow), { [prop]: 0 }); });
    when([flow], AT(12), () => {
      G.timeline()
        .fromTo(qa(".step", flow), { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: .7, stagger: .3, ease })
        .fromTo(qa(".wire", flow), { [prop]: 0 }, { [prop]: 1, duration: .5, stagger: .3, ease: "power2.inOut" }, .25);
    });
  });

  // ---------------------------------------------------------------- numbers count up
  const st = q(".st");
  if (st) {
    const els = qa("[data-count]", st);
    els.forEach((el) => { const end = Number(el.dataset.count); el.textContent = plainN.format(end > 0 ? 0 : 1024); });
    when([st], AT(15), () => els.forEach((el) => {
      const end = Number(el.dataset.count), c = { v: end > 0 ? 0 : 1024 };
      G.to(c, { v: end, duration: 1.8, ease: "power3.out", onUpdate: () => { el.textContent = plainN.format(Math.round(c.v)); } });
    }));
  }

  // ---------------------------------------------------------------- finale and footer
  const finalIcon = q(".final-icon");
  if (finalIcon) {
    when([q(".final")], AHEAD, () => G.set(finalIcon, { scale: .8, opacity: 0 }));
    when([q(".final")], AT(30), () => G.fromTo(finalIcon, { scale: .8, opacity: 0 }, { scale: 1, opacity: 1, duration: 1.2, ease }));
  }
  const mark = q(".foot-mark");
  if (mark) later(() => G.from(mark, { yPercent: 50, opacity: 0, ease: "none", scrollTrigger: { trigger: ".foot", start: "top 85%", end: "bottom bottom", scrub: true } }));

  // "See how it works" goes to the first step of the story, not past it.
  let lenis = null;
  qa("[data-story]").forEach((a) => a.addEventListener("click", (ev) => {
    const s = stage && ST.getAll().find((t) => t.pin && t.trigger === stage);
    if (!s) return;
    ev.preventDefault();
    const y = s.start + (s.end - s.start) * .18;
    if (lenis) lenis.scrollTo(y, { duration: 2 }); else scrollTo({ top: y, behavior: "smooth" });
  }));

  // ---------------------------------------------------------------- smooth scrolling (first of the idle jobs)
  jobs.unshift(() => {
    if (!fine && d.body.classList.contains("page-home") && ST.normalizeScroll) ST.normalizeScroll(true);
    if (!window.Lenis) return;
    lenis = new window.Lenis({ lerp: .09, smoothWheel: true, wheelMultiplier: 1, touchMultiplier: 1.4, syncTouch: false });
    window.__lenis = lenis;
    lenis.on("scroll", ST.update);
    // Pins change the page's height; Lenis keeps its own idea of how far it can scroll, so it is told every time.
    ST.addEventListener("refresh", () => lenis.resize());
    G.ticker.add((time) => lenis.raf(time * 1000));
    G.ticker.lagSmoothing(0);
    qa('a[href^="#"], a[href*="/#"]').forEach((a) => a.addEventListener("click", (ev) => {
      if (a.hasAttribute("data-story")) return;
      const url = new URL(a.href, location.href);
      if (url.pathname !== location.pathname || !url.hash) return;
      const target = url.hash === "#main" ? 0 : q(url.hash);
      if (target === null) return;
      ev.preventDefault();
      // to the section's own top edge: the sections are full bleed and leave room for the nav themselves
      lenis.scrollTo(target === 0 ? 0 : target.getBoundingClientRect().top + scrollY, { duration: 1.6 });
    }));
  });

  // Arriving at /#widgets and the like: pinned sections add height above, so go there again once they are set up.
  const goHash = () => {
    if (!location.hash || location.hash.length < 2) return;
    let t = null;
    try { t = q(location.hash); } catch (err) { return; }
    if (!t) return;
    if (lenis) lenis.scrollTo(t, { immediate: true, force: true }); else t.scrollIntoView();
  };
  // Triggers are made top to bottom, then measured once: every pinned section's extra height is counted for the
  // ones below it. The nav's colour bands are measured after them.
  const settle = () => { ST.sort(); ST.refresh(); measureThemes(); navTheme(); };
  ST.addEventListener("refresh", () => { measureThemes(); navTheme(); });
  const idle = window.requestIdleCallback ? (fn) => requestIdleCallback(fn, { timeout: 400 }) : (fn) => setTimeout(() => fn({ timeRemaining: () => 10, didTimeout: false }), 30);
  const work = (deadline) => {
    do { const job = jobs.shift(); if (job) job(); } while (jobs.length && deadline.timeRemaining() > 12);
    if (jobs.length) { idle(work); return; }
    idle(() => {
      if (location.hash.length > 1) while (scenes.length) scenes.shift().build();   // a deep link needs every pin above it (measured just below)
      settle();
      watchRows();
      setTimeout(warmFonts, 6000);
      scenes.forEach((sc) => when([sc.el], "150% 0px 150% 0px", () => buildTo(sc)));
      setTimeout(() => { const more = () => { if (!scenes.length) return; buildTo(scenes[0]); idle(more); }; idle(more); }, 8000);
      if (d.readyState === "complete") goHash(); else addEventListener("load", goHash, { once: true });
    });
  };
  // Names of the languages and amounts in many scripts: each script needs its own system font, and loading one can
  // take a tenth of a second or more on a slow machine. The rows stay out of layout (CSS) until the reader has been
  // still for a while some seconds after opening the page; then they are refilled two names at a time, each pair laid
  // out in its own moment. Coming close to a row fills it at once.
  const many = qa(".mq, .langs");
  let lastScroll = 0;
  addEventListener("scroll", () => { lastScroll = performance.now(); }, { passive: true });
  const queue = [];
  const flush = (row) => {
    const job = queue.find((j) => j.row === row);
    if (!job) return;
    job.kids.splice(0).forEach((k) => job.box.appendChild(k));
    queue.splice(queue.indexOf(job), 1);
  };
  // Coming close: a row that is still waiting is shown whole, one that is being refilled gets the rest at once.
  const nearRows = (sec) => many.filter((r) => sec.contains(r)).forEach((row) => { if (row.classList.contains("near")) flush(row); else row.classList.add("near"); });
  const watchRows = () => when(many.map((el) => el.closest("section, footer") || el), "120% 0px 120% 0px", nearRows);
  const warmFonts = () => {
    many.filter((row) => !row.classList.contains("near")).forEach((row) => {
      const box = row.classList.contains("mq") ? q(".mq-track", row) : row;
      const kids = [...box.children];
      kids.forEach((k) => k.remove());
      queue.push({ row, box, kids });
      row.classList.add("near");
    });
    const step = (deadline) => {
      if (!queue.length) return;
      if (performance.now() - lastScroll < 900) { setTimeout(() => idle(step), 900); return; }
      if (deadline.timeRemaining() > 12) {
        const job = queue[0];
        for (let k = 0; k < 2 && job.kids.length; k++) job.box.appendChild(job.kids.shift());
        void job.box.offsetWidth;
        if (!job.kids.length) queue.shift();
      }
      idle(step);
    };
    idle(step);
  };
  measureThemes();
  navTheme();
  root.classList.add("ready");
  requestAnimationFrame(() => setTimeout(() => idle(work), 0));
})();
