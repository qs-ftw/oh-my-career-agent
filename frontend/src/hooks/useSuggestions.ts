import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { suggestionApi } from "@/lib/api";
import type { UpdateSuggestion } from "@/types";

export function useSuggestions(filters?: Record<string, string>) {
  return useQuery<UpdateSuggestion[]>({
    queryKey: ["suggestions", filters],
    queryFn: async () => {
      const { data } = await suggestionApi.list(filters);
      return data;
    },
  });
}

export function useAcceptSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await suggestionApi.accept(id);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
    },
  });
}

export function useRejectSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await suggestionApi.reject(id);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
    },
  });
}
