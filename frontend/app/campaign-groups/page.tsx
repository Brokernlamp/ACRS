"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Plus, Loader2, TrendingUp, TrendingDown, Minus, RefreshCw, CheckCircle } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const OBJECTIVES = ["awareness", "consideration", "conversion"];
const PLATFORM_LABELS: Record<string, string> = {
  google_ads: "Google Ads", meta_ads: "Meta Ads",
  linkedin: "LinkedIn", manual: "Manual CSV",
};
const PLATFORM_COLORS: Record<string, string> = {
  google_ads: "bg-blue-100 text-blue-700",
  meta_ads: "bg-indigo-100 text-indigo-700",
  linkedin: "bg-sky-100 text-sky-700",
  manual: "bg-gray-100 text-gray-700",
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const e = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((e as { detail?: string }).detail ?? "Request failed");
  }
  return res.json();
}

interface Campaign { id: number; name: string; platform: string; group_id: number | null; group_name: string | null }
interface Group { id: number; name: string; objective: string; description: string; campaign_count: number }
interface PlatformData { spend: number; leads: number; cpl: number; campaigns: { id: number; name: string; platform: string; spend: number; leads: number; cpl: number }[] }
interface GroupPerf {
  group_id: number; group_name: string; objective: string;
  platforms: Record<string, PlatformData>;
  blended: {
    spend: number; leads: number; cpl: number; ctr: number; roas: number; revenue: number;
    vs_target_cpl_pct?: number; efficiency_status?: string;
    estimated_profit?: number; profit_status?: string;
  };
}
interface CrossPlatform {
  groups: GroupPerf[];
  ungrouped_campaigns: { id: number; name: string; platform: string; spend: number; leads: number; cpl: number }[];
  platform_totals: Record<string, { spend: number; leads: number; cpl: number }>;
}

function StatusBadge({ status }: { status?: string }) {
  if (!status) return null;
  if (status === "profit") return <span className="flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full"><TrendingUp size={11} /> Profit</span>;
  if (status === "loss") return <span className="flex items-center gap-1 text-xs font-semibold text-red-700 bg-red-100 px-2 py-0.5 rounded-full"><TrendingDown size={11} /> Loss</span>;
  return <span className="flex items-center gap-1 text-xs font-semibold text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full"><Minus size={11} /> Neutral</span>;
}

