"use client";
import { createContext, useContext, useState, ReactNode } from "react";
import { AnalyticsResult } from "./api";

interface AppState {
  data: AnalyticsResult | null;
  clientId: number | null;
  clientName: string;
  loading: boolean;
  error: string | null;
  setData: (d: AnalyticsResult) => void;
  setClientId: (id: number | null) => void;
  setClientName: (n: string) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  clearData: () => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<AnalyticsResult | null>(null);
  const [clientId, setClientId] = useState<number | null>(null);
  const [clientName, setClientName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function clearData() {
    setData(null);
    setClientId(null);
    setClientName("");
    setError(null);
  }

  return (
    <Ctx.Provider value={{
      data, clientId, clientName, loading, error,
      setData, setClientId, setClientName, setLoading, setError, clearData,
    }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAppState must be used inside AppProvider");
  return ctx;
}
