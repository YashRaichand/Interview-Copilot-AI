"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

interface ATSGaugeProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
}

function getGradeInfo(score: number) {
  if (score >= 85) return { grade: "A", label: "Excellent", color: "#10b981" };
  if (score >= 70) return { grade: "B", label: "Good", color: "#3b82f6" };
  if (score >= 55) return { grade: "C", label: "Average", color: "#f59e0b" };
  if (score >= 40) return { grade: "D", label: "Below Average", color: "#f97316" };
  return { grade: "F", label: "Poor", color: "#ef4444" };
}

export function ATSGauge({ score, size = 200, strokeWidth = 12, showLabel = true }: ATSGaugeProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.min(100, Math.max(0, score));
  const offset = circumference * (1 - clampedScore / 100);
  const gradeInfo = useMemo(() => getGradeInfo(clampedScore), [clampedScore]);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={strokeWidth} />
          <motion.circle
            cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="url(#atsGaugeGradient)" strokeWidth={strokeWidth} strokeLinecap="round"
            strokeDasharray={circumference} initial={{ strokeDashoffset: circumference }} animate={{ strokeDashoffset: offset }} transition={{ duration: 1.2, ease: "easeOut" }}
          />
          <defs>
            <linearGradient id="atsGaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#7c3aed" />
              <stop offset="100%" stopColor={gradeInfo.color} />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.4, duration: 0.4 }} className="text-4xl font-bold text-white">
            {Math.round(clampedScore)}
          </motion.span>
          {showLabel && <span className="text-xs text-slate-500 mt-1">ATS Score</span>}
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span className="px-3 py-1 rounded-full text-xs font-semibold" style={{ background: `${gradeInfo.color}20`, color: gradeInfo.color, border: `1px solid ${gradeInfo.color}30` }}>
          Grade {gradeInfo.grade} — {gradeInfo.label}
        </span>
      </div>
    </div>
  );
}
