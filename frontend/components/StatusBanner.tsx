"use client";
import { useAppState } from "@/lib/store";
import { X } from "lucide-react";

export default function StatusBanner() {
  const { error, setError } = useAppState();
  if (!error) return null;
  return (
    <div className="flex items-center justify-between bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
      <span>⚠️ {error}</span>
      <button onClick={() => setError(null)}><X size={14} /></button>
    </div>
  );
}
