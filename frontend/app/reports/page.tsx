"use client";
import { useState } from "react";
import { useAppState } from "@/lib/store";
import { api } from "@/lib/api";
import { Download, Send, Loader2 } from "lucide-react";

export default function ReportsPage() {
  const { data, clientName } = useAppState();
  const [senderEmail, setSenderEmail] = useState("");
  const [senderPass, setSenderPass] = useState("");
  const [recipient, setRecipient] = useState("");
  const [emailStatus, setEmailStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [emailLoading, setEmailLoading] = useState(false);

  async function handleEmail() {
    if (!senderEmail || !senderPass || !recipient) {
      return setEmailStatus({ ok: false, msg: "All email fields are required." });
    }
    setEmailLoading(true); setEmailStatus(null);
    try {
      const res = await api.sendEmail({
        client_name: clientName || "Client",
        sender_email: senderEmail,
        sender_password: senderPass,
        recipient_email: recipient,
      });
      setEmailStatus({ ok: true, msg: (res as { message: string }).message });
    } catch (e: unknown) {
      setEmailStatus({ ok: false, msg: e instanceof Error ? e.message : "Failed to send email" });
    } finally {
      setEmailLoading(false);
    }
  }

  if (!data) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p className="text-4xl mb-3">📄</p>
        <p className="text-sm">Upload data on the Dashboard first</p>
      </div>
    );
  }

  const name = clientName || "Client";

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports & Email</h1>
        <p className="text-sm text-gray-500 mt-1">Download PDF reports or send them directly to clients</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Downloads */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">📄 Download Reports</h2>

          <a href={api.reportStandardUrl(name)} target="_blank" rel="noreferrer"
            className="flex items-center gap-3 w-full border border-gray-300 hover:border-indigo-400 hover:bg-indigo-50 rounded-lg px-4 py-3 text-sm font-medium text-gray-700 hover:text-indigo-700 transition-colors">
            <Download size={16} />
            Standard Report (PDF)
          </a>

          <a href={api.reportGrowthUrl(name)} target="_blank" rel="noreferrer"
            className="flex items-center gap-3 w-full bg-indigo-600 hover:bg-indigo-700 rounded-lg px-4 py-3 text-sm font-semibold text-white transition-colors">
            <Download size={16} />
            AI Growth Strategy Report (PDF)
          </a>

          <p className="text-xs text-gray-400">Reports are generated from the currently loaded data for <strong>{name}</strong>.</p>
        </div>

        {/* Email */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">📧 Email Report</h2>

          {[
            { label: "Your Gmail Address", value: senderEmail, set: setSenderEmail, placeholder: "you@gmail.com", type: "email" },
            { label: "Gmail App Password", value: senderPass, set: setSenderPass, placeholder: "xxxx xxxx xxxx xxxx", type: "password" },
            { label: "Recipient Email", value: recipient, set: setRecipient, placeholder: "client@example.com", type: "email" },
          ].map(({ label, value, set, placeholder, type }) => (
            <div key={label}>
              <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
              <input type={type} value={value} onChange={e => set(e.target.value)} placeholder={placeholder}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
            </div>
          ))}

          <p className="text-xs text-gray-400">
            Generate an App Password at{" "}
            <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="text-indigo-500 underline">
              myaccount.google.com → Security → App Passwords
            </a>
          </p>

          <button onClick={handleEmail} disabled={emailLoading}
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-900 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
            {emailLoading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            {emailLoading ? "Sending…" : "Send AI Growth Report"}
          </button>

          {emailStatus && (
            <div className={`text-sm px-4 py-3 rounded-lg border ${emailStatus.ok ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"}`}>
              {emailStatus.ok ? "✅" : "❌"} {emailStatus.msg}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
