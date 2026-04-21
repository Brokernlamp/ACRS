import { KPIs } from "@/lib/api";

const CARDS = [
  { key: "Total Spend",         icon: "💰", bg: "bg-indigo-600",  label: "text-indigo-100",  val: "text-white",        sub: "Total ad spend" },
  { key: "Total Leads",         icon: "🎯", bg: "bg-emerald-600", label: "text-emerald-100", val: "text-white",        sub: "Leads generated" },
  { key: "Blended CPL ($)",     icon: "📉", bg: "bg-violet-600",  label: "text-violet-100",  val: "text-white",        sub: "Spend ÷ leads" },
  { key: "Weighted CTR (%)",    icon: "👆", bg: "bg-sky-600",     label: "text-sky-100",     val: "text-white",        sub: "Clicks ÷ impressions" },
  { key: "Conversion Rate (%)", icon: "🔄", bg: "bg-amber-500",   label: "text-amber-100",   val: "text-white",        sub: "Leads ÷ clicks" },
  { key: "Total Clicks",        icon: "🖱️", bg: "bg-slate-700",   label: "text-slate-300",   val: "text-white",        sub: "Total clicks" },
  { key: "Total Impressions",   icon: "👁️", bg: "bg-slate-700",   label: "text-slate-300",   val: "text-white",        sub: "Total reach" },
  { key: "ROAS",                icon: "📈", bg: "bg-rose-600",    label: "text-rose-100",    val: "text-white",        sub: "Revenue ÷ spend" },
] as const;

function fmt(key: string, val: number | string): string {
  if (typeof val === "string") return val;
  if (key === "ROAS") return val === 0 ? "N/A" : `${val.toFixed(2)}x`;
  if (key.includes("$")) return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  if (key.includes("%")) return `${val.toFixed(2)}%`;
  return val.toLocaleString();
}

export default function KpiCards({ kpis }: { kpis: KPIs }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {CARDS.map(({ key, icon, bg, label, val: valCls, sub }) => {
        const value = kpis[key as keyof KPIs];
        return (
          <div key={key} className={`${bg} rounded-xl p-4 shadow-sm`}>
            <div className={`text-xs font-semibold ${label} mb-1`}>{icon} {key}</div>
            <div className={`text-2xl font-bold ${valCls} tracking-tight`}>{fmt(key, value)}</div>
            <div className={`text-xs ${label} mt-1`}>{sub}</div>
          </div>
        );
      })}
    </div>
  );
}
