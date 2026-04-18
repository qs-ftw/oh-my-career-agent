import { useState, useEffect, useCallback, useRef } from "react";
import { useProfile, useProfileCompleteness, useUpsertProfile } from "@/hooks/useProfile";
import { useQueryClient } from "@tanstack/react-query";
import { profileApi } from "@/lib/api";
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Loader2,
  Pencil,
  X,
  Mail,
  Phone,
  MapPin,
  Globe,
  Github,
  Linkedin,
} from "lucide-react";
import type { ProfileUpsertRequest, ResumeImportResult } from "@/types";

const FIELD_LABELS: Record<string, string> = {
  name: "姓名",
  headline: "职业标语",
  email: "邮箱",
  phone: "电话",
  linkedin_url: "LinkedIn",
  github_url: "GitHub",
  portfolio_url: "作品集",
  location: "地区",
  professional_summary: "专业摘要",
  skill_categories: "技能",
};

export function Profile() {
  const { data: profile, isLoading } = useProfile();
  const { data: completeness } = useProfileCompleteness();
  const upsert = useUpsertProfile();
  const queryClient = useQueryClient();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<ProfileUpsertRequest>({
    name: "",
    headline: "",
    email: "",
    phone: "",
    linkedin_url: "",
    portfolio_url: "",
    github_url: "",
    location: "",
    professional_summary: "",
    skill_categories: {},
  });

  // Import state
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ResumeImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (profile) {
      setForm({
        name: profile.name ?? "",
        headline: profile.headline ?? "",
        email: profile.email ?? "",
        phone: profile.phone ?? "",
        linkedin_url: profile.linkedin_url ?? "",
        portfolio_url: profile.portfolio_url ?? "",
        github_url: profile.github_url ?? "",
        location: profile.location ?? "",
        professional_summary: profile.professional_summary ?? "",
        skill_categories: profile.skill_categories ?? {},
      });
    }
  }, [profile]);

  const handleImport = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setImportError("只支持PDF格式的简历文件");
      return;
    }
    setImporting(true);
    setImportError(null);
    setImportResult(null);

    try {
      const resp = await profileApi.importResume(file);
      const result = resp.data as ResumeImportResult;
      setImportResult(result);
      if (result.profile) {
        setForm({
          name: result.profile.name ?? "",
          headline: result.profile.headline ?? "",
          email: result.profile.email ?? "",
          phone: result.profile.phone ?? "",
          linkedin_url: result.profile.linkedin_url ?? "",
          portfolio_url: result.profile.portfolio_url ?? "",
          github_url: result.profile.github_url ?? "",
          location: result.profile.location ?? "",
          professional_summary: result.profile.professional_summary ?? "",
          skill_categories: result.profile.skill_categories ?? {},
        });
      }
      await queryClient.invalidateQueries({ queryKey: ["profile"] });
      await queryClient.invalidateQueries({ queryKey: ["workExperiences"] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "简历解析失败，请重试";
      setImportError(msg);
    } finally {
      setImporting(false);
    }
  }, [queryClient]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleImport(file);
    },
    [handleImport]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleImport(file);
      e.target.value = "";
    },
    [handleImport]
  );

  const handleSave = () => {
    upsert.mutate(form, {
      onSuccess: () => setEditing(false),
    });
  };

  const handleCancel = () => {
    if (profile) {
      setForm({
        name: profile.name ?? "",
        headline: profile.headline ?? "",
        email: profile.email ?? "",
        phone: profile.phone ?? "",
        linkedin_url: profile.linkedin_url ?? "",
        portfolio_url: profile.portfolio_url ?? "",
        github_url: profile.github_url ?? "",
        location: profile.location ?? "",
        professional_summary: profile.professional_summary ?? "",
        skill_categories: profile.skill_categories ?? {},
      });
    }
    setEditing(false);
  };

  const weCount = importResult?.work_experiences?.length ?? 0;
  const projCount = importResult?.projects?.length ?? 0;
  const achCount = importResult?.achievements?.length ?? 0;

  const hasProfile = profile && (profile.name || profile.headline || profile.email);

  if (isLoading) {
    return <div className="p-6 text-muted-foreground">加载中...</div>;
  }

  return (
    <div className="overflow-y-auto p-6 space-y-6 max-w-3xl">
      {/* ── Header with completeness ──────────────── */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">候选人画像</h2>
        <div className="flex items-center gap-3">
          {completeness && (
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-20 rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    completeness.completeness_pct >= 80
                      ? "bg-green-500"
                      : completeness.completeness_pct >= 40
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${completeness.completeness_pct}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground">
                {completeness.completeness_pct}%
              </span>
            </div>
          )}
          {editing ? (
            <div className="flex items-center gap-2">
              <button
                onClick={handleCancel}
                className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
              >
                <X className="h-3.5 w-3.5" />
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={upsert.isPending}
                className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {upsert.isPending ? "保存中..." : "保存"}
              </button>
            </div>
          ) : (
            <button
              onClick={() => setEditing(true)}
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
            >
              <Pencil className="h-3.5 w-3.5" />
              编辑
            </button>
          )}
        </div>
      </div>

      {/* ── PDF Import ──────────────────────────── */}
      <div className="rounded-lg border bg-card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Upload className="h-4 w-4 text-primary" />
          <h3 className="font-medium text-sm">导入简历 PDF</h3>
          <span className="text-xs text-muted-foreground">— 自动提取信息，快速构建画像</span>
        </div>

        <div
          className={`relative flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-5 transition-colors ${
            dragOver
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/20 hover:border-primary/50 hover:bg-accent/50"
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleFileSelect}
          />
          {importing ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">正在解析简历...</span>
            </div>
          ) : (
            <span className="text-sm text-muted-foreground">
              拖拽 PDF 到此处，或点击选择文件
            </span>
          )}
        </div>

        {importResult && (
          <div className="rounded-md border border-green-200 bg-green-50 p-3 text-xs text-green-700 flex items-center gap-2">
            <CheckCircle className="h-3.5 w-3.5 shrink-0" />
            已提取: {weCount} 段工作经历、{projCount} 个项目、{achCount} 条成果
          </div>
        )}
        {importError && (
          <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-800">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {importError}
          </div>
        )}
      </div>

      {/* ── Profile Content ─────────────────────── */}
      {editing ? (
        /* ========== EDIT MODE ========== */
        <div className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">姓名</label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                placeholder="张三"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">职业标语</label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                value={form.headline}
                onChange={(e) => setForm((p) => ({ ...p, headline: e.target.value }))}
                placeholder="5年经验后端工程师，专注于分布式系统"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">专业摘要</label>
            <textarea
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              rows={3}
              value={form.professional_summary}
              onChange={(e) => setForm((p) => ({ ...p, professional_summary: e.target.value }))}
              placeholder="简要描述你的职业背景和核心优势..."
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">邮箱</label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                value={form.email}
                onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                placeholder="you@example.com"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">电话</label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                value={form.phone}
                onChange={(e) => setForm((p) => ({ ...p, phone: e.target.value }))}
                placeholder="+86 138-xxxx-xxxx"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">地区</label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                value={form.location}
                onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
                placeholder="北京"
              />
            </div>
            <div />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Github className="h-3 w-3" /> GitHub
              </label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                value={form.github_url}
                onChange={(e) => setForm((p) => ({ ...p, github_url: e.target.value }))}
                placeholder="https://github.com/..."
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Linkedin className="h-3 w-3" /> LinkedIn
              </label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                value={form.linkedin_url}
                onChange={(e) => setForm((p) => ({ ...p, linkedin_url: e.target.value }))}
                placeholder="https://linkedin.com/in/..."
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
              <Globe className="h-3 w-3" /> 作品集 / 个人主页
            </label>
            <input
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              value={form.portfolio_url}
              onChange={(e) => setForm((p) => ({ ...p, portfolio_url: e.target.value }))}
              placeholder="https://..."
            />
          </div>

          {upsert.isSuccess && (
            <div className="text-sm text-green-600">保存成功</div>
          )}
        </div>
      ) : (
        /* ========== READ MODE ========== */
        <>
          {hasProfile ? (
            <div className="space-y-6">
              {/* Name & Headline */}
              <div>
                <h1 className="text-xl font-semibold">
                  {profile?.name || "未填写姓名"}
                </h1>
                {profile?.headline && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {profile.headline}
                  </p>
                )}
              </div>

              {/* Completeness hint */}
              {completeness && completeness.completeness_pct < 100 && (
                <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800">
                  <span className="font-medium">可优化: </span>
                  {completeness.missing_high_value.length > 0 && (
                    <span>
                      核心字段缺少 {completeness.missing_high_value.map((f) => FIELD_LABELS[f] || f).join("、")}
                    </span>
                  )}
                  {completeness.missing_low_value.length > 0 && (
                    <span className="text-yellow-600">
                      {completeness.missing_high_value.length > 0 ? "；" : ""}
                      可选补充 {completeness.missing_low_value.map((f) => FIELD_LABELS[f] || f).join("、")}
                    </span>
                  )}
                </div>
              )}

              {/* Professional Summary */}
              {profile?.professional_summary && (
                <div>
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">专业摘要</h3>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {profile.professional_summary}
                  </p>
                </div>
              )}

              {/* Skills */}
              {profile?.skill_categories && Object.keys(profile.skill_categories).length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">技能</h3>
                  <div className="space-y-2">
                    {Object.entries(profile.skill_categories).map(([category, skills]) => (
                      <div key={category} className="flex flex-wrap items-center gap-1.5">
                        <span className="text-xs font-medium text-muted-foreground w-20 shrink-0">
                          {category}
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {(skills as string[]).map((skill) => (
                            <span
                              key={skill}
                              className="inline-flex rounded-full bg-primary/10 px-2.5 py-0.5 text-xs text-primary"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Contact */}
              <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">联系方式</h3>
                <div className="grid gap-2 sm:grid-cols-2">
                  {profile?.email && (
                    <div className="flex items-center gap-2 text-sm">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                      {profile.email}
                    </div>
                  )}
                  {profile?.phone && (
                    <div className="flex items-center gap-2 text-sm">
                      <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                      {profile.phone}
                    </div>
                  )}
                  {profile?.location && (
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                      {profile.location}
                    </div>
                  )}
                  {profile?.github_url && (
                    <a href={profile.github_url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-primary hover:underline">
                      <Github className="h-3.5 w-3.5" />
                      {profile.github_url.replace("https://", "")}
                    </a>
                  )}
                  {profile?.linkedin_url && (
                    <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-primary hover:underline">
                      <Linkedin className="h-3.5 w-3.5" />
                      {profile.linkedin_url.replace("https://", "")}
                    </a>
                  )}
                  {profile?.portfolio_url && (
                    <a href={profile.portfolio_url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-primary hover:underline">
                      <Globe className="h-3.5 w-3.5" />
                      {profile.portfolio_url.replace("https://", "")}
                    </a>
                  )}
                  {/* Show empty contact hints */}
                  {!profile?.email && !profile?.phone && !profile?.location &&
                   !profile?.github_url && !profile?.linkedin_url && !profile?.portfolio_url && (
                    <p className="text-sm text-muted-foreground">暂未填写联系方式，点击右上角编辑</p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            /* Empty state */
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <FileText className="h-10 w-10 mb-3 opacity-40" />
              <p className="text-sm">尚未创建职业画像</p>
              <p className="mt-1 text-xs">
                导入简历或点击右上角编辑手动填写
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
