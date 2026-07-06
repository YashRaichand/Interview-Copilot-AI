"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Upload, FileText, CheckCircle2, Loader2, ArrowRight, Briefcase, Type, Sparkles } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { resumeApi, jdApi, analysisApi, type ResumeResponse, type JobDescriptionResponse } from "@/lib/api";

type Step = "resume" | "jd" | "analyzing" | "done";

export default function UploadPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("resume");
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [jdMode, setJdMode] = useState<"text" | "pdf">("text");
  const [jdTitle, setJdTitle] = useState("");
  const [jdCompany, setJdCompany] = useState("");
  const [jdText, setJdText] = useState("");

  const resumeUploadMutation = useMutation({
    mutationFn: resumeApi.upload,
    onSuccess: (data) => {
      setResume(data);
      toast.success("Resume uploaded! Parsing in progress...");
      setStep("jd");
    },
    onError: () => toast.error("Failed to upload resume"),
  });

  const onResumeDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;
      if (file.type !== "application/pdf") {
        toast.error("Only PDF files are accepted");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error("File size must be under 10MB");
        return;
      }
      resumeUploadMutation.mutate(file);
    },
    [resumeUploadMutation]
  );

  const { getRootProps: getResumeRootProps, getInputProps: getResumeInputProps, isDragActive: isResumeDragActive } = useDropzone({
    onDrop: onResumeDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: resumeUploadMutation.isPending,
  });

  const jdTextMutation = useMutation({
    mutationFn: jdApi.createText,
    onSuccess: (data) => {
      toast.success("Job description saved!");
      runAnalysis(data.id);
    },
    onError: () => toast.error("Failed to save job description"),
  });

  const jdPdfMutation = useMutation({
    mutationFn: ({ file, title, company }: { file: File; title: string; company?: string }) => jdApi.uploadPdf(file, title, company),
    onSuccess: (data) => {
      toast.success("Job description uploaded!");
      runAnalysis(data.id);
    },
    onError: () => toast.error("Failed to upload job description"),
  });

  const onJdDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file || !resume) return;
      jdPdfMutation.mutate({ file, title: jdTitle || file.name, company: jdCompany });
    },
    [jdPdfMutation, resume, jdTitle, jdCompany]
  );

  const { getRootProps: getJdRootProps, getInputProps: getJdInputProps, isDragActive: isJdDragActive } = useDropzone({
    onDrop: onJdDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: jdPdfMutation.isPending,
  });

  const analysisMutation = useMutation({
    mutationFn: ({ resumeId, jdId }: { resumeId: string; jdId: string }) => analysisApi.run(resumeId, jdId),
    onSuccess: (data) => {
      setStep("done");
      toast.success("ATS Analysis complete!");
      setTimeout(() => router.push(`/analysis/${data.id}`), 1200);
    },
    onError: () => {
      toast.error("Analysis failed. Resume or JD may still be processing — try again shortly.");
      setStep("jd");
    },
  });

  const runAnalysis = (jdId: string) => {
    if (!resume) return;
    setStep("analyzing");
    setTimeout(() => {
      analysisMutation.mutate({ resumeId: resume.id, jdId });
    }, 3000);
  };

  const handleJdTextSubmit = () => {
    if (!jdTitle.trim() || jdText.trim().length < 50) {
      toast.error("Please provide a title and at least 50 characters of job description");
      return;
    }
    jdTextMutation.mutate({ title: jdTitle, company: jdCompany || undefined, raw_text: jdText });
  };

  const steps = [
    { key: "resume", label: "Resume", icon: FileText },
    { key: "jd", label: "Job Description", icon: Briefcase },
    { key: "analyzing", label: "Analysis", icon: Sparkles },
  ];

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto px-4 py-10">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-white mb-2">Start Your ATS Analysis</h1>
          <p className="text-slate-500">Upload your resume and job description to get instant feedback</p>
        </div>

        <div className="flex items-center justify-center gap-2 mb-10">
          {steps.map((s, i) => {
            const isActive = step === s.key || (step === "done" && i <= 2);
            const isPast = (s.key === "resume" && resume) || (s.key === "jd" && step !== "resume" && step !== "jd") || (s.key === "analyzing" && step === "done");
            return (
              <div key={s.key} className="flex items-center">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${isPast ? "bg-green-500/20 text-green-400 border border-green-500/30" : isActive ? "bg-gradient-brand text-white shadow-glow-sm" : "bg-white/5 text-slate-500"}`}>
                  {isPast ? <CheckCircle2 className="w-5 h-5" /> : <s.icon className="w-5 h-5" />}
                </div>
                {i < steps.length - 1 && <div className={`w-12 h-0.5 mx-1 ${isPast ? "bg-green-500/30" : "bg-white/10"}`} />}
              </div>
            );
          })}
        </div>

        <AnimatePresence mode="wait">
          {step === "resume" && (
            <motion.div key="resume" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="glass-card p-8">
              <h2 className="text-lg font-semibold text-white mb-1">Upload Your Resume</h2>
              <p className="text-sm text-slate-500 mb-6">PDF format, max 10MB</p>
              <div {...getResumeRootProps()} className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${isResumeDragActive ? "border-brand-500 bg-brand-500/5" : "border-white/10 hover:border-white/20"}`}>
                <input {...getResumeInputProps()} />
                {resumeUploadMutation.isPending ? (
                  <div className="flex flex-col items-center gap-3"><Loader2 className="w-10 h-10 text-brand-400 animate-spin" /><p className="text-slate-400">Uploading and parsing resume...</p></div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-16 h-16 rounded-2xl bg-brand-600/10 flex items-center justify-center"><Upload className="w-7 h-7 text-brand-400" /></div>
                    <p className="text-white font-medium">{isResumeDragActive ? "Drop your resume here" : "Drag & drop your resume"}</p>
                    <p className="text-sm text-slate-500">or click to browse files</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {step === "jd" && (
            <motion.div key="jd" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="glass-card p-8">
              <div className="flex items-center gap-2 mb-1"><CheckCircle2 className="w-4 h-4 text-green-400" /><span className="text-sm text-green-400">{resume?.filename} uploaded</span></div>
              <h2 className="text-lg font-semibold text-white mb-1 mt-3">Add Job Description</h2>
              <p className="text-sm text-slate-500 mb-6">Paste the text or upload a PDF</p>

              <div className="flex gap-2 mb-6">
                <button onClick={() => setJdMode("text")} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${jdMode === "text" ? "bg-gradient-brand text-white" : "bg-white/5 text-slate-400"}`}>
                  <Type className="w-4 h-4" /> Paste Text
                </button>
                <button onClick={() => setJdMode("pdf")} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${jdMode === "pdf" ? "bg-gradient-brand text-white" : "bg-white/5 text-slate-400"}`}>
                  <FileText className="w-4 h-4" /> Upload PDF
                </button>
              </div>

              <div className="grid sm:grid-cols-2 gap-3 mb-4">
                <input value={jdTitle} onChange={(e) => setJdTitle(e.target.value)} placeholder="Job Title (e.g. Senior Software Engineer)" className="input-dark px-4 py-3 text-sm w-full" />
                <input value={jdCompany} onChange={(e) => setJdCompany(e.target.value)} placeholder="Company (optional)" className="input-dark px-4 py-3 text-sm w-full" />
              </div>

              {jdMode === "text" ? (
                <>
                  <textarea value={jdText} onChange={(e) => setJdText(e.target.value)} placeholder="Paste the full job description here..." rows={10} className="input-dark px-4 py-3 text-sm w-full resize-none" />
                  <div className="flex justify-between items-center mt-2 mb-6"><span className="text-xs text-slate-500">{jdText.length} characters (min 50)</span></div>
                  <button onClick={handleJdTextSubmit} disabled={jdTextMutation.isPending} className="btn-gradient w-full py-3 rounded-xl flex items-center justify-center gap-2">
                    {jdTextMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Run Analysis <ArrowRight className="w-4 h-4" /></>}
                  </button>
                </>
              ) : (
                <div {...getJdRootProps()} className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${isJdDragActive ? "border-brand-500 bg-brand-500/5" : "border-white/10 hover:border-white/20"}`}>
                  <input {...getJdInputProps()} />
                  {jdPdfMutation.isPending ? (
                    <div className="flex flex-col items-center gap-3"><Loader2 className="w-8 h-8 text-brand-400 animate-spin" /><p className="text-slate-400 text-sm">Uploading...</p></div>
                  ) : (
                    <div className="flex flex-col items-center gap-3"><Upload className="w-8 h-8 text-brand-400" /><p className="text-white text-sm font-medium">Drop JD PDF here or click to browse</p></div>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {step === "analyzing" && (
            <motion.div key="analyzing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-12 text-center">
              <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }} className="w-16 h-16 mx-auto mb-6"><Sparkles className="w-16 h-16 text-brand-400" /></motion.div>
              <h2 className="text-xl font-semibold text-white mb-2">Analyzing Your Match...</h2>
              <p className="text-slate-500 text-sm">Computing ATS score, skill match, and semantic similarity</p>
            </motion.div>
          )}

          {step === "done" && (
            <motion.div key="done" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="glass-card p-12 text-center">
              <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Analysis Complete!</h2>
              <p className="text-slate-500 text-sm">Redirecting to your results...</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AppLayout>
  );
}
