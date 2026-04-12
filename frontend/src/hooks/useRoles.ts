import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { roleApi } from "@/lib/api";
import type { TargetRole, RoleCreateRequest } from "@/types";

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
