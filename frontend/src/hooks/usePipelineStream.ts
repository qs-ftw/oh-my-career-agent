import { useState, useCallback, useRef } from "react";

export interface PipelineStep {
  node: string;
  label: string;
  status: "pending" | "running" | "completed";
  tokens: string;
  duration_ms?: number;
  summary?: string;
}

export function usePipelineStream() {
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback(async (url: string) => {
    setError(null);
    setSteps([]);
    setIsStreaming(true);
    abortRef.current = new AbortController();

    try {
      const response = await fetch(url, { signal: abortRef.current.signal });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));
            handleEvent(eventType, data, setSteps);
            eventType = "";
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err.message);
      }
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { steps, isStreaming, error, start, cancel, setSteps };
}

function handleEvent(
  type: string,
  data: Record<string, unknown>,
  setSteps: React.Dispatch<React.SetStateAction<PipelineStep[]>>,
) {
  if (type === "node_start") {
    setSteps((prev) => [
      ...prev,
      {
        node: data.node as string,
        label: data.label as string,
        status: "running",
        tokens: "",
      },
    ]);
  } else if (type === "token") {
    setSteps((prev) =>
      prev.map((s) =>
        s.node === data.node && s.status === "running"
          ? { ...s, tokens: s.tokens + (data.text as string) }
          : s
      )
    );
  } else if (type === "node_complete") {
    setSteps((prev) =>
      prev.map((s) =>
        s.node === data.node
          ? {
              ...s,
              status: "completed",
              duration_ms: data.duration_ms as number,
              summary: data.summary as string,
            }
          : s
      )
    );
  }
}
