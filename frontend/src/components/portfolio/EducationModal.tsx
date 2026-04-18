import { useState, type FormEvent } from "react";
import { X, Loader2 } from "lucide-react";
import type { Education } from "@/types";

interface EducationFormData {
  institution_name: string;
  institution_url: string;
  degree: string;
  field_of_study: string;
  location: string;
  start_date: string;
  end_date: string;
  gpa: string;
  description: string;
}

export function EducationModal({
  title,
  initial,
  onSubmit,
  onClose,
  isSubmitting,
}: {
  title: string;
  initial?: Education;
  onSubmit: (data: Record<string, unknown>) => void;
  onClose: () => void;
  isSubmitting: boolean;
}) {
  const [form, setForm] = useState<EducationFormData>({
    institution_name: initial?.institution_name ?? "",
    institution_url: initial?.institution_url ?? "",
    degree: initial?.degree ?? "",
    field_of_study: initial?.field_of_study ?? "",
    location: initial?.location ?? "",
    start_date: initial?.start_date?.split("T")[0] ?? "",
    end_date: initial?.end_date?.split("T")[0] ?? "",
    gpa: initial?.gpa ?? "",
    description: initial?.description ?? "",
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const data: Record<string, unknown> = { ...form };
    if (!data.end_date) data.end_date = null;
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
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium">学校名称 <span className="text-red-500">*</span></label>
              <input
                type="text"
                required
                value={form.institution_name}
                onChange={(e) => setForm((f) => ({ ...f, institution_name: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="例如：清华大学"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">学位</label>
              <select
                value={form.degree}
                onChange={(e) => setForm((f) => ({ ...f, degree: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="">选择学位</option>
                <option value="高中">高中</option>
                <option value="大专">大专</option>
                <option value="本科">本科</option>
                <option value="硕士">硕士</option>
                <option value="博士">博士</option>
                <option value="MBA">MBA</option>
                <option value="其他">其他</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium">专业</label>
            <input
              type="text"
              value={form.field_of_study}
              onChange={(e) => setForm((f) => ({ ...f, field_of_study: e.target.value }))}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="例如：计算机科学与技术"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium">开始时间 <span className="text-red-500">*</span></label>
              <input
                type="date"
                required
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
              <p className="mt-0.5 text-xs text-muted-foreground">留空表示至今</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium">GPA</label>
              <input
                type="text"
                value={form.gpa}
                onChange={(e) => setForm((f) => ({ ...f, gpa: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="例如：3.8/4.0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">所在地</label>
              <input
                type="text"
                value={form.location}
                onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="例如：北京"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium">学校网站</label>
            <input
              type="url"
              value={form.institution_url}
              onChange={(e) => setForm((f) => ({ ...f, institution_url: e.target.value }))}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="https://..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium">描述</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              placeholder="在校经历、学术成就、课外活动等..."
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
