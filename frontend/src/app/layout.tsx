import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { QueryProvider } from "@/components/layout/QueryProvider";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: { default: "Interview Copilot AI", template: "%s | Interview Copilot AI" },
  description: "AI-powered interview preparation platform. Analyze your resume, calculate ATS compatibility, generate interview questions, and ace your next interview.",
  keywords: ["interview preparation", "ATS score", "resume analysis", "AI interview", "mock interview", "job search"],
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body className="font-sans antialiased bg-surface-1 text-white min-h-screen">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          <QueryProvider>
            {children}
            <Toaster
              position="top-right"
              toastOptions={{
                style: { background: "#1a1a2e", color: "#fff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", fontSize: "14px" },
                success: { iconTheme: { primary: "#10b981", secondary: "#fff" } },
                error: { iconTheme: { primary: "#ef4444", secondary: "#fff" } },
                duration: 4000,
              }}
            />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
