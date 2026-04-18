import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { achievementApi, suggestionApi } from "@/lib/api";
import type { Achievement, AchievementCreateRequest, UpdateSuggestion } from "@/types";

export function useAchievements() {
  return useQuery<Achievement[]>({
    queryKey: ["achievements"],
    queryFn: async () => {
      const { data } = await achievementApi.list();
      return data;
    },
  });
}

export function useAchievement(id: string) {
  return useQuery<Achievement>({
    queryKey: ["achievements", id],
    queryFn: async () => {
      const { data } = await achievementApi.get(id);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateAchievement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AchievementCreateRequest) => {
      const res = await achievementApi.create(data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
    },
  });
}

export function useAnalyzeAchievement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await achievementApi.analyze(id);
      return res.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      queryClient.invalidateQueries({ queryKey: ["achievements", id] });
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["gaps"] });
    },
  });
}

export function useUpdateAchievement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const res = await achievementApi.update(id, data);
      return res.data as Achievement;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteAchievement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await achievementApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
    },
  });
}

export function useSuggestionsForAchievement(achievementId: string | null) {
  return useQuery<UpdateSuggestion[]>({
    queryKey: ["suggestions", { achievement_id: achievementId }],
    queryFn: async () => {
      const { data } = await suggestionApi.list({ achievement_id: achievementId! });
      return data;
    },
    enabled: !!achievementId,
  });
}
