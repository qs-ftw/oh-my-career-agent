import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { useRole, useDeleteRole, useInitRoleAssets } from "@/hooks/useRoles";
import { useRoleResume } from "@/hooks/useResumes";
import { useGapsForRole, useUpdateGap } from "@/hooks/useGaps";
import { resumeApi } from "@/lib/api";
import {
  ChevronRight,
  Loader2,
  AlertTriangle,
  Trash2,
  Pencil,
  Briefcase,
  Tag,
  FileText,
  GitCompareArrows,
  ArrowLeft,
  X,
  Save,
  Download,
} from "lucide-react";

export function RoleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: role, isLoading, isError } = useRole(id ?? "");
  const { data: resume } = useRoleResume(id ?? "");
  const { data: gaps } = useGapsForRole(id ?? "");
  const deleteRole = useDeleteRole();
  const initAssets = useInitRoleAssets();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  if (isLoading) {
    return (
      <>
        <Header title="岗位详情" />
        <PageContainer>
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">加载中...</span>
          </div>
        </PageContainer>
      </>
    );
  }

  if (isError || !role) {
    return (
      <>
        <Header title="岗位详情" />
        <PageContainer>
          <div className="flex items-center justify-center rounded-lg border border-red-200 bg-red-50 p-12">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="ml-2 text-red-600">加载失败，请稍后重试</span>
          </div>
        </PageContainer>
      </>
    );
  }

  const statusColor =
    role.status === "active"
      ? "bg-green-100 text-green-700"
      : role.status === "paused"
        ? "bg-yellow-100 text-yellow-700"
        : "bg-gray-100 text-gray-500";

  const statusLabel =
    role.status === "active" ? "进行中" : role.status === "paused" ? "已暂停" : "已删除";

  return (
    <>
      <Header title={role.role_name} description="查看岗位完整职业资产情况" />
      <PageContainer>
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1 text-sm text-muted-foreground">
          <button
            onClick={() => navigate("/roles")}
            className="hover:text-foreground transition-colors inline-flex items-center gap-1"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            岗位列表
          </button>
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="text-foreground font-medium">{role.role_name}</span>
        </nav>

        {/* Action buttons */}
        <div className="mt-4 flex items-center gap-2">
          <button
            onClick={() => setShowEditModal(true)}
            className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
          >
            <Pencil className="h-3.5 w-3.5" />
            编辑
          </button>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="inline-flex items-center gap-1.5 rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5" />
            删除
          </button>
        </div>

        {/* Sections */}
        <div className="mt-6 space-y-6">
          {/* 基本信息 */}
          <section className="rounded-lg border bg-card p-5">
            <h3 className="flex items-center gap-2 text-base font-semibold">
              <Briefcase className="h-4 w-4 text-primary" />
              基本信息
            </h3>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <InfoField label="岗位名称">
                <span className="text-sm">{role.role_name}</span>
              </InfoField>
              <InfoField label="岗位类型">
                <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                  {role.role_type}
                </span>
              </InfoField>
              <InfoField label="状态">
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}
                >
                  {statusLabel}
                </span>
              </InfoField>
              <InfoField label="优先级">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">P{role.priority}</span>
                  <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{
                        width: `${Math.min(role.priority * 10, 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </InfoField>
            </div>
            {role.description && (
              <div className="mt-4">
                <span className="text-sm text-muted-foreground">描述</span>
                <p className="mt-1 text-sm whitespace-pre-wrap">{role.description}</p>
              </div>
            )}
          </section>

          {/* 技能要求 */}
          <section className="rounded-lg border bg-card p-5">
            <h3 className="flex items-center gap-2 text-base font-semibold">
              <Tag className="h-4 w-4 text-primary" />
              技能要求
            </h3>
            <div className="mt-4">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
                必备技能
              </p>
              {role.required_skills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {role.required_skills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-md bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">暂无必备技能</p>
              )}
            </div>
            {role.bonus_skills.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
                  加分技能
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {role.bonus_skills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-md bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* 关键词 */}
          <section className="rounded-lg border bg-card p-5">
            <h3 className="flex items-center gap-2 text-base font-semibold">
              <Tag className="h-4 w-4 text-primary" />
              关键词
            </h3>
            <div className="mt-3">
              {role.keywords.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {role.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded-md bg-purple-100 px-2.5 py-1 text-xs font-medium text-purple-700"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">暂无关键词</p>
              )}
            </div>
          </section>

          {/* 简历 */}
          <section className="rounded-lg border bg-card p-5">
            <h3 className="flex items-center gap-2 text-base font-semibold">
              <FileText className="h-4 w-4 text-primary" />
              简历
            </h3>
            <div className="mt-3">
              {resume ? (
                <div className="space-y-3 rounded-md border p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{resume.resume_name}</p>
                      <p className="text-xs text-muted-foreground">
                        版本 {resume.current_version_no}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => initAssets.mutate(id ?? "")}
                        disabled={initAssets.isPending}
                        className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50 transition-colors"
                      >
                        {initAssets.isPending ? "生成中..." : "重新生成"}
                      </button>
                      <button
                        onClick={async () => {
                          try {
                            const { data } = await resumeApi.exportPdf(resume.id);
                            const url = URL.createObjectURL(data);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `${resume.resume_name.replace(/\s+/g, "_")}.pdf`;
                            a.click();
                            URL.revokeObjectURL(url);
                          } catch (err) {
                            console.error("Export PDF failed:", err);
                          }
                        }}
                        className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors inline-flex items-center gap-1"
                      >
                        <Download className="h-3 w-3" />
                        导出 PDF
                      </button>
                      <button
                        onClick={() => navigate(`/resumes/${resume.id}`)}
                        className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                      >
                        查看简历
                      </button>
                    </div>
                  </div>

                  {/* Match Score Progress Bars */}
                  <div className="space-y-2">
                    <div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">匹配度</span>
                        <span className={`font-bold ${(resume.match_score ?? 0) >= 70 ? "text-green-600" : (resume.match_score ?? 0) >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                          {(resume.match_score ?? 0).toFixed(0)}%
                        </span>
                      </div>
                      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className={`h-full rounded-full transition-all ${(resume.match_score ?? 0) >= 70 ? "bg-green-500" : (resume.match_score ?? 0) >= 40 ? "bg-yellow-500" : "bg-red-500"}`}
                          style={{ width: `${Math.min(resume.match_score ?? 0, 100)}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">完整度</span>
                        <span className={`font-bold ${(resume.completeness_score ?? 0) >= 70 ? "text-green-600" : (resume.completeness_score ?? 0) >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                          {(resume.completeness_score ?? 0).toFixed(0)}%
                        </span>
                      </div>
                      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className={`h-full rounded-full transition-all ${(resume.completeness_score ?? 0) >= 70 ? "bg-green-500" : (resume.completeness_score ?? 0) >= 40 ? "bg-yellow-500" : "bg-red-500"}`}
                          style={{ width: `${Math.min(resume.completeness_score ?? 0, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6">
                  <FileText className="mx-auto h-10 w-10 text-muted-foreground/40" />
                  <p className="mt-2 text-sm text-muted-foreground">暂无简历</p>
                  <button
                    onClick={() => initAssets.mutate(id ?? "")}
                    disabled={initAssets.isPending}
                    className="mt-3 rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  >
                    {initAssets.isPending ? (
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                        生成中...
                      </span>
                    ) : (
                      "生成简历"
                    )}
                  </button>
                </div>
              )}
            </div>
          </section>

          {/* Gap 列表 */}
          <section className="rounded-lg border bg-card p-5">
            <h3 className="flex items-center gap-2 text-base font-semibold">
              <GitCompareArrows className="h-4 w-4 text-primary" />
              Gap 列表
            </h3>
            <div className="mt-3">
              {gaps && gaps.length > 0 ? (
                <div className="space-y-2">
                  {gaps.map((gap) => (
                    <GapCard key={gap.id} gap={gap} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-6">
                  <GitCompareArrows className="mx-auto h-10 w-10 text-muted-foreground/40" />
                  <p className="mt-2 text-sm text-muted-foreground">暂无 Gap 分析</p>
                  <p className="mt-1 text-xs text-muted-foreground/70">生成简历后将自动分析技能差距</p>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Delete Confirmation */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-sm rounded-lg bg-card p-6 shadow-xl">
              <h3 className="text-lg font-semibold">确认删除</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                确定要删除岗位「{role.role_name}」吗？此操作不可撤销。
              </p>
              <div className="mt-4 flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => {
                    deleteRole.mutate(role.id, {
                      onSuccess: () => navigate("/roles"),
                    });
                  }}
                  disabled={deleteRole.isPending}
                  className="inline-flex items-center gap-1.5 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {deleteRole.isPending && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  )}
                  删除
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && role && (
          <EditRoleModal
            role={role}
            onClose={() => setShowEditModal(false)}
          />
        )}
      </PageContainer>
    </>
  );
}

// ── Helper components ─────────────────────────────────

function InfoField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <div className="mt-1">{children}</div>
    </div>
  );
}

// ── EditRoleModal ─────────────────────────────────────

import { useUpdateRole } from "@/hooks/useRoles";
import type { TargetRole, RoleCreateRequest, GapItem } from "@/types";

function EditRoleModal({
  role,
  onClose,
}: {
  role: TargetRole;
  onClose: () => void;
}) {
  const updateRole = useUpdateRole();
  const [form, setForm] = useState<RoleCreateRequest>({
    role_name: role.role_name,
    role_type: role.role_type,
    description: role.description,
    required_skills: role.required_skills,
    bonus_skills: role.bonus_skills,
    keywords: role.keywords,
    priority: role.priority,
  });

  const [skillsInput, setSkillsInput] = useState(
    role.required_skills.join(", ")
  );
  const [keywordsInput, setKeywordsInput] = useState(
    role.keywords.join(", ")
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    updateRole.mutate(
      {
        id: role.id,
        data: {
          ...form,
          required_skills: skillsInput
            ? skillsInput.split(",").map((s) => s.trim()).filter(Boolean)
            : undefined,
          keywords: keywordsInput
            ? keywordsInput.split(",").map((s) => s.trim()).filter(Boolean)
            : undefined,
        },
      },
      { onSuccess: onClose }
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">编辑岗位</h3>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium">岗位名称</label>
            <input
              type="text"
              required
              value={form.role_name}
              onChange={(e) =>
                setForm((f) => ({ ...f, role_name: e.target.value }))
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">岗位类型</label>
            <input
              type="text"
              value={form.role_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, role_type: e.target.value }))
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">岗位描述</label>
            <textarea
              value={form.description ?? ""}
              onChange={(e) =>
                setForm((f) => ({ ...f, description: e.target.value }))
              }
              rows={3}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">核心技能</label>
            <input
              type="text"
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="用逗号分隔"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">关键词</label>
            <input
              type="text"
              value={keywordsInput}
              onChange={(e) => setKeywordsInput(e.target.value)}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="用逗号分隔"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">
              优先级: <span className="text-primary font-bold">{form.priority ?? 5}</span>
            </label>
            <input
              type="range"
              min={0}
              max={10}
              step={1}
              value={form.priority ?? 5}
              onChange={(e) =>
                setForm((f) => ({ ...f, priority: Number(e.target.value) }))
              }
              className="mt-1 w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0 - 低</span>
              <span>10 - 高</span>
            </div>
          </div>

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
              disabled={updateRole.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {updateRole.isPending && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              <Save className="h-3.5 w-3.5" />
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── GapCard ─────────────────────────────────────────────

const GAP_TYPE_LABELS: Record<string, string> = {
  missing: "技能缺失",
  weak_evidence: "证据不足",
  weak_expression: "表达薄弱",
  low_depth: "深度不够",
  low_metrics: "量化不足",
  jd_mismatch: "JD 不匹配",
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  open: { label: "未开始", color: "bg-gray-100 text-gray-600" },
  in_progress: { label: "进行中", color: "bg-blue-100 text-blue-600" },
  closed: { label: "已关闭", color: "bg-green-100 text-green-600" },
};

function GapCard({ gap }: { gap: GapItem }) {
  const updateGap = useUpdateGap();
  const statusInfo = STATUS_LABELS[gap.status] ?? { label: gap.status, color: "bg-gray-100 text-gray-600" };

  const cycleStatus = () => {
    const next = gap.status === "open" ? "in_progress" : gap.status === "in_progress" ? "closed" : "open";
    updateGap.mutate({ id: gap.id, data: { status: next } });
  };

  return (
    <div className="rounded-md border p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="rounded px-1.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-700">
            P{gap.priority}
          </span>
          <span className="text-sm font-medium">{gap.skill_name}</span>
          <span className="text-xs text-muted-foreground">
            {GAP_TYPE_LABELS[gap.gap_type] ?? gap.gap_type}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={cycleStatus}
            className={`text-xs px-1.5 py-0.5 rounded ${statusInfo.color}`}
          >
            {statusInfo.label}
          </button>
          <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full" style={{ width: `${gap.progress}%` }} />
          </div>
        </div>
      </div>
      {(gap.current_state || gap.target_state) && (
        <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
          {gap.current_state && (
            <div>
              <span className="font-medium text-muted-foreground">现状：</span>
              <span>{gap.current_state}</span>
            </div>
          )}
          {gap.target_state && (
            <div>
              <span className="font-medium text-muted-foreground">目标：</span>
              <span>{gap.target_state}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
