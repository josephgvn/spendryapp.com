/* Free calculators on spendryapp.com. Everything runs in the browser; nothing is sent anywhere. */
(() => {
  "use strict";
  const F = window.__spendryFormat;
  const simulate = window.__spendrySimulate;
  if (!F) return;
  const d = document;
  const q = (s, el = d) => el.querySelector(s);
  const qa = (s, el = d) => [...el.querySelectorAll(s)];
  const G = window.gsap;
  const motion = d.documentElement.classList.contains("motion");
  const read = (el) => {
    if (!el) return 0;
    const v = parseFloat(String(el.value).replace(/\s/g, "").replace(",", "."));
    return Number.isFinite(v) ? v : 0;
  };
  const moneyD = F.nf({ style: "currency", currency: F.currency, minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const esc = (s) => String(s).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c]));
  const pop = (els) => { if (G && motion) G.fromTo(els, { y: 8, opacity: .3 }, { y: 0, opacity: 1, duration: .5, ease: "expo.out", stagger: .04 }); };

  // ---------------------------------------------------------------- debt payoff: snowball and avalanche side by side
  const payoff = q("#payoff");
  if (payoff && simulate) {
    const data = JSON.parse(payoff.dataset.payoff);
    const L = data.labels;
    const monthly = data.period === "month";
    const list = q(".debt-list", payoff);
    const field = (label, cls, type, value, extra = "") =>
      `<label class="field"><span>${esc(label)}</span><input class="${cls}" type="${type}" value="${esc(value)}" ${extra}></label>`;
    const add = (x) => {
      const row = d.createElement("div");
      row.className = "debt-row";
      row.innerHTML = field(L.name, "f-name", "text", x.name, 'maxlength="40"') +
        field(L.balance, "f-bal", "number", x.bal, 'inputmode="decimal" min="0"') +
        field(L.rate, "f-rate", "number", x.rate, 'inputmode="decimal" min="0" step="0.01"') +
        field(L.minimum, "f-min", "number", x.min, 'inputmode="decimal" min="0"') +
        `<button type="button" class="x" aria-label="${esc(L.remove)}"><svg class="ic" aria-hidden="true"><use href="#i-close"/></svg></button>`;
      q(".x", row).addEventListener("click", () => {
        if (G && motion) G.to(row, { height: 0, opacity: 0, paddingBlock: 0, duration: .35, ease: "power2.in", onComplete: () => { row.remove(); run(); } });
        else { row.remove(); run(); }
      });
      list.appendChild(row);
      if (G && motion && x.fresh) G.from(row, { y: 20, opacity: 0, duration: .5, ease: "expo.out" });
    };
    data.debts.forEach(add);
    q("[data-add]", payoff).addEventListener("click", () => {
      add({ name: `${L.debt} ${list.children.length + 1}`, bal: "", rate: "", min: "", fresh: true });
      q(".debt-row:last-child .f-bal", list).focus();
    });
    payoff.addEventListener("input", run);
    const card = (el, res, label, best, other, names) => {
      el.classList.toggle("best", best);
      if (res.stuck) { el.innerHTML = `<h2>${esc(label)}</h2><p class="warn">${esc(L.stuck)}</p>`; return; }
      const tag = best ? `<span class="tag">${esc(res.interest < other.interest - 1 ? L.cheaper : L.faster)}</span>` : "";
      const order = res.paid.slice().sort((a, b) => a.month - b.month)
        .map((p) => `<li>${esc(names[p.i])} · ${esc(F.monthYear(p.month))}</li>`).join("");
      el.innerHTML = `${tag}<h2>${esc(label)}</h2><div><span class="k">${esc(L.free_in)}</span><div class="v">${esc(F.monthYear(res.months))}</div>` +
        `<span class="d">${esc(F.duration(res.months))}</span></div><div><span class="k">${esc(L.interest)}</span><div class="v">${esc(F.money(res.interest))}</div></div>` +
        `<div><span class="k">${esc(L.order)}</span><ol>${order}</ol></div>`;
      pop(qa(".v", el));
    };
    function run() {
      const debts = [], names = [];
      qa(".debt-row", list).forEach((row) => {
        const bal = read(q(".f-bal", row)), rate = read(q(".f-rate", row)), min = read(q(".f-min", row));
        if (bal > 0) {
          names.push(q(".f-name", row).value.trim() || L.debt);
          debts.push({ bal, r: (monthly ? rate : rate / 12) / 100, min: Math.max(0, min) });
        }
      });
      const outS = q('[data-res="snowball"]', payoff), outA = q('[data-res="avalanche"]', payoff), same = q(".same", payoff);
      if (!debts.length) { outS.innerHTML = outA.innerHTML = ""; return; }
      const extra = Math.max(0, read(q("[data-extra]", payoff)));
      const s = simulate(debts, extra, "snowball"), a = simulate(debts, extra, "avalanche");
      const aBetter = !a.stuck && (a.interest < s.interest - 1 || (Math.abs(a.interest - s.interest) <= 1 && a.months < s.months));
      const sBetter = !s.stuck && !aBetter && (s.months < a.months || s.interest < a.interest - 1);
      card(outS, s, L.snowball, sBetter, a, names);
      card(outA, a, L.avalanche, aBetter, s, names);
      same.hidden = aBetter || sBetter || s.stuck;
      same.textContent = L.same;
    }
    run();
  }

  // ---------------------------------------------------------------- 50/30/20
  const split = q("#split");
  if (split) {
    const input = q("[data-income]", split);
    const outs = { n: [q('[data-split-out="n"]', split), .5], w: [q('[data-split-out="w"]', split), .3], s: [q('[data-split-out="s"]', split), .2] };
    const shown = { n: 0, w: 0, s: 0 };
    const run = () => {
      const v = Math.max(0, read(input));
      Object.entries(outs).forEach(([k, [el, p]]) => {
        const to = v * p;
        if (G && motion) {
          const o = { v: shown[k] };
          G.to(o, { v: to, duration: .6, ease: "expo.out", onUpdate: () => { el.textContent = F.money(o.v); } });
        } else el.textContent = F.money(to);
        shown[k] = to;
      });
    };
    input.addEventListener("input", run);
    run();
    if (G && motion && window.ScrollTrigger) {
      G.from(qa(".bar i", split), { scaleX: 0, duration: 1.4, ease: "expo.out", stagger: .12, scrollTrigger: { trigger: split, start: "top 80%", once: true } });
      G.from(qa(".donut .d", split), { strokeDasharray: "0 301.6", duration: 1.6, ease: "expo.out", stagger: .15, scrollTrigger: { trigger: split, start: "top 80%", once: true } });
    }
  }

  // ---------------------------------------------------------------- loan installment (KKDF and BSMV are added to each month's interest)
  const loanBox = q("#loan");
  if (loanBox) {
    const labels = JSON.parse(loanBox.dataset.labels);
    const f = (k) => q(`[data-f="${k}"]`, loanBox);
    const o = (k) => q(`[data-o="${k}"]`, loanBox);
    const taxes = { ihtiyac: [15, 15], tasit: [15, 15], konut: [0, 0] };
    const btns = qa("[data-loan-type]", loanBox), thumb = q(".seg-thumb", loanBox);
    let all = false;
    const loan = (P, pct, n, kkdf, bsmv) => {
      const r = pct / 100, re = r * (1 + kkdf / 100 + bsmv / 100);
      const pay = re === 0 ? P / n : (P * re) / (1 - Math.pow(1 + re, -n));
      let bal = P, ti = 0, tt = 0;
      const rows = [];
      for (let i = 1; i <= n; i++) {
        const intr = bal * r, k = (intr * kkdf) / 100, b = (intr * bsmv) / 100;
        const prin = i === n ? bal : pay - intr - k - b;
        bal = Math.max(0, bal - prin);
        ti += intr; tt += k + b;
        rows.push([i, prin + intr + k + b, prin, intr, k, b, bal]);
      }
      return { pay, total: P + ti + tt, interest: ti, tax: tt, rows };
    };
    const run = () => {
      const P = read(f("amount")), rate = read(f("rate")), n = Math.round(read(f("term")));
      if (P <= 0 || n <= 0 || n > 480 || rate < 0) return;
      const res = loan(P, rate, n, read(f("kkdf")), read(f("bsmv")));
      o("payment").textContent = moneyD.format(res.pay);
      o("total").textContent = F.money(res.total);
      o("interest").textContent = F.money(res.interest);
      o("tax").textContent = F.money(res.tax);
      const rows = all ? res.rows : res.rows.slice(0, 12);
      q("[data-rows]", loanBox).innerHTML = rows.map((r) => `<tr><td>${r[0]}</td>${r.slice(1).map((v) => `<td>${moneyD.format(v)}</td>`).join("")}</tr>`).join("");
      const more = q("[data-more]", loanBox);
      more.hidden = res.rows.length <= 12;
      more.textContent = all ? labels.show_less : labels.show_all;
    };
    btns.forEach((b, i) => b.addEventListener("click", () => {
      btns.forEach((x) => x.setAttribute("aria-checked", String(x === b)));
      thumb.style.transform = `translateX(${(d.documentElement.dir === "rtl" ? -1 : 1) * i * 100}%)`;
      const t = taxes[b.dataset.loanType];
      f("kkdf").value = t[0]; f("bsmv").value = t[1];
      run();
      pop([o("payment")]);
    }));
    q("[data-more]", loanBox).addEventListener("click", () => { all = !all; run(); if (window.ScrollTrigger) window.ScrollTrigger.refresh(); });
    loanBox.addEventListener("input", run);
    run();
  }

  // ---------------------------------------------------------------- shared by the newer calculators
  const box = (sel) => {
    const el = q(sel);
    return el && { el, C: JSON.parse(el.dataset.c || "{}"), f: (k) => q(`[data-f="${k}"]`, el), o: (k) => q(`[data-o="${k}"]`, el) };
  };
  const roll = (el, to, fmt) => { // a number rolls to its new value
    if (!el) return;
    const from = +el.dataset.v || 0;
    el.dataset.v = to;
    if (el._tw) el._tw.kill();
    if (G && motion) {
      const t = { v: from };
      el._tw = G.to(t, { v: to, duration: .6, ease: "expo.out", onUpdate: () => { el.textContent = fmt(t.v); } });
    } else el.textContent = fmt(to);
  };
  const money2 = (v) => moneyD.format(v);
  const removeRow = (row, done) => {
    if (G && motion) G.to(row, { height: 0, opacity: 0, paddingBlock: 0, duration: .35, ease: "power2.in", onComplete: () => { row.remove(); done(); } });
    else { row.remove(); done(); }
  };

  // ---------------------------------------------------------------- credit card: your payment against minimum payments only
  const cc = box("#ccpay");
  if (cc) {
    const { el, C, f, o } = cc;
    const L = C.labels;
    const payoffRun = (B, r, payFor) => {
      let bal = B, m = 0, paid = 0;
      const pts = [B];
      while (bal > 0.005) {
        const i = bal * r, pay = Math.min(payFor(bal), bal + i);
        if (pay <= i + 1e-9 || m >= 1200) return { stuck: true, pts };
        bal = Math.max(0, bal + i - pay); paid += pay; m++; pts.push(bal);
      }
      return { months: m, interest: paid - B, pts };
    };
    const show = (k, res, label) => {
      const m = q(`[data-res="${k}"]`, el);
      if (res.stuck) { m.innerHTML = `<h2>${esc(label)}</h2><p class="warn">${esc(L.never)}</p>`; return; }
      m.innerHTML = `<h2>${esc(label)}</h2><div><span class="k">${esc(L.date)}</span><div class="v">${esc(F.monthYear(res.months))}</div>` +
        `<span class="d">${esc(F.duration(res.months))}</span></div><div><span class="k">${esc(L.interest)}</span><div class="v">${esc(F.money(res.interest))}</div></div>`;
    };
    const line = (pts, n, top) => pts.map((v, i) => `${i ? "L" : "M"}${(i / n * 600).toFixed(1)} ${(210 - (v / top) * 200).toFixed(1)}`).join("");
    const paths = [q(".p-fix", el), q(".p-min", el)];
    let drawn = false;
    const update = () => {
      const B = read(f("balance")), rate = Math.max(0, read(f("rate"))), P = read(f("payment")), pct = Math.max(0, read(f("min"))) / 100;
      if (B <= 0) return;
      const r = (C.period === "month" ? rate : rate / 12) / 100;
      const a = payoffRun(B, r, () => P), b = payoffRun(B, r, (bal) => Math.max(bal * pct, C.floor));
      show("fixed", a, L.fixed);
      show("min", b, L.minimum);
      const saved = q(".saved", el);
      saved.hidden = a.stuck || b.stuck || b.interest - a.interest < 1;
      if (!saved.hidden) roll(o("saved"), b.interest - a.interest, F.money);
      const n = Math.max(a.pts.length, b.pts.length, 2) - 1;
      paths[0].setAttribute("d", line(a.pts, n, B));
      paths[1].setAttribute("d", line(b.pts, n, B));
      o("start").textContent = F.monthYear(0);
      o("end").textContent = F.monthYear(n);
      if (!drawn && G && motion) G.fromTo(paths, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1.6, ease: "expo.out", stagger: .2 });
      drawn = true;
      pop(qa(".v", el));
    };
    el.addEventListener("input", update);
    update();
  }

  // ---------------------------------------------------------------- loan: payment, interest and every month
  const lc = box("#loancalc");
  if (lc) {
    const { el, C, f, o } = lc;
    let all = false;
    const update = () => {
      const P = read(f("amount")), rate = read(f("rate")), n = Math.round(read(f("term")));
      if (P <= 0 || n <= 0 || n > 600 || rate < 0) return;
      const r = rate / 1200, pay = r ? (P * r) / (1 - Math.pow(1 + r, -n)) : P / n;
      let bal = P, ti = 0;
      const rows = [];
      for (let i = 1; i <= n; i++) {
        const it = bal * r, pr = i === n ? bal : pay - it;
        bal = Math.max(0, bal - pr); ti += it;
        rows.push([i, pr, it, bal]);
      }
      roll(o("payment"), pay, money2);
      o("principal").textContent = F.money(P);
      o("interest").textContent = F.money(ti);
      o("total").textContent = F.money(P + ti);
      q(".share i", el).style.width = `${(P / (P + ti)) * 100}%`;
      q("[data-rows]", el).innerHTML = (all ? rows : rows.slice(0, 12))
        .map((x) => `<tr><td>${x[0]}</td>${x.slice(1).map((v) => `<td>${money2(v)}</td>`).join("")}</tr>`).join("");
      const more = q("[data-more]", el);
      more.hidden = rows.length <= 12;
      more.textContent = all ? C.show_less : C.show_all;
    };
    q("[data-more]", el).addEventListener("click", () => { all = !all; update(); if (window.ScrollTrigger) window.ScrollTrigger.refresh(); });
    el.addEventListener("input", update);
    update();
  }

  // ---------------------------------------------------------------- savings goal: how much each month
  const sv = box("#saving");
  if (sv) {
    const { el, f, o } = sv;
    const update = () => {
      const goal = read(f("goal")), have = Math.max(0, read(f("have"))), n = Math.round(read(f("months")));
      const r = Math.max(0, read(f("rate"))) / 1200;
      if (goal <= 0 || n <= 0 || n > 600) return;
      const g = Math.pow(1 + r, n), need = goal - have * g, done = need <= 0;
      q(".reached", el).hidden = !done;
      q(".sv-res", el).hidden = done;
      if (done) return;
      const pmt = r ? (need * r) / (g - 1) : need / n, put = pmt * n, earned = Math.max(0, goal - have - put);
      roll(o("monthly"), pmt, money2);
      o("weekly").textContent = money2((pmt * 12) / 52);
      o("have").textContent = F.money(have);
      o("total_in").textContent = F.money(put);
      o("earned").textContent = F.money(earned);
      [have, put, earned].forEach((v, i) => { qa(".stack i", el)[i].style.width = `${(v / goal) * 100}%`; });
    };
    el.addEventListener("input", update);
    update();
  }

  // ---------------------------------------------------------------- subscriptions: the monthly, yearly and five-year total
  const sb = box("#subs");
  if (sb) {
    const { el, C, o } = sb;
    const L = C.labels, list = q(".sub-list", el), bars = q(".sub-bars", el);
    const per = { w: 52 / 12, m: 1, y: 1 / 12 }, cycles = { w: L.weekly, m: L.monthly, y: L.yearly };
    let update = () => {};
    const add = (x) => {
      const row = d.createElement("div");
      row.className = "sub-row";
      row.innerHTML = `<label class="field"><span>${esc(L.name)}</span><input class="f-name" type="text" maxlength="40" value="${esc(x.name)}"></label>` +
        `<label class="field"><span>${esc(L.price)}</span><input class="f-price" type="number" inputmode="decimal" min="0" step="0.01" value="${esc(x.price)}"></label>` +
        `<label class="field"><span>${esc(L.cycle)}</span><select class="f-cycle">${Object.keys(cycles).map((k) =>
          `<option value="${k}"${k === x.cycle ? " selected" : ""}>${esc(cycles[k])}</option>`).join("")}</select></label>` +
        `<button type="button" class="x" aria-label="${esc(L.remove)}"><svg class="ic" aria-hidden="true"><use href="#i-close"/></svg></button>`;
      q(".x", row).addEventListener("click", () => removeRow(row, update));
      list.appendChild(row);
      if (G && motion && x.fresh) G.from(row, { y: 20, opacity: 0, duration: .5, ease: "expo.out" });
    };
    C.items.forEach(add);
    q("[data-add]", el).addEventListener("click", () => {
      add({ name: "", price: "", cycle: "m", fresh: true });
      q(".sub-row:last-child .f-name", list).focus();
    });
    update = () => {
      const items = qa(".sub-row", list).map((row) => ({
        name: q(".f-name", row).value.trim() || L.name,
        m: Math.max(0, read(q(".f-price", row))) * per[q(".f-cycle", row).value],
      })).filter((x) => x.m > 0);
      const month = items.reduce((s, x) => s + x.m, 0), top = Math.max(1e-9, ...items.map((x) => x.m));
      roll(o("year"), month * 12, F.money);
      o("month").textContent = money2(month);
      o("five").textContent = F.money(month * 60);
      bars.innerHTML = items.sort((a, b) => b.m - a.m).map((x) =>
        `<li><span>${esc(x.name)}</span><b>${esc(F.money(x.m * 12))}</b><i style="width:${((x.m / top) * 100).toFixed(1)}%"></i></li>`).join("");
    };
    el.addEventListener("input", update);
    el.addEventListener("change", update);
    update();
  }
})();
