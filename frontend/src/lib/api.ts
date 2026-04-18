import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;

// ── Role APIs ──────────────────────────────────────────
export const roleApi = {
  list: () => apiClient.get("/roles"),
  get: (id: string) => apiClient.get(`/roles/${id}`),
  create: (data: unknown) => apiClient.post("/roles", data),
  update: (id: string, data: unknown) => apiClient.patch(`/roles/${id}`, data),
  delete: (id: string) => apiClient.delete(`/roles/${id}`),
  init: (id: string) => apiClient.post(`/roles/${id}/init`),
  analyzeJd: (raw_jd: string) => apiClient.post("/roles/analyze-jd", { raw_jd }),
  analyzeName: (role_name: string) => apiClient.post("/roles/analyze-name", { role_name }),
};

// ── Resume APIs ────────────────────────────────────────
export const resumeApi = {
  list: (params?: Record<string, string>) =>
    apiClient.get("/resumes", { params }),
  get: (id: string) => apiClient.get(`/resumes/${id}`),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/resumes/${id}`, data),
  delete: (id: string) =>
    apiClient.delete(`/resumes/${id}`),
  versions: (id: string) => apiClient.get(`/resumes/${id}/versions`),
  getVersion: (resumeId: string, versionId: string) =>
    apiClient.get(`/resumes/${resumeId}/versions/${versionId}`),
  deleteVersion: (resumeId: string, versionId: string) =>
    apiClient.delete(`/resumes/${resumeId}/versions/${versionId}`),
  applySuggestion: (id: string, suggestionId: string) =>
    apiClient.post(`/resumes/${id}/apply-suggestion`, { suggestion_id: suggestionId }),
  exportPdf: (id: string) =>
    apiClient.post(`/resumes/${id}/export-pdf`, null, { responseType: "blob" }),
};

// ── Achievement APIs ───────────────────────────────────
export const achievementApi = {
  list: () => apiClient.get("/achievements"),
  get: (id: string) => apiClient.get(`/achievements/${id}`),
  create: (data: unknown) => apiClient.post("/achievements", data),
  analyze: (id: string) => apiClient.post(`/achievements/${id}/analyze`),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/achievements/${id}`, data),
  delete: (id: string) => apiClient.delete(`/achievements/${id}`),
  interactiveStart: (id: string) =>
    apiClient.post(`/achievements/${id}/interactive/start`),
  interactiveChat: (id: string, message: string) =>
    apiClient.post(`/achievements/${id}/interactive/chat`, { message }),
  interactiveGenerate: (id: string) =>
    apiClient.post(`/achievements/${id}/interactive/generate`),
};

// ── Gap APIs ───────────────────────────────────────────
export const gapApi = {
  list: (roleId?: string) =>
    apiClient.get("/gaps", { params: { role_id: roleId } }),
  byRole: (roleId: string) => apiClient.get(`/roles/${roleId}/gaps`),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/gaps/${id}`, data),
};

// ── JD APIs ────────────────────────────────────────────
export const jdApi = {
  parse: (data: { raw_jd: string }) => apiClient.post("/jd/parse", data),
  tailor: (data: unknown) => apiClient.post("/jd/tailor", data),
  getTask: (taskId: string) => apiClient.get(`/jd/tasks/${taskId}`),
  exportPdf: (taskId: string) =>
    apiClient.post(`/jd/tasks/${taskId}/export-pdf`, null, { responseType: "blob" }),
};

// ── Suggestion APIs ────────────────────────────────────
export const suggestionApi = {
  list: (filters?: Record<string, string>) =>
    apiClient.get("/suggestions", { params: filters }),
  accept: (id: string) => apiClient.post(`/suggestions/${id}/accept`),
  reject: (id: string) => apiClient.post(`/suggestions/${id}/reject`),
};

// ── Profile APIs ───────────────────────────────────────
export const profileApi = {
  get: () => apiClient.get("/profile"),
  upsert: (data: unknown) => apiClient.put("/profile", data),
  completeness: () => apiClient.get("/profile/completeness"),
  importResume: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post("/profile/import-resume", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ── Work Experience APIs ────────────────────────────────
export const workExperienceApi = {
  list: () => apiClient.get("/work-experiences"),
  create: (data: unknown) => apiClient.post("/work-experiences", data),
  update: (id: string, data: unknown) => apiClient.patch(`/work-experiences/${id}`, data),
  delete: (id: string) => apiClient.delete(`/work-experiences/${id}`),
};

// ── Education APIs ──────────────────────────────────────
export const educationApi = {
  list: () => apiClient.get("/educations"),
  create: (data: unknown) => apiClient.post("/educations", data),
  update: (id: string, data: unknown) => apiClient.patch(`/educations/${id}`, data),
  delete: (id: string) => apiClient.delete(`/educations/${id}`),
};

// ── Project APIs ────────────────────────────────────────
export const projectApi = {
  list: () => apiClient.get("/projects"),
  create: (data: unknown) => apiClient.post("/projects", data),
  update: (id: string, data: unknown) => apiClient.patch(`/projects/${id}`, data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
};

// ── Story APIs ─────────────────────────────────────────
export const storyApi = {
  list: (params?: Record<string, string>) =>
    apiClient.get("/stories", { params }),
  rebuild: (achievementId: string) =>
    apiClient.post(`/stories/rebuild/${achievementId}`),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/stories/${id}`, data),
};

// ── Dashboard APIs ─────────────────────────────────────
export const dashboardApi = {
  stats: () => apiClient.get("/dashboard/stats"),
  recentJdDecisions: () => apiClient.get("/dashboard/recent-jd-decisions"),
  roleSummaries: () => apiClient.get("/dashboard/role-summaries"),
  highPriorityGaps: () => apiClient.get("/dashboard/high-priority-gaps"),
};
