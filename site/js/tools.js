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
      if (res.stuck) { el.innerHTML = `<h3>${esc(label)}</h3><p class="warn">${esc(L.stuck)}</p>`; return; }
      const tag = best ? `<span class="tag">${esc(res.interest < other.interest - 1 ? L.cheaper : L.faster)}</span>` : "";
      const order = res.paid.slice().sort((a, b) => a.month - b.month)
        .map((p) => `<li>${esc(names[p.i])} · ${esc(F.monthYear(p.month))}</li>`).join("");
      el.innerHTML = `${tag}<h3>${esc(label)}</h3><div><span class="k">${esc(L.free_in)}</span><div class="v">${esc(F.monthYear(res.months))}</div>` +
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
})();
