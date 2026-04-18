import { useState, type FormEvent } from "react";
import { X, Loader2 } from "lucide-react";
import type { WorkExperience } from "@/types";

interface WEFormData {
  company_name: string;
  company_url: string;
  location: string;
  role_title: string;
  start_date: string;
  end_date: string;
  description: string;
}

export function WorkExperienceModal({
  title,
  initial,
  onSubmit,
  onClose,
  isSubmitting,
}: {
  title: string;
  initial?: WorkExperience;
  onSubmit: (data: Record<string, unknown>) => void;
  onClose: () => void;
  isSubmitting: boolean;
}) {
  const [form, setForm] = useState<WEFormData>({
    company_name: initial?.company_name ?? "",
    company_url: initial?.company_url ?? "",
    location: initial?.location ?? "",
    role_title: initial?.role_title ?? "",
    start_date: initial?.start_date?.split("T")[0] ?? "",
    end_date: initial?.end_date?.split("T")[0] ?? "",
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
              <label className="block text-sm font-medium">公司名称 <span className="text-red-500">*</span></label>
              <input
                type="text"
                required
                value={form.company_name}
                onChange={(e) => setForm((f) => ({ ...f, company_name: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="例如：字节跳动"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">职位头衔 <span className="text-red-500">*</span></label>
              <input
                type="text"
                required
                value={form.role_title}
                onChange={(e) => setForm((f) => ({ ...f, role_title: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="例如：高级后端工程师"
              />
            </div>
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
              <label className="block text-sm font-medium">工作地点</label>
              <input
                type="text"
                value={form.location}
                onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="例如：北京"
              />
            </div>
            <div>
              <label className="block text-sm font-medium">公司网站</label>
              <input
                type="url"
                value={form.company_url}
                onChange={(e) => setForm((f) => ({ ...f, company_url: e.target.value }))}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="https://..."
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium">工作描述</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              placeholder="简述你的工作内容和职责..."
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
