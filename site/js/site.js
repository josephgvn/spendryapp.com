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
  // Pictures marked data-near load when the reader is getting close.
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
        setTimeout(() => (q("[aria-current]", langPanel) || q("a", langPanel)).focus({ preventScroll: true }), 250);
      } else {
        langPanel.classList.remove("open");
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
  let playNotes = null, reserveNotes = null;
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
      // Room for every card is kept from the start: cards arriving never push the page below down (and the pinned
      // scenes further down keep the places they were measured at).
      const reserve = () => {
        const ghost = list.cloneNode(false);
        ghost.style.cssText = `position:absolute;visibility:hidden;pointer-events:none;width:${list.clientWidth}px`;
        notes.forEach((n) => ghost.appendChild(make(n)));
        list.after(ghost);
        list.style.minHeight = `${ghost.offsetHeight}px`;
        ghost.remove();
      };
      reserveNotes = () => {   // one of the idle jobs, before the pinned scenes are measured
        reserve();
        let resized;
        addEventListener("resize", () => { clearTimeout(resized); resized = setTimeout(reserve, 250); });
      };
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

  // ---------------------------------------------------------------- the header: a soft shadow once the page has moved
  const nav = q("[data-nav]");
  if (nav) {
    const shade = () => nav.classList.toggle("scrolled", scrollY > 8);
    addEventListener("scroll", shade, { passive: true });
    shade();
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
  if (reserveNotes) later(reserveNotes);
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

  // ---------------------------------------------------------------- the wall of widgets: the tiles come in together
  const wallEl = q(".wall");
  if (wallEl) {
    const tiles = qa(".w", wallEl).filter((w) => getComputedStyle(w).display !== "none");
    when([wallEl], AHEAD, () => G.set(tiles, { y: 40, opacity: 0 }));
    when([wallEl], AT(15), () => G.to(tiles, { y: 0, opacity: 1, duration: 1, ease, stagger: .05 }));
  }

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

  // ---------------------------------------------------------------- finale
  const finalIcon = q(".final-icon");
  if (finalIcon) {
    when([q(".final")], AHEAD, () => G.set(finalIcon, { scale: .8, opacity: 0 }));
    when([q(".final")], AT(30), () => G.fromTo(finalIcon, { scale: .8, opacity: 0 }, { scale: 1, opacity: 1, duration: 1.2, ease }));
  }

  // Jobs that can wait run while the page is idle; then the scroll triggers are measured once.
  const idle = window.requestIdleCallback ? (fn) => requestIdleCallback(fn, { timeout: 400 }) : (fn) => setTimeout(() => fn({ timeRemaining: () => 10, didTimeout: false }), 30);
  const work = (deadline) => {
    do { const job = jobs.shift(); if (job) job(); } while (jobs.length && deadline.timeRemaining() > 12);
    if (jobs.length) { idle(work); return; }
    idle(() => { ST.sort(); ST.refresh(); });
  };
  root.classList.add("ready");
  requestAnimationFrame(() => setTimeout(() => idle(work), 0));
})();
