import { useState, type FormEvent } from "react";
import { X, Loader2 } from "lucide-react";
import type { WorkExperience, Education, Project, AchievementCreateRequest } from "@/types";

interface AchievementCreateModalProps {
  workExperiences: WorkExperience[];
  educations?: Education[];
  projects: Project[];
  onClose: () => void;
  onSubmit: (data: AchievementCreateRequest) => void;
  isSubmitting: boolean;
  defaultProjectId?: string | null;
}

export function AchievementCreateModal({
  workExperiences,
  educations = [],
  projects,
  onClose,
  onSubmit,
  isSubmitting,
  defaultProjectId = null,
}: AchievementCreateModalProps) {
  const [title, setTitle] = useState("");
  const [rawContent, setRawContent] = useState("");
  const [projectId, setProjectId] = useState<string | null>(defaultProjectId);
  const [tagsInput, setTagsInput] = useState("");

  // Group projects by work experience and education
  const projectsByWE = new Map<string, Project[]>();
  const projectsByEdu = new Map<string, Project[]>();
  const standalone: Project[] = [];
  for (const p of projects) {
    if (p.work_experience_id) {
      const list = projectsByWE.get(p.work_experience_id) ?? [];
      list.push(p);
      projectsByWE.set(p.work_experience_id, list);
    } else if (p.education_id) {
      const list = projectsByEdu.get(p.education_id) ?? [];
      list.push(p);
      projectsByEdu.set(p.education_id, list);
    } else {
      standalone.push(p);
    }
  }

  // Resolve work_experience_id / education_id from selected project
  const selectedProject = projects.find((p) => p.id === projectId);
  const workExperienceId = selectedProject?.work_experience_id ?? null;
  const educationId = selectedProject?.education_id ?? null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    onSubmit({
      source_type: "manual",
      title: title.trim(),
      raw_content: rawContent.trim(),
      project_id: projectId,
      work_experience_id: workExperienceId,
      education_id: educationId,
      tags: tagsInput ? tagsInput.split(",").map((s) => s.trim()).filter(Boolean) : undefined,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">新增成果</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted transition-colors">
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
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="例如：完成用户认证系统重构"
            />
          </div>

          {/* Project selection */}
          <div>
            <label className="block text-sm font-medium">绑定项目</label>
            <select
              value={projectId ?? ""}
              onChange={(e) => setProjectId(e.target.value || null)}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">不绑定（独立成果）</option>
              {workExperiences.map((we) => {
                const weProjects = projectsByWE.get(we.id) ?? [];
                if (weProjects.length === 0) return null;
                return (
                  <optgroup key={we.id} label={we.company_name}>
                    {weProjects.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </optgroup>
                );
              })}
              {educations.map((edu) => {
                const eduProjects = projectsByEdu.get(edu.id) ?? [];
                if (eduProjects.length === 0) return null;
                return (
                  <optgroup key={edu.id} label={`🎓 ${edu.institution_name}`}>
                    {eduProjects.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </optgroup>
                );
              })}
              {standalone.length > 0 && (
                <optgroup label="独立项目">
                  {standalone.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>

          {/* Raw Content */}
          <div>
            <label className="block text-sm font-medium">
              内容描述 <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              value={rawContent}
              onChange={(e) => setRawContent(e.target.value)}
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
              disabled={isSubmitting || !title.trim()}
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
