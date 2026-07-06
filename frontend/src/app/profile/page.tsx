"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { User, Award, FileText, Brain, TrendingUp } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { authApi, dashboardApi } from "@/lib/api";
import { format } from "date-fns";

export default function ProfilePage() {
  const { data: user } = useQuery({ queryKey: ["current-user"], queryFn: authApi.getMe });
  const { data: stats } = useQuery({ queryKey: ["dashboard-stats"], queryFn: dashboardApi.getStats });

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-8 text-center">
          <div className="w-20 h-20 rounded-full bg-gradient-brand flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-glow-brand">
            {user?.full_name?.charAt(0)?.toUpperCase() || <User className="w-8 h-8" />}
          </div>
          <h1 className="text-2xl font-bold text-white">{user?.full_name}</h1>
          <p className="text-slate-500 text-sm">{user?.email}</p>
          <p className="text-xs text-slate-600 mt-2">Member since {user?.created_at ? format(new Date(user.created_at), "MMMM yyyy") : "—"}</p>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { icon: FileText, label: "Resumes", value: stats?.total_resumes ?? 0, color: "#7c3aed" },
            { icon: TrendingUp, label: "Analyses", value: stats?.total_analyses ?? 0, color: "#06b6d4" },
            { icon: Brain, label: "Interviews", value: stats?.total_interviews ?? 0, color: "#10b981" },
            { icon: Award, label: "Best Score", value: stats?.best_ats_score?.toFixed(0) ?? "—", color: "#f59e0b" },
          ].map((stat) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-4 text-center">
              <stat.icon className="w-5 h-5 mx-auto mb-2" style={{ color: stat.color }} />
              <div className="text-xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-slate-500">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
