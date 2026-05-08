"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";

interface LicenseStatus {
  valid: boolean;
  expiresAt: string | null;
  machineId: string | null;
  email: string | null;
  plan: string | null;
  token: string | null; // raw JWT — forwarded to backend for Gemini proxy
}

const DEFAULT: LicenseStatus = {
  valid: false, expiresAt: null, machineId: null, email: null, plan: null, token: null,
};

const LicenseCtx = createContext<LicenseStatus>(DEFAULT);

export function useLicense() {
  return useContext(LicenseCtx);
}

declare global {
  interface Window {
    electron?: {
      license: {
        status: () => Promise<Omit<LicenseStatus, "token">>;
      };
    };
  }
}

export function LicenseProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<LicenseStatus>(DEFAULT);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // No window.electron means running in web/browser mode — skip license gate
    if (typeof window === "undefined" || !window.electron) {
      setStatus({ valid: true, expiresAt: null, machineId: null, email: null, plan: null, token: null });
      return;
    }

    async function refresh() {
      const s = await window.electron!.license.status();
      setStatus({ ...s, token: null });
    }

    refresh();
    const t = setInterval(refresh, 5 * 60 * 1000);
    return () => clearInterval(t);
  }, []);

  // Block overlay — only after mount (avoids SSR window access) and only in Electron
  if (mounted && typeof window !== "undefined" && window.electron && !status.valid && status.machineId !== null) {
    return (
      <div className="fixed inset-0 z-[99999] bg-slate-900 flex flex-col items-center justify-center text-white">
        <div className="text-5xl mb-4">🔒</div>
        <h1 className="text-2xl font-bold mb-2">Subscription Ended</h1>
        <p className="text-slate-400 text-sm text-center max-w-sm">
          Your license has expired or been deactivated.<br />
          Please renew your subscription to continue.
        </p>
      </div>
    );
  }

  return <LicenseCtx.Provider value={status}>{children}</LicenseCtx.Provider>;
}
