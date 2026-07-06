"use client";

import { motion } from "framer-motion";
import { Bot, User, AlertCircle } from "lucide-react";

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 7 ? "#10b981" : score >= 5 ? "#f59e0b" : "#ef4444";
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: `${color}20`, color, border: `1px solid ${color}30` }}>
      {score.toFixed(1)}/10
    </span>
  );
}

interface ChatMessageProps {
  role: "user" | "assistant" | "question" | "evaluation";
  content: string;
  score?: number;
  difficulty?: string;
  category?: string;
  feedback?: string;
  suggestions?: string[];
  isTyping?: boolean;
}

export function ChatMessage({ role, content, score, difficulty, category, feedback, suggestions, isTyping }: ChatMessageProps) {
  const isUser = role === "user";

  if (isTyping) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <div className="w-8 h-8 rounded-xl bg-gradient-brand flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div className="glass-card px-4 py-3 flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.div key={i} animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }} className="w-2 h-2 rounded-full bg-slate-400" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex items-start gap-3 max-w-[85%] ${isUser ? "self-end flex-row-reverse" : "self-start"}`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${isUser ? "bg-accent-500/20" : "bg-gradient-brand"}`}>
        {isUser ? <User className="w-4 h-4 text-accent-400" /> : <Bot className="w-4 h-4 text-white" />}
      </div>

      <div className="flex flex-col gap-2">
        {role === "question" && (difficulty || category) && (
          <div className="flex gap-2 mb-1">
            {category && <span className="badge badge-brand text-xs">{category}</span>}
            {difficulty && <span className={`badge text-xs ${difficulty === "hard" ? "badge-high" : difficulty === "medium" ? "badge-medium" : "badge-low"}`}>{difficulty}</span>}
          </div>
        )}

        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${isUser ? "bg-accent-500/10 border border-accent-500/20 text-white" : "glass-card text-slate-200"}`}>{content}</div>

        {role === "evaluation" && (
          <div className="glass-card p-4 space-y-3 border border-brand-600/20">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Evaluation</span>
              {score !== undefined && <ScoreBadge score={score} />}
            </div>
            {feedback && <p className="text-sm text-slate-300">{feedback}</p>}
            {suggestions && suggestions.length > 0 && (
              <div className="space-y-1.5 pt-1">
                {suggestions.map((s, i) => (
                  <div key={i} className="flex gap-2 text-xs text-slate-400">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                    {s}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
