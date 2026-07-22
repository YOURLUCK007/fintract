/* ===================== FinTract app (API-driven) ===================== */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
  const charts = {};
  const state = { user: null, plan: "balanced", risk: 3, filter: "All", ws: null, overview: null };

  /* ---------- theme ---------- */
  const applyTheme = (t) => {
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem("ft-theme", t);
    const icon = t === "dark" ? "🌙" : "☀️";
    ["themeToggleLanding", "themeToggleApp"].forEach((id) => { const b = $("#" + id); if (b) b.textContent = icon; });
    Object.values(charts).forEach((c) => c && c.update());
  };
  const toggleTheme = () => applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
  applyTheme(localStorage.getItem("ft-theme") || "dark");
  $("#themeToggleLanding").onclick = toggleTheme;
  $("#themeToggleApp").onclick = toggleTheme;
  const cssVar = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  /* ---------- toast ---------- */
  const toast = (msg) => {
    const el = document.createElement("div");
    el.className = "toast"; el.innerHTML = msg;
    $("#toastWrap").appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(30px)"; }, 3400);
    setTimeout(() => el.remove(), 3800);
  };

  /* ---------- landing features + hero spark ---------- */
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
    ["💰", "AI budget generator", "Adaptive 50/30/20 budgets built from your real spending."],
    ["🧮", "Savings & what-if sims", "Model spending cuts, raises, purchases & inflation instantly."],
    ["📊", "Net-worth tracker", "Assets vs liabilities with a 5-year growth projection."],
    ["🔁", "Subscription detector", "Finds recurring payments & their monthly/yearly cost."],
    ["📄", "PDF & Excel reports", "One-click exportable financial reports you can share."],
    ["🔐", "Bank-grade security", "JWT, bcrypt hashing, rate limiting & audit logs."],
  ];
  $("#featureGrid").innerHTML = FEATURES.map(([i, t, d]) => `<div class="feature"><span class="fi">${i}</span><h3>${t}</h3><p>${d}</p></div>`).join("");

  new Chart($("#heroSpark"), {
    type: "line",
    data: { labels: [1, 2, 3, 4, 5, 6], datasets: [{ data: [14, 17, 16, 21, 22.5, 24.4], borderColor: cssVar("--accent"), borderWidth: 2, fill: true, backgroundColor: "rgba(24,212,160,.12)", tension: .4, pointRadius: 0 }] },
    options: { plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } }, responsive: true, maintainAspectRatio: false },
  });

  /* ===================== AUTH ===================== */
  let signupMode = false;
  const authOverlay = $("#authOverlay");
  const showAuth = () => { authOverlay.classList.remove("hidden"); };
  const hideAuth = () => { authOverlay.classList.add("hidden"); $("#authError").classList.add("hidden"); };
  const setAuthMode = (signup) => {
    signupMode = signup;
    $$(".signup-only").forEach((e) => e.classList.toggle("hidden", !signup));
    $("#authTitle").textContent = signup ? "Create your account" : "Welcome back";
    $("#authSub").textContent = signup ? "Start with a clean slate — add your income, expenses & goals." : "Log in to your dashboard.";
    $("#authSubmit").textContent = signup ? "Create account" : "Log in";
    $("#authSwitchText").textContent = signup ? "Already have an account?" : "New to FinTract?";
    $("#authSwitch").textContent = signup ? "Log in" : "Create an account";
    $("#authPassword").autocomplete = signup ? "new-password" : "current-password";
  };
  $("#authSwitch").onclick = (e) => { e.preventDefault(); setAuthMode(!signupMode); };
  $("#authClose").onclick = hideAuth;

  const authError = (msg) => { const el = $("#authError"); el.textContent = msg; el.classList.remove("hidden"); };

  $("#authForm").onsubmit = async (e) => {
      e.preventDefault();
      const errEl = $("#authError");
      errEl.classList.add("hidden");
      errEl.classList.remove("auth-success");
      $("#authSubmit").textContent = "Please wait…";
      try {
        let user;
        if (signupMode) {
          const result = await API.register({
            email: $("#authEmail").value.trim(),
            password: $("#authPassword").value,
            full_name: $("#authName").value.trim(),
            monthly_income: +$("#authIncome").value || 95000,
            risk_tolerance: +$("#authRisk").value || 3,
          });
          user = result;
        } else {
          user = await API.login($("#authEmail").value.trim(), $("#authPassword").value);
        }
        await launchApp(user);
      } catch (err) {
        const msg = err.message || "Something went wrong";
        authError(msg);
        $("#authSubmit").textContent = signupMode ? "Create account" : "Log in";
      }
    };

  $("#authDemo").onclick = async () => {
    $("#authError").classList.add("hidden");
    try {
      let user;
      try {
        user = await API.login("demo@fintract.app", "demo1234");
      } catch (loginErr) {
        // Account doesn't exist yet — create it.
        const result = await API.register({ email: "demo@fintract.app", password: "demo1234", full_name: "Demo User", monthly_income: 95000, risk_tolerance: 3 });
        user = result;
      }
      if (!user) { authError("Could not load demo account. Please refresh and try again."); return; }
      await launchApp(user);
    } catch (err) { authError(err.message); }
  };

  /* ---------- landing → auth/app ---------- */
  const onLaunchClick = () => { if (API.isAuthed()) bootFromToken(); else { setAuthMode(false); showAuth(); } };
  ["enterApp", "enterApp2", "watchDemo"].forEach((id) => { const b = $("#" + id); if (b) b.onclick = onLaunchClick; });

  async function bootFromToken() {
    try { const user = await API.me(); await launchApp(user); }
    catch { API.clearToken(); setAuthMode(false); showAuth(); }
  }

  $("#backHome").onclick = () => {
    $("#app").classList.add("hidden");
    $("#landing").classList.remove("hidden");
    if (state.ws) { state.ws.close(); state.ws = null; }
  };

  /* ===================== APP LAUNCH ===================== */
  async function launchApp(user) {
    state.user = user;
    state.risk = user.risk_tolerance || 3;
    hideAuth();
    $("#landing").classList.add("hidden");
    $("#app").classList.remove("hidden");
    window.scrollTo(0, 0);

    // personalize sidebar
    const initials = (user.full_name || user.email).split(/[\s@.]/).filter(Boolean).slice(0, 2).map((s) => s[0].toUpperCase()).join("");
    $(".user-chip .avatar").textContent = initials || "U";
    $(".user-chip strong").textContent = user.full_name || user.email.split("@")[0];
    $(".user-chip span").textContent = user.email;

    connectRealtime();
    await Promise.all([loadOverview(), loadExpenses(), loadGoals()]);
    initChat();
    setupNav();
  }

  /* ---------- realtime ---------- */
  function connectRealtime() {
    if (state.ws) return;
    state.ws = API.connectWs((msg) => {
      if (msg.type === "notification") {
        toast(`🔔 <strong>${msg.title}</strong><br>${msg.body}`);
        $("#notifBtn").classList.add("has-new");
      } else if (msg.type === "expense_added") {
        loadOverview();
      }
    });
  }

  /* ---------- nav ---------- */
  const titles = { overview: "Overview", expenses: "Expenses", forecast: "Savings Forecast", invest: "Investments", budget: "Budget", simulator: "Simulator", networth: "Net Worth", subscriptions: "Subscriptions", goals: "Goals", planner: "Planner", lab: "Portfolio Lab", twin: "Financial Twin", achievements: "Achievements", reports: "Reports", assistant: "AI Assistant" };
  let navSetup = false;
  function setupNav() {
    if (navSetup) return; navSetup = true;
    $$(".nav-item").forEach((btn) => btn.onclick = async () => {
      $$(".nav-item").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const v = btn.dataset.view;
      $$(".view").forEach((s) => s.classList.remove("active"));
      $("#view-" + v).classList.add("active");
      $("#viewTitle").textContent = titles[v];
      $("#sidebar").classList.remove("open");
      if (v === "forecast") await loadForecast();
      if (v === "invest") await loadInvest();
      if (v === "budget") await loadBudget();
      if (v === "simulator") await loadSimulator();
      if (v === "networth") await loadNetworth();
      if (v === "subscriptions") await loadSubscriptions();
      if (v === "reports") await loadReports();
      if (v === "planner") await loadPlanner();
      if (v === "lab") await loadLab();
      if (v === "twin") loadTwin();
      if (v === "achievements") await loadAchievements();
    });
    $("#menuToggle").onclick = () => $("#sidebar").classList.toggle("open");
    $("#notifBtn").onclick = async () => {
      const notifs = await API.notifications();
      if (!notifs.length) return toast("🔔 No notifications yet");
      notifs.slice(0, 3).forEach((n, i) => setTimeout(() => toast(`🔔 <strong>${n.title}</strong><br>${n.body}`), i * 500));
    };
  }

  /* ===================== OVERVIEW ===================== */
  async function loadOverview() {
    const d = await API.overview();
    state.overview = d;

    $("#kpiRow").innerHTML = d.kpis.map((k) => `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta ${k.dir}">${k.delta}</div></div>`).join("");

    // health
    const score = d.health.score;
    $("#healthScore").textContent = score;
    $(".ring.big").style.setProperty("--score", score);
    $$(".ring.mini").forEach((r) => r.style.setProperty("--score", r.dataset.score));
    $("#healthBreakdown").innerHTML = d.health.breakdown.map((b) => `<li><div class="row"><span>${b.label}</span><strong>${b.pct}</strong></div><div class="bar"><span style="width:${b.pct}%"></span></div></li>`).join("");

    $("#insightsList").innerHTML = d.insights.map((i) => `<li><span class="em">${i.em}</span><span>${i.text}</span></li>`).join("");
    renderHeatmap(d.heatmap);
    drawOverviewCharts(d);
  }

  function renderHeatmap(vals) {
    $("#heatmap").innerHTML = vals.map((v) => {
      const op = (0.12 + v * 0.88).toFixed(2);
      const c = v > 0.66 ? cssVar("--danger") : v > 0.33 ? cssVar("--primary") : cssVar("--accent");
      return `<div class="cell" title="intensity ${(v * 100).toFixed(0)}%" style="background:${c};opacity:${op}"></div>`;
    }).join("");
  }

  const gridColor = () => cssVar("--border");
  const tickColor = () => cssVar("--text-dim");
  function baseLineOpts() {
    return {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { labels: { color: tickColor(), boxWidth: 12 } } },
      scales: {
        x: { grid: { color: gridColor() }, ticks: { color: tickColor() } },
        y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: (v) => "₹" + (v / 1000) + "k" } },
      },
    };
  }
  const destroy = (k) => { if (charts[k]) { charts[k].destroy(); charts[k] = null; } };

  function drawOverviewCharts(d) {
    destroy("incomeSpend");
    charts.incomeSpend = new Chart($("#chartIncomeSpend"), {
      type: "line",
      data: { labels: d.months, datasets: [
        { label: "Income", data: d.income, borderColor: cssVar("--accent"), backgroundColor: "rgba(24,212,160,.12)", fill: true, tension: .4, pointRadius: 3 },
        { label: "Spending", data: d.spending, borderColor: cssVar("--danger"), backgroundColor: "rgba(255,107,129,.12)", fill: true, tension: .4, pointRadius: 3 },
      ] },
      options: baseLineOpts(),
    });

    destroy("category");
    charts.category = new Chart($("#chartCategory"), {
      type: "doughnut",
      data: { labels: d.categories.map((c) => c.name), datasets: [{ data: d.categories.map((c) => c.value), backgroundColor: d.categories.map((c) => c.color), borderWidth: 0 }] },
      options: { plugins: { legend: { position: "bottom", labels: { color: tickColor(), boxWidth: 10, font: { size: 10 } } } }, cutout: "62%", responsive: true, maintainAspectRatio: true },
    });

    destroy("trend");
    charts.trend = new Chart($("#chartTrend"), {
      type: "bar",
      data: { labels: d.months, datasets: [{ label: "Spend", data: d.trend, backgroundColor: cssVar("--primary"), borderRadius: 6 }] },
      options: { ...baseLineOpts(), plugins: { legend: { display: false } } },
    });
  }

  /* ===================== EXPENSES ===================== */
  async function loadExpenses() {
    await renderFilters();
    await renderTx();
    await renderAnomalies();
    setupExpenseForm();
  }

  async function renderFilters() {
    const cats = ["All", "Food", "Travel", "Shopping", "Bills", "Healthcare", "Entertainment", "Education", "Investments", "Others"];
    $("#catFilters").innerHTML = cats.map((c) => `<button class="chip ${c === state.filter ? "active" : ""}" data-cat="${c}">${c}</button>`).join("");
    $$("#catFilters .chip").forEach((b) => b.onclick = async () => {
      state.filter = b.dataset.cat;
      $$("#catFilters .chip").forEach((x) => x.classList.toggle("active", x.dataset.cat === state.filter));
      await renderTx();
    });
  }

  async function renderTx() {
    const rows = await API.expenses(state.filter);
    $("#txBody").innerHTML = rows.length ? rows.map((t) => {
      const flags = [t.is_anomaly ? "⚠️" : "", t.is_duplicate ? "🔁" : ""].join(" ");
      return `<tr><td>${t.spent_on}</td><td>${t.description} ${flags}</td><td><span class="cat-tag">${t.category}</span></td><td class="r">${inr(t.amount)}</td><td class="r"><button class="tx-del" data-id="${t.id}" title="Delete">🗑️</button></td></tr>`;
    }).join("") : `<tr><td colspan="5" class="empty">No transactions in this category.</td></tr>`;
    $$("#txBody .tx-del").forEach((b) => b.onclick = async () => {
      await API.deleteExpense(+b.dataset.id);
      await Promise.all([renderTx(), renderAnomalies(), loadOverview()]);
      toast("🗑️ Transaction deleted");
    });
  }

  async function renderAnomalies() {
    const { anomalies } = await API.anomalies();
    $("#anomalyList").innerHTML = anomalies.length
      ? anomalies.map((a) => `<li class="${a.type === "dup" ? "dup" : ""}"><span>${a.type === "dup" ? "🔁" : "⚠️"}</span><span>${a.text}</span></li>`).join("")
      : `<li class="empty" style="border:none;background:none">No anomalies detected — your spending looks consistent. ✅</li>`;
  }

  let expenseFormReady = false;
  function setupExpenseForm() {
    if (expenseFormReady) return; expenseFormReady = true;
    $("#addForm").onsubmit = async (e) => {
      e.preventDefault();
      const description = $("#exDesc").value.trim();
      const amount = +$("#exAmt").value;
      const catSel = $("#exCat").value;
      try {
        const created = await API.addExpense({ description, amount, category: catSel === "auto" ? null : catSel });
        toast(`✅ Added <strong>${inr(amount)}</strong> → <strong>${created.category}</strong>`);
        e.target.reset(); $("#nlpHint").textContent = "";
        await Promise.all([renderTx(), renderAnomalies(), loadOverview()]);
      } catch (err) { toast(`⚠️ ${err.message}`); }
    };

    let nlpTimer;
    $("#exDesc").oninput = (e) => {
      clearTimeout(nlpTimer);
      const v = e.target.value.trim();
      if (!v || $("#exCat").value !== "auto") { $("#nlpHint").textContent = ""; return; }
      nlpTimer = setTimeout(async () => {
        try { const r = await API.categorize(v); $("#nlpHint").innerHTML = `🤖 ML predicts: <strong>${r.category}</strong> (${(r.confidence * 100).toFixed(0)}% conf.)`; }
        catch {}
      }, 350);
    };

    $("#csvInput").onchange = async (e) => {
      const file = e.target.files[0]; if (!file) return;
      try {
        const created = await API.importCsv(file);
        toast(`📎 Imported <strong>${created.length}</strong> transactions`);
        await Promise.all([renderTx(), renderAnomalies(), loadOverview()]);
      } catch (err) { toast(`⚠️ Import failed: ${err.message}`); }
      e.target.value = "";
    };

    setupVoiceEntry();
    setupReceiptOcr();
  }

  /* ---------- voice expense entry (Web Speech API) ---------- */
  function setupVoiceEntry() {
    const btn = $("#voiceBtn");
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { btn.onclick = () => toast("⚠️ Voice input needs Chrome/Edge"); return; }
    btn.onclick = () => {
      const rec = new SR();
      rec.lang = "en-IN"; rec.interimResults = false;
      btn.textContent = "🎤 Listening…";
      $("#smartHint").textContent = 'Say something like "450 rupees swiggy dinner"';
      rec.onresult = (ev) => {
        const text = ev.results[0][0].transcript;
        const m = text.match(/(\d[\d,]*(?:\.\d+)?)/);
        if (m) $("#exAmt").value = m[1].replace(/,/g, "");
        const desc = text.replace(/(\d[\d,]*(?:\.\d+)?)/, "").replace(/rupees?|rs\.?|₹/gi, "").trim();
        if (desc) { $("#exDesc").value = desc; $("#exDesc").dispatchEvent(new Event("input")); }
        $("#smartHint").textContent = `🎤 Heard: “${text}” — review & click Add`;
      };
      rec.onerror = (e) => { $("#smartHint").textContent = `⚠️ Voice error: ${e.error}`; };
      rec.onend = () => { btn.textContent = "🎤 Voice entry"; };
      rec.start();
    };
  }

  /* ---------- OCR receipt scanning (Tesseract.js, lazy-loaded) ---------- */
  let tesseractLoading = null;
  function loadTesseract() {
    if (window.Tesseract) return Promise.resolve();
    if (!tesseractLoading) tesseractLoading = new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js";
      s.onload = res; s.onerror = () => rej(new Error("Could not load OCR engine"));
      document.head.appendChild(s);
    });
    return tesseractLoading;
  }
  function setupReceiptOcr() {
    $("#receiptInput").onchange = async (e) => {
      const file = e.target.files[0]; if (!file) return;
      try {
        $("#smartHint").textContent = "📷 Reading receipt… (first scan downloads the OCR engine)";
        await loadTesseract();
        const { data } = await Tesseract.recognize(file, "eng");
        const text = data.text || "";
        // Amount: prefer a line with total/amount, else the largest number found.
        let amount = null;
        const totalLine = text.split("\n").find((l) => /total|amount|grand/i.test(l) && /\d/.test(l));
        const nums = (totalLine || text).match(/\d[\d,]*(?:\.\d{1,2})?/g) || [];
        const parsed = nums.map((n) => parseFloat(n.replace(/,/g, ""))).filter((n) => n > 0 && n < 10000000);
        if (parsed.length) amount = totalLine ? parsed[parsed.length - 1] : Math.max(...parsed);
        const firstLine = text.split("\n").map((l) => l.trim()).find((l) => l.length > 2 && !/^\d/.test(l));
        if (amount) $("#exAmt").value = amount;
        if (firstLine) { $("#exDesc").value = firstLine.slice(0, 60); $("#exDesc").dispatchEvent(new Event("input")); }
        $("#smartHint").textContent = amount
          ? `📷 Found ${inr(amount)}${firstLine ? ` at “${firstLine.slice(0, 30)}”` : ""} — review & click Add`
          : "⚠️ Couldn't find an amount on that receipt — enter it manually.";
      } catch (err) { $("#smartHint").textContent = `⚠️ OCR failed: ${err.message}`; }
      e.target.value = "";
    };
  }

  /* ===================== FORECAST ===================== */
  let forecastNavReady = false;
  async function loadForecast() {
    if (!forecastNavReady) {
      forecastNavReady = true;
      $$("#scenarioTabs .chip").forEach((b) => b.onclick = async () => {
        state.plan = b.dataset.plan;
        $$("#scenarioTabs .chip").forEach((x) => x.classList.toggle("active", x.dataset.plan === state.plan));
        await drawForecast();
      });
    }
    $$("#scenarioTabs .chip").forEach((x) => x.classList.toggle("active", x.dataset.plan === state.plan));
    await drawForecast();
    const { recommendations } = await API.recommendations();
    $("#recList").innerHTML = recommendations.map((r) => `<li><div class="rec-txt"><strong>${r.title}</strong><span>${r.why}</span></div><div class="rec-amt">${inr(r.save)}</div></li>`).join("");
  }

  async function drawForecast() {
    const p = await API.savings(state.plan);
    $("#forecastKpis").innerHTML = [
      { label: "Weekly savings", value: inr(p.weekly), note: "projected" },
      { label: "Monthly savings", value: inr(p.monthly), note: "projected" },
      { label: "Yearly savings", value: inr(p.yearly), note: "12-month" },
      { label: "Plan", value: state.plan[0].toUpperCase() + state.plan.slice(1), note: `${(p.growth * 100).toFixed(0)}% growth assumption` },
    ].map((k) => `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta up">${k.note}</div></div>`).join("");

    destroy("forecast");
    charts.forecast = new Chart($("#chartForecast"), {
      type: "line",
      data: { labels: p.labels, datasets: [
        { label: "Upper", data: p.upper, borderColor: "transparent", backgroundColor: "rgba(108,140,255,.10)", fill: "+1", pointRadius: 0, tension: .4 },
        { label: "Projected savings", data: p.projection, borderColor: cssVar("--primary"), fill: false, pointRadius: 2, tension: .4, borderWidth: 3 },
        { label: "Lower", data: p.lower, borderColor: "transparent", backgroundColor: "rgba(108,140,255,.10)", fill: "-1", pointRadius: 0, tension: .4 },
      ] },
      options: baseLineOpts(),
    });

    const cf = await API.cashflow();
    destroy("cashflow");
    charts.cashflow = new Chart($("#chartCashflow"), {
      type: "bar",
      data: { labels: cf.labels, datasets: [
        { label: "Inflow", data: cf.inflow, backgroundColor: cssVar("--accent"), borderRadius: 5 },
        { label: "Outflow", data: cf.outflow, backgroundColor: cssVar("--danger"), borderRadius: 5 },
      ] },
      options: baseLineOpts(),
    });
  }

  /* ===================== INVEST ===================== */
  const RISK_NAMES = { 1: "Very safe", 2: "Conservative", 3: "Balanced", 4: "Growth", 5: "Aggressive" };
  let investNavReady = false;
  async function loadInvest() {
    if (!investNavReady) {
      investNavReady = true;
      $("#riskSlider").value = state.risk;
      $("#riskSlider").oninput = async (e) => {
        state.risk = +e.target.value;
        $("#riskReadout").textContent = RISK_NAMES[state.risk];
        await drawInvest();
      };
    }
    $("#riskSlider").value = state.risk;
    $("#riskReadout").textContent = RISK_NAMES[state.risk];
    await drawInvest();
  }

  async function drawInvest() {
    const d = await API.invest(state.risk);
    $("#allocGrid").innerHTML = d.allocation.map((a, i) => {
      const color = ["#6c8cff", "#8a6bff", "#18d4a0", "#ffb23e", "#ff6b81", "#46c2ff", "#c98bff"][i % 7];
      return `<div class="alloc-item" style="border-left-color:${color}"><div class="a-name">${a.name}</div><div class="a-pct">${a.percent}%</div><div class="a-amt">${inr(a.monthly)}/mo</div></div>`;
    }).join("");

    const colors = d.allocation.map((_, i) => ["#6c8cff", "#8a6bff", "#18d4a0", "#ffb23e", "#ff6b81", "#46c2ff", "#c98bff"][i % 7]);
    destroy("allocation");
    charts.allocation = new Chart($("#chartAllocation"), {
      type: "polarArea",
      data: { labels: d.allocation.map((a) => a.name), datasets: [{ data: d.allocation.map((a) => a.percent), backgroundColor: colors }] },
      options: { plugins: { legend: { position: "right", labels: { color: tickColor(), boxWidth: 10, font: { size: 10 } } } }, scales: { r: { grid: { color: gridColor() }, ticks: { display: false } } }, responsive: true, maintainAspectRatio: true },
    });

    destroy("growth");
    charts.growth = new Chart($("#chartGrowth"), {
      type: "line",
      data: { labels: d.growth.labels, datasets: [{ label: `Projected @ ${d.growth.rate}%/yr`, data: d.growth.values, borderColor: cssVar("--primary-2"), backgroundColor: "rgba(138,107,255,.12)", fill: true, tension: .35, pointRadius: 2 }] },
      options: { ...baseLineOpts(), scales: { x: { grid: { color: gridColor() }, ticks: { color: tickColor() } }, y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: (v) => "₹" + (v / 100000).toFixed(1) + "L" } } } },
    });
  }

  /* ===================== GOALS ===================== */
  async function loadGoals() {
    await renderGoals();
    if (!$("#goalForm").dataset.ready) {
      $("#goalForm").dataset.ready = "1";
      $("#goalForm").onsubmit = async (e) => {
        e.preventDefault();
        try {
          await API.addGoal({
            name: $("#goalName").value.trim(),
            target_amount: +$("#goalTarget").value,
            saved_amount: +$("#goalSaved").value || 0,
            monthly_contribution: +$("#goalMonthly").value,
          });
          e.target.reset();
          await renderGoals();
          toast("🎯 Goal added — completion date computed");
        } catch (err) { toast(`⚠️ ${err.message}`); }
      };
    }
  }

  async function renderGoals() {
    const goals = await API.goals();
    $("#goalsGrid").innerHTML = goals.length ? goals.map(goalCard).join("") : `<div class="empty">No goals yet — add one above.</div>`;
    $$("#goalsGrid .g-del").forEach((b) => b.onclick = async () => {
      await API.deleteGoal(+b.dataset.id);
      await renderGoals();
      toast("🗑️ Goal removed");
    });
  }

  function goalCard(g) {
    return `<div class="goal">
      <button class="g-del" data-id="${g.id}" title="Delete">🗑️</button>
      <div class="g-top"><span class="g-emoji">${g.emoji}</span><h4>${g.name}</h4></div>
      <div class="g-meta"><span>${inr(g.saved_amount)} saved</span><span>${inr(g.target_amount)} goal</span></div>
      <div class="g-bar"><span style="width:${g.percent}%"></span></div>
      <div class="g-meta"><span>${g.percent}% funded</span><span>${inr(g.monthly_contribution)}/mo</span></div>
      <div class="g-eta">Est. completion: <strong>${g.eta}</strong>${g.months_left ? ` · ${g.months_left} mo` : ""}</div>
    </div>`;
  }

  /* ===================== BUDGET ===================== */
  async function loadBudget() {
    const b = await API.budget();
    $("#budgetKpis").innerHTML = [
      { label: "Monthly income", value: inr(b.monthly_income), note: "profile" },
      { label: "Current spend", value: inr(b.current_spend), note: `${b.months_analyzed} mo avg` },
      { label: "Recommended spend", value: inr(b.recommended_spend), note: "AI plan" },
      { label: "Projected savings", value: inr(b.projected_savings), note: "if followed" },
    ].map((k) => `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta up">${k.note}</div></div>`).join("");

    $("#budgetBody").innerHTML = b.categories.map((c) => {
      const cls = c.delta < 0 ? "down" : (c.delta > 0 ? "up" : "");
      const sign = c.delta > 0 ? "+" : "";
      return `<tr><td>${c.category}</td><td><span class="cat-tag">${c.bucket}</span></td><td class="r">${inr(c.current)}</td><td class="r">${inr(c.recommended)}</td><td class="r"><span class="k-delta ${cls}">${sign}${inr(c.delta)}</span></td></tr>`;
    }).join("");

    destroy("budgetSplit");
    charts.budgetSplit = new Chart($("#chartBudgetSplit"), {
      type: "bar",
      data: {
        labels: ["Needs", "Wants", "Savings"],
        datasets: [
          { label: "Target", data: [b.split.needs.target, b.split.wants.target, b.split.savings.target], backgroundColor: cssVar("--accent"), borderRadius: 5 },
          { label: "Current", data: [b.split.needs.current, b.split.wants.current, b.split.savings.projected], backgroundColor: cssVar("--primary"), borderRadius: 5 },
        ],
      },
      options: baseLineOpts(),
    });

    destroy("budgetBars");
    charts.budgetBars = new Chart($("#chartBudgetBars"), {
      type: "bar",
      data: {
        labels: b.categories.map((c) => c.category),
        datasets: [
          { label: "Current", data: b.categories.map((c) => c.current), backgroundColor: cssVar("--danger"), borderRadius: 4 },
          { label: "Recommended", data: b.categories.map((c) => c.recommended), backgroundColor: cssVar("--accent"), borderRadius: 4 },
        ],
      },
      options: baseLineOpts(),
    });
  }

  /* ===================== SIMULATOR ===================== */
  let simReady = false;
  async function loadSimulator() {
    if (!simReady) {
      simReady = true;
      $$(".sim-tabs .chip").forEach((b) => b.onclick = () => {
        $$(".sim-tabs .chip").forEach((x) => x.classList.toggle("active", x === b));
        const which = b.dataset.sim;
        $("#sim-savings").classList.toggle("hidden", which !== "savings");
        $("#sim-whatif").classList.toggle("hidden", which !== "whatif");
      });
      $("#simExtra").oninput = () => runSavingsSim();
      buildWhatIf();
    }
    // Build category sliders from current spend (overview categories).
    const d = state.overview || (await API.overview());
    const cats = (d.categories || []).slice(0, 6);
    $("#simSliders").innerHTML = cats.map((c) => `
      <div class="sim-row">
        <label>${c.name} <span class="muted">${inr(c.value)}</span></label>
        <input type="range" class="sim-slider" data-cat="${c.name}" min="0" max="50" value="0" />
        <span class="sim-pct" data-for="${c.name}">0%</span>
      </div>`).join("");
    $$(".sim-slider").forEach((s) => s.oninput = () => {
      $(`.sim-pct[data-for="${s.dataset.cat}"]`).textContent = s.value + "%";
      runSavingsSim();
    });
    await runSavingsSim();
  }

  async function runSavingsSim() {
    const adjustments = {};
    $$(".sim-slider").forEach((s) => { if (+s.value > 0) adjustments[s.dataset.cat] = +s.value; });
    const extra = +$("#simExtra").value || 0;
    const r = await API.simulateSavings({ adjustments, extra_investment: extra });
    $("#simResult").innerHTML = `
      <div class="sim-stat"><span>Base savings</span><strong>${inr(r.base_monthly_savings)}/mo</strong></div>
      <div class="sim-stat"><span>New savings</span><strong>${inr(r.new_monthly_savings)}/mo</strong></div>
      <div class="sim-stat hi"><span>Monthly gain</span><strong>+${inr(r.monthly_gain)}</strong></div>
      <div class="sim-stat"><span>Yearly gain</span><strong>+${inr(r.annual_gain)}</strong></div>`;
    destroy("simProjection");
    charts.simProjection = new Chart($("#chartSimProjection"), {
      type: "line",
      data: { labels: r.projection_5yr.map((p) => "Yr " + p.year), datasets: [{ label: "Balance @8%", data: r.projection_5yr.map((p) => p.balance), borderColor: cssVar("--primary"), backgroundColor: "rgba(108,140,255,.12)", fill: true, tension: .35, pointRadius: 3 }] },
      options: { ...baseLineOpts(), scales: { x: { grid: { color: gridColor() }, ticks: { color: tickColor() } }, y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: (v) => "₹" + (v / 100000).toFixed(1) + "L" } } } },
    });
  }

  const WHATIF = [
    { scenario: "extra_savings", label: "💸 Save ₹10,000 more/month", params: { amount: 10000 } },
    { scenario: "purchase", label: "🛒 Can I afford a ₹1,20,000 laptop?", params: { amount: 120000 } },
    { scenario: "salary_change", label: "📈 Salary increases 20%", params: { percent: 20 } },
    { scenario: "loan_prepay", label: "🏦 Prepay a ₹3,00,000 loan", params: { balance: 300000, rate: 10, emi: 10000 } },
    { scenario: "inflation", label: "🔥 Inflation rises to 6%/yr", params: { rate: 6 } },
  ];
  function buildWhatIf() {
    $("#whatifButtons").innerHTML = WHATIF.map((w, i) => `<button class="chip whatif-btn" data-i="${i}">${w.label}</button>`).join("");
    $$(".whatif-btn").forEach((b) => b.onclick = async () => {
      const w = WHATIF[+b.dataset.i];
      const r = await API.whatIf(w.scenario, w.params);
      $("#whatifResultCard").style.display = "block";
      $("#whatifTitle").textContent = r.headline || "Result";
      const rows = [];
      if (r.monthly_savings != null) rows.push(["Monthly savings", inr(r.monthly_savings)]);
      if (r.annual_savings != null) rows.push(["Annual savings", inr(r.annual_savings)]);
      if (r.new_income != null) rows.push(["New income", inr(r.new_income) + "/mo"]);
      if (r.months_to_afford != null) rows.push(["Months to afford", r.months_to_afford]);
      if (r.affordable != null) rows.push(["Affordable soon", r.affordable ? "Yes ✅" : "Not yet ⚠️"]);
      if (r.interest_saved != null) rows.push(["Interest saved", inr(r.interest_saved)]);
      if (r.spend_in_5yr != null) rows.push(["Spend in 5 yrs", inr(r.spend_in_5yr) + "/mo"]);
      $("#whatifResult").innerHTML = rows.map(([k, v]) => `<div class="sim-stat"><span>${k}</span><strong>${v}</strong></div>`).join("") + `<p class="muted" style="margin-top:8px">${r.summary || ""}</p>`;
      destroy("whatif");
      if (r.projection_5yr) {
        charts.whatif = new Chart($("#chartWhatIf"), {
          type: "line",
          data: { labels: r.projection_5yr.map((p) => "Yr " + p.year), datasets: [{ label: "Balance @8%", data: r.projection_5yr.map((p) => p.balance), borderColor: cssVar("--primary-2"), backgroundColor: "rgba(138,107,255,.12)", fill: true, tension: .35, pointRadius: 3 }] },
          options: { ...baseLineOpts(), scales: { x: { grid: { color: gridColor() }, ticks: { color: tickColor() } }, y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: (v) => "₹" + (v / 100000).toFixed(1) + "L" } } } },
        });
      }
    });
  }

  /* ===================== NET WORTH ===================== */
  let networthReady = false;
  async function loadNetworth() {
    if (!networthReady) {
      networthReady = true;
      $("#assetForm").onsubmit = async (e) => {
        e.preventDefault();
        try {
          await API.addAsset({ name: $("#assetName").value.trim(), kind: $("#assetKind").value, value: +$("#assetValue").value });
          e.target.reset(); await loadNetworth(); toast("✅ Asset added");
        } catch (err) { toast(`⚠️ ${err.message}`); }
      };
      $("#liabForm").onsubmit = async (e) => {
        e.preventDefault();
        try {
          await API.addLiability({ name: $("#liabName").value.trim(), balance: +$("#liabBalance").value, monthly_payment: +$("#liabPay").value || 0 });
          e.target.reset(); await loadNetworth(); toast("✅ Liability added");
        } catch (err) { toast(`⚠️ ${err.message}`); }
      };
    }
    const d = await API.networth();
    $("#networthKpis").innerHTML = [
      { label: "Net worth", value: inr(d.net_worth), note: d.net_worth >= 0 ? "positive" : "negative", dir: d.net_worth >= 0 ? "up" : "down" },
      { label: "Total assets", value: inr(d.total_assets), note: `${d.assets.length} items`, dir: "up" },
      { label: "Total liabilities", value: inr(d.total_liabilities), note: `${d.liabilities.length} items`, dir: "down" },
      { label: "In 5 years", value: inr(d.projection[d.projection.length - 1].net_worth), note: "projected", dir: "up" },
    ].map((k) => `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta ${k.dir}">${k.note}</div></div>`).join("");

    $("#assetList").innerHTML = d.assets.map((a) => `<li><span>${a.name} <em class="muted">(${a.kind})</em></span><span>${inr(a.value)} <button class="tx-del" data-t="a" data-id="${a.id}">🗑️</button></span></li>`).join("") || `<li class="empty">No assets yet.</li>`;
    $("#liabList").innerHTML = d.liabilities.map((l) => `<li><span>${l.name} <em class="muted">(${l.kind})</em></span><span>${inr(l.balance)} <button class="tx-del" data-t="l" data-id="${l.id}">🗑️</button></span></li>`).join("") || `<li class="empty">No liabilities — debt free! 🎉</li>`;
    $$("#assetList .tx-del, #liabList .tx-del").forEach((b) => b.onclick = async () => {
      if (b.dataset.t === "a") await API.deleteAsset(+b.dataset.id); else await API.deleteLiability(+b.dataset.id);
      await loadNetworth();
    });

    destroy("networth");
    charts.networth = new Chart($("#chartNetworth"), {
      type: "doughnut",
      data: { labels: ["Assets", "Liabilities"], datasets: [{ data: [d.total_assets, d.total_liabilities], backgroundColor: [cssVar("--accent"), cssVar("--danger")], borderWidth: 0 }] },
      options: { plugins: { legend: { position: "bottom", labels: { color: tickColor(), boxWidth: 12 } } }, cutout: "60%", responsive: true, maintainAspectRatio: true },
    });
    destroy("networthProj");
    charts.networthProj = new Chart($("#chartNetworthProj"), {
      type: "line",
      data: { labels: d.projection.map((p) => "Yr " + p.year), datasets: [{ label: "Net worth", data: d.projection.map((p) => p.net_worth), borderColor: cssVar("--primary"), backgroundColor: "rgba(108,140,255,.12)", fill: true, tension: .35, pointRadius: 3 }] },
      options: { ...baseLineOpts(), scales: { x: { grid: { color: gridColor() }, ticks: { color: tickColor() } }, y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: (v) => "₹" + (v / 100000).toFixed(1) + "L" } } } },
    });
  }

  /* ===================== SUBSCRIPTIONS ===================== */
  async function loadSubscriptions() {
    const d = await API.subscriptions();
    $("#subsKpis").innerHTML = [
      { label: "Subscriptions found", value: d.count, note: "recurring" },
      { label: "Monthly cost", value: inr(d.total_monthly), note: "estimated" },
      { label: "Yearly cost", value: inr(d.total_annual), note: "estimated" },
    ].map((k) => `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta up">${k.note}</div></div>`).join("");
    $("#subsBody").innerHTML = d.subscriptions.length ? d.subscriptions.map((s) => `<tr><td>${s.name}</td><td><span class="cat-tag">${s.category}</span></td><td>${s.cadence}</td><td class="r">${inr(s.amount)}</td><td class="r">${inr(s.monthly_cost)}</td><td class="r">${inr(s.annual_cost)}</td></tr>`).join("") : `<tr><td colspan="6" class="empty">No recurring payments detected yet.</td></tr>`;
  }

  /* ===================== REPORTS ===================== */
  let reportsReady = false;
  async function loadReports() {
    if (!reportsReady) {
      reportsReady = true;
      $("#dlPdf").onclick = () => downloadReport("pdf");
      $("#dlExcel").onclick = () => downloadReport("excel");
    }
    const r = await API.reportSummary();
    $("#reportPreview").innerHTML = `
      <div class="rep-grid">
        <div class="rep-stat"><span>Monthly income</span><strong>${inr(r.monthly_income)}</strong></div>
        <div class="rep-stat"><span>Monthly spend</span><strong>${inr(r.monthly_spend)}</strong></div>
        <div class="rep-stat"><span>Monthly savings</span><strong>${inr(r.monthly_savings)}</strong></div>
        <div class="rep-stat"><span>Savings rate</span><strong>${r.savings_rate}%</strong></div>
        <div class="rep-stat"><span>Health score</span><strong>${r.health_score}/100</strong></div>
        <div class="rep-stat"><span>Subscriptions</span><strong>${r.subscriptions.count} · ${inr(r.subscriptions.total_monthly)}/mo</strong></div>
      </div>
      <h4 style="margin:14px 0 6px">Top categories</h4>
      <ul class="rep-list">${r.categories.slice(0, 6).map((c) => `<li><span>${c.category}</span><strong>${inr(c.monthly)}/mo</strong></li>`).join("")}</ul>
      <h4 style="margin:14px 0 6px">Recommendations</h4>
      <ul class="rep-list">${r.recommendations.map((x) => `<li><span>${x.title}</span><strong>${inr(x.save)}/mo</strong></li>`).join("")}</ul>`;
  }

  async function downloadReport(format) {
    try {
      toast(`📄 Generating ${format.toUpperCase()}…`);
      const blob = await API.reportDownload(format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `fintract-report.${format === "excel" ? "xlsx" : "pdf"}`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (err) { toast(`⚠️ ${err.message}`); }
  }

  /* ===================== PLANNER ===================== */
  async function loadPlanner() {
    const [em, ru, dv, su] = await Promise.all([API.emergency(), API.roundup(), API.diversification(), API.sustainability()]);

    $("#emergencyBody").innerHTML = `
      <div class="sim-stat"><span>Target (${em.months_cover} mo)</span><strong>${inr(em.target)}</strong></div>
      <div class="sim-stat"><span>Current</span><strong>${inr(em.current)}</strong></div>
      <div class="sim-stat hi"><span>Progress</span><strong>${em.progress_pct}%</strong></div>
      <div class="sim-stat"><span>Suggested/mo</span><strong>${inr(em.suggested_monthly_contribution)}</strong></div>
      <div class="g-bar" style="margin-top:10px"><span style="width:${em.progress_pct}%"></span></div>
      <p class="muted" style="margin-top:8px">${em.summary}</p>`;

    $("#roundupBody").innerHTML = `
      <div class="sim-stat"><span>Saved so far</span><strong>${inr(ru.total_roundups)}</strong></div>
      <div class="sim-stat"><span>Monthly avg</span><strong>${inr(ru.monthly_average)}</strong></div>
      <div class="sim-stat hi"><span>Yearly estimate</span><strong>${inr(ru.yearly_estimate)}</strong></div>
      <div class="sim-stat"><span>5-year estimate</span><strong>${inr(ru.five_year_estimate)}</strong></div>
      <p class="muted" style="margin-top:8px">${ru.summary}</p>`;

    destroy("diversify");
    if (dv.allocation.length) {
      charts.diversify = new Chart($("#chartDiversify"), {
        type: "doughnut",
        data: { labels: dv.allocation.map((a) => a.kind), datasets: [{ data: dv.allocation.map((a) => a.value), backgroundColor: ["#6c8cff", "#18d4a0", "#ffb23e", "#ff6b81", "#8a6bff"], borderWidth: 0 }] },
        options: { plugins: { legend: { position: "bottom", labels: { color: tickColor(), boxWidth: 10, font: { size: 10 } } } }, cutout: "60%", responsive: true, maintainAspectRatio: true },
      });
    }
    const dvItems = [
      ...(dv.score != null ? [`📊 Diversification score: <strong>${dv.score}/100</strong>`] : []),
      ...dv.warnings.map((w) => `⚠️ ${w}`),
      ...dv.suggestions.map((s) => `💡 ${s}`),
    ];
    $("#diversifyList").innerHTML = dvItems.map((t) => `<li><span>${t}</span></li>`).join("");

    $("#carbonKpis").innerHTML = `
      <div class="sim-stat"><span>Monthly footprint</span><strong>${su.monthly_kg_co2} kg CO₂e</strong></div>
      <div class="sim-stat"><span>Yearly footprint</span><strong>${su.yearly_kg_co2} kg CO₂e</strong></div>
      <div class="sim-stat hi"><span>Trees to offset/yr</span><strong>🌳 ${su.trees_equivalent_per_year}</strong></div>`;
    $("#carbonList").innerHTML = su.by_category.length
      ? su.by_category.slice(0, 5).map((r) => `<li><span>${r.category}: <strong>${r.monthly_kg_co2} kg/mo</strong>${r.tip ? ` — ${r.tip}` : ""}</span></li>`).join("")
      : `<li><span>${su.summary}</span></li>`;
  }

  /* ===================== PORTFOLIO LAB ===================== */
  const QUIZ = [
    ["If your portfolio dropped 20% in a month, you would…", ["Sell everything", "Sell some", "Do nothing", "Buy a little more", "Buy a lot more"]],
    ["Your investment horizon is…", ["< 1 year", "1–3 years", "3–5 years", "5–10 years", "10+ years"]],
    ["How stable is your income?", ["Very unstable", "Somewhat unstable", "Average", "Stable", "Very stable"]],
    ["What matters more to you?", ["Never losing money", "Mostly safety", "A balance", "Mostly growth", "Maximum growth"]],
    ["Your experience with investing?", ["None", "Beginner", "Some experience", "Experienced", "Expert"]],
  ];
  let labReady = false;
  async function loadLab() {
    if (!labReady) {
      labReady = true;
      $("#mcForm").onsubmit = async (e) => { e.preventDefault(); await runMonteCarlo(); };
      $("#quizBody").innerHTML = QUIZ.map(([q, opts], qi) => `
        <div class="quiz-q"><strong>${qi + 1}. ${q}</strong>
          <div class="filters">${opts.map((o, oi) => `<button type="button" class="chip quiz-opt" data-q="${qi}" data-v="${oi + 1}">${o}</button>`).join("")}</div>
        </div>`).join("");
      $$(".quiz-opt").forEach((b) => b.onclick = () => {
        $$(`.quiz-opt[data-q="${b.dataset.q}"]`).forEach((x) => x.classList.toggle("active", x === b));
      });
      $("#quizSubmit").onclick = async () => {
        const answers = QUIZ.map((_, qi) => { const sel = $(`.quiz-opt.active[data-q="${qi}"]`); return sel ? +sel.dataset.v : 0; });
        if (answers.some((a) => !a)) return toast("⚠️ Answer all 5 questions first");
        const r = await API.riskQuiz(answers);
        state.risk = r.risk_tolerance;
        $("#mcRisk").value = r.risk_tolerance;
        $("#quizResult").innerHTML = `✅ ${r.summary}`;
        toast(`🧭 Risk profile set: <strong>${r.profile}</strong>`);
        await runMonteCarlo();
      };
    }
    $("#mcRisk").value = state.risk;
    await runMonteCarlo();
  }

  async function runMonteCarlo() {
    const r = await API.monteCarlo({ monthly_investment: +$("#mcMonthly").value || 0, years: +$("#mcYears").value || 10, risk: +$("#mcRisk").value || 3 });
    $("#mcResult").innerHTML = `
      <div class="sim-stat"><span>Total invested</span><strong>${inr(r.total_invested)}</strong></div>
      <div class="sim-stat hi"><span>Median outcome</span><strong>${inr(r.final_median)}</strong></div>
      <div class="sim-stat"><span>In today's money</span><strong>${inr(r.final_median_real)}</strong></div>
      <div class="sim-stat"><span>Beats inflation in</span><strong>${r.prob_beating_inflation}% of runs</strong></div>`;
    destroy("montecarlo");
    charts.montecarlo = new Chart($("#chartMonteCarlo"), {
      type: "line",
      data: { labels: r.yearly.map((y) => "Yr " + y.year), datasets: [
        { label: "Optimistic (90th pct)", data: r.yearly.map((y) => y.optimistic), borderColor: "transparent", backgroundColor: "rgba(24,212,160,.10)", fill: "+1", pointRadius: 0, tension: .35 },
        { label: "Median", data: r.yearly.map((y) => y.median), borderColor: cssVar("--primary"), borderWidth: 3, fill: false, pointRadius: 2, tension: .35 },
        { label: "Pessimistic (10th pct)", data: r.yearly.map((y) => y.pessimistic), borderColor: "transparent", backgroundColor: "rgba(24,212,160,.10)", fill: "-1", pointRadius: 0, tension: .35 },
        { label: "Median (inflation-adj.)", data: r.yearly.map((y) => y.median_inflation_adjusted), borderColor: cssVar("--warning") || "#ffb23e", borderDash: [6, 4], fill: false, pointRadius: 0, tension: .35 },
      ] },
      options: { ...baseLineOpts(), scales: { x: { grid: { color: gridColor() }, ticks: { color: tickColor() } }, y: { grid: { color: gridColor() }, ticks: { color: tickColor(), callback: (v) => "₹" + (v / 100000).toFixed(1) + "L" } } } },
    });
  }

  /* ===================== FINANCIAL TWIN ===================== */
  const TWIN = [
    { scenario: "buy_car", label: "🚗 Buy a ₹8,00,000 car", params: { price: 800000 } },
    { scenario: "home_loan", label: "🏠 ₹50L home on a 20-yr loan", params: { price: 5000000, years: 20 } },
    { scenario: "rent_vs_buy", label: "🔑 Rent ₹20,000/mo vs buy ₹50L", params: { price: 5000000, rent: 20000 } },
    { scenario: "job_loss", label: "💼 What if I lose my job?", params: {} },
    { scenario: "salary_change", label: "📈 Salary increases 20%", params: { percent: 20 } },
    { scenario: "marriage", label: "💍 Getting married", params: { spend_increase_pct: 40 } },
    { scenario: "start_business", label: "🚀 Start a ₹5L business", params: { capital: 500000 } },
  ];
  let twinReady = false;
  function loadTwin() {
    if (twinReady) return; twinReady = true;
    $("#twinButtons").innerHTML = TWIN.map((t, i) => `<button class="chip whatif-btn" data-i="${i}">${t.label}</button>`).join("");
    $$("#twinButtons .whatif-btn").forEach((b) => b.onclick = async () => {
      const t = TWIN[+b.dataset.i];
      const r = await API.twin(t.scenario, t.params);
      $("#twinResultCard").style.display = "block";
      $("#twinTitle").textContent = r.headline || "Result";
      const skip = new Set(["headline", "summary", "verdict"]);
      const label = (k) => k.replace(/_/g, " ").replace(/\bpct\b/i, "%").replace(/^./, (c) => c.toUpperCase());
      const rows = Object.entries(r).filter(([k, v]) => !skip.has(k) && v !== null && typeof v !== "object")
        .map(([k, v]) => [label(k), typeof v === "number" && !/pct|months|runway/i.test(k) ? inr(v) : (typeof v === "boolean" ? (v ? "Yes ✅" : "No ⚠️") : v)]);
      $("#twinResult").innerHTML =
        rows.map(([k, v]) => `<div class="sim-stat"><span>${k}</span><strong>${v}</strong></div>`).join("") +
        (r.verdict ? `<div class="sim-stat hi"><span>Verdict</span><strong>${r.verdict}</strong></div>` : "") +
        `<p class="muted" style="margin-top:8px">${r.summary || ""}</p>`;
    });
  }

  /* ===================== ACHIEVEMENTS ===================== */
  async function loadAchievements() {
    const g = await API.gamification();
    $("#gameKpis").innerHTML = [
      { label: "Level", value: `${g.level} · ${g.level_name}`, note: "keep going!", dir: "up" },
      { label: "Points", value: g.points, note: "earned", dir: "up" },
      { label: "Saving streak", value: `${g.saving_streak_months} mo`, note: "spending under income", dir: "up" },
      { label: "Badges", value: `${g.badges_earned}/${g.badges.length}`, note: "unlocked", dir: "up" },
    ].map((k) => `<div class="kpi"><div class="k-label">${k.label}</div><div class="k-val">${k.value}</div><div class="k-delta ${k.dir}">${k.note}</div></div>`).join("");
    $("#badgeCount").textContent = `${g.badges_earned} of ${g.badges.length} earned`;
    $("#badgeGrid").innerHTML = g.badges.map((b) => `
      <div class="badge-card ${b.earned ? "earned" : "locked"}">
        <span class="badge-icon">${b.earned ? b.icon : "🔒"}</span>
        <strong>${b.name}</strong><span class="muted">${b.desc}</span>
      </div>`).join("");
    const ch = g.weekly_challenge;
    $("#challengeBody").innerHTML = `
      <div class="sim-stat"><span>${ch.name}</span><strong>${ch.on_track ? "On track ✅" : "Over budget ⚠️"}</strong></div>
      <div class="sim-stat"><span>This week</span><strong>${inr(ch.this_week)}</strong></div>
      <div class="sim-stat"><span>Last week</span><strong>${inr(ch.last_week)}</strong></div>`;
  }

  /* ===================== CHAT ===================== */
  let chatReady = false;
  function initChat() {
    if (chatReady) return; chatReady = true;
    const suggestions = ["Where did I spend the most this month?", "How can I save ₹5,000 next month?", "Can I afford a ₹50,000 purchase?", "Suggest an investment plan based on my finances."];
    $("#chatSuggestions").innerHTML = suggestions.map((s) => `<button class="chip" type="button">${s}</button>`).join("");
    $$("#chatSuggestions .chip").forEach((b) => b.onclick = () => { $("#chatText").value = b.textContent; sendChat(); });
    if (!$("#chatLog").childElementCount)
      pushMsg("bot", "👋 Hi! I'm your FinTract assistant, connected to your real data. Ask me anything or tap a suggestion.");
    $("#chatForm").onsubmit = (e) => { e.preventDefault(); sendChat(); };
  }
  function pushMsg(who, html) {
    const el = document.createElement("div"); el.className = "msg " + who; el.innerHTML = html;
    $("#chatLog").appendChild(el); $("#chatLog").scrollTop = $("#chatLog").scrollHeight; return el;
  }
  async function sendChat() {
    const t = $("#chatText").value.trim(); if (!t) return;
    pushMsg("user", t.replace(/</g, "&lt;")); $("#chatText").value = "";
    const typing = pushMsg("bot", `<span class="typing"><span></span><span></span><span></span></span>`);
    try { const r = await API.chat(t); typing.innerHTML = r.reply; }
    catch (err) { typing.innerHTML = `⚠️ ${err.message}`; }
    $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
  }
    $("#logoutBtn").onclick = () => {
    API.clearToken();
    $("#app").classList.add("hidden");
    $("#landing").classList.remove("hidden");
    if (state.ws) { state.ws.close(); state.ws = null; }
    state.user = null;
    setAuthMode(false);
    showAuth();
  };
   

  /* ---------- Firebase Google sign-in ---------- */
  let _fbAuth = null;
  fetch("/api/auth/firebase-config")
    .then(r => r.json())
    .then(cfg => {
      if (!cfg.apiKey) return; // Firebase not configured — hide Google button
      firebase.initializeApp(cfg);
      _fbAuth = firebase.auth();
    })
    .catch(() => {
      const btn = $("#authGoogle");
      if (btn) btn.style.display = "none";
    });

  $("#authGoogle").onclick = async () => {
    if (!_fbAuth) { authError("Google sign-in not available. Please try again in a moment."); return; }
    const btn = $("#authGoogle");
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = btn.innerHTML.replace("Continue with Google", "Opening Google…");
    try {
      const provider = new firebase.auth.GoogleAuthProvider();
      const result = await _fbAuth.signInWithPopup(provider);
      const idToken = await result.user.getIdToken();
      const user = await API.googleAuth(idToken);
      await launchApp(user);
    } catch (err) {
      if (err.code !== "auth/popup-closed-by-user") {
        authError(err.message || "Google sign-in failed. Please try again.");
      }
    } finally {
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  };

  /* ---------- auto-login if token present ---------- */
  if (API.isAuthed()) {
    // Keep user on landing but let them click in instantly; optionally auto-enter.
    // Auto-enter for a smoother return experience:
    bootFromToken();
  }
})();
