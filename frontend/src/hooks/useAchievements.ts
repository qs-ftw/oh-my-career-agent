import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { achievementApi } from "@/lib/api";
import type { Achievement, AchievementCreateRequest } from "@/types";

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
