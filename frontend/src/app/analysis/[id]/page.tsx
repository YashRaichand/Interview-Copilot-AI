"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { AlertTriangle, CheckCircle2, Lightbulb, Brain, Map, TrendingUp, ArrowRight, Loader2 } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { ATSGauge } from "@/components/charts/ATSGauge";
import { analysisApi, roadmapApi, interviewApi } from "@/lib/api";

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5"><span className="text-slate-400">{label}</span><span className="text-white font-medium">{value.toFixed(0)}%</span></div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 0.8, ease: "easeOut" }} className="h-full rounded-full" style={{ background: color }} />
      </div>
    </div>
  );
}

const PRIORITY_STYLES: Record<string, { badge: string; label: string }> = {
  high: { badge: "badge-high", label: "High Priority" },
  medium: { badge: "badge-medium", label: "Medium Priority" },
  low: { badge: "badge-low", label: "Low Priority" },
};

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = params.id as string;

  const { data: analysis, isLoading } = useQuery({ queryKey: ["analysis", analysisId], queryFn: () => analysisApi.get(analysisId), enabled: !!analysisId });

  const roadmapMutation = useMutation({
    mutationFn: () => roadmapApi.generate(analysisId),
    onSuccess: () => { toast.success("Roadmap generated!"); router.push("/roadmap"); },
    onError: () => toast.error("Failed to generate roadmap"),
  });

  const interviewMutation = useMutation({
    mutationFn: () => interviewApi.create({ analysis_id: analysisId, interview_type: "mixed", num_questions: 10 }),
    onSuccess: (data) => { toast.success("Mock interview created!"); router.push(`/interview/${data.id}`); },
    onError: () => toast.error("Failed to create interview"),
  });

  if (isLoading) {
    return (
      <AppLayout>
        <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
          <div className="skeleton h-64 rounded-2xl" />
          <div className="skeleton h-48 rounded-2xl" />
        </div>
      </AppLayout>
    );
  }

  if (!analysis) {
    return (
      <AppLayout>
        <div className="flex flex-col items-center justify-center h-64"><AlertTriangle className="w-10 h-10 text-slate-600 mb-3" /><p className="text-slate-400">Analysis not found</p></div>
      </AppLayout>
    );
  }

  const breakdown = analysis.score_breakdown;

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">ATS Analysis Results</h1>
          <p className="text-slate-500 text-sm">Generated {new Date(analysis.created_at).toLocaleDateString()}</p>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-8 grid md:grid-cols-2 gap-8 items-center">
          <div className="flex justify-center"><ATSGauge score={analysis.ats_score ?? 0} size={220} /></div>
          <div className="space-y-4">
            {breakdown && (
              <>
                <ScoreBar label="Keyword Match" value={breakdown.keyword_match} color="linear-gradient(90deg,#7c3aed,#a78bfa)" />
                <ScoreBar label="Semantic Similarity" value={breakdown.semantic_similarity} color="linear-gradient(90deg,#06b6d4,#67e8f9)" />
                <ScoreBar label="Skill Match" value={breakdown.skill_match} color="linear-gradient(90deg,#10b981,#34d399)" />
                <ScoreBar label="Experience Match" value={breakdown.experience_match} color="linear-gradient(90deg,#f59e0b,#fbbf24)" />
              </>
            )}
          </div>
        </motion.div>

        {analysis.success_probability !== undefined && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-brand-600/15 flex items-center justify-center"><TrendingUp className="w-6 h-6 text-brand-400" /></div>
              <div><h3 className="text-white font-semibold">Interview Success Probability</h3><p className="text-sm text-slate-500">Based on ATS score and skill match</p></div>
            </div>
            <div className="text-3xl font-bold gradient-text">{((analysis.success_probability ?? 0) * 100).toFixed(0)}%</div>
          </motion.div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4"><AlertTriangle className="w-5 h-5 text-amber-400" /><h3 className="text-white font-semibold">Missing Skills</h3></div>
            {analysis.missing_skills && analysis.missing_skills.length > 0 ? (
              <div className="space-y-3">
                {analysis.missing_skills.map((skill, i) => {
                  const style = PRIORITY_STYLES[skill.priority] || PRIORITY_STYLES.low;
                  return (
                    <div key={i} className="flex items-start justify-between gap-3 p-3 bg-white/3 rounded-xl">
                      <div><div className="text-sm font-medium text-white">{skill.skill}</div><div className="text-xs text-slate-500 mt-0.5">{skill.category}</div></div>
                      <span className={`badge ${style.badge} text-xs flex-shrink-0`}>{skill.priority}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-slate-500">No missing skills detected — great match!</p>
            )}
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4"><CheckCircle2 className="w-5 h-5 text-green-400" /><h3 className="text-white font-semibold">Matching Skills</h3></div>
            {analysis.matching_skills && analysis.matching_skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">{analysis.matching_skills.map((skill) => <span key={skill} className="badge badge-low text-xs">{skill}</span>)}</div>
            ) : (
              <p className="text-sm text-slate-500">No matching skills found.</p>
            )}
          </motion.div>
        </div>

        {analysis.recommendations && analysis.recommendations.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4"><Lightbulb className="w-5 h-5 text-yellow-400" /><h3 className="text-white font-semibold">Recommendations</h3></div>
            <div className="space-y-3">
              {analysis.recommendations.map((rec, i) => (
                <div key={i} className="flex gap-3">
                  <div className="w-5 h-5 rounded-full bg-brand-600/20 text-brand-400 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{i + 1}</div>
                  <p className="text-sm text-slate-300 leading-relaxed">{rec}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="grid sm:grid-cols-2 gap-4">
          <button onClick={() => interviewMutation.mutate()} disabled={interviewMutation.isPending} className="glass-card-hover p-5 flex items-center justify-between group">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-600/15 flex items-center justify-center"><Brain className="w-5 h-5 text-brand-400" /></div>
              <div className="text-left"><div className="text-white font-medium text-sm">Start Mock Interview</div><div className="text-xs text-slate-500">10 AI-generated questions</div></div>
            </div>
            {interviewMutation.isPending ? <Loader2 className="w-4 h-4 text-slate-400 animate-spin" /> : <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-white transition-colors" />}
          </button>

          <button onClick={() => roadmapMutation.mutate()} disabled={roadmapMutation.isPending} className="glass-card-hover p-5 flex items-center justify-between group">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-accent-500/15 flex items-center justify-center"><Map className="w-5 h-5 text-accent-400" /></div>
              <div className="text-left"><div className="text-white font-medium text-sm">Generate Roadmap</div><div className="text-xs text-slate-500">30-day preparation plan</div></div>
            </div>
            {roadmapMutation.isPending ? <Loader2 className="w-4 h-4 text-slate-400 animate-spin" /> : <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-white transition-colors" />}
          </button>
        </motion.div>
      </div>
    </AppLayout>
  );
}
