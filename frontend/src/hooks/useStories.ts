import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { storyApi } from "@/lib/api";
import type { InterviewStory } from "@/types";

interface StoriesListResponse {
  items: InterviewStory[];
  total: number;
}

export function useStories(theme?: string, sourceType?: string) {
  return useQuery<StoriesListResponse>({
    queryKey: ["stories", theme, sourceType],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (theme) params.theme = theme;
      if (sourceType) params.source_type = sourceType;
      const { data } = await storyApi.list(params);
      return data;
    },
  });
}

export function useRebuildStories() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (achievementId: string) => {
      const res = await storyApi.rebuild(achievementId);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stories"] });
    },
  });
}

export function useUpdateStory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: unknown }) => {
      const res = await storyApi.update(id, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stories"] });
    },
  });
}
