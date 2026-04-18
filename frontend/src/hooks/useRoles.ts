import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { roleApi } from "@/lib/api";
import type { TargetRole, RoleCreateRequest, RoleAnalysisResponse } from "@/types";

interface RolesListResponse {
  items: TargetRole[];
  total: number;
}

export function useRoles() {
  return useQuery<RolesListResponse>({
    queryKey: ["roles"],
    queryFn: async () => {
      const { data } = await roleApi.list();
      return data;
    },
  });
}

export function useRole(id: string) {
  return useQuery<TargetRole>({
    queryKey: ["roles", id],
    queryFn: async () => {
      const { data } = await roleApi.get(id);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RoleCreateRequest) => {
      const res = await roleApi.create(data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
  });
}

export function useUpdateRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<RoleCreateRequest> }) => {
      const res = await roleApi.update(id, data);
      return res.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["roles"] });
      queryClient.invalidateQueries({ queryKey: ["roles", variables.id] });
    },
  });
}

export function useDeleteRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await roleApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
  });
}

export function usePauseRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, pause }: { id: string; pause: boolean }) => {
      const { data } = await roleApi.update(id, { status: pause ? "paused" : "active" });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
  });
}

export function useInitRoleAssets() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await roleApi.init(id);
      return res.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["roles", id] });
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      queryClient.invalidateQueries({ queryKey: ["resumes", "role", id] });
      queryClient.invalidateQueries({ queryKey: ["gaps", "role", id] });
    },
  });
}

export function useAnalyzeJd() {
  return useMutation({
    mutationFn: async (raw_jd: string) => {
      const res = await roleApi.analyzeJd(raw_jd);
      return res.data as RoleAnalysisResponse;
    },
  });
}

export function useAnalyzeName() {
  return useMutation({
    mutationFn: async (role_name: string) => {
      const res = await roleApi.analyzeName(role_name);
      return res.data as RoleAnalysisResponse;
    },
  });
}
