/* Spendry web tools: loan installment, debt payoff (snowball and avalanche), 50/30/20 budget.
   Everything runs in the browser; nothing is sent anywhere. */
(function () {
  'use strict';
  var lang = (document.documentElement.lang || 'tr').slice(0, 2);
  var L = {
    tr: {
      locale: 'tr-TR', currency: 'TRY', months: '%d ay', monthsYears: '%y yıl %m ay',
      snowball: 'Kar topu', avalanche: 'Çığ', debt: 'Borç', stuck: 'Bu ödemelerle borç bitmiyor: aylık ödeme faizi karşılamıyor. Ek ödemeyi artırın.',
      order: 'Kapanma sırası', freeBy: 'Borçsuz', interest: 'Toplam faiz', faster: 'Daha hızlı', cheaper: 'Daha az faiz', same: 'İki yöntem aynı sonucu veriyor',
      showAll: 'Tüm ayları göster', showLess: 'İlk 12 ayı göster', name: 'Ad', remove: 'Borcu sil'
    },
    en: {
      locale: 'en-US', currency: 'USD', months: '%d months', monthsYears: '%y yr %m mo',
      snowball: 'Snowball', avalanche: 'Avalanche', debt: 'Debt', stuck: 'These payments never clear the debt: they do not cover the interest. Raise the extra payment.',
      order: 'Payoff order', freeBy: 'Debt-free', interest: 'Total interest', faster: 'Faster', cheaper: 'Less interest', same: 'Both methods give the same result',
      showAll: 'Show every month', showLess: 'Show the first 12 months', name: 'Name', remove: 'Remove debt'
    }
  }[lang === 'en' ? 'en' : 'tr'];

  var money = function (v, digits) {
    return new Intl.NumberFormat(L.locale, {style: 'currency', currency: L.currency, maximumFractionDigits: digits || 0, minimumFractionDigits: digits || 0}).format(v || 0);
  };
  var read = function (el) {
    if (!el) return 0;
    var v = parseFloat(String(el.value).replace(/\s/g, '').replace(',', '.'));
    return isFinite(v) ? v : 0;
  };
  var $ = function (id) { return document.getElementById(id); };
  var duration = function (m) {
    if (m < 12) return L.months.replace('%d', m);
    var y = Math.floor(m / 12), r = m % 12;
    return r ? L.monthsYears.replace('%y', y).replace('%m', r) : (lang === 'en' ? y + (y === 1 ? ' year' : ' years') : y + ' yıl');
  };
  var monthName = function (offset) {
    var d = new Date(); d.setDate(1); d.setMonth(d.getMonth() + offset);
    return new Intl.DateTimeFormat(L.locale, {month: 'long', year: 'numeric'}).format(d);
  };

  /* ---------- Loan installment (Turkish banks: KKDF and BSMV are charged on each month's interest) ---------- */
  function loan(principal, monthlyPct, n, kkdfPct, bsmvPct) {
    var r = monthlyPct / 100, tax = 1 + kkdfPct / 100 + bsmvPct / 100, re = r * tax;
    var pay = re === 0 ? principal / n : principal * re / (1 - Math.pow(1 + re, -n));
    var bal = principal, rows = [], totInt = 0, totKkdf = 0, totBsmv = 0;
    for (var i = 1; i <= n; i++) {
      var intr = bal * r, kkdf = intr * kkdfPct / 100, bsmv = intr * bsmvPct / 100;
      var prin = i === n ? bal : pay - intr - kkdf - bsmv;
      bal = Math.max(0, bal - prin);
      totInt += intr; totKkdf += kkdf; totBsmv += bsmv;
      rows.push([i, prin + intr + kkdf + bsmv, prin, intr, kkdf, bsmv, bal]);
    }
    return {pay: pay, total: principal + totInt + totKkdf + totBsmv, interest: totInt, tax: totKkdf + totBsmv, rows: rows};
  }

  function setupLoan() {
    var form = $('loan-form'); if (!form) return;
    var taxes = {ihtiyac: [15, 15], tasit: [15, 15], konut: [0, 0]};
    var showAll = false;
    form.querySelectorAll('[data-loan-type]').forEach(function (b) {
      b.addEventListener('click', function () {
        form.querySelectorAll('[data-loan-type]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        var t = taxes[b.dataset.loanType]; $('loan-kkdf').value = t[0]; $('loan-bsmv').value = t[1];
        run();
      });
    });
    var toggle = $('loan-more');
    if (toggle) toggle.addEventListener('click', function () { showAll = !showAll; run(); });
    form.addEventListener('input', run);
    function run() {
      var P = read($('loan-amount')), rate = read($('loan-rate')), n = Math.round(read($('loan-term')));
      if (P <= 0 || n <= 0 || n > 480 || rate < 0) return;
      var res = loan(P, rate, n, read($('loan-kkdf')), read($('loan-bsmv')));
      $('out-payment').textContent = money(res.pay, 2);
      $('out-total').textContent = money(res.total);
      $('out-interest').textContent = money(res.interest);
      $('out-tax').textContent = money(res.tax);
      var body = $('loan-rows'), html = '';
      var rows = showAll ? res.rows : res.rows.slice(0, 12);
      rows.forEach(function (r) {
        html += '<tr><td>' + r[0] + '</td><td>' + money(r[1], 2) + '</td><td>' + money(r[2], 2) + '</td><td>' + money(r[3], 2) +
          '</td><td>' + money(r[4], 2) + '</td><td>' + money(r[5], 2) + '</td><td>' + money(r[6], 2) + '</td></tr>';
      });
      body.innerHTML = html;
      if (toggle) { toggle.hidden = res.rows.length <= 12; toggle.textContent = showAll ? L.showLess : L.showAll; }
    }
    run();
  }

  /* ---------- Debt payoff: snowball (smallest balance first) and avalanche (highest rate first) ---------- */
  function simulate(debts, extra, method) {
    var ds = debts.map(function (d, i) { return {id: i, name: d.name, bal: d.bal, rate: d.rate, min: d.min, paid: 0}; })
      .filter(function (d) { return d.bal > 0; });
    var order = ds.slice().sort(method === 'snowball'
      ? function (a, b) { return a.bal - b.bal || b.rate - a.rate; }
      : function (a, b) { return b.rate - a.rate || a.bal - b.bal; });
    var budget = ds.reduce(function (s, d) { return s + d.min; }, 0) + extra;
    var month = 0, interest = 0, closed = [];
    while (ds.some(function (d) { return d.bal > 0.005; }) && month < 600) {
      month++;
      ds.forEach(function (d) { if (d.bal > 0) { var i = d.bal * d.rate; d.bal += i; interest += i; } });
      var pool = budget;
      ds.forEach(function (d) { if (d.bal > 0) { var p = Math.min(d.min, d.bal, pool); d.bal -= p; pool -= p; } });
      order.forEach(function (d) { if (d.bal > 0 && pool > 0) { var p = Math.min(pool, d.bal); d.bal -= p; pool -= p; } });
      ds.forEach(function (d) { if (d.bal <= 0.005 && !d.paid) { d.bal = 0; d.paid = month; closed.push(d); } });
    }
    return {months: month, interest: interest, closed: closed, stuck: month >= 600};
  }

  function setupPayoff() {
    var box = $('payoff'); if (!box) return;
    var list = $('debt-list'), tpl = $('debt-template');
    var yearly = box.dataset.rate === 'yearly';
    function add(d) {
      var node = tpl.content.firstElementChild.cloneNode(true);
      node.querySelector('[data-f=name]').value = d.name; node.querySelector('[data-f=bal]').value = d.bal;
      node.querySelector('[data-f=rate]').value = d.rate; node.querySelector('[data-f=min]').value = d.min;
      node.querySelector('.x').addEventListener('click', function () { node.remove(); run(); });
      list.appendChild(node);
    }
    JSON.parse(box.dataset.sample).forEach(add);
    $('debt-add').addEventListener('click', function () { add({name: L.debt + ' ' + (list.children.length + 1), bal: '', rate: '', min: ''}); });
    box.addEventListener('input', run);
    function card(el, res, label, other, best) {
      el.classList.toggle('best', best);
      var tag = best ? '<span class="tag">' + (res.interest < other.interest - 1 ? L.cheaper : L.faster) + '</span>' : '';
      if (res.stuck) { el.innerHTML = '<h3>' + label + '</h3><p class="warn">' + L.stuck + '</p>'; return; }
      var items = res.closed.map(function (d) { return '<li>' + d.name.replace(/[<>&]/g, '') + ' · ' + monthName(d.paid) + '</li>'; }).join('');
      el.innerHTML = tag + '<h3>' + label + '</h3>' +
        '<p><span class="muted small">' + L.freeBy + '</span><br><b class="num" style="font-size:22px">' + monthName(res.months) + '</b> <span class="muted small">(' + duration(res.months) + ')</span></p>' +
        '<p><span class="muted small">' + L.interest + '</span><br><b class="num" style="font-size:22px">' + money(res.interest) + '</b></p>' +
        '<p class="muted small">' + L.order + '</p><ol>' + items + '</ol>';
    }
    function run() {
      var debts = [];
      list.querySelectorAll('.debt').forEach(function (row) {
        var bal = read(row.querySelector('[data-f=bal]')), rate = read(row.querySelector('[data-f=rate]')), min = read(row.querySelector('[data-f=min]'));
        var name = row.querySelector('[data-f=name]').value.trim() || L.debt;
        if (bal > 0) debts.push({name: name, bal: bal, rate: (yearly ? rate / 12 : rate) / 100, min: Math.max(0, min)});
      });
      if (!debts.length) return;
      var extra = Math.max(0, read($('debt-extra')));
      var s = simulate(debts, extra, 'snowball'), a = simulate(debts, extra, 'avalanche');
      var aBetter = !a.stuck && (a.interest < s.interest - 1 || (Math.abs(a.interest - s.interest) <= 1 && a.months < s.months));
      var sBetter = !s.stuck && !aBetter && (s.months < a.months || s.interest < a.interest - 1);
      card($('res-snowball'), s, L.snowball, a, sBetter);
      card($('res-avalanche'), a, L.avalanche, s, aBetter);
      $('payoff-same').hidden = aBetter || sBetter || s.stuck;
      $('payoff-same').textContent = L.same;
    }
    run();
  }

  /* ---------- 50/30/20 ---------- */
  function setupSplit() {
    var inp = $('split-income'); if (!inp) return;
    function run() {
      var v = read(inp);
      $('split-needs').textContent = money(v * 0.5);
      $('split-wants').textContent = money(v * 0.3);
      $('split-save').textContent = money(v * 0.2);
    }
    inp.addEventListener('input', run); run();
  }

  setupLoan(); setupPayoff(); setupSplit();
})();
