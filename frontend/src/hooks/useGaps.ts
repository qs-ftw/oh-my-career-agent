import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { gapApi } from "@/lib/api";
import type { GapItem } from "@/types";

export function useGaps(roleId?: string) {
  return useQuery<GapItem[]>({
    queryKey: ["gaps", roleId],
    queryFn: async () => {
      const { data } = await gapApi.list(roleId);
      return data;
    },
  });
}

export function useGapsForRole(roleId: string) {
  return useQuery<GapItem[]>({
    queryKey: ["gaps", "role", roleId],
    queryFn: async () => {
      const { data } = await gapApi.byRole(roleId);
      return data;
    },
    enabled: !!roleId,
  });
}

export function useUpdateGap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { status?: string; progress?: number } }) => {
      const res = await gapApi.update(id, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gaps"] });
    },
  });
}
