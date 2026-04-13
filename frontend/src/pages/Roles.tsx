import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import {
  useRoles,
  useCreateRole,
  useDeleteRole,
  useUpdateRole,
  usePauseRole,
  useRole,
} from "@/hooks/useRoles";
import {
  Plus,
  Trash2,
  Eye,
  Loader2,
  Briefcase,
  X,
  AlertTriangle,
  Pause,
  Play,
  Pencil,
  Save,
} from "lucide-react";
import type { RoleCreateRequest } from "@/types";

const ROLE_TYPES = [
  "全职",
  "兼职",
  "实习",
  "远程",
  "合同工",
  "自由职业",
];

export function Roles() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useRoles();
  const createRole = useCreateRole();
  const deleteRole = useDeleteRole();
  const pauseRole = usePauseRole();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [editRoleId, setEditRoleId] = useState<string | null>(null);

  const roles = data?.items ?? [];

  const handlePause = (role: { id: string; status: string }) => {
    pauseRole.mutate({ id: role.id, pause: role.status === "active" });
  };

  return (
    <>
      <Header title="岗位目标" description="管理所有长期目标岗位" />
      <PageContainer>
        {/* Toolbar */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">
            岗位列表
            {data?.total !== undefined && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                共 {data.total} 个岗位
              </span>
            )}
          </h3>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            新增岗位
          </button>
        </div>

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

          {!isLoading && !isError && roles.length === 0 && (
            <div className="rounded-lg border bg-card p-8 text-center">
              <Briefcase className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">
                暂无岗位目标。点击「新增岗位」开始添加。
              </p>
            </div>
          )}

          {!isLoading && !isError && roles.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {roles.map((role) => (
                <RoleCard
                  key={role.id}
                  role={role}
                  onView={() => navigate(`/roles/${role.id}`)}
                  onDelete={() => setDeleteConfirmId(role.id)}
                  onEdit={() => setEditRoleId(role.id)}
                  onPause={() => handlePause(role)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <CreateRoleModal
            onClose={() => setShowCreateModal(false)}
            onSubmit={(data) => {
              createRole.mutate(data, {
                onSuccess: () => {
                  setShowCreateModal(false);
                },
              });
            }}
            isSubmitting={createRole.isPending}
          />
        )}

        {/* Edit Modal */}
        {editRoleId && (
          <EditRoleInlineModal
            roleId={editRoleId}
            onClose={() => setEditRoleId(null)}
          />
        )}

        {/* Delete Confirmation */}
        {deleteConfirmId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-sm rounded-lg bg-card p-6 shadow-xl">
              <h3 className="text-lg font-semibold">确认删除</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                确定要删除该岗位吗？此操作不可撤销。
              </p>
              <div className="mt-4 flex justify-end gap-3">
                <button
                  onClick={() => setDeleteConfirmId(null)}
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => {
                    deleteRole.mutate(deleteConfirmId, {
                      onSuccess: () => setDeleteConfirmId(null),
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
      </PageContainer>
    </>
  );
}

// ── RoleCard ──────────────────────────────────────────

function RoleCard({
  role,
  onView,
  onDelete,
  onEdit,
  onPause,
}: {
  role: {
    id: string;
    role_name: string;
    role_type: string;
    priority: number;
    status: string;
    required_skills: string[];
  };
  onView: () => void;
  onDelete: () => void;
  onEdit: () => void;
  onPause: () => void;
}) {
  const statusColor =
    role.status === "active"
      ? "bg-green-100 text-green-700"
      : role.status === "paused"
        ? "bg-yellow-100 text-yellow-700"
        : "bg-gray-100 text-gray-500";

  const statusLabel =
    role.status === "active" ? "进行中" : role.status === "paused" ? "已暂停" : "已删除";

  return (
    <div className="group rounded-lg border bg-card p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h4 className="truncate text-base font-semibold text-foreground">
            {role.role_name}
          </h4>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              {role.role_type}
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}
            >
              {statusLabel}
            </span>
          </div>
        </div>
        <div className="ml-2 flex items-center gap-1 text-xs text-muted-foreground">
          <span className="font-medium">
            P{role.priority}
          </span>
          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${Math.min(role.priority * 10, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Skills */}
      {role.required_skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {role.required_skills.slice(0, 5).map((skill) => (
            <span
              key={skill}
              className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
            >
              {skill}
            </span>
          ))}
          {role.required_skills.length > 5 && (
            <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              +{role.required_skills.length - 5}
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 flex items-center justify-end gap-2 border-t pt-3">
        <button
          onClick={onEdit}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
        >
          <Pencil className="h-3.5 w-3.5" />
          编辑
        </button>
        <button
          onClick={onPause}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
        >
          {role.status === "active" ? (
            <><Pause className="h-3.5 w-3.5" /> 暂停</>
          ) : (
            <><Play className="h-3.5 w-3.5" /> 恢复</>
          )}
        </button>
        <button
          onClick={onDelete}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
        >
          <Trash2 className="h-3.5 w-3.5" />
          删除
        </button>
        <button
          onClick={onView}
          className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Eye className="h-3.5 w-3.5" />
          查看详情
        </button>
      </div>
    </div>
  );
}

// ── EditRoleInlineModal ────────────────────────────────

function EditRoleInlineModal({
  roleId,
  onClose,
}: {
  roleId: string;
  onClose: () => void;
}) {
  const { data: role, isLoading } = useRole(roleId);
  const updateRole = useUpdateRole();
  const [form, setForm] = useState<RoleCreateRequest>({
    role_name: "",
    role_type: ROLE_TYPES[0],
    description: "",
    required_skills: [],
    bonus_skills: [],
    keywords: [],
    priority: 5,
  });
  const [skillsInput, setSkillsInput] = useState("");
  const [keywordsInput, setKeywordsInput] = useState("");
  const [initialized, setInitialized] = useState(false);

  // Sync form when role data loads
  if (role && !initialized) {
    setForm({
      role_name: role.role_name,
      role_type: role.role_type,
      description: role.description,
      required_skills: role.required_skills,
      bonus_skills: role.bonus_skills,
      keywords: role.keywords,
      priority: role.priority,
    });
    setSkillsInput(role.required_skills.join(", "));
    setKeywordsInput(role.keywords.join(", "));
    setInitialized(true);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    updateRole.mutate(
      {
        id: roleId,
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

  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <Loader2 className="h-6 w-6 animate-spin text-white" />
      </div>
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
            <select
              value={form.role_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, role_type: e.target.value }))
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            >
              {ROLE_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
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

// ── CreateRoleModal ───────────────────────────────────

function CreateRoleModal({
  onClose,
  onSubmit,
  isSubmitting,
}: {
  onClose: () => void;
  onSubmit: (data: RoleCreateRequest) => void;
  isSubmitting: boolean;
}) {
  const [form, setForm] = useState<RoleCreateRequest>({
    role_name: "",
    role_type: ROLE_TYPES[0],
    description: "",
    required_skills: [],
    bonus_skills: [],
    keywords: [],
    priority: 5,
    source_jd: "",
  });

  const [skillsInput, setSkillsInput] = useState("");
  const [keywordsInput, setKeywordsInput] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      ...form,
      required_skills: skillsInput
        ? skillsInput.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined,
      keywords: keywordsInput
        ? keywordsInput.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">新增岗位</h3>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* 岗位名称 */}
          <div>
            <label className="block text-sm font-medium">
              岗位名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={form.role_name}
              onChange={(e) =>
                setForm((f) => ({ ...f, role_name: e.target.value }))
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="例如：高级前端工程师"
            />
          </div>

          {/* 岗位类型 */}
          <div>
            <label className="block text-sm font-medium">
              岗位类型 <span className="text-red-500">*</span>
            </label>
            <select
              value={form.role_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, role_type: e.target.value }))
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            >
              {ROLE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* 岗位描述 */}
          <div>
            <label className="block text-sm font-medium">岗位描述</label>
            <textarea
              value={form.description ?? ""}
              onChange={(e) =>
                setForm((f) => ({ ...f, description: e.target.value }))
              }
              rows={3}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              placeholder="描述该岗位的主要职责和要求..."
            />
          </div>

          {/* 核心技能 */}
          <div>
            <label className="block text-sm font-medium">核心技能</label>
            <input
              type="text"
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="用逗号分隔，例如：React, TypeScript, Node.js"
            />
          </div>

          {/* 关键词 */}
          <div>
            <label className="block text-sm font-medium">关键词</label>
            <input
              type="text"
              value={keywordsInput}
              onChange={(e) => setKeywordsInput(e.target.value)}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="用逗号分隔，例如：全栈, 远程, 初创"
            />
          </div>

          {/* 优先级 */}
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
