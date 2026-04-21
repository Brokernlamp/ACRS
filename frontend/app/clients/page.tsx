"use client";
import { useEffect, useState } from "react";
import { api, Client } from "@/lib/api";
import { Loader2, RefreshCw, Plus } from "lucide-react";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [targetCpl, setTargetCpl] = useState("");
  const [budget, setBudget] = useState("");
  const [adding, setAdding] = useState(false);

  async function load() {
    setLoading(true); setError(null);
    try { setClients(await api.listClients()); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Failed to load clients"); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleAdd() {
    if (!name.trim()) return setError("Client name is required.");
    setAdding(true); setError(null); setSuccess(null);
    try {
      await api.addClient({
        name: name.trim(), industry: industry || undefined,
        target_cpl: targetCpl ? Number(targetCpl) : undefined,
        monthly_budget: budget ? Number(budget) : undefined,
      });
      setSuccess(`Client "${name}" added successfully.`);
      setName(""); setIndustry(""); setTargetCpl(""); setBudget("");
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to add client");
    } finally { setAdding(false); }
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your agency clients</p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">⚠️ {error}</div>}
      {success && <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm px-4 py-3 rounded-lg">✅ {success}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Client list */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">Your Clients</h2>
            <button onClick={load} disabled={loading}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 transition-colors">
              {loading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />} Refresh
            </button>
          </div>
          {clients.length === 0 ? (
            <div className="text-center py-12 text-gray-400 text-sm">No clients yet. Add one →</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                <tr>{["Client", "Industry", "Campaigns", "Total Spend", "Leads", "Avg CPL"].map(h =>
                  <th key={h} className="px-4 py-3 text-left font-semibold">{h}</th>)}</tr>
              </thead>
              <tbody>
                {clients.map((c, i) => (
                  <tr key={c.id} className={`border-t border-gray-100 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                    <td className="px-4 py-3 font-semibold text-gray-900">{c.name}</td>
                    <td className="px-4 py-3 text-gray-700">{c.industry}</td>
                    <td className="px-4 py-3 text-gray-700">{c.campaigns}</td>
                    <td className="px-4 py-3 text-gray-700">${c.total_spend.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-gray-700">{c.total_leads.toLocaleString()}</td>
                    <td className="px-4 py-3 font-semibold text-gray-900">${c.avg_cpl.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Add client form */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">Add New Client</h2>
          {[
            { label: "Client Name *", value: name, set: setName, placeholder: "Acme Corp" },
            { label: "Industry", value: industry, set: setIndustry, placeholder: "SaaS" },
            { label: "Target CPL ($)", value: targetCpl, set: setTargetCpl, placeholder: "50" },
            { label: "Monthly Budget ($)", value: budget, set: setBudget, placeholder: "10000" },
          ].map(({ label, value, set, placeholder }) => (
            <div key={label}>
              <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
              <input value={value} onChange={e => set(e.target.value)} placeholder={placeholder}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
            </div>
          ))}
          <button onClick={handleAdd} disabled={adding}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
            {adding ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            {adding ? "Adding…" : "Add Client"}
          </button>
        </div>
      </div>
    </div>
  );
}
