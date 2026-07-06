"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileBarChart, Download, FileText, Brain } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { reportsApi } from "@/lib/api";
import { format } from "date-fns";

export default function ReportsPage() {
  const { data: reports, isLoading } = useQuery({ queryKey: ["reports"], queryFn: reportsApi.list });
  const reportList = (reports as any[]) || [];

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto px-4 py-10">
        <div className="mb-8"><h1 className="text-3xl font-bold text-white mb-1">Reports</h1><p className="text-slate-500 text-sm">Download your ATS and interview reports as PDF</p></div>

        {isLoading ? (
          <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-20 rounded-2xl" />)}</div>
        ) : reportList.length > 0 ? (
          <div className="space-y-3">
            {reportList.map((report, i) => (
              <motion.div key={report.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="glass-card-hover p-5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-2xl bg-brand-600/15 flex items-center justify-center">
                    {report.report_type === "interview" ? <Brain className="w-5 h-5 text-brand-400" /> : <FileText className="w-5 h-5 text-brand-400" />}
                  </div>
                  <div><div className="text-white font-medium">{report.title}</div><div className="text-sm text-slate-500">{format(new Date(report.created_at), "MMM d, yyyy")}</div></div>
                </div>
                {report.cloudinary_url ? (
                  <a href={report.cloudinary_url} target="_blank" rel="noopener noreferrer" className="btn-outline px-4 py-2 text-sm rounded-xl flex items-center gap-2"><Download className="w-4 h-4" /> Download</a>
                ) : (
                  <span className="text-xs text-slate-500">Generating...</span>
                )}
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="glass-card p-16 text-center">
            <FileBarChart className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-white font-medium mb-2">No reports yet</h3>
            <p className="text-slate-500 text-sm">Reports are generated from your ATS analyses and completed interviews</p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
