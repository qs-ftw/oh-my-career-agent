import { useState } from "react";
import { Loader2, X, Zap, Sparkles, CheckCircle } from "lucide-react";
import { useAnalyzeName, useCreateRole } from "@/hooks/useRoles";
import type { RoleAnalysisResponse, RoleCreateRequest } from "@/types";

interface Props {
  onClose: () => void;
}

export function CreateRoleQuick({ onClose }: Props) {
  const analyzeName = useAnalyzeName();
  const createRole = useCreateRole();

  const [roleName, setRoleName] = useState("");
  const [preview, setPreview] = useState<RoleAnalysisResponse | null>(null);
  const [editData, setEditData] = useState<RoleAnalysisResponse | null>(null);

  const handleAnalyze = () => {
    if (!roleName.trim()) return;
    analyzeName.mutate(roleName.trim(), {
      onSuccess: (data) => {
        setPreview(data);
        setEditData(data);
      },
    });
  };

  const handleCreate = (skipInit: boolean) => {
    if (!editData) return;
    const payload: RoleCreateRequest = {
      role_name: editData.role_name,
      role_type: editData.role_type || "全职",
      description: editData.description,
      required_skills: editData.required_skills,
      bonus_skills: editData.bonus_skills,
      keywords: editData.keywords,
      skip_init: skipInit,
    };
    createRole.mutate(payload, { onSuccess: onClose });
  };

  const updateField = (field: keyof RoleAnalysisResponse, value: string | string[]) => {
    if (!editData) return;
    setEditData({ ...editData, [field]: value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-lg bg-card shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h3 className="text-lg font-semibold">快捷创建岗位</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!preview ? (
            /* Step 1: Enter role name */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium">岗位名称</label>
                <input
                  type="text"
                  value={roleName}
                  onChange={(e) => setRoleName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="例如：高级前端工程师"
                  autoFocus
                />
              </div>
              <button
                onClick={handleAnalyze}
                disabled={!roleName.trim() || analyzeName.isPending}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {analyzeName.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4" />
                    分析岗位
                  </>
                )}
              </button>
              {analyzeName.isError && (
                <p className="text-sm text-red-500">分析失败，请重试</p>
              )}
            </div>
          ) : (
            /* Step 2: Preview & Edit */
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" />
                分析完成，可编辑后提交
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium">岗位名称</label>
                  <input
                    type="text"
                    value={editData!.role_name}
                    onChange={(e) => updateField("role_name", e.target.value)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium">岗位类型</label>
                  <input
                    type="text"
                    value={editData!.role_type}
                    onChange={(e) => updateField("role_type", e.target.value)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">岗位描述</label>
                <textarea
                  value={editData!.description}
                  onChange={(e) => updateField("description", e.target.value)}
                  rows={5}
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium">核心技能</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.required_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                    >
                      {skill}
                      <button
                        onClick={() => {
                          const updated = editData!.required_skills.filter((_, i) => i !== idx);
                          updateField("required_skills", updated);
                        }}
                        className="text-blue-400 hover:text-blue-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">加分技能</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.bonus_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-green-50 px-2 py-0.5 text-xs text-green-700"
                    >
                      {skill}
                      <button
                        onClick={() => {
                          const updated = editData!.bonus_skills.filter((_, i) => i !== idx);
                          updateField("bonus_skills", updated);
                        }}
                        className="text-green-400 hover:text-green-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">关键词</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.keywords.map((kw, idx) => (
                    <span
                      key={idx}
                      className="rounded-md bg-purple-50 px-2 py-0.5 text-xs text-purple-700"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {/* Re-analyze */}
              <button
                onClick={() => { setPreview(null); setEditData(null); }}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                重新输入岗位名称
              </button>
            </div>
          )}
        </div>

        {/* Footer with action buttons */}
        {preview && (
          <div className="flex justify-end gap-3 border-t px-6 py-4">
            <button
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              取消
            </button>
            <button
              onClick={() => handleCreate(true)}
              disabled={createRole.isPending}
              className="rounded-md border border-primary px-4 py-2 text-sm font-medium text-primary hover:bg-primary/5 disabled:opacity-50"
            >
              仅创建岗位
            </button>
            <button
              onClick={() => handleCreate(false)}
              disabled={createRole.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createRole.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <Sparkles className="h-3.5 w-3.5" />
              创建并生成简历
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
