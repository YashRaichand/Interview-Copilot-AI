import axios, { AxiosInstance, AxiosError } from "axios";
import Cookies from "js-cookie";
import toast from "react-hot-toast";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface ResumeResponse {
  id: string;
  filename: string;
  cloudinary_url: string;
  candidate_name?: string;
  email?: string;
  phone?: string;
  location?: string;
  summary?: string;
  skills?: {
    technical: string[]; soft: string[]; languages: string[]; frameworks: string[]; tools: string[]; databases: string[]; cloud: string[];
  };
  experience?: Array<{ company: string; role: string; start_date?: string; end_date?: string; duration?: string; description?: string; achievements: string[] }>;
  education?: Array<{ institution: string; degree: string; field?: string; graduation_year?: string; gpa?: string }>;
  projects?: Array<{ name: string; description?: string; tech_stack: string[]; url?: string; github_url?: string }>;
  certifications?: Array<{ name: string; issuer?: string; year?: string; url?: string }>;
  total_experience_years?: number;
  resume_category?: string;
  is_parsed: boolean;
  created_at: string;
}

export interface JobDescriptionResponse {
  id: string;
  title: string;
  company?: string;
  raw_text: string;
  required_skills?: string[];
  preferred_skills?: string[];
  experience_required?: string;
  education_required?: string;
  responsibilities?: string[];
  employment_type?: string;
  location?: string;
  is_parsed: boolean;
  created_at: string;
}

export interface MissingSkill {
  skill: string;
  priority: "high" | "medium" | "low";
  category: string;
  reason: string;
}

export interface AnalysisResponse {
  id: string;
  resume_id: string;
  job_description_id: string;
  ats_score?: number;
  skill_match_percentage?: number;
  semantic_similarity?: number;
  score_breakdown?: { keyword_match: number; semantic_similarity: number; skill_match: number; experience_match: number; weights: Record<string, number> };
  missing_skills?: MissingSkill[];
  matching_skills?: string[];
  recommendations?: string[];
  success_probability?: number;
  created_at: string;
}

export interface QuestionResponse {
  id: string;
  question_text: string;
  question_type: string;
  difficulty: string;
  category?: string;
  order_index: number;
  is_follow_up: boolean;
}

export interface InterviewResponse {
  id: string;
  title: string;
  status: string;
  interview_type: string;
  overall_score?: number;
  technical_score?: number;
  communication_score?: number;
  total_questions: number;
  answered_questions: number;
  duration_minutes?: number;
  feedback_summary?: string;
  improvement_areas?: string[];
  strengths?: string[];
  questions: QuestionResponse[];
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface AnswerEvaluation {
  relevance_score: number;
  technical_accuracy_score: number;
  completeness_score: number;
  communication_score: number;
  overall_score: number;
  feedback: string;
  improvement_suggestions: string[];
  model_answer?: string;
  keywords_used: string[];
  keywords_missed: string[];
}

export interface AnswerResponse extends AnswerEvaluation {
  id: string;
  question_id: string;
  answer_text: string;
  created_at: string;
}

export interface MockInterviewResponse {
  message: string;
  question?: QuestionResponse;
  evaluation?: AnswerEvaluation;
  is_complete: boolean;
  next_action: string;
}

export interface WeekPlan {
  week: number;
  focus: string;
  topics: string[];
  resources: Array<{ title: string; url: string; type: string }>;
  projects: string[];
  goals: string[];
  estimated_hours: number;
}

export interface RoadmapResponse {
  id: string;
  title: string;
  target_role?: string;
  target_company?: string;
  duration_days: number;
  weeks?: WeekPlan[];
  skills_to_learn?: string[];
  resources?: Array<{ title: string; url: string; type: string; description?: string }>;
  milestones?: Array<{ day: number; milestone: string; check: string }>;
  progress_percentage: number;
  completed_items?: string[];
  is_active: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_resumes: number;
  total_analyses: number;
  total_interviews: number;
  best_ats_score?: number;
  average_ats_score?: number;
  latest_ats_score?: number;
  latest_skill_match?: number;
  success_probability?: number;
  recent_interviews: Array<{ id: string; title: string; status: string; interview_type: string; overall_score?: number; total_questions: number; answered_questions: number; created_at: string }>;
  ats_trend: Array<{ date: string; score: number }>;
  missing_skills_summary: string[];
  active_roadmap?: RoadmapResponse;
}

// ── Axios Instance ────────────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use(
  (config) => {
    const token = Cookies.get("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers!.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = Cookies.get("refresh_token");
      if (!refreshToken) {
        processQueue(error, null);
        isRefreshing = false;
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        if (typeof window !== "undefined") window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, { refresh_token: refreshToken });
        const { access_token, refresh_token: newRefresh } = response.data;
        Cookies.set("access_token", access_token, { expires: 1, secure: true, sameSite: "strict" });
        Cookies.set("refresh_token", newRefresh, { expires: 7, secure: true, sameSite: "strict" });

        api.defaults.headers.common.Authorization = `Bearer ${access_token}`;
        processQueue(null, access_token);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        if (typeof window !== "undefined") window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response?.status !== 401) {
      const message = (error.response?.data as { detail?: string })?.detail || "An unexpected error occurred";
      if (typeof window !== "undefined") toast.error(message);
    }

    return Promise.reject(error);
  }
);

