import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import type { DashboardStats, JDRecentDecision, RoleSummary, GapSummary } from "@/types";

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

export function useRoleSummaries() {
  return useQuery<RoleSummary[]>({
    queryKey: ["dashboard", "role-summaries"],
    queryFn: async () => {
      const { data } = await dashboardApi.roleSummaries();
      return data;
    },
  });
}

export function useHighPriorityGaps() {
  return useQuery<GapSummary[]>({
    queryKey: ["dashboard", "high-priority-gaps"],
    queryFn: async () => {
      const { data } = await dashboardApi.highPriorityGaps();
      return data;
    },
  });
}
