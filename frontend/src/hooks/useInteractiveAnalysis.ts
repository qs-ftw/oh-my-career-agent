import { useState, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { achievementApi } from "@/lib/api";
import type { InteractiveChatResponse } from "@/types";

export function useInteractiveAnalysis(achievementId: string | null) {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<Array<{ role: "ai" | "user"; content: string }>>([]);
  const [readyToGenerate, setReadyToGenerate] = useState(false);
  const [sufficiency, setSufficiency] = useState<Record<string, number>>({});

  const startMutation = useMutation({
    mutationFn: async () => {
      if (!achievementId) throw new Error("No achievement ID");
      const { data } = await achievementApi.interactiveStart(achievementId);
      return data as InteractiveChatResponse;
    },
    onSuccess: (data) => {
      setMessages([{ role: "ai", content: data.reply }]);
      setSufficiency(data.sufficiency);
      setReadyToGenerate(data.ready_to_generate);
      // Invalidate so achievement card shows updated analysis_chat
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
    },
  });

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!achievementId) throw new Error("No achievement ID");
      const { data } = await achievementApi.interactiveChat(achievementId, message);
      return data as InteractiveChatResponse;
    },
    // Show user message IMMEDIATELY on mutate (before API response)
    onMutate: (message) => {
      setMessages((prev) => [...prev, { role: "user", content: message }]);
    },
    onSuccess: (data) => {
      // Add AI reply after the user message
      setMessages((prev) => [...prev, { role: "ai", content: data.reply }]);
      setSufficiency(data.sufficiency);
      setReadyToGenerate(data.ready_to_generate);
      // Real-time: invalidate so achievement card shows updated content
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
    },
    onError: (_err, _message) => {
      // Remove the optimistically added user message on error
      setMessages((prev) => {
        const next = [...prev];
        // Remove last user message if it was optimistically added
        if (next.length > 0 && next[next.length - 1].role === "user") {
          next.pop();
        }
        return next;
      });
    },
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!achievementId) throw new Error("No achievement ID");
      const { data } = await achievementApi.interactiveGenerate(achievementId);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
    },
  });

  const start = useCallback(() => startMutation.mutate(), [startMutation]);
  const sendMessage = useCallback(
    (msg: string) => chatMutation.mutate(msg),
    [chatMutation]
  );
  const generate = useCallback(() => generateMutation.mutate(), [generateMutation]);

  const reset = useCallback(() => {
    setMessages([]);
    setReadyToGenerate(false);
    setSufficiency({});
    startMutation.reset();
    chatMutation.reset();
    generateMutation.reset();
  }, [startMutation, chatMutation, generateMutation]);

  return {
    messages,
    readyToGenerate,
    sufficiency,
    isStarting: startMutation.isPending,
    isSending: chatMutation.isPending,
    isGenerating: generateMutation.isPending,
    start,
    sendMessage,
    generate,
    reset,
    isActive: messages.length > 0,
  };
}
