import { useMutation, useQuery } from "@tanstack/react-query";
import { jdApi } from "@/lib/api";
import type { JDParsed, JDTailorResult } from "@/types";

interface JDRequestBody {
  raw_jd: string;
  mode?: "generate_new" | "tune_existing";
  base_resume_id?: string;
}

export function useJDParse() {
  return useMutation<JDParsed, Error, string>({
    mutationFn: async (rawJd: string) => {
      const { data } = await jdApi.parse({ raw_jd: rawJd });
      return data;
    },
  });
}

export function useJDTailor() {
  return useMutation<JDTailorResult, Error, JDRequestBody>({
    mutationFn: async (body: JDRequestBody) => {
      const { data } = await jdApi.tailor(body);
      return data;
    },
  });
}

export function useJDTask(taskId: string) {
  return useQuery<Record<string, unknown>>({
    queryKey: ["jd-task", taskId],
    queryFn: async () => {
      const { data } = await jdApi.getTask(taskId);
      return data;
    },
    enabled: !!taskId,
  });
}
