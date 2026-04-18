import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "@/lib/api";
import type { CareerProfile, ProfileUpsertRequest, ProfileCompleteness } from "@/types";

export function useProfile() {
  return useQuery<CareerProfile | null>({
    queryKey: ["profile"],
    queryFn: async () => {
      const { data } = await profileApi.get();
      return data;
    },
  });
}

export function useProfileCompleteness() {
  return useQuery<ProfileCompleteness>({
    queryKey: ["profile", "completeness"],
    queryFn: async () => {
      const { data } = await profileApi.completeness();
      return data;
    },
  });
}

export function useUpsertProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ProfileUpsertRequest) => {
      const res = await profileApi.upsert(data);
      return res.data as CareerProfile;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });
}
