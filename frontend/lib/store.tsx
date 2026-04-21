"use client";
import { createContext, useContext, useState, ReactNode } from "react";
import { AnalyticsResult } from "./api";

interface AppState {
  data: AnalyticsResult | null;
  clientName: string;
  loading: boolean;
  error: string | null;
  setData: (d: AnalyticsResult) => void;
  setClientName: (n: string) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<AnalyticsResult | null>(null);
  const [clientName, setClientName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <Ctx.Provider value={{ data, clientName, loading, error, setData, setClientName, setLoading, setError }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAppState must be used inside AppProvider");
  return ctx;
}
