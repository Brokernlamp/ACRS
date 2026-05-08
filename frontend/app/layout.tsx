import type { Metadata } from "next";
import "./globals.css";
import { AppProvider } from "@/lib/store";
import { LicenseProvider } from "@/lib/license";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "AI Growth Operator",
  description: "Marketing analytics platform for agencies",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-100 text-gray-900 antialiased">
        <LicenseProvider>
          <AppProvider>
            <div className="flex h-screen overflow-hidden">
              <Sidebar />
              <main className="flex-1 overflow-y-auto p-6 bg-slate-100">{children}</main>
            </div>
          </AppProvider>
        </LicenseProvider>
      </body>
    </html>
  );
}
