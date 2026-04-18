import { useState, useRef, useEffect } from "react";
import { X, Loader2, Sparkles, Send, CheckCircle, Zap } from "lucide-react";
import { useInteractiveAnalysis } from "@/hooks/useInteractiveAnalysis";

interface InteractiveAnalysisPanelProps {
  achievementId: string;
  achievementTitle: string;
  onClose: () => void;
}

export function InteractiveAnalysisPanel({
  achievementId,
  achievementTitle,
  onClose,
}: InteractiveAnalysisPanelProps) {
  const {
    messages,
    readyToGenerate,
    sufficiency,
    isStarting,
    isSending,
    isGenerating,
    start,
    sendMessage,
    generate,
    reset,
    isActive,
  } = useInteractiveAnalysis(achievementId);

  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-start on mount
  useEffect(() => {
    if (!isActive) start();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || isSending) return;
    setInput("");
    sendMessage(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Sufficiency bar colors
  const barColor = (val: number) =>
    val >= 0.7 ? "bg-green-500" : val >= 0.4 ? "bg-yellow-500" : "bg-red-400";

  const DIMENSION_LABELS: Record<string, string> = {
    situation: "情境",
    task: "任务",
    action: "行动",
    result: "结果",
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[420px] flex flex-col bg-card border-l shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold flex items-center gap-1.5">
            <Sparkles className="h-4 w-4 text-primary" />
            AI 互动剖析
          </h3>
          <p className="text-xs text-muted-foreground truncate">{achievementTitle}</p>
        </div>
        <button
          onClick={() => { reset(); onClose(); }}
          className="rounded p-1 hover:bg-muted transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Sufficiency indicators */}
      {Object.keys(sufficiency).length > 0 && (
        <div className="px-4 py-2 border-b bg-muted/30">
          <div className="grid grid-cols-4 gap-2">
            {Object.entries(sufficiency).map(([key, val]) => (
              <div key={key} className="text-center">
                <div className="text-xs text-muted-foreground mb-1">
                  {DIMENSION_LABELS[key] ?? key}
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${barColor(val)}`}
                    style={{ width: `${Math.round(val * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {isStarting && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在分析成果内容...
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isSending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            思考中...
          </div>
        )}
        {isGenerating && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在生成最终成果...
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Ready to generate banner */}
      {readyToGenerate && !isGenerating && (
        <div className="px-4 py-2 border-t bg-green-50">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
            <span className="text-xs text-green-700 flex-1">信息已充分，可以生成最终成果</span>
            <button
              onClick={generate}
              className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 shrink-0"
            >
              <Sparkles className="h-3 w-3" />
              生成成果
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t px-4 py-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的回答..."
            rows={2}
            disabled={isSending || isGenerating || isStarting}
            className="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isSending || isGenerating || isStarting}
            className="rounded-md bg-primary p-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        {!isGenerating && !isStarting && isActive && (
          <div className="mt-2 flex items-center justify-between">
            <button
              onClick={generate}
              disabled={isSending}
              className="inline-flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors disabled:opacity-50"
            >
              <Zap className="h-3 w-3" />
              直接生成成果
            </button>
            <span className="text-xs text-muted-foreground">
              或输入 "够了" 自动生成
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
