import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { resumeApi } from "@/lib/api";
import type { Resume, ResumeContent, ResumeVersion, PaginatedResponse } from "@/types";

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
      const resp = data as PaginatedResponse<Resume>;
      return resp.items?.[0] ?? null;
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
