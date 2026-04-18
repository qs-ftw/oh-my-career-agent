import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { educationApi } from "@/lib/api";
import type { Education } from "@/types";

export function useEducations() {
  return useQuery<Education[]>({
    queryKey: ["educations"],
    queryFn: async () => {
      const { data } = await educationApi.list();
      return data;
    },
  });
}

export function useCreateEducation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await educationApi.create(data);
      return res.data as Education;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["educations"] });
    },
  });
}

export function useUpdateEducation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const res = await educationApi.update(id, data);
      return res.data as Education;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["educations"] });
    },
  });
}

export function useDeleteEducation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await educationApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["educations"] });
    },
  });
}
