import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import type { DashboardStats, JDRecentDecision } from "@/types";

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard", "stats"],
    queryFn: async () => {
      const { data } = await dashboardApi.stats();
      return data;
    },
  });
}

export function useRecentJdDecisions() {
  return useQuery<JDRecentDecision[]>({
    queryKey: ["dashboard", "jd-decisions"],
    queryFn: async () => {
      const { data } = await dashboardApi.recentJdDecisions();
      return data;
    },
  });
}
