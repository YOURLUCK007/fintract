/* ===================== FinTract app logic ===================== */
(() => {
  const D = window.FINTRACT_DATA;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const inr = n => "₹" + Math.round(n).toLocaleString("en-IN");
  const charts = {};

  /* ---------- theme ---------- */
  const applyTheme = t => {
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem("ft-theme", t);
    const icon = t === "dark" ? "🌙" : "☀️";
    ["themeToggleLanding", "themeToggleApp"].forEach(id => { const b = $("#" + id); if (b) b.textContent = icon; });
    Object.values(charts).forEach(c => c && c.update());
  };
  const toggleTheme = () => applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
  applyTheme(localStorage.getItem("ft-theme") || "dark");
  $("#themeToggleLanding").onclick = toggleTheme;
  $("#themeToggleApp").onclick = toggleTheme;

  const cssVar = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  /* ---------- toast ---------- */
  const toast = (msg) => {
    const el = document.createElement("div");
    el.className = "toast"; el.innerHTML = msg;
    $("#toastWrap").appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(30px)"; }, 3200);
    setTimeout(() => el.remove(), 3600);
  };

  /* ---------- landing → app routing ---------- */
  const enterApp = () => { $("#landing").classList.add("hidden"); $("#app").classList.remove("hidden"); window.scrollTo(0, 0); renderApp(); };
  ["enterApp", "enterApp2", "watchDemo"].forEach(id => { const b = $("#" + id); if (b) b.onclick = enterApp; });
  $("#backHome").onclick = () => { $("#app").classList.add("hidden"); $("#landing").classList.remove("hidden"); };

  /* ---------- landing features ---------- */
  const FEATURES = [
    ["🧾", "Smart expense tracking", "Manual or CSV/PDF import. ML + NLP auto-categorize every transaction."],
    ["🧠", "AI spending analysis", "Trends, anomalies, recurring subscriptions, and overspend detection."],
    ["💡", "Saving recommendations", "Realistic actions with estimated monthly savings and reasoning."],
    ["📈", "Savings forecast engine", "Weekly/monthly/yearly projections across 3 scenarios with confidence bands."],
    ["💼", "AI investment advisor", "Allocations tuned to income, risk & goals with growth simulations."],
    ["❤️", "Financial health score", "A 0–100 score across 6 dimensions, with how to improve each."],
    ["🤖", "Predictive ML models", "Expense, savings, cash-flow, anomaly & suitability models."],
    ["💬", "AI chat assistant", "Ask natural questions and get grounded, numeric answers."],
    ["🎯", "Goal planning", "Completion dates & required monthly contributions per goal."],
    ["🔔", "Smart notifications", "Overspending, bills, milestones & investment reminders."],
    ["🔐", "Bank-grade security", "JWT, OAuth, hashing, encryption, rate limiting & audit logs."],
    ["🌍", "Bonus power-ups", "OCR receipts, voice entry, multi-currency, PDF/Excel export."]
  ];
  $("#featureGrid").innerHTML = FEATURES.map(([i, t, d]) =>
    `<div class="feature"><span class="fi">${i}</span><h3>${t}</h3><p>${d}</p></div>`).join("");

  /* ---------- hero sparkline ---------- */
  const drawHeroSpark = () => {
    const ctx = $("#heroSpark"); if (!ctx) return;
    charts.spark = new Chart(ctx, {
      type: "line",
      data: { labels: D.months, datasets: [{ data: [14, 17, 19, 21, 22.5, 24.4], borderColor: cssVar("--accent"), borderWidth: 2, fill: true, backgroundColor: "rgba(24,212,160,.12)", tension: .4, pointRadius: 0 }] },
      options: { plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } }, responsive: true, maintainAspectRatio: false }
    });
  };
  drawHeroSpark();

  /* ===================== APP RENDER ===================== */
  let appRendered = false;
  function renderApp() {
    if (appRendered) return; appRendered = true;
    renderKpis(); renderHealth(); renderInsights(); renderHeatmap();
    renderExpenses(); renderForecast(); renderInvest(); renderGoals(); initChat();
    drawOverviewCharts();
  }

  /* ---------- nav ---------- */
  const titles = { overview: "Overview", expenses: "Expenses", forecast: "Savings Forecast", invest: "Investments", goals: "Goals", assistant: "AI Assistant" };
  $$(".nav-item").forEach(btn => btn.onclick = () => {
    $$(".nav-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const v = btn.dataset.view;
    $$(".view").forEach(s => s.classList.remove("active"));
    $("#view-" + v).classList.add("active");
    $("#viewTitle").textContent = titles[v];
    $("#sidebar").classList.remove("open");
    if (v === "forecast") drawForecastCharts();
    if (v === "invest") drawInvestCharts();
  });
  $("#menuToggle").onclick = () => $("#sidebar").classList.toggle("open");
  $("#notifBtn").onclick = () => {
    toast("🔔 <strong>Bill reminder:</strong> Electricity due in 3 days");
    setTimeout(() => toast("🎉 <strong>Milestone:</strong> Emergency fund 73% funded"), 600);
  };

  /* ---------- KPIs ---------- */
  function renderKpis() {
    $("#kpiRow").innerHTML = D.kpis.map(k =>
      `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta ${k.dir}">${k.delta}</div></div>`).join("");
  }

  /* ---------- health ---------- */
  function renderHealth() {
    $(".ring.big").style.setProperty("--score", D.health.score);
    $$(".ring.mini").forEach(r => r.style.setProperty("--score", r.dataset.score));
    $("#healthBreakdown").innerHTML = D.health.breakdown.map(b =>
      `<li><div class="row"><span>${b.label}</span><strong>${b.pct}</strong></div><div class="bar"><span style="width:${b.pct}%"></span></div></li>`).join("");
  }

  /* ---------- insights ---------- */
  function renderInsights() {
    $("#insightsList").innerHTML = D.insights.map(i =>
      `<li><span class="em">${i.em}</span><span>${i.text}</span></li>`).join("");
  }

  /* ---------- heatmap (26 weeks x intensity) ---------- */
  function renderHeatmap() {
    const cells = 26 * 5;
    let html = "";
    for (let i = 0; i < cells; i++) {
      const intensity = Math.random();
      const op = (.12 + intensity * .88).toFixed(2);
      const c = intensity > .66 ? cssVar("--danger") : intensity > .33 ? cssVar("--primary") : cssVar("--accent");
      html += `<div class="cell" title="₹${Math.round(intensity * 3000)}" style="background:${c};opacity:${op}"></div>`;
    }
    $("#heatmap").innerHTML = html;
  }

  /* ---------- overview charts ---------- */
  function gridColor() { return cssVar("--border"); }
  function tickColor() { return cssVar("--text-dim"); }

  function drawOverviewCharts() {
    charts.incomeSpend = new Chart($("#chartIncomeSpend"), {
      type: "line",
      data: {
        labels: D.months,
        datasets: [
          { label: "Income", data: D.income, borderColor: cssVar("--accent"), backgroundColor: "rgba(24,212,160,.12)", fill: true, tension: .4, pointRadius: 3 },
          { label: "Spending", data: D.spending, borderColor: cssVar("--danger"), backgroundColor: "rgba(255,107,129,.12)", fill: true, tension: .4, pointRadius: 3 }
        ]
      },
      options: baseLineOpts()
    });

    charts.category = new Chart($("#chartCategory"), {
      type: "doughnut",
      data: { labels: D.categories.map(c => c.name), datasets: [{ data: D.categories.map(c => c.value), backgroundColor: D.categories.map(c => c.color), borderWidth: 0 }] },
      options: { plugins: { legend: { position: "bottom", labels: { color: tickColor(), boxWidth: 10, font: { size: 10 } } } }, cutout: "62%", responsive: true, maintainAspectRatio: true }
    });

    charts.trend = new Chart($("#chartTrend"), {
      type: "bar",
      data: { labels: D.months, datasets: [{ label: "Spend", data: D.trend, backgroundColor: cssVar("--primary"), borderRadius: 6 }] },
      options: baseBarOpts()
    });
  }

  function baseLineOpts() {
    return {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { labels: { color: tickColor(), boxWidth: 12 } } },
      scales: {
        x: { grid: { color: gridColor() }, ticks: { color: tickColor() } },
        y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: v => "₹" + (v / 1000) + "k" } }
      }
    };
  }
  function baseBarOpts() {
    const o = baseLineOpts(); o.plugins.legend.display = false; return o;
  }

  /* ===================== EXPENSES ===================== */
  let txns = [...D.transactions];
  let activeFilter = "All";
  const NLP_MAP = [
    [/swiggy|zomato|restaurant|dinner|lunch|grocery|bigbasket|food|cafe|pizza/i, "Food"],
    [/uber|ola|petrol|fuel|flight|train|metro|cab|travel|airport/i, "Travel"],
    [/amazon|myntra|flipkart|apparel|shoe|shopping|mall/i, "Shopping"],
    [/electricity|bill|recharge|water|gas|broadband|rent/i, "Bills"],
    [/pharmacy|apollo|hospital|doctor|medic|health/i, "Healthcare"],
    [/netflix|spotify|prime|movie|game|entertain/i, "Entertainment"],
    [/course|udemy|coursera|book|tuition|school|education/i, "Education"],
    [/sip|stock|mutual|index|invest|etf/i, "Investments"]
  ];
  const nlpCategorize = desc => { for (const [re, c] of NLP_MAP) if (re.test(desc)) return c; return "Others"; };

  function renderExpenses() {
    const cats = ["All", ...new Set(D.categories.map(c => c.name)), "Investments"];
    $("#catFilters").innerHTML = cats.map(c => `<button class="chip ${c === activeFilter ? "active" : ""}" data-cat="${c}">${c}</button>`).join("");
    $$("#catFilters .chip").forEach(b => b.onclick = () => { activeFilter = b.dataset.cat; renderTx(); $$("#catFilters .chip").forEach(x => x.classList.toggle("active", x.dataset.cat === activeFilter)); });
    renderTx();
    $("#anomalyList").innerHTML = D.anomalies.map(a => `<li class="${a.type === "dup" ? "dup" : ""}"><span>${a.type === "dup" ? "🔁" : "⚠️"}</span><span>${a.text}</span></li>`).join("");

    $("#addForm").onsubmit = e => {
      e.preventDefault();
      const desc = $("#exDesc").value.trim();
      const amt = +$("#exAmt").value;
      let cat = $("#exCat").value;
      if (cat === "auto") cat = nlpCategorize(desc);
      txns.unshift({ date: new Date().toISOString().slice(0, 10), desc, cat, amt });
      renderTx();
      toast(`✅ Added <strong>${inr(amt)}</strong> → auto-categorized as <strong>${cat}</strong>`);
      e.target.reset();
      $("#nlpHint").textContent = "";
    };
    $("#exDesc").oninput = e => {
      const v = e.target.value.trim();
      $("#nlpHint").innerHTML = v && $("#exCat").value === "auto" ? `🤖 NLP suggests category: <strong>${nlpCategorize(v)}</strong>` : "";
    };
  }
  function renderTx() {
    const rows = txns.filter(t => activeFilter === "All" || t.cat === activeFilter);
    $("#txBody").innerHTML = rows.map(t =>
      `<tr><td>${t.date}</td><td>${t.desc}</td><td><span class="cat-tag">${t.cat}</span></td><td class="r">${inr(t.amt)}</td></tr>`).join("")
      || `<tr><td colspan="4" class="muted" style="padding:1.5rem;text-align:center">No transactions in this category.</td></tr>`;
  }

  /* ===================== FORECAST ===================== */
  let plan = "balanced";
  function renderForecast() {
    $$("#scenarioTabs .chip").forEach(b => b.onclick = () => {
      plan = b.dataset.plan;
      $$("#scenarioTabs .chip").forEach(x => x.classList.toggle("active", x.dataset.plan === plan));
      renderForecastKpis(); drawForecastCharts();
    });
    renderForecastKpis();
    $("#recList").innerHTML = D.recommendations.map(r =>
      `<li><div class="rec-txt"><strong>${r.title}</strong><span>${r.why}</span></div><div class="rec-amt">${inr(r.save)}</div></li>`).join("");
  }
  function renderForecastKpis() {
    const p = D.forecastPlans[plan];
    $("#forecastKpis").innerHTML = [
      { label: "Weekly savings", value: inr(p.weekly) },
      { label: "Monthly savings", value: inr(p.monthly) },
      { label: "Yearly savings", value: inr(p.yearly) },
      { label: "Plan", value: plan[0].toUpperCase() + plan.slice(1), note: p.kpiNote }
    ].map(k => `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta up">${k.note || "projected"}</div></div>`).join("");
  }
  function drawForecastCharts() {
    const p = D.forecastPlans[plan];
    const labels = ["M1","M2","M3","M4","M5","M6","M7","M8","M9","M10","M11","M12"];
    const upper = p.base.map(v => v * 1.12);
    const lower = p.base.map(v => v * 0.9);
    charts.forecast && charts.forecast.destroy();
    charts.forecast = new Chart($("#chartForecast"), {
      type: "line",
      data: {
        labels,
        datasets: [
          { label: "Upper (confidence)", data: upper, borderColor: "transparent", backgroundColor: "rgba(108,140,255,.10)", fill: "+1", pointRadius: 0, tension: .4 },
          { label: "Projected savings", data: p.base, borderColor: cssVar("--primary"), backgroundColor: "transparent", fill: false, pointRadius: 2, tension: .4, borderWidth: 3 },
          { label: "Lower (confidence)", data: lower, borderColor: "transparent", backgroundColor: "rgba(108,140,255,.10)", fill: "-1", pointRadius: 0, tension: .4 }
        ]
      },
      options: baseLineOpts()
    });

    charts.cashflow && charts.cashflow.destroy();
    charts.cashflow = new Chart($("#chartCashflow"), {
      type: "bar",
      data: { labels: D.cashflow.months, datasets: [
        { label: "Inflow", data: D.cashflow.inflow, backgroundColor: cssVar("--accent"), borderRadius: 5 },
        { label: "Outflow", data: D.cashflow.outflow, backgroundColor: cssVar("--danger"), borderRadius: 5 }
      ] },
      options: baseLineOpts()
    });
  }

  /* ===================== INVEST ===================== */
  let risk = 3;
  const RISK_NAMES = { 1: "Very safe", 2: "Conservative", 3: "Balanced", 4: "Growth", 5: "Aggressive" };
  function renderInvest() {
    $("#riskSlider").oninput = e => { risk = +e.target.value; $("#riskReadout").textContent = RISK_NAMES[risk]; renderAllocGrid(); drawInvestCharts(); };
    renderAllocGrid();
  }
  function renderAllocGrid() {
    const alloc = D.allocations[risk];
    $("#allocGrid").innerHTML = alloc.map(([name, pct], i) => {
      const color = D.allocColors[i % D.allocColors.length];
      const amt = D.investableMonthly * pct / 100;
      return `<div class="alloc-item" style="border-left-color:${color}"><div class="a-name">${name}</div><div class="a-pct">${pct}%</div><div class="a-amt">${inr(amt)}/mo</div></div>`;
    }).join("");
  }
  function drawInvestCharts() {
    const alloc = D.allocations[risk];
    charts.allocation && charts.allocation.destroy();
    charts.allocation = new Chart($("#chartAllocation"), {
      type: "polarArea",
      data: { labels: alloc.map(a => a[0]), datasets: [{ data: alloc.map(a => a[1]), backgroundColor: alloc.map((_, i) => D.allocColors[i % D.allocColors.length]) }] },
      options: { plugins: { legend: { position: "right", labels: { color: tickColor(), boxWidth: 10, font: { size: 10 } } } }, scales: { r: { grid: { color: gridColor() }, ticks: { display: false } } }, responsive: true, maintainAspectRatio: true }
    });

    const g = D.forecastPlans[plan] ? D.forecastPlans[plan].growth : 0.07;
    const annual = D.investableMonthly * 12;
    const years = Array.from({ length: 11 }, (_, i) => "Y" + i);
    const rate = 0.05 + risk * 0.015;
    let acc = 0; const vals = years.map((_, i) => { if (i > 0) acc = (acc + annual) * (1 + rate); return Math.round(acc); });
    charts.growth && charts.growth.destroy();
    charts.growth = new Chart($("#chartGrowth"), {
      type: "line",
      data: { labels: years, datasets: [{ label: `Projected @ ${(rate * 100).toFixed(1)}%/yr`, data: vals, borderColor: cssVar("--primary-2"), backgroundColor: "rgba(138,107,255,.12)", fill: true, tension: .35, pointRadius: 2 }] },
      options: { ...baseLineOpts(), scales: { x: { grid: { color: gridColor() }, ticks: { color: tickColor() } }, y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: v => "₹" + (v / 100000).toFixed(1) + "L" } } } }
    });
  }

  /* ===================== GOALS ===================== */
  let goals = [...D.goals];
  function renderGoals() {
    $("#goalsGrid").innerHTML = goals.map(goalCard).join("");
    $("#goalForm").onsubmit = e => {
      e.preventDefault();
      goals.push({ name: $("#goalName").value, emoji: "🎯", target: +$("#goalTarget").value, saved: +$("#goalSaved").value, monthly: +$("#goalMonthly").value });
      renderGoals(); e.target.reset();
      toast("🎯 Goal added — completion date calculated");
    };
  }
  function goalCard(g) {
    const pct = Math.min(100, Math.round(g.saved / g.target * 100));
    const remaining = Math.max(0, g.target - g.saved);
    const monthsLeft = g.monthly > 0 ? Math.ceil(remaining / g.monthly) : 0;
    const eta = new Date(); eta.setMonth(eta.getMonth() + monthsLeft);
    const etaStr = remaining === 0 ? "Completed 🎉" : eta.toLocaleDateString("en-IN", { month: "short", year: "numeric" });
    return `<div class="goal">
      <div class="g-top"><span class="g-emoji">${g.emoji}</span><h4>${g.name}</h4></div>
      <div class="g-meta"><span>${inr(g.saved)} saved</span><span>${inr(g.target)} goal</span></div>
      <div class="g-bar"><span style="width:${pct}%"></span></div>
      <div class="g-meta"><span>${pct}% funded</span><span>${inr(g.monthly)}/mo</span></div>
      <div class="g-eta">Est. completion: <strong>${etaStr}</strong>${remaining ? ` · ${monthsLeft} mo` : ""}</div>
    </div>`;
  }

  /* ===================== CHAT ===================== */
  function initChat() {
    $("#chatSuggestions").innerHTML = D.chatSuggestions.map(s => `<button class="chip" type="button">${s}</button>`).join("");
    $$("#chatSuggestions .chip").forEach(b => b.onclick = () => { $("#chatText").value = b.textContent; sendChat(); });
    pushMsg("bot", "👋 Hi! I'm your FinTract assistant. Ask me about your spending, savings, or investments — try a suggestion below.");
    $("#chatForm").onsubmit = e => { e.preventDefault(); sendChat(); };
  }
  function pushMsg(who, html) {
    const el = document.createElement("div"); el.className = "msg " + who; el.innerHTML = html;
    $("#chatLog").appendChild(el); $("#chatLog").scrollTop = $("#chatLog").scrollHeight; return el;
  }
  function sendChat() {
    const t = $("#chatText").value.trim(); if (!t) return;
    pushMsg("user", t.replace(/</g, "&lt;")); $("#chatText").value = "";
    const typing = pushMsg("bot", `<span class="typing"><span></span><span></span><span></span></span>`);
    setTimeout(() => { typing.innerHTML = answer(t); $("#chatLog").scrollTop = $("#chatLog").scrollHeight; }, 700);
  }
  function answer(q) {
    const s = q.toLowerCase();
    const topCat = [...D.categories].sort((a, b) => b.value - a.value)[0];
    if (/most|highest|where.*spend|top categ/.test(s))
      return `Your biggest category this month is <strong>${topCat.name}</strong> at <strong>${inr(topCat.value)}</strong> — about ${Math.round(topCat.value / D.categories.reduce((a, c) => a + c.value, 0) * 100)}% of total spend. Food delivery is the main driver.`;
    if (/save.*5000|save ₹5|how.*save/.test(s))
      return `To save <strong>₹5,000</strong> next month, combine: cut food delivery 20% (<strong>₹2,400</strong>), cancel 2 unused subscriptions (<strong>₹1,180</strong>), and cap shopping at ₹6k (<strong>₹2,200</strong>). That's <strong>₹5,780/mo</strong> — comfortably past your target.`;
    if (/afford|can i.*buy|50,?000|50000/.test(s))
      return `A <strong>₹50,000</strong> purchase ≈ 2 months of your current savings (₹24,380/mo). You can afford it without touching your emergency fund if you spread it over ~2 months, or pay now and pause your aggressive SIP for one cycle. ✅ Affordable.`;
    if (/invest|portfolio|allocat|plan based/.test(s))
      return `Based on a <strong>Balanced</strong> risk profile and ₹24,380 investable/month, I'd suggest: <strong>20% emergency fund, 24% index funds, 18% mutual funds, 14% FD, 12% ETFs, 8% gold, 4% bonds</strong>. Projected ~7%/yr. <em>Educational only, not guaranteed advice.</em>`;
    if (/year|forecast|how much.*save.*year/.test(s))
      return `Following the Balanced plan, you'd save about <strong>${inr(D.forecastPlans.balanced.yearly)}</strong> over 12 months. The Aggressive plan reaches <strong>${inr(D.forecastPlans.aggressive.yearly)}</strong> if you adopt every recommendation.`;
    if (/health|score/.test(s))
      return `Your financial health score is <strong>${D.health.score}/100</strong> 💪. Strongest: emergency fund (90). Weakest: budget adherence (68) — tightening your shopping budget would lift it the most.`;
    if (/subscription|recurring/.test(s))
      return `I detected recurring charges including Netflix (₹649), Spotify (₹119), plus 2 unused services flagged 60+ days inactive. Cancelling the unused ones saves <strong>₹1,180/mo</strong>.`;
    return `Great question! Based on your data: savings rate <strong>31%</strong>, monthly savings <strong>₹24,380</strong>, top category <strong>${topCat.name}</strong>. Try asking about saving ₹5,000, affording a purchase, or an investment plan.`;
  }

  /* welcome toast on first app open */
  const origEnter = enterApp;
})();