// ── Auth API ──────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; full_name: string; password: string }) => api.post<TokenResponse>("/auth/register", data).then((r) => r.data),
  login: (data: { email: string; password: string }) => api.post<TokenResponse>("/auth/login", data).then((r) => r.data),
  logout: () => api.post("/auth/logout").then((r) => r.data),
  getMe: () => api.get<UserResponse>("/auth/me").then((r) => r.data),
  getGoogleUrl: () => api.get<{ url: string }>("/auth/google/url").then((r) => r.data),
  googleCallback: (code: string, redirectUri: string) => api.post<TokenResponse>("/auth/google", { code, redirect_uri: redirectUri }).then((r) => r.data),
  saveTokens: (tokens: TokenResponse) => {
    Cookies.set("access_token", tokens.access_token, { expires: 1, secure: true, sameSite: "strict" });
    Cookies.set("refresh_token", tokens.refresh_token, { expires: 7, secure: true, sameSite: "strict" });
  },
  clearTokens: () => {
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
  },
  isAuthenticated: () => !!Cookies.get("access_token"),
};

// ── Resume API ────────────────────────────────────────────────────────────────

export const resumeApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<ResumeResponse>("/resumes/upload", form, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
  list: () => api.get<ResumeResponse[]>("/resumes/").then((r) => r.data),
  get: (id: string) => api.get<ResumeResponse>(`/resumes/${id}`).then((r) => r.data),
  delete: (id: string) => api.delete(`/resumes/${id}`).then((r) => r.data),
  reparse: (id: string) => api.post(`/resumes/${id}/reparse`).then((r) => r.data),
};

// ── Job Description API ───────────────────────────────────────────────────────

export const jdApi = {
  createText: (data: { title: string; company?: string; raw_text: string }) => api.post<JobDescriptionResponse>("/job-descriptions/", data).then((r) => r.data),
  uploadPdf: (file: File, title: string, company?: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", title);
    if (company) form.append("company", company);
    return api.post<JobDescriptionResponse>("/job-descriptions/upload", form, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
  list: () => api.get<JobDescriptionResponse[]>("/job-descriptions/").then((r) => r.data),
  get: (id: string) => api.get<JobDescriptionResponse>(`/job-descriptions/${id}`).then((r) => r.data),
  delete: (id: string) => api.delete(`/job-descriptions/${id}`).then((r) => r.data),
};

// ── Analysis API ──────────────────────────────────────────────────────────────

export const analysisApi = {
  run: (resumeId: string, jobDescriptionId: string) => api.post<AnalysisResponse>("/analyses/", { resume_id: resumeId, job_description_id: jobDescriptionId }).then((r) => r.data),
  list: () => api.get<AnalysisResponse[]>("/analyses/").then((r) => r.data),
  get: (id: string) => api.get<AnalysisResponse>(`/analyses/${id}`).then((r) => r.data),
};

// ── Interview API ─────────────────────────────────────────────────────────────

export const interviewApi = {
  create: (data: { analysis_id?: string; interview_type?: string; title?: string; num_questions?: number }) => api.post<InterviewResponse>("/interviews/", data).then((r) => r.data),
  list: () => api.get<InterviewResponse[]>("/interviews/").then((r) => r.data),
  get: (id: string) => api.get<InterviewResponse>(`/interviews/${id}`).then((r) => r.data),
  submitAnswer: (interviewId: string, data: { question_id: string; answer_text: string; time_taken_seconds?: number }) => api.post<AnswerResponse>(`/interviews/${interviewId}/answer`, data).then((r) => r.data),
  complete: (id: string) => api.post<InterviewResponse>(`/interviews/${id}/complete`).then((r) => r.data),
  chat: (data: { interview_id: string; message: string; question_id?: string }) => api.post<MockInterviewResponse>("/interviews/chat", data).then((r) => r.data),
};

// ── Roadmap API ───────────────────────────────────────────────────────────────

export const roadmapApi = {
  generate: (analysisId: string) => api.post<RoadmapResponse>(`/roadmaps/generate?analysis_id=${analysisId}`).then((r) => r.data),
  list: () => api.get<RoadmapResponse[]>("/roadmaps/").then((r) => r.data),
  getActive: () => api.get<RoadmapResponse>("/roadmaps/active").then((r) => r.data),
  updateProgress: (roadmapId: string, data: { completed_item_id: string; is_completed: boolean }) => api.patch<RoadmapResponse>(`/roadmaps/${roadmapId}/progress`, data).then((r) => r.data),
};

// ── Reports API ───────────────────────────────────────────────────────────────

export const reportsApi = {
  generate: (data: { analysis_id?: string; interview_id?: string; report_type: string }) => api.post("/reports/generate", data).then((r) => r.data),
  list: () => api.get("/reports/").then((r) => r.data),
};

// ── Dashboard API ─────────────────────────────────────────────────────────────

export const dashboardApi = {
  getStats: () => api.get<DashboardStats>("/dashboard/stats").then((r) => r.data),
};

export default api;
