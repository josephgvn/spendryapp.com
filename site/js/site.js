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

  // ---------------------------------------------------------------- hero and story
  /* One pinned scene. The words of the first screen leave before anything moves into their place; the side phones
     slide in behind the middle one (never across the words); each step's words come in only once the phone has
     settled, and each step's card grows out of the phone toward the words only as far as the room between them. */
  const stage = q(".stage");
  if (stage) {
    const pin = q(".stage-pin", stage);
    const phonesEl = q(".phones", stage), pc = q(".pw-c", stage), pl = q(".pw-l", stage), pr = q(".pw-r", stage);
    const copy = q(".hero-copy", stage), capsBox = q(".caps", stage), caps = qa(".cap", stage);
    const scr = qa(".scr", stage), lifts = qa(".lift", stage), slots = qa(".slot", stage), toast = q(".toast", stage);
    G.set(pl, { xPercent: -56, yPercent: 4, scale: .84, force3D: false });
    G.set(pr, { xPercent: 56, yPercent: 4, scale: .84, force3D: false });
    G.set(lifts, { autoAlpha: 0 });
    G.set(scr.slice(1), { xPercent: 100 * dir });
    stage.classList.add("set");

    // Now and then one of the app's own notifications slides down inside the phone's screen, the way iOS shows one.
    const N = window.__spendryNotes;
    if (N && N.notes.length && toast) {
      const order = [2, 3, 1, 4];
      let k = 0;
      const show = () => {
        if (scrollY > innerHeight * .1 || d.hidden) return;
        toast.innerHTML = "";
        const cardEl = N.make(N.notes[order[k++ % order.length]]);
        toast.appendChild(cardEl);
        const away = () => -(toast.offsetTop + cardEl.offsetHeight + 30);
        G.set(toast, { visibility: "visible" });
        G.timeline({ onComplete: () => G.set(toast, { visibility: "hidden" }) })
          .fromTo(cardEl, { y: away }, { y: 0, duration: .75, ease: "back.out(1.1)" })
          .to(cardEl, { y: away, duration: .45, ease: "power3.in" }, "+=3.6");
      };
      G.delayedCall(2.6, function loop() { show(); G.delayedCall(7.5, loop); });
    }

    later(() => {
      const mm = G.matchMedia();
      mm.add({ wide: "(min-width: 900px)", narrow: "(max-width: 899px)" }, (ctx) => {
        const { wide } = ctx.conditions;
        const tl = G.timeline({
          defaults: { ease: "power2.inOut" },
          scrollTrigger: { trigger: stage, pin, start: "top top", end: () => `+=${Math.round(innerHeight * (wide ? 3.2 : 3))}`, scrub: .8, invalidateOnRefresh: true, anticipatePin: 1 },
        });
        // A notification on screen goes back up as soon as the page moves (its height is not known ahead: the width is a safe bound).
        if (toast) tl.to(toast, { y: () => -(toast.offsetTop + toast.offsetWidth * .6), duration: .3, ease: "power2.in" }, 0);
        tl.to(copy, { y: -60, opacity: 0, duration: wide ? .7 : .4, ease: "power1.in" }, 0)
          .to([pl, pr], { xPercent: 0, yPercent: 2, scale: .72, opacity: 0, duration: 1, force3D: false }, 0);
        let capsAt = 1;
        if (!wide) {
          // The phone comes up under the header and shrinks to fit above the steps' words, after the words above have gone.
          const fit = () => {
            const top = (nav ? nav.offsetHeight : 56) + 12;
            const below = capsBox.getBoundingClientRect().top - pin.getBoundingClientRect().top - 16;
            return { y: top - (phonesEl.offsetTop + pc.offsetTop), k: clamp((below - top) / (pc.offsetHeight || 1), .3, .92) };
          };
          tl.to(pc, { y: () => fit().y, scale: () => fit().k, transformOrigin: "50% 0%", duration: .9, force3D: false }, .4);
          capsAt = 1.35;
        }
        const capIn = (i, at) => tl.fromTo(caps[i], { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: .8, ease: "power3.out", immediateRender: false }, at);
        const capOut = (i, at) => tl.to(caps[i], { opacity: 0, y: -40, duration: .6, ease: "power2.in" }, at);
        // How far a card may move toward the words: never past the gap between the phone and their column.
        const grow = wide ? 1.2 : 1.06;
        const reach = (i) => {
          if (!wide) return 0;
          const r = slots[i].getBoundingClientRect(), c = capsBox.getBoundingClientRect(), spill = (grow - 1) * r.width / 2;
          const room = rtl ? (c.left - 28) - (r.right + spill) : (r.left - spill) - (c.right + 28);
          return -dir * clamp(room, 0, r.width * .26);
        };
        const pop = (i, at) => {
          tl.set(lifts[i], { autoAlpha: 1 }, at)
            .fromTo(slots[i], { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: false }, at + .15)
            .to(slots[i], { opacity: 0, duration: .4 }, at + 1.75)
            .fromTo(lifts[i], { scale: 1, x: 0, yPercent: 0, boxShadow: "0 0 0 0 rgba(0,0,0,0)" },
              { scale: grow, x: () => reach(i), yPercent: wide ? -4 : 0, boxShadow: "0 50px 80px -30px rgba(0,0,0,.8)", duration: .9, ease: "power3.out", immediateRender: false, force3D: false }, at)
            .to(lifts[i], { scale: 1, x: 0, yPercent: 0, boxShadow: "0 0 0 0 rgba(0,0,0,0)", duration: .7, force3D: false }, at + 1.5)
            .set(lifts[i], { autoAlpha: 0 }, at + 2.25);
        };
        // Moving to the next step: the screens slide inside the phone, like swiping between tabs.
        const push = (a, b, at) => {
          tl.to(scr[a], { xPercent: -100 * dir, duration: 1, ease: "power3.inOut" }, at)
            .fromTo(scr[b], { xPercent: 100 * dir }, { xPercent: 0, duration: 1, ease: "power3.inOut", immediateRender: false }, at);
        };
        capIn(0, capsAt);
        pop(0, capsAt + .7);
        capOut(0, 4.1); push(0, 1, 4.1); capIn(1, 4.7);
        pop(1, 5.3);
        capOut(1, 7.7); push(1, 2, 7.7); capIn(2, 8.3);
        pop(2, 8.9);
        tl.to({}, { duration: .6 }, 11.1);
        return () => { G.set(caps, { clearProps: "all" }); };
      });
    });
  }

  // ---------------------------------------------------------------- statement: words light up with the scroll
  const wordsEl = q(".words");
  if (wordsEl) later(() => {
    const ws = qa(".w", wordsEl);
    let lit = -1;
    ST.create({
      trigger: wordsEl, start: "top 82%", end: "bottom 50%", scrub: true,
      onUpdate: (st) => {
        const n = Math.round(st.progress * ws.length);
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
    let dx = 0, dy = 0, s0 = 2, sf = 1, y0 = 0, yf = 0;
    // Centred by GSAP itself (xPercent and yPercent), so measuring never loses the centring. The close-up starts
    // below the title and is never enlarged past the picture's own pixels; the whole wall ends up in the room below
    // the header.
    const measure = () => {
      G.set(wall, { x: 0, y: 0, scale: 1, xPercent: -50, yPercent: -50, force3D: false });
      const a = wall.getBoundingClientRect(), b = focus.getBoundingClientRect(), c = box.getBoundingClientRect(), head = copyW.getBoundingClientRect();
      const fx = b.left + b.width / 2, fy = b.top + b.height * opts.focusY;
      dx = (a.left + a.width / 2) - fx;
      dy = (a.top + a.height / 2) - fy;
      const top = nav ? nav.offsetHeight : 0;
      sf = Math.min(1, (c.height - top - opts.margin) / a.height, (innerWidth - 32) / a.width);
      yf = top / 2;
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
    // The title is gone before the others arrive, so nothing ever shows through the words.
    tl.fromTo(wall, { scale: () => s0, x: () => dx * s0, y: () => dy * s0 + y0 }, { scale: () => sf, x: 0, y: () => yf, duration: 1, ease: "power2.inOut", force3D: false }, 0)
      .to(copyW, { opacity: 0, y: -40, duration: .15, ease: "power1.in" }, .02)
      .fromTo(others, { opacity: 0, scale: .8 }, { opacity: 1, scale: 1, duration: .5, stagger: { each: .03, from: "random" }, ease: "power2.out", force3D: false }, .2)
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
    if (url.pathname === location.pathname && url.hash.length > 1) buildAll();
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

  // "See how it works" goes to the first step of the story, not past it.
  qa("[data-story]").forEach((a) => a.addEventListener("click", (ev) => {
    const s = stage && ST.getAll().find((t) => t.pin && t.trigger === stage);
    if (!s) return;
    ev.preventDefault();
    scrollTo({ top: s.start + (s.end - s.start) * .18, behavior: "smooth" });
  }));

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

  // Arriving at /#widgets and the like: pinned sections add height above, so go there again once they are set up.
  const goHash = () => {
    if (!location.hash || location.hash.length < 2) return;
    let t = null;
    try { t = q(location.hash); } catch (err) { return; }
    if (t) t.scrollIntoView();
  };
  // Jobs that can wait run while the page is idle. Triggers are made top to bottom, then measured once: every pinned
  // section's extra height is counted for the ones below it.
  const idle = window.requestIdleCallback ? (fn) => requestIdleCallback(fn, { timeout: 400 }) : (fn) => setTimeout(() => fn({ timeRemaining: () => 10, didTimeout: false }), 30);
  const work = (deadline) => {
    do { const job = jobs.shift(); if (job) job(); } while (jobs.length && deadline.timeRemaining() > 12);
    if (jobs.length) { idle(work); return; }
    idle(() => {
      if (location.hash.length > 1) while (scenes.length) scenes.shift().build();   // a deep link needs every pin above it
      ST.sort();
      ST.refresh();
      scenes.forEach((sc) => when([sc.el], "150% 0px 150% 0px", () => buildTo(sc)));
      setTimeout(() => { const more = () => { if (!scenes.length) return; buildTo(scenes[0]); idle(more); }; idle(more); }, 8000);
      if (d.readyState === "complete") goHash(); else addEventListener("load", goHash, { once: true });
    });
  };
  root.classList.add("ready");
  requestAnimationFrame(() => setTimeout(() => idle(work), 0));
})();
