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
};

// ── Resume APIs ────────────────────────────────────────
export const resumeApi = {
  list: (params?: Record<string, string>) =>
    apiClient.get("/resumes", { params }),
  get: (id: string) => apiClient.get(`/resumes/${id}`),
  update: (id: string, data: unknown) =>
    apiClient.patch(`/resumes/${id}`, data),
  versions: (id: string) => apiClient.get(`/resumes/${id}/versions`),
  deleteVersion: (resumeId: string, versionId: string) =>
    apiClient.delete(`/resumes/${resumeId}/versions/${versionId}`),
  applySuggestion: (id: string, suggestionId: string) =>
    apiClient.post(`/resumes/${id}/apply-suggestion`, { suggestion_id: suggestionId }),
};

// ── Achievement APIs ───────────────────────────────────
export const achievementApi = {
  list: () => apiClient.get("/achievements"),
  get: (id: string) => apiClient.get(`/achievements/${id}`),
  create: (data: unknown) => apiClient.post("/achievements", data),
  analyze: (id: string) => apiClient.post(`/achievements/${id}/analyze`),
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
