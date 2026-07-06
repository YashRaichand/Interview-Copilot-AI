"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Brain, Target, MessageSquare, TrendingUp, FileText, Map, ArrowRight, ChevronRight, Star, CheckCircle2, Upload, BarChart3, Sparkles } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" } }),
};

const FEATURES = [
  { icon: FileText, color: "#7c3aed", title: "Resume Parser", desc: "Extract structured data from any PDF resume using SpaCy NER and smart regex patterns." },
  { icon: Target, color: "#06b6d4", title: "ATS Score Engine", desc: "Calculate ATS compatibility using keyword match, semantic similarity, skill match, and experience factors." },
  { icon: Brain, color: "#8b5cf6", title: "AI Question Generator", desc: "Generate HR, technical, behavioral, and project-specific questions tailored to your resume and JD." },
  { icon: MessageSquare, color: "#0891b2", title: "Mock Interviews", desc: "Adaptive chat-based interviews that adjust question difficulty based on your previous answers." },
  { icon: TrendingUp, color: "#10b981", title: "Answer Evaluation", desc: "AI-powered scoring on relevance, technical accuracy, completeness, and communication clarity." },
  { icon: Map, color: "#f59e0b", title: "Learning Roadmaps", desc: "Personalized 30-day preparation plans with resources, projects, and milestones." },
];

const STATS = [
  { value: "95%", label: "ATS Accuracy" },
  { value: "10K+", label: "Interviews Conducted" },
  { value: "3.5x", label: "Faster Preparation" },
  { value: "85%", label: "Success Rate" },
];

const HOW_IT_WORKS = [
  { step: "01", icon: Upload, title: "Upload Your Resume", desc: "Drop your PDF resume. We extract skills, experience, and education using advanced NLP." },
  { step: "02", icon: FileText, title: "Add Job Description", desc: "Paste or upload the JD. We parse requirements and calculate your ATS compatibility." },
  { step: "03", icon: BarChart3, title: "Get ATS Analysis", desc: "See your score breakdown, missing skills, and personalized recommendations instantly." },
  { step: "04", icon: Brain, title: "Practice & Improve", desc: "Run AI mock interviews, evaluate your answers, and follow your 30-day roadmap." },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-surface-1 overflow-hidden">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-brand-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-accent-500/8 rounded-full blur-[100px]" />
      </div>

      <nav className="relative z-50 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-brand flex items-center justify-center shadow-glow-sm">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="text-white font-bold text-lg tracking-tight">Interview Copilot AI</span>
        </Link>

        <div className="hidden md:flex items-center gap-6 text-sm text-slate-400">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-white transition-colors">How it Works</a>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/login" className="btn-outline px-4 py-2 text-sm rounded-xl">Sign In</Link>
          <Link href="/register" className="btn-gradient px-5 py-2 text-sm rounded-xl inline-flex items-center gap-1.5">
            Get Started <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      <section className="relative pt-20 pb-32 px-6 text-center max-w-6xl mx-auto">
        <motion.div initial="hidden" animate="show" variants={fadeUp} custom={0}>
          <span className="inline-flex items-center gap-2 badge badge-brand mb-6 text-xs">
            <Sparkles className="w-3.5 h-3.5" /> Powered by Claude AI & Advanced NLP
          </span>
        </motion.div>

        <motion.h1 initial="hidden" animate="show" variants={fadeUp} custom={1} className="text-5xl md:text-7xl font-bold leading-tight mb-6">
          Ace Your Next <span className="gradient-text">Interview</span><br />with AI Precision
        </motion.h1>

        <motion.p initial="hidden" animate="show" variants={fadeUp} custom={2} className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Upload your resume and job description. Get instant ATS analysis, personalized interview questions, AI mock interviews, and a 30-day preparation roadmap.
        </motion.p>

        <motion.div initial="hidden" animate="show" variants={fadeUp} custom={3} className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/register" className="btn-gradient px-8 py-4 text-base rounded-2xl inline-flex items-center gap-2 shadow-glow-brand">
            Start for Free <ArrowRight className="w-4 h-4" />
          </Link>
          {/* Scrolls to the features section on this same page — no dead route. */}
          <a href="#features" className="btn-outline px-8 py-4 text-base rounded-2xl inline-flex items-center gap-2">
            See How It Works <ChevronRight className="w-4 h-4" />
          </a>
        </motion.div>

        <motion.div initial="hidden" animate="show" variants={fadeUp} custom={4} className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold gradient-text mb-1">{stat.value}</div>
              <div className="text-sm text-slate-500">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      <section id="features" className="relative px-6 py-24 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">Everything You Need to <span className="gradient-text">Land the Job</span></h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">A complete AI-powered toolkit that takes you from resume upload to interview confidence.</p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feature, i) => (
            <motion.div key={feature.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }} className="glass-card-hover p-6 group">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110" style={{ background: `${feature.color}20`, border: `1px solid ${feature.color}30` }}>
                <feature.icon className="w-6 h-6" style={{ color: feature.color }} />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="relative px-6 py-24 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">How It <span className="gradient-text">Works</span></h2>
          <p className="text-slate-400 text-lg">Four steps to interview readiness</p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6">
          {HOW_IT_WORKS.map((step, i) => (
            <motion.div key={step.step} initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="glass-card p-6 flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-2xl bg-gradient-brand flex items-center justify-center shadow-glow-sm">
                  <step.icon className="w-5 h-5 text-white" />
                </div>
              </div>
              <div>
                <div className="text-xs font-mono text-brand-400 mb-1">{step.step}</div>
                <h3 className="text-lg font-semibold text-white mb-1">{step.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{step.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="relative px-6 py-24">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} className="max-w-4xl mx-auto glass-card p-12 text-center border border-brand-600/20 relative overflow-hidden">
          <div className="relative">
            <div className="flex justify-center gap-1 mb-4">
              {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />)}
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">Ready to Land Your Dream Job?</h2>
            <p className="text-slate-400 text-lg mb-8 max-w-xl mx-auto">Join thousands of candidates who used Interview Copilot AI to prepare smarter and interview with confidence.</p>
            <Link href="/register" className="btn-gradient px-8 py-4 text-base rounded-2xl inline-flex items-center gap-2 justify-center shadow-glow-brand">
              Start Free Today <ArrowRight className="w-4 h-4" />
            </Link>
            <div className="mt-6 flex items-center justify-center gap-6 text-sm text-slate-500 flex-wrap">
              {["No credit card required", "Free ATS analysis", "Cancel anytime"].map((t) => (
                <span key={t} className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-green-500" /> {t}</span>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      <footer className="border-t border-white/5 px-6 py-10 text-center text-sm text-slate-600">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="w-6 h-6 rounded-lg bg-gradient-brand flex items-center justify-center"><Brain className="w-3.5 h-3.5 text-white" /></div>
          <span className="text-slate-400 font-medium">Interview Copilot AI</span>
        </div>
        <p>© {new Date().getFullYear()} Interview Copilot AI. Built with Next.js, FastAPI & Claude.</p>
      </footer>
    </main>
  );
}
