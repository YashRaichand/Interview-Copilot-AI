"use client";

import { motion } from "framer-motion";

interface SkillMatchBarProps {
  percentage: number;
}

export function SkillMatchBar({ percentage }: SkillMatchBarProps) {
  const clamped = Math.min(100, Math.max(0, percentage));
  const color = clamped >= 70 ? "#10b981" : clamped >= 45 ? "#f59e0b" : "#ef4444";

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <span className="text-3xl font-bold text-white">{Math.round(clamped)}%</span>
        <span className="text-sm text-slate-500 mb-1">skills matched</span>
      </div>
      <div className="h-3 bg-white/5 rounded-full overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${clamped}%` }} transition={{ duration: 1, ease: "easeOut" }} className="h-full rounded-full" style={{ background: `linear-gradient(90deg, #7c3aed, ${color})` }} />
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div><div className="w-2 h-2 rounded-full bg-green-500 mx-auto mb-1" /><span className="text-xs text-slate-500">Strong (70%+)</span></div>
        <div><div className="w-2 h-2 rounded-full bg-yellow-500 mx-auto mb-1" /><span className="text-xs text-slate-500">Fair (45-70%)</span></div>
        <div><div className="w-2 h-2 rounded-full bg-red-500 mx-auto mb-1" /><span className="text-xs text-slate-500">Weak (&lt;45%)</span></div>
      </div>
    </div>
  );
}
