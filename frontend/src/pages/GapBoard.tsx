import { useState, useMemo } from "react";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { useGaps, useUpdateGap } from "@/hooks/useGaps";
import { useRoles } from "@/hooks/useRoles";
import {
  Columns,
  Filter,
  Target,
  ChevronRight,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import type { GapItem } from "@/types";

// ── Constants ──────────────────────────────────────────

const COLUMNS: { key: GapItem["status"]; label: string }[] = [
  { key: "open", label: "未开始" },
  { key: "in_progress", label: "进行中" },
  { key: "closed", label: "已完成" },
];

const GAP_TYPE_CONFIG: Record<
  GapItem["gap_type"],
  { label: string; color: string }
> = {
  missing: { label: "缺失", color: "bg-red-100 text-red-700" },
  weak_evidence: { label: "证据不足", color: "bg-orange-100 text-orange-700" },
  weak_expression: { label: "表达不足", color: "bg-yellow-100 text-yellow-700" },
  low_depth: { label: "深度不够", color: "bg-blue-100 text-blue-700" },
  low_metrics: { label: "量化不足", color: "bg-purple-100 text-purple-700" },
  jd_mismatch: { label: "JD 不匹配", color: "bg-gray-100 text-gray-600" },
};

const STATUS_PROGRESS_COLOR: Record<GapItem["status"], string> = {
  open: "bg-yellow-400",
  in_progress: "bg-blue-500",
  closed: "bg-green-500",
};

// ── Page Component ─────────────────────────────────────

export function GapBoard() {
  const [roleIdFilter, setRoleIdFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [selectedGap, setSelectedGap] = useState<GapItem | null>(null);

  const { data: rolesData } = useRoles();
  const { data: gaps, isLoading, isError } = useGaps(
    roleIdFilter !== "all" ? roleIdFilter : undefined
  );
  const updateGap = useUpdateGap();

  const roles = rolesData?.items ?? [];

  const filteredGaps = useMemo(() => {
    if (!gaps) return [];
    let result = gaps;
    if (priorityFilter !== "all") {
      const p = Number(priorityFilter);
      result = result.filter((g) => g.priority >= p);
    }
    return result;
  }, [gaps, priorityFilter]);

  const columnsData = useMemo(() => {
    const map: Record<string, GapItem[]> = {
      open: [],
      in_progress: [],
      closed: [],
    };
    for (const gap of filteredGaps) {
      if (map[gap.status]) {
        map[gap.status].push(gap);
      }
    }
    return map;
  }, [filteredGaps]);

  function handleStatusChange(newStatus: GapItem["status"]) {
    if (!selectedGap) return;
    updateGap.mutate(
      { id: selectedGap.id, data: { status: newStatus } },
      {
        onSuccess: () => {
          setSelectedGap({ ...selectedGap, status: newStatus });
        },
      }
    );
  }

  function handleProgressChange(value: number) {
    if (!selectedGap) return;
    updateGap.mutate(
      { id: selectedGap.id, data: { progress: value } },
      {
        onSuccess: () => {
          setSelectedGap({ ...selectedGap, progress: value });
        },
      }
    );
  }

  return (
    <>
      <Header title="Gap 看板" description="帮助理解自己离每个岗位还差什么" />
      <PageContainer>
        {/* Toolbar */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Filter className="h-4 w-4" />
            <span>筛选</span>
          </div>

          {/* Role filter */}
          <select
            value={roleIdFilter}
            onChange={(e) => setRoleIdFilter(e.target.value)}
            className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value="all">全部岗位</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.role_name}
              </option>
            ))}
          </select>

          {/* Priority filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value="all">全部优先级</option>
            <option value="7">P7 及以上</option>
            <option value="5">P5 及以上</option>
            <option value="3">P3 及以上</option>
          </select>

          <div className="ml-auto text-sm text-muted-foreground">
            共 {filteredGaps.length} 个 Gap
          </div>
        </div>

        {/* Kanban Board */}
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

          {!isLoading && !isError && (
            <div className="grid grid-cols-3 gap-6">
              {COLUMNS.map((col) => {
                const items = columnsData[col.key] ?? [];
                return (
                  <div
                    key={col.key}
                    className="rounded-lg border bg-muted/30"
                  >
                    {/* Column header */}
                    <div className="flex items-center justify-between border-b px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Columns className="h-4 w-4 text-muted-foreground" />
                        <h4 className="text-sm font-semibold">{col.label}</h4>
                      </div>
                      <span className="inline-flex items-center justify-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        {items.length}
                      </span>
                    </div>

                    {/* Column body */}
                    <div className="space-y-3 p-3 min-h-[200px]">
                      {items.length === 0 && (
                        <div className="flex items-center justify-center rounded-lg border border-dashed py-8 text-xs text-muted-foreground">
                          暂无 Gap
                        </div>
                      )}
                      {items.map((gap) => (
                        <GapCard
                          key={gap.id}
                          gap={gap}
                          onClick={() => setSelectedGap(gap)}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Detail Drawer */}
        {selectedGap && (
          <GapDetailDrawer
            gap={selectedGap}
            onClose={() => setSelectedGap(null)}
            onStatusChange={handleStatusChange}
            onProgressChange={handleProgressChange}
            isUpdating={updateGap.isPending}
          />
        )}
      </PageContainer>
    </>
  );
}

// ── Gap Card ───────────────────────────────────────────

function GapCard({
  gap,
  onClick,
}: {
  gap: GapItem;
  onClick: () => void;
}) {
  const typeConfig = GAP_TYPE_CONFIG[gap.gap_type];
  const progressColor = STATUS_PROGRESS_COLOR[gap.status];

  return (
    <button
      onClick={onClick}
      className="w-full rounded-lg border bg-card p-3 text-left hover:shadow-md transition-shadow group"
    >
      {/* Skill name + priority */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm font-semibold text-foreground leading-snug">
          {gap.skill_name}
        </span>
        <div className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
          <Target className="h-3 w-3" />
          <span className="font-medium">P{gap.priority}</span>
        </div>
      </div>

      {/* Gap type badge */}
      <div className="mt-2">
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeConfig.color}`}
        >
          {typeConfig.label}
        </span>
      </div>

      {/* Progress bar */}
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all ${progressColor}`}
          style={{ width: `${gap.progress * 100}%` }}
        />
      </div>

      {/* Current / Target state preview */}
      <div className="mt-2 space-y-1">
        <div className="flex items-start gap-1 text-xs text-muted-foreground">
          <span className="shrink-0 font-medium">现状:</span>
          <span className="line-clamp-1">{gap.current_state || "-"}</span>
        </div>
        <div className="flex items-start gap-1 text-xs text-muted-foreground">
          <span className="shrink-0 font-medium">目标:</span>
          <span className="line-clamp-1">{gap.target_state || "-"}</span>
        </div>
      </div>

      {/* Expand indicator */}
      <div className="mt-2 flex justify-end">
        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50 group-hover:text-muted-foreground transition-colors" />
      </div>
    </button>
  );
}

// ── Detail Drawer ──────────────────────────────────────

function GapDetailDrawer({
  gap,
  onClose,
  onStatusChange,
  onProgressChange,
  isUpdating,
}: {
  gap: GapItem;
  onClose: () => void;
  onStatusChange: (status: GapItem["status"]) => void;
  onProgressChange: (value: number) => void;
  isUpdating: boolean;
}) {
  const typeConfig = GAP_TYPE_CONFIG[gap.gap_type];
  const progressColor = STATUS_PROGRESS_COLOR[gap.status];

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Drawer panel */}
      <div className="relative w-full max-w-md flex flex-col bg-card shadow-xl animate-in slide-in-from-right duration-200">
        {/* Drawer header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h3 className="text-lg font-semibold">Gap 详情</h3>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-muted transition-colors"
          >
            <ChevronRight className="h-5 w-5 rotate-180" />
          </button>
        </div>

        {/* Drawer body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Skill name */}
          <div>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              技能名称
            </span>
            <p className="mt-1 text-base font-semibold">{gap.skill_name}</p>
          </div>

          {/* Gap type */}
          <div>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Gap 类型
            </span>
            <div className="mt-1">
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${typeConfig.color}`}
              >
                {typeConfig.label}
              </span>
            </div>
          </div>

          {/* Priority */}
          <div>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              优先级
            </span>
            <div className="mt-1 flex items-center gap-2">
              <span className="text-sm font-medium">P{gap.priority}</span>
              <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{
                    width: `${Math.min(gap.priority * 10, 100)}%`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Current state */}
          <div>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              现状
            </span>
            <p className="mt-1 text-sm whitespace-pre-wrap rounded-md border bg-background p-3">
              {gap.current_state || "无"}
            </p>
          </div>

          {/* Target state */}
          <div>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              目标状态
            </span>
            <p className="mt-1 text-sm whitespace-pre-wrap rounded-md border bg-background p-3">
              {gap.target_state || "无"}
            </p>
          </div>

          {/* Progress */}
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                进度
              </span>
              <span className="text-sm font-medium">
                {Math.round(gap.progress * 100)}%
              </span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full rounded-full transition-all ${progressColor}`}
                style={{ width: `${gap.progress * 100}%` }}
              />
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={gap.progress}
              onChange={(e) => onProgressChange(Number(e.target.value))}
              disabled={isUpdating}
              className="mt-2 w-full accent-primary"
            />
          </div>

          {/* Evidence */}
          {gap.evidence && Object.keys(gap.evidence).length > 0 && (
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                证据
              </span>
              <pre className="mt-1 overflow-x-auto rounded-md border bg-background p-3 text-xs">
                {JSON.stringify(gap.evidence, null, 2)}
              </pre>
            </div>
          )}

          {/* Improvement plan */}
          {gap.improvement_plan && Object.keys(gap.improvement_plan).length > 0 && (
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                改进计划
              </span>
              <pre className="mt-1 overflow-x-auto rounded-md border bg-background p-3 text-xs">
                {JSON.stringify(gap.improvement_plan, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Drawer footer: status toggle */}
        <div className="border-t px-6 py-4">
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            状态
          </span>
          <div className="mt-2 flex gap-2">
            {COLUMNS.map((col) => {
              const isActive = gap.status === col.key;
              return (
                <button
                  key={col.key}
                  onClick={() => onStatusChange(col.key)}
                  disabled={isUpdating}
                  className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "border hover:bg-muted"
                  }`}
                >
                  {col.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
