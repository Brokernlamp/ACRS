"use client";
import { useRef, useState } from "react";
import { Upload, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAppState } from "@/lib/store";

export default function UploadPanel() {
  const { setData, setClientName, clientName, setLoading, loading, setError } = useAppState();
  const [localClient, setLocalClient] = useState(clientName);
  const [fileName, setFileName] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleUpload() {
    if (!file) return setError("Please select a CSV file.");
    if (!localClient.trim()) return setError("Please enter a client name.");
    setLoading(true);
    setError(null);
    try {
      const result = await api.upload(file, localClient.trim());
      setData(result);
      setClientName(localClient.trim());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 flex flex-col sm:flex-row gap-4 items-end">
      <div className="flex-1">
        <label className="block text-xs font-medium text-gray-600 mb-1">Client Name</label>
        <input
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          placeholder="e.g. Acme Corp"
          value={localClient}
          onChange={(e) => setLocalClient(e.target.value)}
        />
      </div>
      <div className="flex-1">
        <label className="block text-xs font-medium text-gray-600 mb-1">Campaign CSV</label>
        <button
          onClick={() => inputRef.current?.click()}
          className="w-full border border-dashed border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors text-left"
        >
          {fileName ?? "📂 Choose CSV file…"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0] ?? null;
            setFile(f);
            setFileName(f?.name ?? null);
          }}
        />
      </div>
      <button
        onClick={handleUpload}
        disabled={loading}
        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2 rounded-lg transition-colors"
      >
        {loading ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />}
        {loading ? "Processing…" : "Activate Engine"}
      </button>
    </div>
  );
}
