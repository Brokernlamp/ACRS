const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface KPIs {
  "Total Spend": string;
  "Total Leads": number;
  "Total Clicks": number;
  "Total Impressions": number;
  "Blended CPL ($)": number;
  "Weighted CTR (%)": number;
  "Conversion Rate (%)": number;
  "ROAS": number;
}

export interface Prediction {
  predicted_leads: number;
  growth_rate_pct: number;
  trend: string;
  days_ahead: number;
}

export interface CplPrediction { predicted_cpl: number; direction: string }
export interface CtrPrediction { predicted_ctr: number; drop_pct: number; refresh_needed: boolean }

export interface Waste {
  total_wasted: number;
  worst_campaign: string;
  worst_waste: number;
  savings_opportunity: number;
}

export interface AllocationRow {
  campaign: string;
  score: number;
  budget_share_pct: number;
  recommended_budget: number;
}

export interface SimResult {
  campaign: string;
  action: string;
  spend_change: number;
  leads_change: number;
  cpl_change: number;
  summary: string;
}

export interface CampRow {
  campaign: string;
  impressions: number;
  clicks: number;
  spend: number;
  leads: number;
  ctr: number;
  cpl: number;
  conversion_rate: number;
}

export interface AnalyticsResult {
  kpis: KPIs;
  insights: string[];
  campaigns: string[];
  camp_summary: CampRow[];
  predictions: Prediction;
  cpl_prediction: CplPrediction;
  ctr_prediction: CtrPrediction;
  actions: string[];
  waste: Waste;
  allocation: AllocationRow[];
  patterns: string[];
  charts: {
    leads_over_time: object;
    spend_vs_leads: object;
    campaign_performance: object;
    performance_scores: object;
    budget_allocation: object;
    leads_forecast: object;
  };
  comparison_summary?: string;
}

export interface Client {
  id: number;
  name: string;
  industry: string;
  campaigns: number;
  total_spend: number;
  total_leads: number;
  avg_cpl: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

export const api = {
  upload: (file: File, clientName: string): Promise<AnalyticsResult> => {
    const form = new FormData();
    form.append("file", file);
    form.append("client_name", clientName);
    return request("/api/upload", { method: "POST", body: form });
  },

  refresh: (startDate: string, endDate: string, comparisonPeriod = "None", clientId?: number): Promise<AnalyticsResult> =>
    request("/api/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ start_date: startDate, end_date: endDate, comparison_period: comparisonPeriod, client_id: clientId }),
    }),

  dataCoverage: (clientId: number): Promise<{ has_data: boolean; earliest: string | null; latest: string | null; rows: number; days: number; }> =>
    request(`/api/clients/${clientId}/data-coverage`),

  syncLatest: (clientId: number): Promise<{ status: string; campaigns_added: number; total_rows: number; aggregated: Record<string, unknown> }> =>
    request(`/api/clients/${clientId}/sync-platforms`, { method: "POST" }),

  simulate: (campaign: string, deltaPct: number): Promise<SimResult> =>
    request("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ campaign, delta_pct: deltaPct }),
    }),

  simulatePause: (campaign: string): Promise<SimResult> =>
    request("/api/simulate/pause", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ campaign, delta_pct: 0 }),
    }),

  reportStandardUrl: (clientName: string) =>
    `${BASE}/api/report/standard?client_name=${encodeURIComponent(clientName)}`,

  reportGrowthUrl: (clientName: string) =>
    `${BASE}/api/report/growth?client_name=${encodeURIComponent(clientName)}`,

  sendEmail: (payload: {
    client_name: string;
    sender_email: string;
    sender_password: string;
    recipient_email: string;
  }): Promise<{ message: string }> =>
    request("/api/email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  listClients: (): Promise<Client[]> => request("/api/clients"),

  addClient: (payload: {
    name: string;
    industry?: string;
    target_cpl?: number;
    monthly_budget?: number;
    revenue_per_lead?: number;
  }): Promise<Client> =>
    request("/api/clients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  chatStatus: (): Promise<{ gemini_configured: boolean; rag_documents_indexed: number; ready: boolean }> =>
    request("/api/chat/status"),

  chat: (message: string): Promise<{ reply: string; history: { role: string; content: string }[] }> =>
    request("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    }),

  chatReset: (): Promise<{ status: string }> =>
    request("/api/chat/reset", { method: "POST" }),

  getSettings: (): Promise<{ gemini_api_key_set: boolean; gemini_api_key_preview: string; gemini_model: string; database_url: string }> =>
    request("/api/settings"),

  saveSettings: (gemini_api_key: string): Promise<{ status: string }> =>
    request("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gemini_api_key }),
    }),

  reportSimulationUrl: () => `${BASE}/api/report/simulation`,

  reportSimulation: (clientName: string, simulations: SimResult[]): Promise<Blob> =>
    fetch(`${BASE}/api/report/simulation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_name: clientName, simulations }),
    }).then(r => { if (!r.ok) throw new Error("Failed to generate report"); return r.blob(); }),

  sampleDataUrl: () => `${BASE}/api/settings/sample-data`,
};
