"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Map, CheckCircle2, Circle, ExternalLink, Calendar, Target, BookOpen, Code2, Award } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { roadmapApi } from "@/lib/api";

const RESOURCE_ICONS: Record<string, any> = { course: BookOpen, docs: BookOpen, practice: Code2, book: BookOpen, video: BookOpen, guide: BookOpen, community: Target };

export default function RoadmapPage() {
  const [activeWeek, setActiveWeek] = useState(1);
  const [localCompleted, setLocalCompleted] = useState<Set<string>>(new Set());

  const { data: roadmap, isLoading } = useQuery({ queryKey: ["active-roadmap"], queryFn: roadmapApi.getActive, retry: false });

  const progressMutation = useMutation({
    mutationFn: ({ itemId, completed }: { itemId: string; completed: boolean }) => roadmapApi.updateProgress(roadmap!.id, { completed_item_id: itemId, is_completed: completed }),
    onError: () => toast.error("Failed to update progress"),
  });

  const toggleItem = (itemId: string) => {
    const isCompleted = localCompleted.has(itemId) || roadmap?.completed_items?.includes(itemId);
    setLocalCompleted((prev) => {
      const next = new Set(prev);
      if (isCompleted) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
    progressMutation.mutate({ itemId, completed: !isCompleted });
  };

  const isItemCompleted = (itemId: string) => localCompleted.has(itemId) || (roadmap?.completed_items?.includes(itemId) ?? false);

  if (isLoading) {
    return (
      <AppLayout>
        <div className="max-w-5xl mx-auto px-4 py-10 space-y-4"><div className="skeleton h-32 rounded-2xl" /><div className="skeleton h-96 rounded-2xl" /></div>
      </AppLayout>
    );
  }

  if (!roadmap) {
    return (
      <AppLayout>
        <div className="max-w-3xl mx-auto px-4 py-20 text-center">
          <Map className="w-14 h-14 text-slate-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No Active Roadmap</h2>
          <p className="text-slate-500 text-sm mb-6">Run an ATS analysis first, then generate a personalized 30-day roadmap.</p>
        </div>
      </AppLayout>
    );
  }

  const currentWeek = roadmap.weeks?.find((w) => w.week === activeWeek);

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-brand flex items-center justify-center shadow-glow-sm"><Map className="w-6 h-6 text-white" /></div>
              <div><h1 className="text-xl font-bold text-white">{roadmap.title}</h1><p className="text-sm text-slate-500">{roadmap.target_role} {roadmap.target_company && `at ${roadmap.target_company}`}</p></div>
            </div>
            <div className="text-right"><div className="text-2xl font-bold gradient-text">{roadmap.progress_percentage.toFixed(0)}%</div><div className="text-xs text-slate-500">Complete</div></div>
          </div>
          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
            <motion.div initial={{ width: 0 }} animate={{ width: `${roadmap.progress_percentage}%` }} transition={{ duration: 0.8 }} className="h-full bg-gradient-brand rounded-full" />
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1">
          {roadmap.weeks?.map((week) => (
            <button key={week.week} onClick={() => setActiveWeek(week.week)} className={`flex-shrink-0 px-5 py-2.5 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${activeWeek === week.week ? "bg-gradient-brand text-white shadow-glow-sm" : "bg-white/5 text-slate-400 hover:bg-white/10"}`}>
              Week {week.week}
            </button>
          ))}
        </div>

        {currentWeek && (
          <motion.div key={activeWeek} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold text-white">{currentWeek.focus}</h2>
                <span className="badge badge-brand text-xs flex items-center gap-1"><Calendar className="w-3 h-3" /> {currentWeek.estimated_hours}h estimated</span>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2"><Target className="w-4 h-4 text-brand-400" /> Topics to Cover</h3>
                <div className="space-y-2 mb-6">
                  {currentWeek.topics.map((topic, i) => {
                    const itemId = `week${activeWeek}-topic-${i}`;
                    const completed = isItemCompleted(itemId);
                    return (
                      <button key={itemId} onClick={() => toggleItem(itemId)} className="flex items-center gap-3 w-full text-left group">
                        {completed ? <CheckCircle2 className="w-4.5 h-4.5 text-green-400 flex-shrink-0" /> : <Circle className="w-4.5 h-4.5 text-slate-600 group-hover:text-slate-400 flex-shrink-0" />}
                        <span className={`text-sm ${completed ? "text-slate-500 line-through" : "text-slate-300"}`}>{topic}</span>
                      </button>
                    );
                  })}
                </div>

                <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2"><Award className="w-4 h-4 text-accent-400" /> Goals</h3>
                <div className="space-y-2">
                  {currentWeek.goals.map((goal, i) => (
                    <div key={i} className="flex items-start gap-2"><div className="w-1.5 h-1.5 rounded-full bg-accent-400 mt-1.5 flex-shrink-0" /><span className="text-sm text-slate-400">{goal}</span></div>
                  ))}
                </div>
              </div>

              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2"><Code2 className="w-4 h-4 text-green-400" /> Projects</h3>
                <div className="space-y-2 mb-6">
                  {currentWeek.projects.map((project, i) => {
                    const itemId = `week${activeWeek}-project-${i}`;
                    const completed = isItemCompleted(itemId);
                    return (
                      <button key={itemId} onClick={() => toggleItem(itemId)} className="flex items-center gap-3 w-full text-left group">
                        {completed ? <CheckCircle2 className="w-4.5 h-4.5 text-green-400 flex-shrink-0" /> : <Circle className="w-4.5 h-4.5 text-slate-600 group-hover:text-slate-400 flex-shrink-0" />}
                        <span className={`text-sm ${completed ? "text-slate-500 line-through" : "text-slate-300"}`}>{project}</span>
                      </button>
                    );
                  })}
                </div>

                <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2"><BookOpen className="w-4 h-4 text-yellow-400" /> Resources</h3>
                <div className="space-y-2">
                  {currentWeek.resources.map((resource, i) => {
                    const Icon = RESOURCE_ICONS[resource.type] || BookOpen;
                    return (
                      <a key={i} href={resource.url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between p-2.5 rounded-xl bg-white/3 hover:bg-white/5 transition-colors group">
                        <div className="flex items-center gap-2.5"><Icon className="w-4 h-4 text-slate-500" /><span className="text-sm text-slate-300">{resource.title}</span></div>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400" />
                      </a>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {roadmap.milestones && roadmap.milestones.length > 0 && (
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Milestones</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {roadmap.milestones.map((m, i) => (
                <div key={i} className="text-center">
                  <div className="text-lg font-bold gradient-text mb-1">Day {m.day}</div>
                  <div className="text-xs text-slate-400 mb-1">{m.milestone}</div>
                  <div className="text-xs text-slate-600">{m.check}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
