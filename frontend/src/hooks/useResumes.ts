import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { resumeApi } from "@/lib/api";
import type { Resume, ResumeContent, ResumeVersion } from "@/types";

export function useListResumes() {
  return useQuery<Resume[]>({
    queryKey: ["resumes"],
    queryFn: async () => {
      const { data } = await resumeApi.list();
      return data;
    },
  });
}

export function useResume(id: string) {
  return useQuery<Resume>({
    queryKey: ["resumes", id],
    queryFn: async () => {
      const { data } = await resumeApi.get(id);
      return data;
    },
    enabled: !!id,
  });
}

export function useRoleResume(roleId: string) {
  return useQuery<Resume | null>({
    queryKey: ["resumes", "role", roleId],
    queryFn: async () => {
      const { data } = await resumeApi.list({ target_role_id: roleId });
      const list = Array.isArray(data) ? data : [];
      return list[0] ?? null;
    },
    enabled: !!roleId,
  });
}

export function useUpdateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { resume_name?: string; content?: Partial<ResumeContent> } }) => {
      const res = await resumeApi.update(id, data);
      return res.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["resumes", variables.id] });
    },
  });
}

export function useDeleteResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await resumeApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
  });
}

export function useResumeVersions(id: string) {
  return useQuery<ResumeVersion[]>({
    queryKey: ["resumes", id, "versions"],
    queryFn: async () => {
      const { data } = await resumeApi.versions(id);
      return data;
    },
    enabled: !!id,
  });
}

export function useResumeVersion(resumeId: string, versionId: string | null) {
  return useQuery<{ id: string; version_no: number; content: ResumeContent }>({
    queryKey: ["resumes", resumeId, "versions", versionId],
    queryFn: async () => {
      const { data } = await resumeApi.getVersion(resumeId, versionId!);
      return data;
    },
    enabled: !!resumeId && !!versionId,
  });
}

export function useDeleteVersion(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (versionId: string) => {
      await resumeApi.deleteVersion(resumeId, versionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "versions"] });
    },
  });
}