export default function CampaignGroupsPage() {
  const [clientId, setClientId] = useState<number | null>(null);
  const [clients, setClients] = useState<{ id: number; name: string }[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [crossPlatform, setCrossPlatform] = useState<CrossPlatform | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [newName, setNewName] = useState("");
  const [newObjective, setNewObjective] = useState("conversion");
  const [creating, setCreating] = useState(false);

  // Per-campaign inline assign state
  const [assigningId, setAssigningId] = useState<number | null>(null);

  useEffect(() => {
    api.listClients().then(cs => {
      // Filter out clients with empty names
      const valid = cs.filter(c => c.name.trim());
      setClients(valid.map(c => ({ id: c.id, name: c.name })));
      if (valid.length > 0) setClientId(valid[0].id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!clientId) return;
    loadAll();
  }, [clientId]);

  async function loadAll() {
    if (!clientId) return;
    setLoading(true); setError(null);
    try {
      const [g, c, cp] = await Promise.all([
        req<Group[]>(`/api/campaign-groups/${clientId}`),
        req<Campaign[]>(`/api/clients/${clientId}/campaigns`),
        req<CrossPlatform>(`/api/clients/${clientId}/cross-platform`),
      ]);
      setGroups(g);
      setCampaigns(c);
      setCrossPlatform(cp);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateGroup() {
    if (!newName.trim() || !clientId) return;
    setCreating(true); setError(null);
    try {
      await req("/api/campaign-groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: clientId, name: newName.trim(), objective: newObjective }),
      });
      setNewName("");
      setSuccessMsg(`Group "${newName.trim()}" created.`);
      setTimeout(() => setSuccessMsg(null), 3000);
      await loadAll();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create group");
    } finally {
      setCreating(false);
    }
  }

  async function handleAssignCampaign(campaignId: number, groupId: number | null) {
    setAssigningId(campaignId); setError(null);
    try {
      await req("/api/campaign-groups/assign-campaign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ campaign_id: campaignId, group_id: groupId }),
      });
      setSuccessMsg("Assignment saved.");
      setTimeout(() => setSuccessMsg(null), 2000);
      await loadAll();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to assign");
    } finally {
      setAssigningId(null);
    }
  }

  const hasCampaigns = campaigns.length > 0;
  const hasGroups = groups.length > 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaign Groups</h1>
          <p className="text-sm text-gray-500 mt-1">Group campaigns across platforms to see blended performance and P&L</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={clientId ?? ""} onChange={e => setClientId(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
            {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <button onClick={loadAll} disabled={loading}
            className="flex items-center gap-1.5 text-sm text-gray-600 border border-gray-200 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} Refresh
          </button>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">⚠️ {error}</div>}
      {successMsg && <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm px-4 py-3 rounded-lg"><CheckCircle size={14} /> {successMsg}</div>}

      {/* No data state */}
      {!hasCampaigns && !loading && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 rounded-lg">
          ⚠️ No campaigns found for this client. Upload a CSV on the Dashboard first, then come back here to group them.
        </div>
      )}

      {/* Platform totals */}
      {crossPlatform && Object.keys(crossPlatform.platform_totals).length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Object.entries(crossPlatform.platform_totals).map(([platform, t]) => (
            <div key={platform} className="bg-white border border-gray-200 rounded-xl p-4">
              <div className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full mb-2 ${PLATFORM_COLORS[platform] ?? "bg-gray-100 text-gray-700"}`}>
                {PLATFORM_LABELS[platform] ?? platform}
              </div>
              <div className="text-xl font-bold text-gray-900">${t.spend.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
              <div className="text-xs text-gray-500 mt-0.5">{t.leads} leads · CPL ${t.cpl}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* LEFT PANEL */}
        <div className="space-y-4">

          {/* Step 1: Create group */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">1</span>
              <h2 className="text-sm font-semibold text-gray-800">Create a Group</h2>
            </div>
            <p className="text-xs text-gray-500">A group holds campaigns from different platforms that serve the same goal. e.g. "Retargeting" = Google Display + Meta Retargeting.</p>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Group Name</label>
              <input value={newName} onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleCreateGroup()}
                placeholder="e.g. Retargeting, Brand Awareness"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Objective</label>
              <select value={newObjective} onChange={e => setNewObjective(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
                {OBJECTIVES.map(o => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
              </select>
            </div>
            <button onClick={handleCreateGroup} disabled={creating || !newName.trim()}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
              {creating ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
              {creating ? "Creating…" : "Create Group"}
            </button>
          </div>

          {/* Step 2: Assign campaigns */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">2</span>
              <h2 className="text-sm font-semibold text-gray-800">Assign Campaigns</h2>
            </div>
            <p className="text-xs text-gray-500">Each row below is a campaign. Use the dropdown to assign it to a group. Campaigns from different platforms can share the same group.</p>

            {!hasCampaigns && (
              <p className="text-xs text-gray-400 italic">No campaigns yet — upload data on Dashboard first.</p>
            )}

            {!hasGroups && hasCampaigns && (
              <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">Create a group first (Step 1), then assign campaigns here.</p>
            )}

            {hasCampaigns && hasGroups && (
              <div className="space-y-2">
                {campaigns.map(c => (
                  <div key={c.id} className="border border-gray-200 rounded-lg p-3 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full shrink-0 ${PLATFORM_COLORS[c.platform] ?? "bg-gray-100 text-gray-700"}`}>
                        {PLATFORM_LABELS[c.platform] ?? c.platform}
                      </span>
                      <span className="text-xs font-medium text-gray-800 truncate">{c.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <select
                        defaultValue={c.group_id ?? ""}
                        onChange={e => handleAssignCampaign(c.id, e.target.value ? Number(e.target.value) : null)}
                        disabled={assigningId === c.id}
                        className="flex-1 border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50">
                        <option value="">— Unassigned —</option>
                        {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                      </select>
                      {assigningId === c.id && <Loader2 size={13} className="animate-spin text-indigo-500 shrink-0" />}
                      {c.group_name && assigningId !== c.id && (
                        <span className="text-xs text-emerald-600 font-medium shrink-0">✓ {c.group_name}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL — Group performance */}
        <div className="lg:col-span-2 space-y-4">

          {!hasGroups && (
            <div className="bg-white border border-dashed border-gray-300 rounded-xl p-12 text-center">
              <p className="text-3xl mb-3">📊</p>
              <p className="text-sm font-semibold text-gray-600 mb-1">No groups yet</p>
              <p className="text-xs text-gray-400">Create a group on the left, assign campaigns to it, and the blended performance will appear here.</p>
            </div>
          )}

          {crossPlatform?.groups.map(gp => (
            <div key={gp.group_id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">{gp.group_name}</span>
                  <span className="text-xs text-gray-500 capitalize bg-gray-200 px-2 py-0.5 rounded-full">{gp.objective}</span>
                  <span className="text-xs text-gray-400">{Object.keys(gp.platforms).length} platform{Object.keys(gp.platforms).length !== 1 ? "s" : ""}</span>
                </div>
                <div className="flex items-center gap-2">
                  {gp.blended.profit_status && <StatusBadge status={gp.blended.profit_status} />}
                  {!gp.blended.profit_status && gp.blended.efficiency_status && <StatusBadge status={gp.blended.efficiency_status} />}
                </div>
              </div>

              {/* Blended metrics row */}
              <div className="grid grid-cols-3 sm:grid-cols-5 divide-x divide-gray-100 border-b border-gray-100">
                {[
                  { label: "Total Spend", value: `$${gp.blended.spend.toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
                  { label: "Total Leads", value: gp.blended.leads.toLocaleString() },
                  {
                    label: "Blended CPL", value: `$${gp.blended.cpl}`,
                    sub: gp.blended.vs_target_cpl_pct !== undefined
                      ? `${gp.blended.vs_target_cpl_pct > 0 ? "+" : ""}${gp.blended.vs_target_cpl_pct}% vs target`
                      : undefined,
                    subColor: gp.blended.efficiency_status === "profit" ? "text-emerald-600" : "text-red-500",
                  },
                  {
                    label: "Est. Profit",
                    value: gp.blended.estimated_profit !== undefined
                      ? `$${gp.blended.estimated_profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                      : "—",
                  },
                  { label: "ROAS", value: gp.blended.roas ? `${gp.blended.roas}x` : "—" },
                ].map(({ label, value, sub, subColor }) => (
                  <div key={label} className="px-4 py-3">
                    <div className="text-xs text-gray-500 mb-0.5">{label}</div>
                    <div className="text-sm font-bold text-gray-900">{value}</div>
                    {sub && <div className={`text-xs font-medium ${subColor}`}>{sub}</div>}
                  </div>
                ))}
              </div>

              {/* Per-platform breakdown */}
              <div className="p-4 space-y-3">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Platform Breakdown</div>
                {Object.entries(gp.platforms).map(([platform, pdata]) => (
                  <div key={platform} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${PLATFORM_COLORS[platform] ?? "bg-gray-100 text-gray-700"}`}>
                        {PLATFORM_LABELS[platform] ?? platform}
                      </span>
                      <span className="text-xs text-gray-500">
                        ${pdata.spend.toLocaleString(undefined, { minimumFractionDigits: 2 })} · {pdata.leads} leads · CPL ${pdata.cpl}
                      </span>
                    </div>
                    {pdata.campaigns.map(c => (
                      <div key={c.id} className="ml-4 flex items-center justify-between text-xs text-gray-600 bg-gray-50 rounded-lg px-3 py-2">
                        <span className="truncate max-w-[200px] font-medium">{c.name}</span>
                        <span className="text-gray-400 shrink-0 ml-2">
                          ${c.spend.toLocaleString(undefined, { minimumFractionDigits: 2 })} · {c.leads} leads · CPL ${c.cpl}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Ungrouped campaigns */}
          {crossPlatform && crossPlatform.ungrouped_campaigns.length > 0 && (
            <div className="bg-white border border-dashed border-gray-300 rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-500">
                  Ungrouped Campaigns
                  <span className="ml-2 text-xs font-normal text-gray-400">({crossPlatform.ungrouped_campaigns.length})</span>
                </span>
                <span className="text-xs text-gray-400">Assign these using Step 2 on the left</span>
              </div>
              <div className="divide-y divide-gray-100">
                {crossPlatform.ungrouped_campaigns.map(c => (
                  <div key={c.id} className="flex items-center justify-between px-5 py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${PLATFORM_COLORS[c.platform] ?? "bg-gray-100 text-gray-700"}`}>
                        {PLATFORM_LABELS[c.platform] ?? c.platform}
                      </span>
                      <span className="text-gray-800 font-medium">{c.name}</span>
                    </div>
                    <span className="text-gray-500 text-xs">
                      ${c.spend.toLocaleString(undefined, { minimumFractionDigits: 2 })} · {c.leads} leads · CPL ${c.cpl}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
