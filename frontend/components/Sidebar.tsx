"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, Brain, Users, FileText, Zap, MessageSquare, Settings, Layers, Globe } from "lucide-react";

const nav = [
  { href: "/",           label: "Dashboard",          icon: BarChart2 },
  { href: "/ai-engine",  label: "AI Growth Engine",   icon: Brain },
  { href: "/platforms",  label: "Platform Connections", icon: Globe },
  { href: "/campaign-groups", label: "Campaign Groups", icon: Layers },
  { href: "/clients",    label: "Clients",             icon: Users },
  { href: "/reports",    label: "Reports & Email",     icon: FileText },
  { href: "/chatbot",    label: "AI Chatbot",          icon: MessageSquare },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-56 bg-slate-900 flex flex-col shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-slate-700">
        <div className="w-7 h-7 bg-indigo-500 rounded-lg flex items-center justify-center">
          <Zap size={15} className="text-white" />
        </div>
        <span className="font-bold text-white text-sm leading-tight">AI Growth<br />Operator</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = path === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Settings + version */}
      <div className="px-3 pb-4 space-y-0.5 border-t border-slate-700 pt-3">
        <Link
          href="/settings"
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            path === "/settings"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:bg-slate-800 hover:text-white"
          }`}
        >
          <Settings size={16} />
          Settings
        </Link>
        <div className="px-3 pt-2 text-xs text-slate-600">v0.3.0-alpha</div>
      </div>
    </aside>
  );
}
