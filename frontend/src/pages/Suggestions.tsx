import { useState, useMemo } from "react";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import {
  useSuggestions,
  useAcceptSuggestion,
  useRejectSuggestion,
} from "@/hooks/useSuggestions";
import { cn, formatDate } from "@/lib/utils";
import {
  Check,
  X,
  Loader2,
  AlertTriangle,
  Lightbulb,
  FileText,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface UpdateSuggestion {
  id: string;
  suggestion_type: "resume_update" | "gap_update" | "jd_tune";
  target_role_id: string;
  resume_id?: string;
  source_achievement_id?: string;
  title: string;
  content: Record<string, unknown>;
  impact_score: number;
  risk_level: "low" | "medium" | "high";
  status: "pending" | "accepted" | "rejected" | "applied";
  created_at: string;
  updated_at: string;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const TYPE_TABS = [
  { value: "", label: "全部" },
  { value: "resume_update", label: "resume_update" },
  { value: "gap_update", label: "gap_update" },
] as const;

const STATUS_TABS = [
  { value: "", label: "全部" },
  { value: "pending", label: "pending" },
  { value: "accepted", label: "accepted" },
  { value: "rejected", label: "rejected" },
] as const;

const TYPE_BADGE: Record<string, { label: string; cls: string; icon: typeof Lightbulb }> = {
  resume_update: {
    label: "简历更新",
    cls: "bg-blue-100 text-blue-700 border-blue-200",
    icon: FileText,
  },
  gap_update: {
    label: "Gap 更新",
    cls: "bg-orange-100 text-orange-700 border-orange-200",
    icon: AlertTriangle,
  },
  jd_tune: {
    label: "JD 定制",
    cls: "bg-purple-100 text-purple-700 border-purple-200",
    icon: Lightbulb,
  },
};

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  pending: { label: "待处理", cls: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  accepted: { label: "已接受", cls: "bg-green-100 text-green-700 border-green-200" },
  rejected: { label: "已拒绝", cls: "bg-red-100 text-red-700 border-red-200" },
  applied: { label: "已应用", cls: "bg-blue-100 text-blue-700 border-blue-200" },
};

const RISK_BADGE: Record<string, { label: string; cls: string }> = {
  low: { label: "低风险", cls: "bg-green-100 text-green-700 border-green-200" },
  medium: { label: "中风险", cls: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  high: { label: "高风险", cls: "bg-red-100 text-red-700 border-red-200" },
};

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function extractContentPreview(content: Record<string, unknown>): string {
  if (typeof content === "string") return content;
  const text =
    (content.text as string) ??
    (content.reasoning as string) ??
    (content.description as string) ??
    null;
  if (text) return text.length > 200 ? text.slice(0, 200) + "..." : text;
  const json = JSON.stringify(content);
  return json.length > 200 ? json.slice(0, 200) + "..." : json;
}

function formatImpactScore(score: number): string {
  if (score == null) return "-";
  return `${Math.round(score)}%`;
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function Badge({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        className,
      )}
    >
      {children}
    </span>
  );
}

function FilterBar({
  label,
  tabs,
  value,
  onChange,
}: {
  label: string;
  tabs: readonly { value: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium text-muted-foreground">{label}:</span>
      <div className="flex rounded-lg border bg-muted p-0.5">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onChange(tab.value)}
            className={cn(
              "rounded-md px-3 py-1 text-sm font-medium transition-colors",
              value === tab.value
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function SuggestionCard({
  suggestion,
  onAccept,
  onReject,
  isAccepting,
  isRejecting,
}: {
  suggestion: UpdateSuggestion;
  onAccept: () => void;
  onReject: () => void;
  isAccepting: boolean;
  isRejecting: boolean;
}) {
  const typeMeta = TYPE_BADGE[suggestion.suggestion_type] ?? {
    label: suggestion.suggestion_type,
    cls: "bg-gray-100 text-gray-700 border-gray-200",
    icon: Lightbulb,
  };
  const statusMeta = STATUS_BADGE[suggestion.status] ?? {
    label: suggestion.status,
    cls: "bg-gray-100 text-gray-700 border-gray-200",
  };
  const riskMeta = RISK_BADGE[suggestion.risk_level] ?? {
    label: suggestion.risk_level,
    cls: "bg-gray-100 text-gray-700 border-gray-200",
  };
  const TypeIcon = typeMeta.icon;
  const isPending = suggestion.status === "pending";
  const isMutating = isAccepting || isRejecting;

  return (
    <div className="rounded-lg border bg-card shadow-sm transition-shadow hover:shadow-md">
      {/* Card header */}
      <div className="flex items-start justify-between gap-3 border-b px-5 py-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
            <TypeIcon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <h4 className="font-semibold leading-snug">{suggestion.title}</h4>
            <p className="mt-0.5 text-xs text-muted-foreground">
              目标岗位 ID: {suggestion.target_role_id}
              {suggestion.resume_id && ` / 简历 ID: ${suggestion.resume_id}`}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Badge className={typeMeta.cls}>{typeMeta.label}</Badge>
          <Badge className={statusMeta.cls}>{statusMeta.label}</Badge>
          <Badge className={riskMeta.cls}>{riskMeta.label}</Badge>
        </div>
      </div>

      {/* Card body */}
      <div className="px-5 py-4">
        <p className="text-sm leading-relaxed text-muted-foreground">
          {extractContentPreview(suggestion.content)}
        </p>

        {/* Meta row */}
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <span>
            影响分数:{" "}
            <span className="font-medium text-foreground">
              {formatImpactScore(suggestion.impact_score)}
            </span>
          </span>
          <span>创建时间: {formatDate(suggestion.created_at)}</span>
        </div>
      </div>

      {/* Card actions */}
      {isPending && (
        <div className="flex items-center justify-end gap-2 border-t bg-muted/30 px-5 py-3">
          <button
            onClick={onReject}
            disabled={isMutating}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border border-red-200 bg-white px-3 py-1.5 text-sm font-medium text-red-600 transition-colors hover:bg-red-50",
              isMutating && "cursor-not-allowed opacity-50",
            )}
          >
            {isRejecting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <X className="h-3.5 w-3.5" />
            )}
            拒绝
          </button>
          <button
            onClick={onAccept}
            disabled={isMutating}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-green-700",
              isMutating && "cursor-not-allowed opacity-50",
            )}
          >
            {isAccepting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Check className="h-3.5 w-3.5" />
            )}
            接受
          </button>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export function Suggestions() {
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const filters = useMemo(() => {
    const f: Record<string, string> = {};
    if (typeFilter) f.suggestion_type = typeFilter;
    if (statusFilter) f.status = statusFilter;
    return f;
  }, [typeFilter, statusFilter]);

  const { data: suggestions = [], isLoading, isError } = useSuggestions(filters);
  const acceptMutation = useAcceptSuggestion();
  const rejectMutation = useRejectSuggestion();

  return (
    <>
      <Header
        title="更新建议"
        description="统一管理所有 Agent 生成的待确认更新建议"
      />
      <PageContainer>
        {/* Toolbar */}
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <FilterBar
            label="类型"
            tabs={TYPE_TABS}
            value={typeFilter}
            onChange={setTypeFilter}
          />
          <FilterBar
            label="状态"
            tabs={STATUS_TABS}
            value={statusFilter}
            onChange={setStatusFilter}
          />
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <span className="ml-3 text-muted-foreground">加载建议中...</span>
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            加载建议失败，请稍后重试。
          </div>
        )}

        {/* Empty */}
        {!isLoading && !isError && suggestions.length === 0 && (
          <div className="rounded-lg border bg-card p-8 text-center">
            <p className="text-muted-foreground">
              暂无待确认的更新建议。录入成果或更新岗位后，Agent
              会自动生成建议。
            </p>
          </div>
        )}

        {/* Card list */}
        {!isLoading && !isError && suggestions.length > 0 && (
          <div className="flex flex-col gap-4">
            {suggestions.map((s) => (
              <SuggestionCard
                key={s.id}
                suggestion={s}
                onAccept={() => acceptMutation.mutate(s.id)}
                onReject={() => rejectMutation.mutate(s.id)}
                isAccepting={acceptMutation.isPending && acceptMutation.variables === s.id}
                isRejecting={rejectMutation.isPending && rejectMutation.variables === s.id}
              />
            ))}
          </div>
        )}
      </PageContainer>
    </>
  );
}
