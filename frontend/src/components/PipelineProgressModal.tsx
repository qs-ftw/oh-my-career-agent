import { useEffect, useRef } from "react";
import type { PipelineStep } from "@/hooks/usePipelineStream";
import { Loader2, CheckCircle, Clock, X } from "lucide-react";

interface Props {
  steps: PipelineStep[];
  isStreaming: boolean;
  error: string | null;
  onCancel: () => void;
}

export function PipelineProgressModal({ steps, isStreaming, error, onCancel }: Props) {
  const tokenEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    tokenEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps]);

  if (steps.length === 0 && !isStreaming) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg border bg-card p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">AI 分析中</h3>
          <button onClick={onCancel} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-3">
          {steps.map((step) => (
            <div key={step.node} className="rounded-md border p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {step.status === "completed" ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : step.status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : (
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className="text-sm font-medium">{step.label}</span>
                </div>
                {step.status === "completed" && step.duration_ms != null && (
                  <span className="text-xs text-muted-foreground">
                    {(step.duration_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>

              {step.status === "running" && step.tokens && (
                <div className="mt-2 max-h-32 overflow-y-auto rounded bg-muted/50 p-2">
                  <p className="whitespace-pre-wrap text-xs text-muted-foreground">
                    {step.tokens}
                  </p>
                  <div ref={tokenEndRef} />
                </div>
              )}

              {step.status === "completed" && step.summary && (
                <p className="mt-1 text-xs text-muted-foreground">{step.summary}</p>
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="mt-3 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button
            onClick={onCancel}
            className="rounded-md border px-4 py-1.5 text-sm hover:bg-accent"
          >
            {isStreaming ? "取消分析" : "关闭"}
          </button>
        </div>
      </div>
    </div>
  );
}
