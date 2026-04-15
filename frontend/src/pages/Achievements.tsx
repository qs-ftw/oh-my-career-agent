import { useState, useMemo, useCallback, type FormEvent } from "react";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import {
  useAchievements,
  useCreateAchievement,
  useAnalyzeAchievement,
} from "@/hooks/useAchievements";
import {
  useSuggestions,
  useAcceptSuggestion,
  useRejectSuggestion,
} from "@/hooks/useSuggestions";
import {
  Plus,
  Tag,
  Sparkles,
  Eye,
  Loader2,
  AlertTriangle,
  FileText,
  X,
  CheckCircle2,
  Clock,
  CircleDot,
  Layers,
  AlertCircle,
} from "lucide-react";
import type { Achievement, AchievementCreateRequest, UpdateSuggestion } from "@/types";

const SOURCE_TYPE_LABELS: Record<string, string> = {
  manual: "手动录入",
  git_commit: "Git 提交",
  slack_message: "Slack 消息",
};

const SOURCE_TYPES = ["manual", "git_commit", "slack_message"];

// ── Main Page ──────────────────────────────────────────

export function Achievements() {
  const { data, isLoading, isError } = useAchievements();
  const createAchievement = useCreateAchievement();
  const analyzeAchievement = useAnalyzeAchievement();

  // Fetch pending suggestions to determine which achievements have pending suggestions
  const { data: pendingSuggestions } = useSuggestions({ status: "pending" });

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"all" | "unanalyzed" | "pending" | "done">("all");
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const handleAnalyze = useCallback(
    (id: string) => {
      setAnalysisError(null);
      analyzeAchievement.mutate(id, {
        onSuccess: (result) => {
          if (result?.analysis_error) {
            setAnalysisError(`分析部分失败: ${result.analysis_error}`);
          }
        },
        onError: (err: Error) => {
          setAnalysisError(`分析失败: ${err.message || "请稍后重试"}`);
        },
      });
    },
    [analyzeAchievement]
  );

  const achievements = data ?? [];
  const selectedAchievement = selectedId
    ? achievements.find((a) => a.id === selectedId) ?? null
    : null;

  // Build a Set of achievement IDs that have pending suggestions
  const pendingAchievementIds = useMemo(() => {
    const ids = new Set<string>();
    if (pendingSuggestions) {
      for (const s of pendingSuggestions) {
        if (s.source_achievement_id) {
          ids.add(s.source_achievement_id);
        }
      }
    }
    return ids;
  }, [pendingSuggestions]);

  // Tab counts
  const tabCounts = useMemo(() => {
    const unanalyzed = achievements.filter((a) => !a.parsed_summary).length;
    const pending = achievements.filter(
      (a) => a.parsed_summary && pendingAchievementIds.has(a.id)
    ).length;
    const done = achievements.filter(
      (a) => a.parsed_summary && !pendingAchievementIds.has(a.id)
    ).length;
    return { all: achievements.length, unanalyzed, pending, done };
  }, [achievements, pendingAchievementIds]);

  // Filter achievements by active tab
  const filteredAchievements = useMemo(() => {
    switch (activeTab) {
      case "unanalyzed":
        return achievements.filter((a) => !a.parsed_summary);
      case "pending":
        return achievements.filter(
          (a) => a.parsed_summary && pendingAchievementIds.has(a.id)
        );
      case "done":
        return achievements.filter(
          (a) => a.parsed_summary && !pendingAchievementIds.has(a.id)
        );
      default:
        return achievements;
    }
  }, [achievements, activeTab, pendingAchievementIds]);

  const tabs = [
    { key: "all" as const, label: "全部", icon: Layers },
    { key: "unanalyzed" as const, label: "未分析", icon: CircleDot },
    { key: "pending" as const, label: "待处理", icon: Clock },
    { key: "done" as const, label: "已完成", icon: CheckCircle2 },
  ];

  return (
    <>
      <Header title="成果中心" description="管理所有沉淀下来的成果资产" />
      {/* Sticky toolbar */}
      <div className="sticky top-0 z-10 bg-card border-b">
        <PageContainer>
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <tab.icon className="h-3.5 w-3.5" />
                  {tab.label}
                  <span className={`ml-0.5 rounded-full px-1.5 py-0.5 text-xs ${
                    activeTab === tab.key
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}>
                    {tabCounts[tab.key]}
                  </span>
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              新增成果
            </button>
          </div>
        </PageContainer>
      </div>
      <PageContainer>
        {/* Content */}
        <div className="mt-4">
          {isLoading && (
            <div className="flex items-center justify-center rounded-lg border bg-card p-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">加载中...</span>
            </div>
          )}

          {isError && (
            <div className="flex items-center justify-center rounded-lg border border-red-200 bg-red-50 p-12">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span className="ml-2 text-red-600">加载失败，请稍后重试</span>
            </div>
          )}

          {!isLoading && !isError && filteredAchievements.length === 0 && (
            <div className="rounded-lg border bg-card p-8 text-center">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">
                {activeTab !== "all"
                  ? `没有${tabs.find((t) => t.key === activeTab)?.label ?? ""}的成果`
                  : "暂无成果记录"}
              </p>
              {activeTab === "all" && (
                <p className="mt-1 text-sm text-muted-foreground">
                  点击「新增成果」开始录入你的工作成果。
                </p>
              )}
            </div>
          )}

          {!isLoading && !isError && filteredAchievements.length > 0 && (
            <div className="space-y-4">
              {/* Analysis error toast */}
              {analysisError && (
                <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
                  <span className="text-sm text-red-700">{analysisError}</span>
                  <button
                    onClick={() => setAnalysisError(null)}
                    className="ml-auto shrink-0 rounded p-0.5 hover:bg-red-100"
                  >
                    <X className="h-3.5 w-3.5 text-red-500" />
                  </button>
                </div>
              )}
              {filteredAchievements.map((achievement) => (
                <AchievementCard
                  key={achievement.id}
                  achievement={achievement}
                  onAnalyze={() => handleAnalyze(achievement.id)}
                  isAnalyzing={
                    analyzeAchievement.isPending &&
                    analyzeAchievement.variables === achievement.id
                  }
                  onViewDetail={() => setSelectedId(achievement.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <CreateAchievementModal
            onClose={() => setShowCreateModal(false)}
            onSubmit={(data) => {
              createAchievement.mutate(data, {
                onSuccess: () => {
                  setShowCreateModal(false);
                },
              });
            }}
            isSubmitting={createAchievement.isPending}
          />
        )}

        {/* Detail Drawer */}
        {selectedAchievement && (
          <DetailDrawer
            achievement={selectedAchievement}
            onClose={() => setSelectedId(null)}
            onAnalyze={() => handleAnalyze(selectedAchievement.id)}
            isAnalyzing={
              analyzeAchievement.isPending &&
              analyzeAchievement.variables === selectedAchievement.id
            }
            analysisError={analysisError}
          />
        )}
      </PageContainer>
    </>
  );
}

// ── AchievementCard ────────────────────────────────────

function AchievementCard({
  achievement,
  onAnalyze,
  isAnalyzing,
  onViewDetail,
}: {
  achievement: Achievement;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  onViewDetail: () => void;
}) {
  const hasParsed = !!achievement.parsed_summary;
  const score = achievement.importance_score;

  const scoreColor =
    score >= 8
      ? "bg-orange-100 text-orange-700"
      : score >= 5
        ? "bg-blue-100 text-blue-700"
        : "bg-gray-100 text-gray-600";

  return (
    <div className="group rounded-lg border bg-card p-5 hover:shadow-md transition-shadow">
      {/* Left accent bar for timeline feel */}
      <div className="flex gap-4">
        <div className="flex flex-col items-center">
          <div className="h-3 w-3 rounded-full bg-primary mt-1.5 shrink-0" />
          <div className="w-px flex-1 bg-border" />
        </div>
        <div className="min-w-0 flex-1">
          {/* Title row */}
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h4 className="truncate text-base font-semibold text-foreground">
                {achievement.title}
              </h4>
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {new Date(achievement.created_at).toLocaleDateString("zh-CN")}
                </span>
                <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                  {SOURCE_TYPE_LABELS[achievement.source_type] ?? achievement.source_type}
                </span>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${scoreColor}`}
                >
                  重要度 {score}
                </span>
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="mt-3">
            {hasParsed ? (
              <p className="text-sm text-muted-foreground line-clamp-2">
                {achievement.parsed_summary}
              </p>
            ) : (
              <p className="text-sm italic text-muted-foreground/60">未分析</p>
            )}
          </div>

          {/* Tags */}
          {achievement.tags.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {achievement.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                >
                  <Tag className="mr-1 h-3 w-3" />
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="mt-4 flex items-center justify-end gap-2 border-t pt-3">
            {!hasParsed && (
              <button
                onClick={onAnalyze}
                disabled={isAnalyzing}
                className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 disabled:opacity-50 transition-colors"
              >
                {isAnalyzing ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5" />
                )}
                分析
              </button>
            )}
            <button
              onClick={onViewDetail}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Eye className="h-3.5 w-3.5" />
              详情
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── CreateAchievementModal ─────────────────────────────

function CreateAchievementModal({
  onClose,
  onSubmit,
  isSubmitting,
}: {
  onClose: () => void;
  onSubmit: (data: AchievementCreateRequest) => void;
  isSubmitting: boolean;
}) {
  const [form, setForm] = useState<AchievementCreateRequest>({
    source_type: "manual",
    title: "",
    raw_content: "",
    tags: [],
  });
  const [tagsInput, setTagsInput] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      ...form,
      tags: tagsInput
        ? tagsInput.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">新增成果</h3>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium">
              标题 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) =>
                setForm((f) => ({ ...f, title: e.target.value }))
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="例如：完成用户认证系统重构"
            />
          </div>

          {/* Source Type */}
          <div>
            <label className="block text-sm font-medium">
              来源类型 <span className="text-red-500">*</span>
            </label>
            <select
              value={form.source_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, source_type: e.target.value }))
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            >
              {SOURCE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {SOURCE_TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </div>

          {/* Raw Content */}
          <div>
            <label className="block text-sm font-medium">
              原始内容 <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              value={form.raw_content}
              onChange={(e) =>
                setForm((f) => ({ ...f, raw_content: e.target.value }))
              }
              rows={5}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              placeholder="描述你的工作成果，包括背景、技术方案、结果等..."
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium">标签</label>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="用逗号分隔，例如：前端, 重构, 性能优化"
            />
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isSubmitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              创建
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── SuggestionCard ─────────────────────────────────────

const SUGGESTION_TYPE_LABELS: Record<string, string> = {
  resume_update: "简历更新",
  gap_update: "Gap 更新",
  jd_tune: "JD 调整",
};

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

const SUGGESTION_STATUS_STYLES: Record<string, { label: string; color: string }> = {
  pending: { label: "待处理", color: "bg-yellow-100 text-yellow-700" },
  accepted: { label: "已采纳", color: "bg-green-100 text-green-700" },
  applied: { label: "已应用", color: "bg-green-100 text-green-700" },
  rejected: { label: "已拒绝", color: "bg-gray-100 text-gray-500" },
};

function SuggestionCard({
  suggestion,
  onAccept,
  onReject,
  isAccepting,
  isRejecting,
}: {
  suggestion: UpdateSuggestion;
  onAccept: (id: string) => void;
  onReject: (id: string) => void;
  isAccepting: boolean;
  isRejecting: boolean;
}) {
  const statusInfo = SUGGESTION_STATUS_STYLES[suggestion.status] ?? {
    label: suggestion.status,
    color: "bg-gray-100 text-gray-500",
  };
  const isPending = suggestion.status === "pending";

  return (
    <div className="rounded-md border p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground truncate">
              {suggestion.title}
            </span>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700">
              {SUGGESTION_TYPE_LABELS[suggestion.suggestion_type] ?? suggestion.suggestion_type}
            </span>
            <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${RISK_COLORS[suggestion.risk_level] ?? RISK_COLORS.low}`}>
              {suggestion.risk_level === "low" ? "低风险" : suggestion.risk_level === "medium" ? "中风险" : "高风险"}
            </span>
            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-muted text-muted-foreground">
              影响度 {suggestion.impact_score.toFixed(1)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {isPending ? (
            <>
              <button
                onClick={() => onReject(suggestion.id)}
                disabled={isRejecting}
                className="rounded-md border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted disabled:opacity-50 transition-colors"
              >
                {isRejecting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "拒绝"}
              </button>
              <button
                onClick={() => onAccept(suggestion.id)}
                disabled={isAccepting}
                className="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {isAccepting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "采纳"}
              </button>
            </>
          ) : (
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusInfo.color}`}>
              {statusInfo.label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── DetailDrawer (slide-in panel) ──────────────────────

function DetailDrawer({
  achievement,
  onClose,
  onAnalyze,
  isAnalyzing,
  analysisError,
}: {
  achievement: Achievement;
  onClose: () => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  analysisError?: string | null;
}) {
  const hasParsed = !!achievement.parsed_summary;

  // Fetch suggestions for this achievement
  const { data: suggestions } = useSuggestions({
    achievement_id: achievement.id,
  });

  const acceptSuggestion = useAcceptSuggestion();
  const rejectSuggestion = useRejectSuggestion();

  const pendingCount = suggestions?.filter((s) => s.status === "pending").length ?? 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50"
        onClick={onClose}
      />
      {/* Panel */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl overflow-y-auto bg-card shadow-xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-card px-6 py-4">
          <h3 className="text-lg font-semibold truncate pr-4">
            {achievement.title}
          </h3>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-muted transition-colors shrink-0"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Meta */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {new Date(achievement.created_at).toLocaleDateString("zh-CN")}
            </span>
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              {SOURCE_TYPE_LABELS[achievement.source_type] ?? achievement.source_type}
            </span>
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
              重要度 {achievement.importance_score}
            </span>
            {achievement.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
              >
                <Tag className="mr-1 h-3 w-3" />
                {tag}
              </span>
            ))}
          </div>

          {/* Raw Content */}
          <section>
            <h4 className="text-sm font-semibold text-foreground">原始内容</h4>
            <p className="mt-2 whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm text-foreground">
              {achievement.raw_content}
            </p>
          </section>

          {/* Parsed sections (only if analyzed) */}
          {hasParsed && (
            <>
              {/* Summary */}
              <section>
                <h4 className="text-sm font-semibold text-foreground">解析摘要</h4>
                <p className="mt-2 text-sm text-muted-foreground">
                  {achievement.parsed_summary}
                </p>
              </section>

              {/* Technical Points */}
              {achievement.technical_points && achievement.technical_points.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">技术要点</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.technical_points.map((point, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground"
                      >
                        {String(point.description ?? point.content ?? JSON.stringify(point))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Challenges */}
              {achievement.challenges && achievement.challenges.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">挑战</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.challenges.map((c, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-orange-50 px-3 py-2 text-sm text-orange-800"
                      >
                        {String(c.description ?? c.content ?? JSON.stringify(c))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Solutions */}
              {achievement.solutions && achievement.solutions.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">解决方案</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.solutions.map((s, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-green-50 px-3 py-2 text-sm text-green-800"
                      >
                        {String(s.description ?? s.content ?? JSON.stringify(s))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Metrics */}
              {achievement.metrics && achievement.metrics.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">量化指标</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.metrics.map((m, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-blue-50 px-3 py-2 text-sm text-blue-800"
                      >
                        {String(m.description ?? m.content ?? JSON.stringify(m))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Interview Points */}
              {achievement.interview_points && achievement.interview_points.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">面试要点</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.interview_points.map((point, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 rounded-md border bg-purple-50 px-3 py-2 text-sm text-purple-800"
                      >
                        <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Update Suggestions */}
              {suggestions && suggestions.length > 0 && (
                <section>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    更新建议
                    <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                      {suggestions.length}
                      {pendingCount > 0 && ` (${pendingCount} 待处理)`}
                    </span>
                  </h4>
                  <div className="mt-3 space-y-2">
                    {suggestions.map((sug) => (
                      <SuggestionCard
                        key={sug.id}
                        suggestion={sug}
                        onAccept={(id) => acceptSuggestion.mutate(id)}
                        onReject={(id) => rejectSuggestion.mutate(id)}
                        isAccepting={acceptSuggestion.isPending && acceptSuggestion.variables === sug.id}
                        isRejecting={rejectSuggestion.isPending && rejectSuggestion.variables === sug.id}
                      />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}

          {/* Un-analyzed prompt */}
          {!hasParsed && (
            <section className="rounded-lg border border-dashed p-6 text-center">
              <FileText className="mx-auto h-10 w-10 text-muted-foreground/40" />
              <p className="mt-3 text-sm text-muted-foreground">
                该成果尚未分析
              </p>
              {analysisError && (
                <div className="mt-3 flex items-center justify-center gap-2 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{analysisError}</span>
                </div>
              )}
              <button
                onClick={onAnalyze}
                disabled={isAnalyzing}
                className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {isAnalyzing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                开始分析
              </button>
            </section>
          )}
        </div>
      </div>
    </>
  );
}
