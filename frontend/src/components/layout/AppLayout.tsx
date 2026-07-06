"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { LayoutDashboard, Upload, Target, MessageSquare, Map, FileBarChart, Settings, User, LogOut, Brain, Menu, X, ChevronDown, Bell } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/analysis", label: "ATS Analysis", icon: Target },
  { href: "/interview", label: "Mock Interview", icon: MessageSquare },
  { href: "/roadmap", label: "Roadmap", icon: Map },
  { href: "/reports", label: "Reports", icon: FileBarChart },
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const { data: user } = useQuery({ queryKey: ["current-user"], queryFn: authApi.getMe, retry: false });

  useEffect(() => {
    if (!authApi.isAuthenticated()) {
      router.push("/login");
    }
  }, [router]);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } finally {
      authApi.clearTokens();
      router.push("/login");
    }
  };

  return (
    <div className="min-h-screen bg-surface-1 flex">
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
        )}
      </AnimatePresence>

      <aside className={`fixed lg:sticky top-0 left-0 h-screen w-64 bg-surface-2 border-r border-white/5 z-50 transform transition-transform duration-300 flex flex-col ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        <div className="flex items-center justify-between px-5 py-5 border-b border-white/5">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-brand flex items-center justify-center shadow-glow-sm">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="text-white font-bold text-sm">Interview Copilot</span>
          </Link>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all relative ${isActive ? "text-white bg-gradient-to-r from-brand-600/20 to-accent-500/10 border border-brand-500/20" : "text-slate-400 hover:text-white hover:bg-white/5"}`}
              >
                {isActive && <motion.div layoutId="activeNavIndicator" className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-gradient-brand rounded-full" />}
                <item.icon className="w-4.5 h-4.5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-3 py-4 border-t border-white/5 space-y-1">
          <Link href="/settings" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-all">
            <Settings className="w-4.5 h-4.5" /> Settings
          </Link>
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/5 transition-all">
            <LogOut className="w-4.5 h-4.5" /> Logout
          </button>
        </div>
      </aside>

      <div className="flex-1 min-w-0">
        <header className="sticky top-0 z-30 bg-surface-1/80 backdrop-blur-xl border-b border-white/5">
          <div className="flex items-center justify-between px-4 lg:px-8 py-4">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-slate-400">
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex-1" />
            <div className="flex items-center gap-4">
              <button className="relative text-slate-400 hover:text-white transition-colors">
                <Bell className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-brand-500 rounded-full" />
              </button>
              <div className="relative">
                <button onClick={() => setProfileOpen(!profileOpen)} className="flex items-center gap-2 hover:bg-white/5 px-2 py-1.5 rounded-xl transition-colors">
                  <div className="w-8 h-8 rounded-full bg-gradient-brand flex items-center justify-center text-white text-sm font-semibold">
                    {user?.full_name?.charAt(0)?.toUpperCase() || <User className="w-4 h-4" />}
                  </div>
                  <span className="text-sm text-slate-300 hidden md:block">{user?.full_name || "..."}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                </button>
                <AnimatePresence>
                  {profileOpen && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="absolute right-0 mt-2 w-48 glass-card border border-white/10 shadow-card py-1 z-50">
                      <Link href="/profile" className="block px-4 py-2 text-sm text-slate-300 hover:bg-white/5">Profile</Link>
                      <Link href="/settings" className="block px-4 py-2 text-sm text-slate-300 hover:bg-white/5">Settings</Link>
                      <div className="border-t border-white/5 my-1" />
                      <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/5">Logout</button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </header>
        <main className="page-enter">{children}</main>
      </div>
    </div>
  );
}
