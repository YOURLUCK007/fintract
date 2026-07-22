/* ===================== FinTract API client ===================== */
(() => {
  // API base: same-origin "/api" in production (served behind one host), or a
  // local backend during dev. Override by setting window.FINTRACT_API_BASE.
  const guessBase = () => {
    if (window.FINTRACT_API_BASE) return window.FINTRACT_API_BASE;
    const { protocol, hostname, port } = window.location;
    // Static dev server (e.g. :8080 / :3000) -> talk to backend on :8000
    if (port && port !== "8000") return `${protocol}//${hostname}:8000`;
    return "";
  };

  const BASE = guessBase();
  const TOKEN_KEY = "ft-token";

  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
  const clearToken = () => localStorage.removeItem(TOKEN_KEY);

  async function request(path, { method = "GET", body, form, auth = true } = {}) {
    const headers = {};
    const opts = { method, headers };
    if (auth && getToken()) headers["Authorization"] = `Bearer ${getToken()}`;
    if (form) {
      opts.body = form; // FormData / URLSearchParams
    } else if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(`${BASE}${path}`, opts);
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data && data.detail ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)) : `Request failed (${res.status})`;
      throw new Error(msg);
    }
    return data;
  }

  window.API = {
    base: BASE,
    getToken, setToken, clearToken,
    isAuthed: () => !!getToken(),

    // auth
    async register(payload) {
      const data = await request("/api/auth/register", { method: "POST", body: payload, auth: false });
      setToken(data.access_token);
      return data.user;
    },
    async login(email, password) {
      const form = new URLSearchParams();
      form.set("username", email);
      form.set("password", password);
      const data = await request("/api/auth/login", { method: "POST", form, auth: false });
      setToken(data.access_token);
      return data.user;
    },
    googleAuth: async (idToken) => {
      const data = await request("/api/auth/google", { method: "POST", body: { id_token: idToken }, auth: false });
      setToken(data.access_token);
      return data.user;
    },
    me: () => request("/api/auth/me"),
    updateMe: (payload) => request("/api/auth/me", { method: "PATCH", body: payload }),

    // data
    overview: () => request("/api/analytics/overview"),
    anomalies: () => request("/api/analytics/anomalies"),
    expenses: (category) => request(`/api/expenses${category && category !== "All" ? `?category=${encodeURIComponent(category)}` : ""}`),
    addExpense: (payload) => request("/api/expenses", { method: "POST", body: payload }),
    deleteExpense: (id) => request(`/api/expenses/${id}`, { method: "DELETE" }),
    categorize: (description) => request("/api/expenses/categorize", { method: "POST", body: { description } }),
    importCsv: (file) => {
      const fd = new FormData();
      fd.append("file", file);
      return request("/api/expenses/import", { method: "POST", form: fd });
    },
    savings: (plan) => request(`/api/forecast/savings?plan=${plan}`),
    cashflow: () => request("/api/forecast/cashflow"),
    recommendations: () => request("/api/forecast/recommendations"),
    invest: (risk) => request(`/api/invest/advice${risk ? `?risk=${risk}` : ""}`),
    goals: () => request("/api/goals"),
    addGoal: (payload) => request("/api/goals", { method: "POST", body: payload }),
    deleteGoal: (id) => request(`/api/goals/${id}`, { method: "DELETE" }),
    chat: (message) => request("/api/chat", { method: "POST", body: { message } }),
    notifications: () => request("/api/notifications"),

    // new high-impact features
    budget: () => request("/api/budget"),
    subscriptions: () => request("/api/subscriptions"),
    networth: () => request("/api/networth"),
    addAsset: (payload) => request("/api/networth/assets", { method: "POST", body: payload }),
    deleteAsset: (id) => request(`/api/networth/assets/${id}`, { method: "DELETE" }),
    addLiability: (payload) => request("/api/networth/liabilities", { method: "POST", body: payload }),
    deleteLiability: (id) => request(`/api/networth/liabilities/${id}`, { method: "DELETE" }),
    simulateSavings: (payload) => request("/api/simulate/savings", { method: "POST", body: payload }),
    whatIf: (scenario, params) => request("/api/simulate/whatif", { method: "POST", body: { scenario, params } }),
    reportSummary: () => request("/api/reports/summary"),

    // planner / advanced features
    roundup: () => request("/api/plan/roundup"),
    emergency: () => request("/api/plan/emergency"),
    diversification: () => request("/api/plan/diversification"),
    monteCarlo: (payload) => request("/api/plan/montecarlo", { method: "POST", body: payload }),
    twin: (scenario, params) => request("/api/plan/twin", { method: "POST", body: { scenario, params } }),
    gamification: () => request("/api/plan/gamification"),
    sustainability: () => request("/api/plan/sustainability"),
    riskQuiz: (answers) => request("/api/plan/risk-quiz", { method: "POST", body: { answers } }),
    reportDownload(format) {
      const url = `${BASE}/api/reports/export?format=${format}`;
      return fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } })
        .then((r) => { if (!r.ok) throw new Error("Export failed"); return r.blob(); });
    },

    // payments / Stripe
    createCheckout: () => request("/api/payments/create-checkout", { method: "POST" }),
    subscriptionStatus: () => request("/api/payments/status"),

    connectWs(onMessage) {
      const token = getToken();
      if (!token) return null;
      const wsBase = (BASE || window.location.origin).replace(/^http/, "ws");
      const ws = new WebSocket(`${wsBase}/ws?token=${token}`);
      ws.onmessage = (ev) => {
        try { onMessage(JSON.parse(ev.data)); } catch (_) {}
      };
      return ws;
    },
  };
})();
