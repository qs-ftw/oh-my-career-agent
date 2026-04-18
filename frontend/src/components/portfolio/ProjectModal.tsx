import { useState, type FormEvent } from "react";
import { X, Loader2 } from "lucide-react";
import { useWorkExperiences } from "@/hooks/useWorkExperiences";
import { useEducations } from "@/hooks/useEducations";
import type { Project } from "@/types";

interface ProjectFormData {
  name: string;
  work_experience_id: string;
  education_id: string;
  description: string;
  tech_stack: string;
  url: string;
  start_date: string;
  end_date: string;
}

export function ProjectModal({
  title,
  initial,
  defaultWorkExperienceId,
  onSubmit,
  onClose,
  isSubmitting,
}: {
  title: string;
  initial?: Project;
  defaultWorkExperienceId?: string | null;
  onSubmit: (data: Record<string, unknown>) => void;
  onClose: () => void;
  isSubmitting: boolean;
}) {
  const { data: workExperiences } = useWorkExperiences();
  const { data: educations } = useEducations();

  const [form, setForm] = useState<ProjectFormData>({
    name: initial?.name ?? "",
    work_experience_id: initial?.work_experience_id ?? defaultWorkExperienceId ?? "",
    education_id: initial?.education_id ?? "",
    description: initial?.description ?? "",
    tech_stack: initial?.tech_stack?.join(", ") ?? "",
    url: initial?.url ?? "",
    start_date: initial?.start_date?.split("T")[0] ?? "",
    end_date: initial?.end_date?.split("T")[0] ?? "",
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const data: Record<string, unknown> = {
      name: form.name,
      description: form.description,
      url: form.url || null,
      work_experience_id: form.work_experience_id || null,
      education_id: form.education_id || null,
      tech_stack: form.tech_stack
        ? form.tech_stack.split(",").map((s) => s.trim()).filter(Boolean)
        : [],
      start_date: form.start_date || null,
      end_date: form.end_date || null,
    };
    onSubmit(data);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium">项目名称 <span className="text-red-500">*</span></label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="例如：用户认证系统重构"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">所属公司</label>
            <select
              value={form.work_experience_id}
              onChange={(e) => setForm((f) => ({ ...f, work_experience_id: e.target.value }))}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">独立项目（不属于任何公司）</option>
              {workExperiences?.map((we) => (
                <option key={we.id} value={we.id}>
                  {we.company_name} - {we.role_title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium">所属学校</label>
            <select
              value={form.education_id}
              onChange={(e) => setForm((f) => ({ ...f, education_id: e.target.value }))}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">不属于任何学校</option>
              {educations?.map((edu) => (
                <option key={edu.id} value={edu.id}>
                  {edu.institution_name}{edu.degree ? ` - ${edu.degree}` : ""}{edu.field_of_study ? ` ${edu.field_of_study}` : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium">项目描述</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              placeholder="描述项目的内容、你的角色和技术方案..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium">技术栈</label>
            <input
              type="text"
              value={form.tech_stack}
              onChange={(e) => setForm((f) => ({ ...f, tech_stack: e.target.value }))}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="用逗号分隔，例如：Python, FastAPI, PostgreSQL"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium">开始时间</label>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">结束时间</label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium">项目链接</label>
            <input
              type="url"
              value={form.url}
              onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="https://..."
            />
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
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isSubmitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
