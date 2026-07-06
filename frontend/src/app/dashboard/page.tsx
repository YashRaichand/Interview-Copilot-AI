"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import { Target, Brain, FileText, TrendingUp, Map, Plus, ArrowRight, Clock, CheckCircle2, XCircle, Loader2, BarChart2, AlertCircle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import { dashboardApi, type DashboardStats } from "@/lib/api";
import { AppLayout } from "@/components/layout/AppLayout";
import { ATSGauge } from "@/components/charts/ATSGauge";
import { SkillMatchBar } from "@/components/charts/SkillMatchBar";
import { format } from "date-fns";

function StatCardSkeleton() {
  return <div className="glass-card p-6 skeleton h-32" />;
}

function StatCard({ icon: Icon, label, value, sub, color, href }: { icon: React.ElementType; label: string; value: string | number; sub?: string; color: string; href?: string }) {
  const Wrapper: any = href ? Link : "div";
  return (
    <Wrapper href={href as string} className="glass-card-hover p-6 flex flex-col gap-3 cursor-pointer group">
      <div className="flex items-center justify-between">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}20`, border: `1px solid ${color}30` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        {href && <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-colors" />}
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm text-slate-500">{label}</div>
        {sub && <div className="text-xs text-slate-600 mt-0.5">{sub}</div>}
      </div>
    </Wrapper>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config = ({
    completed: { label: "Completed", icon: CheckCircle2, className: "badge-low" },
    active: { label: "Active", icon: Loader2, className: "badge-brand" },
    pending: { label: "Pending", icon: Clock, className: "badge-medium" },
    cancelled: { label: "Cancelled", icon: XCircle, className: "badge-high" },
  } as any)[status] || { label: status, icon: AlertCircle, className: "badge-medium" };

  return (
    <span className={`badge ${config.className} text-xs`}>
      <config.icon className="w-3 h-3" /> {config.label}
    </span>
  );
}

function ATSTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card px-3 py-2 text-sm shadow-card border border-white/10">
      <p className="text-slate-400 text-xs mb-1">{label}</p>
      <p className="text-white font-semibold">Score: {payload[0].value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery<DashboardStats>({ queryKey: ["dashboard-stats"], queryFn: dashboardApi.getStats, refetchInterval: 30000 });

  const fadeUp = (delay: number) => ({ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { delay, duration: 0.4 } });

  if (error) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-64 text-slate-400">
          <AlertCircle className="w-6 h-6 mr-2" /> Failed to load dashboard stats. Please refresh.
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        <motion.div {...fadeUp(0)} className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-1">Dashboard</h1>
            <p className="text-slate-500 text-sm">{new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</p>
          </div>
          <Link href="/upload" className="btn-gradient px-5 py-2.5 text-sm rounded-xl flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Analysis
          </Link>
        </motion.div>

        <motion.div {...fadeUp(0.05)} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {isLoading ? (
            [...Array(4)].map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard icon={FileText} label="Total Resumes" value={stats?.total_resumes ?? 0} color="#7c3aed" href="/upload" />
              <StatCard icon={Target} label="ATS Analyses" value={stats?.total_analyses ?? 0} color="#06b6d4" href="/analysis" />
              <StatCard icon={Brain} label="Mock Interviews" value={stats?.total_interviews ?? 0} color="#10b981" href="/interview" />
              <StatCard icon={TrendingUp} label="Success Probability" value={stats?.success_probability ? `${(stats.success_probability * 100).toFixed(0)}%` : "—"} color="#f59e0b" sub={stats?.success_probability ? "of passing interview" : "Run an analysis first"} />
            </>
          )}
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          <motion.div {...fadeUp(0.1)} className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white">ATS Score</h2>
              <span className="text-xs text-slate-500">Latest analysis</span>
            </div>
            {isLoading ? (
              <div className="skeleton h-48 rounded-2xl" />
            ) : stats?.latest_ats_score !== undefined ? (
              <>
                <ATSGauge score={stats.latest_ats_score} size={180} />
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <div className="glass-card p-3 text-center"><div className="text-lg font-bold text-white">{stats.best_ats_score?.toFixed(0) ?? "—"}</div><div className="text-xs text-slate-500">Best Score</div></div>
                  <div className="glass-card p-3 text-center"><div className="text-lg font-bold text-white">{stats.average_ats_score?.toFixed(0) ?? "—"}</div><div className="text-xs text-slate-500">Average</div></div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <Target className="w-10 h-10 text-slate-600 mb-3" />
                <p className="text-slate-500 text-sm">No analysis yet</p>
                <Link href="/upload" className="btn-gradient px-4 py-2 text-xs rounded-xl mt-3">Start Analysis</Link>
              </div>
            )}
          </motion.div>

          <motion.div {...fadeUp(0.15)} className="glass-card p-6 lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white">ATS Score Trend</h2>
              <BarChart2 className="w-4 h-4 text-slate-500" />
            </div>
            {isLoading ? (
              <div className="skeleton h-48 rounded-2xl" />
            ) : stats?.ats_trend && stats.ats_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={stats.ats_trend}>
                  <defs>
                    <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#7c3aed" /><stop offset="100%" stopColor="#06b6d4" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<ATSTooltip />} />
                  <Line type="monotone" dataKey="score" stroke="url(#lineGradient)" strokeWidth={2.5} dot={{ fill: "#7c3aed", strokeWidth: 2, r: 4 }} activeDot={{ fill: "#06b6d4", r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <BarChart2 className="w-10 h-10 text-slate-600 mb-3" />
                <p className="text-slate-500 text-sm">Complete analyses to see your trend</p>
              </div>
            )}
          </motion.div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <motion.div {...fadeUp(0.2)} className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Skill Coverage</h2>
            {isLoading ? (
              <div className="skeleton h-40 rounded-2xl" />
            ) : stats?.latest_skill_match !== undefined ? (
              <SkillMatchBar percentage={stats.latest_skill_match} />
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-center"><p className="text-slate-500 text-sm">No skill data yet</p></div>
            )}
            {stats?.missing_skills_summary && stats.missing_skills_summary.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-xs text-slate-500 mb-2">Top missing skills:</p>
                {stats.missing_skills_summary.slice(0, 4).map((skill) => (
                  <div key={skill} className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-400 flex-shrink-0" /><span className="text-sm text-slate-300">{skill}</span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          <motion.div {...fadeUp(0.25)} className="glass-card p-6 lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Recent Interviews</h2>
              <Link href="/interview" className="text-sm text-brand-400 hover:text-brand-300 flex items-center gap-1">View all <ArrowRight className="w-3.5 h-3.5" /></Link>
            </div>
            {isLoading ? (
              <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}</div>
            ) : stats?.recent_interviews && stats.recent_interviews.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_interviews.map((interview) => (
                  <Link key={interview.id} href={`/interview/${interview.id}`} className="flex items-center justify-between p-3 glass-card hover:bg-white/5 transition-colors rounded-xl group">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-xl bg-brand-600/20 flex items-center justify-center"><Brain className="w-4 h-4 text-brand-400" /></div>
                      <div>
                        <div className="text-sm font-medium text-white">{interview.title}</div>
                        <div className="text-xs text-slate-500">{interview.answered_questions}/{interview.total_questions} questions • {format(new Date(interview.created_at), "MMM d")}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {interview.overall_score !== undefined && interview.overall_score !== null && <span className="text-sm font-bold text-white">{interview.overall_score.toFixed(1)}<span className="text-slate-500 text-xs">/10</span></span>}
                      <StatusBadge status={interview.status} />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-center">
                <Brain className="w-10 h-10 text-slate-600 mb-3" />
                <p className="text-slate-500 text-sm mb-3">No interviews yet</p>
                <Link href="/interview" className="btn-gradient px-4 py-2 text-xs rounded-xl">Start Mock Interview</Link>
              </div>
            )}
          </motion.div>
        </div>

        {stats?.active_roadmap && (
          <motion.div {...fadeUp(0.3)} className="glass-card p-6 border border-brand-600/20">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-brand flex items-center justify-center shadow-glow-sm"><Map className="w-5 h-5 text-white" /></div>
                <div>
                  <h2 className="text-lg font-semibold text-white">{stats.active_roadmap.title}</h2>
                  <p className="text-xs text-slate-500">30-day preparation roadmap</p>
                </div>
              </div>
              <Link href="/roadmap" className="btn-outline px-4 py-2 text-sm rounded-xl">View Roadmap</Link>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm mb-2"><span className="text-slate-400">Overall Progress</span><span className="text-white font-medium">{stats.active_roadmap.progress_percentage.toFixed(0)}%</span></div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${stats.active_roadmap.progress_percentage}%` }} transition={{ duration: 1, ease: "easeOut" }} className="h-full rounded-full bg-gradient-brand" />
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </AppLayout>
  );
}
