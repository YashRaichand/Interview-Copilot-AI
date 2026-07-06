"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { User, Bell, Trash2 } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { authApi } from "@/lib/api";

export default function SettingsPage() {
  const { data: user } = useQuery({ queryKey: ["current-user"], queryFn: authApi.getMe });

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">
        <h1 className="text-3xl font-bold text-white mb-1">Settings</h1>
        <p className="text-slate-500 text-sm mb-6">Manage your account preferences</p>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4"><User className="w-5 h-5 text-brand-400" /><h2 className="text-white font-semibold">Profile</h2></div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div><label className="text-sm text-slate-400 mb-1.5 block">Full Name</label><input defaultValue={user?.full_name} className="input-dark w-full px-4 py-2.5 text-sm" /></div>
            <div><label className="text-sm text-slate-400 mb-1.5 block">Email</label><input defaultValue={user?.email} disabled className="input-dark w-full px-4 py-2.5 text-sm opacity-60" /></div>
          </div>
          <button className="btn-gradient px-5 py-2.5 text-sm rounded-xl mt-4">Save Changes</button>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4"><Bell className="w-5 h-5 text-accent-400" /><h2 className="text-white font-semibold">Notifications</h2></div>
          {["Email me about new features", "Weekly progress summary", "Interview reminders"].map((label) => (
            <div key={label} className="flex items-center justify-between py-2">
              <span className="text-sm text-slate-300">{label}</span>
              <div className="w-10 h-5 rounded-full bg-brand-600/40 relative cursor-pointer"><div className="absolute right-0.5 top-0.5 w-4 h-4 rounded-full bg-brand-400" /></div>
            </div>
          ))}
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6 border border-red-500/10">
          <div className="flex items-center gap-2 mb-4"><Trash2 className="w-5 h-5 text-red-400" /><h2 className="text-white font-semibold">Danger Zone</h2></div>
          <p className="text-sm text-slate-500 mb-4">Permanently delete your account and all associated data. This action cannot be undone.</p>
          <button className="border border-red-500/30 text-red-400 hover:bg-red-500/10 px-5 py-2.5 text-sm rounded-xl transition-colors">Delete Account</button>
        </motion.div>
      </div>
    </AppLayout>
  );
}
