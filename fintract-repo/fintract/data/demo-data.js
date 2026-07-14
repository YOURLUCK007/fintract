/* ============ FinTract demo dataset (representative, INR) ============ */
window.FINTRACT_DATA = {
  user: { name: "Karthik S.", income: 95000, currency: "₹" },

  kpis: [
    { label: "Net worth", value: "₹8,42,300", delta: "+4.2% MoM", dir: "up" },
    { label: "This month spend", value: "₹54,120", delta: "-8.1% vs avg", dir: "up" },
    { label: "Monthly savings", value: "₹24,380", delta: "+12.6%", dir: "up" },
    { label: "Savings rate", value: "31%", delta: "+3 pts", dir: "up" }
  ],

  months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
  income:   [92000, 92000, 95000, 95000, 95000, 95000],
  spending: [71000, 68500, 66200, 61000, 58900, 54120],

  categories: [
    { name: "Food",          value: 14200, color: "#6c8cff" },
    { name: "Travel",        value: 8600,  color: "#8a6bff" },
    { name: "Shopping",      value: 9100,  color: "#18d4a0" },
    { name: "Bills",         value: 11200, color: "#ffb23e" },
    { name: "Healthcare",    value: 3400,  color: "#ff6b81" },
    { name: "Entertainment", value: 4200,  color: "#46c2ff" },
    { name: "Education",     value: 2200,  color: "#c98bff" },
    { name: "Others",        value: 1220,  color: "#88e0c0" }
  ],

  trend: [71000, 68500, 66200, 61000, 58900, 54120],

  health: {
    score: 78,
    breakdown: [
      { label: "Savings ratio",     pct: 84 },
      { label: "Spending discipline", pct: 76 },
      { label: "Investment habits", pct: 71 },
      { label: "Emergency fund",    pct: 90 },
      { label: "Debt levels",       pct: 82 },
      { label: "Budget adherence",  pct: 68 }
    ]
  },

  insights: [
    { em: "🍽️", text: "Dining spend dropped <strong>31%</strong> vs last month — keep it up to save ₹4,400/mo." },
    { em: "🔁", text: "3 recurring subscriptions detected. Cancelling unused ones saves <strong>₹1,180/mo</strong>." },
    { em: "📈", text: "Your savings rate of <strong>31%</strong> beats the 20% benchmark for your income bracket." },
    { em: "⚠️", text: "Shopping is up <strong>18%</strong> this month — your only over-budget category." }
  ],

  transactions: [
    { date: "2026-06-19", desc: "Swiggy — dinner order", cat: "Food", amt: 540 },
    { date: "2026-06-18", desc: "Uber to airport", cat: "Travel", amt: 720 },
    { date: "2026-06-18", desc: "Amazon — headphones", cat: "Shopping", amt: 2499 },
    { date: "2026-06-17", desc: "Electricity bill", cat: "Bills", amt: 2150 },
    { date: "2026-06-16", desc: "Netflix subscription", cat: "Entertainment", amt: 649 },
    { date: "2026-06-16", desc: "Apollo Pharmacy", cat: "Healthcare", amt: 880 },
    { date: "2026-06-15", desc: "Coursera — ML course", cat: "Education", amt: 1499 },
    { date: "2026-06-14", desc: "Zomato — lunch", cat: "Food", amt: 320 },
    { date: "2026-06-14", desc: "SIP — Nifty index fund", cat: "Investments", amt: 10000 },
    { date: "2026-06-13", desc: "Spotify Premium", cat: "Entertainment", amt: 119 },
    { date: "2026-06-12", desc: "BigBasket groceries", cat: "Food", amt: 2840 },
    { date: "2026-06-11", desc: "Petrol — HP", cat: "Travel", amt: 1500 },
    { date: "2026-06-10", desc: "Myntra — apparel", cat: "Shopping", amt: 3299 },
    { date: "2026-06-09", desc: "Mobile recharge", cat: "Bills", amt: 399 },
    { date: "2026-06-08", desc: "Swiggy — dinner order", cat: "Food", amt: 560 }
  ],

  anomalies: [
    { type: "dup", text: "Possible duplicate: <strong>Swiggy ₹540</strong> on Jun 19 & ₹560 on Jun 08 within similar window." },
    { type: "spike", text: "Unusual: <strong>Myntra ₹3,299</strong> is 2.4× your typical shopping transaction." },
    { type: "spike", text: "Recurring charge increased: <strong>Netflix ₹499 → ₹649</strong>." }
  ],

  forecastPlans: {
    conservative: { weekly: 4200, monthly: 18000, yearly: 216000, growth: 0.04,
      base: [18,36.5,55,74,93.5,113,133,153.5,174,195,216.5,238].map(v=>v*1000),
      kpiNote: "Low risk · minimal lifestyle change" },
    balanced:     { weekly: 5700, monthly: 24380, yearly: 292560, growth: 0.07,
      base: [24.4,49.5,75.5,102,129,156.5,184.5,213,242,271.5,301.5,332].map(v=>v*1000),
      kpiNote: "Moderate · follow 3 of 4 recommendations" },
    aggressive:   { weekly: 7400, monthly: 31800, yearly: 381600, growth: 0.10,
      base: [31.8,64.5,98,132.5,167.5,203.5,240,277,315,353.5,393,433].map(v=>v*1000),
      kpiNote: "High discipline · follow all recommendations" }
  },

  recommendations: [
    { title: "Reduce food delivery by 20%", why: "You order out 14×/mo; cook 3 more meals weekly.", save: 2400 },
    { title: "Cancel 2 unused subscriptions", why: "Detected: a fitness app + a cloud plan unused 60+ days.", save: 1180 },
    { title: "Shift to public transport 2×/week", why: "Cuts fuel & ride-hailing spend meaningfully.", save: 1600 },
    { title: "Set a ₹6k shopping cap", why: "Shopping is your only over-budget category this month.", save: 2200 },
    { title: "Auto-sweep idle balance to liquid fund", why: "Earn ~6% on cash that sits idle in savings.", save: 900 }
  ],

  cashflow: { months: ["Jul","Aug","Sep","Oct","Nov","Dec"], inflow: [95000,95000,98000,95000,95000,112000], outflow: [54000,56000,53000,58000,55000,61000] },

  // allocation by risk level 1..5
  allocations: {
    1: [["Emergency fund",30],["Fixed deposits",28],["Govt bonds",20],["Gold",12],["Index funds",10]],
    2: [["Emergency fund",25],["Fixed deposits",22],["Govt bonds",16],["Index funds",18],["Gold",10],["Mutual funds",9]],
    3: [["Emergency fund",20],["Index funds",24],["Mutual funds",18],["Fixed deposits",14],["ETFs",12],["Gold",8],["Govt bonds",4]],
    4: [["Index funds",30],["ETFs",22],["Mutual funds",20],["Emergency fund",12],["Gold",8],["Retirement",8]],
    5: [["Index funds",34],["ETFs",26],["Mutual funds",22],["Retirement",10],["Emergency fund",8]]
  },
  allocColors: ["#6c8cff","#8a6bff","#18d4a0","#ffb23e","#ff6b81","#46c2ff","#c98bff"],
  investableMonthly: 24380,

  goals: [
    { name: "Emergency fund", emoji: "🛟", target: 300000, saved: 220000, monthly: 15000 },
    { name: "New laptop",     emoji: "💻", target: 120000, saved: 48000,  monthly: 12000 },
    { name: "Goa vacation",   emoji: "🏖️", target: 80000,  saved: 26000,  monthly: 8000 },
    { name: "Home down payment", emoji: "🏠", target: 2000000, saved: 540000, monthly: 40000 }
  ],

  chatSuggestions: [
    "Where did I spend the most this month?",
    "How can I save ₹5,000 next month?",
    "Can I afford a ₹50,000 purchase?",
    "Suggest an investment plan based on my finances."
  ]
};
