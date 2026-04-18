import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workExperienceApi } from "@/lib/api";
import type { WorkExperience } from "@/types";

export function useWorkExperiences() {
  return useQuery<WorkExperience[]>({
    queryKey: ["workExperiences"],
    queryFn: async () => {
      const { data } = await workExperienceApi.list();
      return data;
    },
  });
}

export function useCreateWorkExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await workExperienceApi.create(data);
      return res.data as WorkExperience;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workExperiences"] });
    },
  });
}

export function useUpdateWorkExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const res = await workExperienceApi.update(id, data);
      return res.data as WorkExperience;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workExperiences"] });
    },
  });
}

export function useDeleteWorkExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await workExperienceApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workExperiences"] });
    },
  });
}
