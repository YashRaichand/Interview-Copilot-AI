"use client";

import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import { Send, Loader2, ArrowLeft, Award } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { ChatMessage } from "@/components/interview/ChatMessage";
import { interviewApi, type QuestionResponse } from "@/lib/api";

interface ChatItem {
  id: string;
  role: "user" | "assistant" | "question" | "evaluation";
  content: string;
  score?: number;
  difficulty?: string;
  category?: string;
  feedback?: string;
  suggestions?: string[];
}

export default function MockInterviewPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const interviewId = params.id as string;

  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionResponse | null>(null);
  const [input, setInput] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const scrollRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);

  const { data: interview } = useQuery({ queryKey: ["interview", interviewId], queryFn: () => interviewApi.get(interviewId), enabled: !!interviewId });

  const chatMutation = useMutation({
    mutationFn: interviewApi.chat,
    onMutate: () => setIsTyping(true),
    onSuccess: (response) => {
      setIsTyping(false);

      if (response.evaluation) {
        setMessages((prev) => [...prev, { id: `eval-${Date.now()}`, role: "evaluation", content: "", score: response.evaluation!.overall_score, feedback: response.evaluation!.feedback, suggestions: response.evaluation!.improvement_suggestions }]);
      }

      if (response.is_complete) {
        setIsComplete(true);
        setMessages((prev) => [...prev, { id: `complete-${Date.now()}`, role: "assistant", content: response.message }]);
        queryClient.invalidateQueries({ queryKey: ["interview", interviewId] });
        return;
      }

      if (response.question) {
        setCurrentQuestion(response.question);
        setStartTime(Date.now());
        setTimeout(() => {
          setMessages((prev) => [...prev, { id: `q-${response.question!.id}`, role: "question", content: response.question!.question_text, difficulty: response.question!.difficulty, category: response.question!.category }]);
        }, 400);
      }
    },
    onError: () => {
      setIsTyping(false);
      toast.error("Something went wrong. Please try again.");
    },
  });

  useEffect(() => {
    if (!initialized.current && interviewId) {
      initialized.current = true;
      chatMutation.mutate({ interview_id: interviewId, message: "start" });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interviewId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSubmit = () => {
    if (!input.trim() || !currentQuestion || chatMutation.isPending) return;

    setMessages((prev) => [...prev, { id: `a-${Date.now()}`, role: "user", content: input }]);
    chatMutation.mutate({ interview_id: interviewId, message: input, question_id: currentQuestion.id });
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const progress = interview ? Math.round((interview.answered_questions / Math.max(interview.total_questions, 1)) * 100) : 0;

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto px-4 py-6 h-[calc(100vh-80px)] flex flex-col">
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <button onClick={() => router.push("/interview")} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="flex items-center gap-2">
            <div className="w-32 h-1.5 bg-white/5 rounded-full overflow-hidden">
              <motion.div animate={{ width: `${progress}%` }} className="h-full bg-gradient-brand rounded-full" />
            </div>
            <span className="text-xs text-slate-500">{interview?.answered_questions ?? 0}/{interview?.total_questions ?? 0}</span>
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 px-1 py-4 flex flex-col">
          {messages.length === 0 && chatMutation.isPending && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Loader2 className="w-8 h-8 text-brand-400 animate-spin mb-3" />
              <p className="text-slate-500 text-sm">Preparing your interview questions...</p>
            </div>
          )}

          <AnimatePresence>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} role={msg.role} content={msg.content} score={msg.score} difficulty={msg.difficulty} category={msg.category} feedback={msg.feedback} suggestions={msg.suggestions} />
            ))}
          </AnimatePresence>

          {isTyping && <ChatMessage role="assistant" content="" isTyping />}

          {isComplete && interview && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass-card p-6 mt-4 border border-brand-600/20 self-center w-full">
              <div className="flex items-center justify-center mb-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-brand flex items-center justify-center shadow-glow-brand"><Award className="w-8 h-8 text-white" /></div>
              </div>
              <h3 className="text-center text-xl font-bold text-white mb-1">Interview Complete!</h3>
              <p className="text-center text-slate-500 text-sm mb-6">Here&apos;s how you did</p>

              <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="glass-card p-3 text-center"><div className="text-2xl font-bold text-white">{interview.overall_score?.toFixed(1) ?? "—"}</div><div className="text-xs text-slate-500">Overall</div></div>
                <div className="glass-card p-3 text-center"><div className="text-2xl font-bold text-white">{interview.technical_score?.toFixed(1) ?? "—"}</div><div className="text-xs text-slate-500">Technical</div></div>
                <div className="glass-card p-3 text-center"><div className="text-2xl font-bold text-white">{interview.communication_score?.toFixed(1) ?? "—"}</div><div className="text-xs text-slate-500">Communication</div></div>
              </div>

              <div className="flex gap-3">
                <button onClick={() => router.push("/interview")} className="btn-outline flex-1 py-2.5 rounded-xl text-sm">View All Interviews</button>
                <button onClick={() => router.push("/reports")} className="btn-gradient flex-1 py-2.5 rounded-xl text-sm">Get Full Report</button>
              </div>
            </motion.div>
          )}
        </div>

        {!isComplete && (
          <div className="flex-shrink-0 pt-4 border-t border-white/5">
            <div className="flex items-end gap-3">
              <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Type your answer here..." rows={3} disabled={!currentQuestion || chatMutation.isPending} className="input-dark flex-1 px-4 py-3 text-sm resize-none disabled:opacity-50" />
              <button onClick={handleSubmit} disabled={!input.trim() || !currentQuestion || chatMutation.isPending} className="btn-gradient w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 disabled:opacity-40">
                {chatMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-slate-600 mt-2">Press Enter to send, Shift+Enter for new line</p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
