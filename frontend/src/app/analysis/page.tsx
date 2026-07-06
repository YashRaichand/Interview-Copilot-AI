"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import { Target, ArrowRight, Plus, FileText } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { analysisApi } from "@/lib/api";
import { format } from "date-fns";

function getGradeColor(score: number) {
  if (score >= 85) return "#10b981";
  if (score >= 70) return "#3b82f6";
  if (score >= 55) return "#f59e0b";
  return "#ef4444";
}

export default function AnalysisListPage() {
  const { data: analyses, isLoading } = useQuery({ queryKey: ["analyses"], queryFn: analysisApi.list });

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div><h1 className="text-3xl font-bold text-white mb-1">ATS Analyses</h1><p className="text-slate-500 text-sm">All your resume-to-job analyses</p></div>
          <Link href="/upload" className="btn-gradient px-5 py-2.5 text-sm rounded-xl flex items-center gap-2"><Plus className="w-4 h-4" /> New Analysis</Link>
        </div>

        {isLoading ? (
          <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-24 rounded-2xl" />)}</div>
        ) : analyses && analyses.length > 0 ? (
          <div className="space-y-4">
            {analyses.map((analysis, i) => (
              <motion.div key={analysis.id} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <Link href={`/analysis/${analysis.id}`} className="glass-card-hover p-5 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center font-bold text-lg" style={{ background: `${getGradeColor(analysis.ats_score ?? 0)}15`, color: getGradeColor(analysis.ats_score ?? 0), border: `1px solid ${getGradeColor(analysis.ats_score ?? 0)}30` }}>
                      {Math.round(analysis.ats_score ?? 0)}
                    </div>
                    <div>
                      <div className="text-white font-medium">ATS Score: {analysis.ats_score?.toFixed(0)}/100</div>
                      <div className="text-sm text-slate-500">Skill Match: {analysis.skill_match_percentage?.toFixed(0)}% • {format(new Date(analysis.created_at), "MMM d, yyyy")}</div>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-slate-600" />
                </Link>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="glass-card p-16 text-center">
            <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-white font-medium mb-2">No analyses yet</h3>
            <p className="text-slate-500 text-sm mb-6">Upload a resume and job description to get your first ATS score</p>
            <Link href="/upload" className="btn-gradient px-6 py-3 rounded-xl inline-flex items-center gap-2"><FileText className="w-4 h-4" /> Get Started</Link>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
