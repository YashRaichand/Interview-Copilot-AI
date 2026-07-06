"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Brain, Plus, Loader2, X, MessageSquare, Code, Users, Briefcase } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { interviewApi } from "@/lib/api";
import { format } from "date-fns";

const INTERVIEW_TYPES = [
  { value: "mixed", label: "Mixed", icon: Brain },
  { value: "technical", label: "Technical", icon: Code },
  { value: "behavioral", label: "Behavioral", icon: Users },
  { value: "hr", label: "HR Round", icon: Briefcase },
];

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = { completed: "#10b981", active: "#7c3aed", pending: "#f59e0b", cancelled: "#ef4444" };
  return <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: colors[status] || "#64748b" }} />;
}

export default function InterviewListPage() {
  const router = useRouter();
  const [showNewModal, setShowNewModal] = useState(false);
  const [selectedType, setSelectedType] = useState("mixed");
  const [numQuestions, setNumQuestions] = useState(10);

  const { data: interviews, isLoading } = useQuery({ queryKey: ["interviews"], queryFn: interviewApi.list });

  const createMutation = useMutation({
    mutationFn: () => interviewApi.create({ interview_type: selectedType, num_questions: numQuestions }),
    onSuccess: (data) => { toast.success("Interview created!"); router.push(`/interview/${data.id}`); },
    onError: () => toast.error("Failed to create interview"),
  });

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div><h1 className="text-3xl font-bold text-white mb-1">Mock Interviews</h1><p className="text-slate-500 text-sm">Practice with AI-powered adaptive interviews</p></div>
          <button onClick={() => setShowNewModal(true)} className="btn-gradient px-5 py-2.5 text-sm rounded-xl flex items-center gap-2"><Plus className="w-4 h-4" /> New Interview</button>
        </div>

        {isLoading ? (
          <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-20 rounded-2xl" />)}</div>
        ) : interviews && interviews.length > 0 ? (
          <div className="space-y-3">
            {interviews.map((interview, i) => (
              <motion.div key={interview.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }} onClick={() => router.push(`/interview/${interview.id}`)} className="glass-card-hover p-5 flex items-center justify-between cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-2xl bg-brand-600/15 flex items-center justify-center"><Brain className="w-5 h-5 text-brand-400" /></div>
                  <div>
                    <div className="flex items-center gap-2"><span className="text-white font-medium">{interview.title}</span><StatusDot status={interview.status} /></div>
                    <div className="text-sm text-slate-500 capitalize">{interview.interview_type} • {interview.answered_questions}/{interview.total_questions} answered • {format(new Date(interview.created_at), "MMM d, yyyy")}</div>
                  </div>
                </div>
                {interview.overall_score !== undefined && interview.overall_score !== null ? (
                  <div className="text-right"><div className="text-xl font-bold text-white">{interview.overall_score.toFixed(1)}</div><div className="text-xs text-slate-500">/ 10</div></div>
                ) : (
                  <span className="badge badge-medium text-xs">In Progress</span>
                )}
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="glass-card p-16 text-center">
            <MessageSquare className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-white font-medium mb-2">No interviews yet</h3>
            <p className="text-slate-500 text-sm mb-6">Start your first AI mock interview to practice and improve</p>
            <button onClick={() => setShowNewModal(true)} className="btn-gradient px-6 py-3 rounded-xl inline-flex items-center gap-2"><Plus className="w-4 h-4" /> Start Interview</button>
          </div>
        )}

        {showNewModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass-card border border-white/10 p-6 w-full max-w-md">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white">New Mock Interview</h3>
                <button onClick={() => setShowNewModal(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
              </div>

              <p className="text-sm text-slate-400 mb-3">Interview Type</p>
              <div className="grid grid-cols-2 gap-3 mb-6">
                {INTERVIEW_TYPES.map((type) => (
                  <button key={type.value} onClick={() => setSelectedType(type.value)} className={`p-3 rounded-xl text-left transition-all ${selectedType === type.value ? "bg-gradient-brand text-white" : "bg-white/5 text-slate-400 hover:bg-white/10"}`}>
                    <type.icon className="w-4 h-4 mb-1.5" />
                    <div className="text-sm font-medium">{type.label}</div>
                  </button>
                ))}
              </div>

              <p className="text-sm text-slate-400 mb-3">Number of Questions</p>
              <div className="flex gap-2 mb-6">
                {[5, 10, 15, 20].map((n) => (
                  <button key={n} onClick={() => setNumQuestions(n)} className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${numQuestions === n ? "bg-gradient-brand text-white" : "bg-white/5 text-slate-400"}`}>{n}</button>
                ))}
              </div>

              <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending} className="btn-gradient w-full py-3 rounded-xl flex items-center justify-center gap-2">
                {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Start Interview"}
              </button>
            </motion.div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
