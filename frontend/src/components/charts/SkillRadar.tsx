"use client";

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";

interface SkillRadarProps {
  data: Array<{ category: string; matched: number; total: number }>;
}

function RadarTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="glass-card px-3 py-2 text-sm shadow-card border border-white/10">
      <p className="text-white font-medium">{item.category}</p>
      <p className="text-slate-400 text-xs">{item.matched}% coverage</p>
    </div>
  );
}

export function SkillRadar({ data }: SkillRadarProps) {
  const chartData = data.map((d) => ({ category: d.category, matched: d.total > 0 ? Math.round((d.matched / d.total) * 100) : 0 }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={chartData}>
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis dataKey="category" tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} />
        <Radar name="Skill Match" dataKey="matched" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.25} strokeWidth={2} />
        <Tooltip content={<RadarTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
