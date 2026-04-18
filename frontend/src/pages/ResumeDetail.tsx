import { useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { useResume, useUpdateResume, useResumeVersions, useDeleteVersion, useResumeVersion, useDeleteResume } from "@/hooks/useResumes";
import { resumeApi } from "@/lib/api";
import type { ContactInfo, ResumeContent } from "@/types";
import {
  Loader2,
  AlertTriangle,
  ArrowLeft,
  ChevronRight,
  User,
  Wrench,
  Building2,
  FolderGit2,
  Lightbulb,
  BarChart3,
  MessageSquare,
  History,
  Pencil,
  X,
  Save,
  Plus,
  Calendar,
  GitBranch,
  Clock,
  Info,
  Trash2,
  Download,
  Mail,
  Phone,
  Linkedin,
  Globe,
  MapPin,
} from "lucide-react";

// ── Default values ────────────────────────────────────

const EMPTY_CONTACT: ContactInfo = { email: "", phone: "", linkedin_url: "", portfolio_url: "", location: "" };

function emptyContent(): ResumeContent {
  return { summary: "", skills: [], experiences: [], projects: [], highlights: [], metrics: [], interview_points: [], contact: { ...EMPTY_CONTACT } };
}

// ── Main Component ────────────────────────────────────

export function ResumeDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: resume, isLoading, isError } = useResume(id ?? "");
  const { data: versions } = useResumeVersions(id ?? "");
  const [viewingVersionId, setViewingVersionId] = useState<string | null>(null);
  const { data: viewingVersion } = useResumeVersion(id ?? "", viewingVersionId);

  // Global edit state
  const updateResume = useUpdateResume();
  const [isEditing, setIsEditing] = useState(false);
  const [editingContent, setEditingContent] = useState<ResumeContent>(emptyContent());
  const [editingName, setEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState("");

  // Compute display content (safe even when resume is null)
  const isViewingHistory = viewingVersionId !== null && !!viewingVersion?.content;
  const displayContent: ResumeContent = isViewingHistory
    ? { ...emptyContent(), ...viewingVersion!.content }
    : (resume?.content ?? emptyContent());

  // Detect if editingContent differs from original
  const hasChanges = useMemo(() => {
    if (!isEditing) return false;
    return JSON.stringify(editingContent) !== JSON.stringify(displayContent);
  }, [isEditing, editingContent, displayContent]);

  if (isLoading) {
    return (
      <>
        <Header title="简历详情" />
        <PageContainer>
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">加载中...</span>
          </div>
        </PageContainer>
      </>
    );
  }

  if (isError || !resume) {
    return (
      <>
        <Header title="简历详情" />
        <PageContainer>
          <div className="flex items-center justify-center rounded-lg border border-red-200 bg-red-50 p-12">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="ml-2 text-red-600">加载失败，请稍后重试</span>
          </div>
        </PageContainer>
      </>
    );
  }

  const handleStartEdit = () => {
    setEditingContent(JSON.parse(JSON.stringify(displayContent)));
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditingContent(emptyContent());
  };

  const handleSave = () => {
    updateResume.mutate(
      { id: resume.id, data: { content: editingContent } },
      {
        onSuccess: () => {
          setIsEditing(false);
          setViewingVersionId(null);
        },
      }
    );
  };

  // Helper to update a single field in editingContent
  const updateField = <K extends keyof ResumeContent>(key: K, value: ResumeContent[K]) => {
    setEditingContent((prev) => ({ ...prev, [key]: value }));
  };

  const statusColor =
    resume.status === "active"
      ? "bg-green-100 text-green-700"
      : resume.status === "draft"
        ? "bg-yellow-100 text-yellow-700"
        : "bg-gray-100 text-gray-500";

  const statusLabel =
    resume.status === "active"
      ? "生效中"
      : resume.status === "draft"
        ? "草稿"
        : "已归档";

  const resumeTypeLabel =
    resume.resume_type === "master" ? "主简历" : "定制简历";

  // The content to render (editing draft or display content)
  const content = isEditing ? editingContent : displayContent;

  return (
    <>
      <Header
        title={
          editingName ? (
            <input
              type="text"
              value={nameDraft}
              onChange={(e) => setNameDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  updateResume.mutate(
                    { id: resume.id, data: { resume_name: nameDraft } },
                    { onSuccess: () => setEditingName(false) }
                  );
                }
                if (e.key === "Escape") setEditingName(false);
              }}
              onBlur={() => {
                if (nameDraft.trim() && nameDraft !== resume.resume_name) {
                  updateResume.mutate(
                    { id: resume.id, data: { resume_name: nameDraft } },
                    { onSuccess: () => setEditingName(false) }
                  );
                } else {
                  setEditingName(false);
                }
              }}
              autoFocus
              className="rounded border bg-background px-2 py-0.5 text-2xl font-bold outline-none focus:ring-2 focus:ring-primary/50"
            />
          ) : (
            <span className="inline-flex items-center gap-2">
              {resume.resume_name}
              <button
                onClick={() => { setNameDraft(resume.resume_name); setEditingName(true); }}
                className="text-muted-foreground hover:text-foreground"
              >
                <Pencil className="h-4 w-4" />
              </button>
            </span>
          )
        }
        description="查看、编辑简历内容"
      />
      <PageContainer>
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1 text-sm text-muted-foreground">
          <button
            onClick={() => navigate(`/roles/${resume.target_role_id}`)}
            className="hover:text-foreground transition-colors inline-flex items-center gap-1"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            返回岗位
          </button>
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="text-foreground font-medium">{editingName ? nameDraft : resume.resume_name}</span>
        </nav>

        {/* Action buttons */}
        <div className="mt-4 flex items-center gap-2 flex-wrap">
          {isViewingHistory && (
            <button
              onClick={() => setViewingVersionId(null)}
              className="inline-flex items-center gap-1.5 rounded-md border border-amber-300 bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-700 hover:bg-amber-100 transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              返回当前版本
            </button>
          )}

          {/* Global Edit / Save / Cancel */}
          {isEditing ? (
            <>
              <button
                onClick={handleCancelEdit}
                className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
              >
                <X className="h-3.5 w-3.5" />
                取消编辑
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || updateResume.isPending}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {updateResume.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Save className="h-3.5 w-3.5" />
                )}
                保存{hasChanges ? "（有修改）" : ""}
              </button>
            </>
          ) : (
            <button
              onClick={handleStartEdit}
              className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
            >
              <Pencil className="h-3.5 w-3.5" />
              编辑
            </button>
          )}

          <div className="flex-1" />

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
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            导出 PDF
          </button>
          {!isEditing && <DeleteResumeButton resumeId={resume.id} resumeName={resume.resume_name} />}
        </div>

        {/* Two-column layout */}
        <div className="mt-6 grid gap-6 lg:grid-cols-[3fr_2fr]">
          {/* Left Column — Content */}
          <div className="space-y-5">
            {isViewingHistory && !isEditing && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-700">
                正在查看历史版本 v{viewingVersion?.version_no}
              </div>
            )}
            <ContactInfoSection content={content} isEditing={isEditing} onChange={(c) => updateField("contact", c)} />
            <SummarySection content={content} isEditing={isEditing} onChange={(v) => updateField("summary", v)} />
            <SkillsSection content={content} isEditing={isEditing} onChange={(v) => updateField("skills", v)} />
            <ExperiencesSection content={content} isEditing={isEditing} onChange={(v) => updateField("experiences", v)} />
            <ProjectsSection content={content} isEditing={isEditing} onChange={(v) => updateField("projects", v)} />
            <HighlightsSection content={content} isEditing={isEditing} onChange={(v) => updateField("highlights", v)} />
            <MetricsSection content={content} isEditing={isEditing} onChange={(v) => updateField("metrics", v)} />
            <InterviewPointsSection content={content} isEditing={isEditing} onChange={(v) => updateField("interview_points", v)} />
          </div>

          {/* Right Column — Info Panel */}
          <div className="space-y-5">
            {/* Resume Info */}
            <section className="rounded-lg border bg-card p-5">
              <h3 className="flex items-center gap-2 text-base font-semibold">
                <Info className="h-4 w-4 text-primary" />
                简历信息
              </h3>
              <div className="mt-4 space-y-3">
                <InfoField label="简历名称">
                  <span className="text-sm">{resume.resume_name}</span>
                </InfoField>
                <InfoField label="类型">
                  <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                    {resumeTypeLabel}
                  </span>
                </InfoField>
                <InfoField label="状态">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}>
                    {statusLabel}
                  </span>
                </InfoField>
                <InfoField label="版本号">
                  <span className="text-sm font-medium">v{resume.current_version_no}</span>
                </InfoField>
                <InfoField label="创建时间">
                  <span className="text-sm text-muted-foreground">{formatDate(resume.created_at)}</span>
                </InfoField>
                <InfoField label="更新时间">
                  <span className="text-sm text-muted-foreground">{formatDate(resume.updated_at)}</span>
                </InfoField>
              </div>
            </section>

            {/* Scores */}
            <section className="rounded-lg border bg-card p-5">
              <h3 className="flex items-center gap-2 text-base font-semibold">
                <BarChart3 className="h-4 w-4 text-primary" />
                评分
              </h3>
              <div className="mt-4 space-y-4">
                <ScoreBar label="完成度" value={resume.completeness_score} colorClass="bg-blue-500" />
                <ScoreBar label="匹配度" value={resume.match_score} colorClass="bg-emerald-500" />
              </div>
            </section>

            {/* Version History */}
            <section className="rounded-lg border bg-card p-5">
              <h3 className="flex items-center gap-2 text-base font-semibold">
                <History className="h-4 w-4 text-primary" />
                版本历史
              </h3>
              <div className="mt-4">
                {versions && versions.length > 0 ? (
                  <VersionTimeline
                    versions={versions}
                    resumeId={resume.id}
                    viewingVersionId={viewingVersionId}
                    onViewVersion={(versionId) => {
                      if (!isEditing) setViewingVersionId(versionId || null);
                    }}
                  />
                ) : (
                  <div className="py-6 text-center">
                    <GitBranch className="mx-auto h-8 w-8 text-muted-foreground/40" />
                    <p className="mt-2 text-sm text-muted-foreground">暂无版本记录</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </PageContainer>
    </>
  );
}

// ── Delete Resume Button ───────────────────────────────

function DeleteResumeButton({ resumeId, resumeName }: { resumeId: string; resumeName: string }) {
  const deleteResume = useDeleteResume();
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState(false);

  if (confirming) {
    return (
      <>
        <span className="text-sm text-red-600">确认删除 "{resumeName}"？</span>
        <button
          onClick={() => { deleteResume.mutate(resumeId, { onSuccess: () => navigate(-1) }); }}
          disabled={deleteResume.isPending}
          className="inline-flex items-center gap-1.5 rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
        >
          {deleteResume.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
          确认删除
        </button>
        <button onClick={() => setConfirming(false)} className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors">
          取消
        </button>
      </>
    );
  }

  return (
    <button onClick={() => setConfirming(true)} className="inline-flex items-center gap-1.5 rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors">
      <Trash2 className="h-3.5 w-3.5" />
      删除简历
    </button>
  );
}

// ── Helper components ─────────────────────────────────

function InfoField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
      <div>{children}</div>
    </div>
  );
}

function ScoreBar({ label, value, colorClass }: { label: string; value: number; colorClass: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold">{value}%</span>
      </div>
      <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full transition-all ${colorClass}`} style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} />
      </div>
    </div>
  );
}

function formatDate(dateStr: string) {
  try { return new Date(dateStr).toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }); }
  catch { return dateStr; }
}

function sourceTypeLabel(sourceType: string) {
  switch (sourceType) {
    case "achievement": return "成就分析";
    case "jd": return "JD 解析";
    case "manual_edit": return "手动编辑";
    case "initial_draft": return "初始生成";
    default: return sourceType;
  }
}

// ── Section card (no edit/save buttons) ────────────────

function SectionCard({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border bg-card p-5">
      <h3 className="flex items-center gap-2 text-base font-semibold">{icon}{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}

// ── Contact Info Section ───────────────────────────────

const CONTACT_FIELDS = [
  { key: "email" as const, label: "邮箱", icon: Mail, placeholder: "you@example.com" },
  { key: "phone" as const, label: "电话", icon: Phone, placeholder: "+86 138-xxxx-xxxx" },
  { key: "linkedin_url" as const, label: "LinkedIn", icon: Linkedin, placeholder: "https://linkedin.com/in/..." },
  { key: "portfolio_url" as const, label: "作品集", icon: Globe, placeholder: "https://..." },
  { key: "location" as const, label: "地区", icon: MapPin, placeholder: "北京" },
];

function ContactInfoSection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (c: ContactInfo) => void }) {
  const contact = content.contact || { ...EMPTY_CONTACT };

  return (
    <SectionCard icon={<User className="h-4 w-4 text-primary" />} title="联系方式">
      {isEditing ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {CONTACT_FIELDS.map((f) => (
            <div key={f.key}>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">{f.label}</label>
              <input
                type="text"
                value={contact[f.key] ?? ""}
                onChange={(e) => onChange({ ...contact, [f.key]: e.target.value })}
                className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                placeholder={f.placeholder}
              />
            </div>
          ))}
        </div>
      ) : (
        <div>
          {CONTACT_FIELDS.some((f) => contact[f.key]) ? (
            <div className="flex flex-wrap gap-3">
              {CONTACT_FIELDS.map((f) =>
                contact[f.key] ? (
                  <span key={f.key} className="inline-flex items-center gap-1.5 text-sm">
                    <f.icon className="h-3.5 w-3.5 text-muted-foreground" />
                    {contact[f.key]}
                  </span>
                ) : null
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无联系方式</p>
          )}
        </div>
      )}
    </SectionCard>
  );
}

// ── Summary Section ───────────────────────────────────

function SummarySection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (v: string) => void }) {
  return (
    <SectionCard icon={<User className="h-4 w-4 text-primary" />} title="个人摘要">
      {isEditing ? (
        <textarea
          value={content.summary ?? ""}
          onChange={(e) => onChange(e.target.value)}
          rows={5}
          className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
          placeholder="输入个人摘要..."
        />
      ) : (
        <p className="text-sm whitespace-pre-wrap leading-relaxed">
          {content.summary || <span className="text-muted-foreground italic">暂无个人摘要</span>}
        </p>
      )}
    </SectionCard>
  );
}

// ── Skills Section ────────────────────────────────────

function SkillsSection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (v: string[]) => void }) {
  const [newSkill, setNewSkill] = useState("");
  const skills = content.skills ?? [];

  const addSkill = () => {
    const trimmed = newSkill.trim();
    if (trimmed && !skills.includes(trimmed)) {
      onChange([...skills, trimmed]);
      setNewSkill("");
    }
  };

  const removeSkill = (skill: string) => {
    onChange(skills.filter((s) => s !== skill));
  };

  return (
    <SectionCard icon={<Wrench className="h-4 w-4 text-primary" />} title="核心技能">
      {isEditing ? (
        <div>
          <div className="flex flex-wrap gap-1.5">
            {skills.map((skill) => (
              <span key={skill} className="inline-flex items-center gap-1 rounded-md bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700">
                {skill}
                <button onClick={() => removeSkill(skill)} className="hover:text-blue-900 transition-colors">
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addSkill(); } }}
              className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="输入技能名称，按 Enter 添加"
            />
            <button onClick={addSkill} className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium hover:bg-muted transition-colors">
              <Plus className="h-3 w-3" />添加
            </button>
          </div>
        </div>
      ) : (
        <div>
          {skills.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {skills.map((skill) => (
                <span key={skill} className="rounded-md bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700">{skill}</span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无核心技能</p>
          )}
        </div>
      )}
    </SectionCard>
  );
}

// ── Experiences Section ────────────────────────────────

function ExperiencesSection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (v: Record<string, unknown>[]) => void }) {
  const experiences = content.experiences ?? [];

  const addItem = () => onChange([...experiences, { company: "", title: "", period: "", description: "" }]);
  const removeItem = (i: number) => onChange(experiences.filter((_, idx) => idx !== i));
  const updateItem = (i: number, field: string, value: string) => {
    const updated = [...experiences];
    updated[i] = { ...updated[i], [field]: value };
    onChange(updated);
  };

  return (
    <SectionCard icon={<Building2 className="h-4 w-4 text-primary" />} title="工作经历">
      {isEditing ? (
        <div className="space-y-4">
          {experiences.map((exp, idx) => (
            <div key={idx} className="rounded-md border p-3 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-medium text-muted-foreground">#{idx + 1}</span>
                <button onClick={() => removeItem(idx)} className="text-muted-foreground hover:text-red-600 transition-colors"><X className="h-3.5 w-3.5" /></button>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <input type="text" value={(exp.company as string) ?? ""} onChange={(e) => updateItem(idx, "company", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="公司名称" />
                <input type="text" value={(exp.title as string) ?? ""} onChange={(e) => updateItem(idx, "title", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="职位" />
                <input type="text" value={(exp.period as string) ?? ""} onChange={(e) => updateItem(idx, "period", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="时间段" />
              </div>
              <textarea value={(exp.description as string) ?? ""} onChange={(e) => updateItem(idx, "description", e.target.value)} className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50 min-h-[60px]" placeholder="工作描述" rows={3} />
            </div>
          ))}
          <button onClick={addItem} className="inline-flex items-center gap-1 rounded-md border border-dashed px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors">
            <Plus className="h-3 w-3" />添加工作经历
          </button>
        </div>
      ) : (
        <div>
          {experiences.length > 0 ? (
            <div className="space-y-3">{experiences.map((exp, idx) => <ExperienceCard key={idx} entry={exp} />)}</div>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无工作经历</p>
          )}
        </div>
      )}
    </SectionCard>
  );
}

function ExperienceCard({ entry }: { entry: Record<string, unknown> }) {
  const company = (entry.company as string) ?? "";
  const title = (entry.title as string) ?? (entry.role as string) ?? "";
  const period = (entry.period as string) ?? (entry.date_range as string) ?? "";
  const description = (entry.description as string) ?? (entry.responsibilities as string) ?? (entry.summary as string) ?? "";
  return (
    <div className="rounded-md border p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          {company && <p className="text-sm font-semibold">{company}</p>}
          {title && <p className="text-sm text-muted-foreground">{title}</p>}
        </div>
        {period && <span className="inline-flex items-center gap-1 text-xs text-muted-foreground"><Calendar className="h-3 w-3" />{period}</span>}
      </div>
      {description && <p className="mt-2 text-sm whitespace-pre-wrap leading-relaxed">{description}</p>}
    </div>
  );
}

// ── Projects Section ───────────────────────────────────

function ProjectsSection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (v: Record<string, unknown>[]) => void }) {
  const projects = content.projects ?? [];

  const addItem = () => onChange([...projects, { name: "", role: "", period: "", description: "", tech_stack: [] }]);
  const removeItem = (i: number) => onChange(projects.filter((_, idx) => idx !== i));
  const updateItem = (i: number, field: string, value: string | string[]) => {
    const updated = [...projects];
    updated[i] = { ...updated[i], [field]: value };
    onChange(updated);
  };

  return (
    <SectionCard icon={<FolderGit2 className="h-4 w-4 text-primary" />} title="项目经历">
      {isEditing ? (
        <div className="space-y-4">
          {projects.map((proj, idx) => (
            <div key={idx} className="rounded-md border p-3 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-medium text-muted-foreground">#{idx + 1}</span>
                <button onClick={() => removeItem(idx)} className="text-muted-foreground hover:text-red-600 transition-colors"><X className="h-3.5 w-3.5" /></button>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <input type="text" value={(proj.name as string) ?? ""} onChange={(e) => updateItem(idx, "name", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="项目名称" />
                <input type="text" value={(proj.role as string) ?? ""} onChange={(e) => updateItem(idx, "role", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="担任角色" />
                <input type="text" value={(proj.period as string) ?? ""} onChange={(e) => updateItem(idx, "period", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="时间段" />
              </div>
              <textarea value={(proj.description as string) ?? ""} onChange={(e) => updateItem(idx, "description", e.target.value)} className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50 min-h-[60px]" placeholder="项目描述" rows={3} />
              <input type="text" value={((proj.tech_stack as string[]) ?? []).join(", ")} onChange={(e) => updateItem(idx, "tech_stack", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))} className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="技术栈（逗号分隔）" />
            </div>
          ))}
          <button onClick={addItem} className="inline-flex items-center gap-1 rounded-md border border-dashed px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors">
            <Plus className="h-3 w-3" />添加项目经历
          </button>
        </div>
      ) : (
        <div>
          {projects.length > 0 ? (
            <div className="space-y-3">{projects.map((proj, idx) => <ProjectCard key={idx} entry={proj} />)}</div>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无项目经历</p>
          )}
        </div>
      )}
    </SectionCard>
  );
}

function ProjectCard({ entry }: { entry: Record<string, unknown> }) {
  const name = (entry.name as string) ?? (entry.project_name as string) ?? "";
  const role = (entry.role as string) ?? "";
  const period = (entry.period as string) ?? (entry.date_range as string) ?? "";
  const description = (entry.description as string) ?? (entry.summary as string) ?? "";
  const techStack = entry.tech_stack as string[] | undefined;
  return (
    <div className="rounded-md border p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          {name && <p className="text-sm font-semibold">{name}</p>}
          {role && <p className="text-sm text-muted-foreground">{role}</p>}
        </div>
        {period && <span className="inline-flex items-center gap-1 text-xs text-muted-foreground"><Calendar className="h-3 w-3" />{period}</span>}
      </div>
      {description && <p className="mt-2 text-sm whitespace-pre-wrap leading-relaxed">{description}</p>}
      {techStack && techStack.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {techStack.map((tech) => <span key={tech} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">{tech}</span>)}
        </div>
      )}
    </div>
  );
}

// ── Highlights Section ────────────────────────────────

function HighlightsSection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (v: string[]) => void }) {
  const [newItem, setNewItem] = useState("");
  const items = content.highlights ?? [];

  const addItem = () => { const t = newItem.trim(); if (t) { onChange([...items, t]); setNewItem(""); } };
  const removeItem = (i: number) => onChange(items.filter((_, idx) => idx !== i));

  return (
    <SectionCard icon={<Lightbulb className="h-4 w-4 text-primary" />} title="技术亮点">
      {isEditing ? (
        <div>
          <ul className="space-y-2">
            {items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 rounded-md border px-3 py-2 text-sm">
                <span className="mt-0.5 shrink-0 text-primary">&bull;</span>
                <span className="flex-1">{item}</span>
                <button onClick={() => removeItem(idx)} className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"><X className="h-3.5 w-3.5" /></button>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex gap-2">
            <input type="text" value={newItem} onChange={(e) => setNewItem(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addItem(); } }} className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="输入亮点，按 Enter 添加" />
            <button onClick={addItem} className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium hover:bg-muted transition-colors"><Plus className="h-3 w-3" />添加</button>
          </div>
        </div>
      ) : (
        <div>
          {items.length > 0 ? (
            <ul className="space-y-1.5">{items.map((item, idx) => <li key={idx} className="flex items-start gap-2 text-sm"><span className="mt-1 shrink-0 text-primary">&bull;</span><span className="leading-relaxed">{item}</span></li>)}</ul>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无技术亮点</p>
          )}
        </div>
      )}
    </SectionCard>
  );
}

// ── Metrics Section ────────────────────────────────────

function MetricsSection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (v: Record<string, unknown>[]) => void }) {
  const metrics = content.metrics ?? [];

  const addItem = () => onChange([...metrics, { label: "", value: "", description: "" }]);
  const removeItem = (i: number) => onChange(metrics.filter((_, idx) => idx !== i));
  const updateItem = (i: number, field: string, value: string) => {
    const updated = [...metrics];
    updated[i] = { ...updated[i], [field]: value };
    onChange(updated);
  };

  return (
    <SectionCard icon={<BarChart3 className="h-4 w-4 text-primary" />} title="量化指标">
      {isEditing ? (
        <div className="space-y-3">
          {metrics.map((m, idx) => (
            <div key={idx} className="rounded-md border p-3 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-medium text-muted-foreground">指标 #{idx + 1}</span>
                <button onClick={() => removeItem(idx)} className="text-muted-foreground hover:text-red-600 transition-colors"><X className="h-3.5 w-3.5" /></button>
              </div>
              <div className="grid gap-2 sm:grid-cols-3">
                <input type="text" value={(m.label as string) ?? ""} onChange={(e) => updateItem(idx, "label", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="指标名称" />
                <input type="text" value={(m.value as string) ?? ""} onChange={(e) => updateItem(idx, "value", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="数值" />
                <input type="text" value={(m.description as string) ?? ""} onChange={(e) => updateItem(idx, "description", e.target.value)} className="rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="说明" />
              </div>
            </div>
          ))}
          <button onClick={addItem} className="inline-flex items-center gap-1 rounded-md border border-dashed px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors">
            <Plus className="h-3 w-3" />添加量化指标
          </button>
        </div>
      ) : (
        <div>
          {metrics.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">{metrics.map((metric, idx) => <MetricCard key={idx} metric={metric} />)}</div>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无量化指标</p>
          )}
        </div>
      )}
    </SectionCard>
  );
}

function MetricCard({ metric }: { metric: Record<string, unknown> }) {
  const label = (metric.label as string) ?? (metric.name as string) ?? (metric.title as string) ?? "";
  const value = (metric.value as string) ?? (metric.metric as string) ?? "";
  const description = (metric.description as string) ?? (metric.context as string) ?? "";
  return (
    <div className="rounded-md border p-3">
      {label && <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>}
      {value && <p className="mt-1 text-sm font-semibold text-primary">{value}</p>}
      {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
    </div>
  );
}

// ── Interview Points Section ──────────────────────────

function InterviewPointsSection({ content, isEditing, onChange }: { content: ResumeContent; isEditing: boolean; onChange: (v: string[]) => void }) {
  const [newItem, setNewItem] = useState("");
  const items = content.interview_points ?? [];

  const addItem = () => { const t = newItem.trim(); if (t) { onChange([...items, t]); setNewItem(""); } };
  const removeItem = (i: number) => onChange(items.filter((_, idx) => idx !== i));

  return (
    <SectionCard icon={<MessageSquare className="h-4 w-4 text-primary" />} title="面试展开点">
      {isEditing ? (
        <div>
          <ul className="space-y-2">
            {items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 rounded-md border px-3 py-2 text-sm">
                <span className="mt-0.5 shrink-0 text-primary">&bull;</span>
                <span className="flex-1">{item}</span>
                <button onClick={() => removeItem(idx)} className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"><X className="h-3.5 w-3.5" /></button>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex gap-2">
            <input type="text" value={newItem} onChange={(e) => setNewItem(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addItem(); } }} className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50" placeholder="输入面试展开点，按 Enter 添加" />
            <button onClick={addItem} className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium hover:bg-muted transition-colors"><Plus className="h-3 w-3" />添加</button>
          </div>
        </div>
      ) : (
        <div>
          {items.length > 0 ? (
            <ul className="space-y-1.5">{items.map((item, idx) => <li key={idx} className="flex items-start gap-2 text-sm"><span className="mt-1 shrink-0 text-primary">&bull;</span><span className="leading-relaxed">{item}</span></li>)}</ul>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无面试展开点</p>
          )}
        </div>
      )}
    </SectionCard>
  );
}

// ── Version Timeline ──────────────────────────────────

function VersionTimeline({ versions, resumeId, viewingVersionId, onViewVersion }: {
  versions: { id?: string; version_no: number; created_at: string; source_type: string; summary_note?: string; generated_by: string }[];
  resumeId: string;
  viewingVersionId: string | null;
  onViewVersion: (versionId: string) => void;
}) {
  const sorted = [...versions].sort((a, b) => b.version_no - a.version_no);
  const latestVersionNo = sorted[0]?.version_no;
  const deleteVersion = useDeleteVersion(resumeId);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  return (
    <div className="relative space-y-0">
      {sorted.map((v, idx) => {
        const isLatest = v.version_no === latestVersionNo;
        const versionId = (v as Record<string, unknown>).id as string | undefined;
        const showDelete = !isLatest && versionId;
        const confirmingDelete = confirmDeleteId === versionId;
        const isViewing = viewingVersionId === versionId;

        return (
          <div key={v.version_no} className="relative flex gap-3 pb-4">
            {idx < sorted.length - 1 && <div className="absolute left-[11px] top-6 bottom-0 w-px bg-border" />}
            <div className="mt-1 shrink-0">
              <div className={`h-[22px] w-[22px] rounded-full border-2 flex items-center justify-center ${isViewing ? "border-amber-500 bg-amber-100" : "border-primary bg-primary/10"}`}>
                <div className={`h-2 w-2 rounded-full ${isViewing ? "bg-amber-500" : "bg-primary"}`} />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <button
                onClick={() => { if (versionId) onViewVersion(isViewing ? "" : versionId); }}
                className={`text-left w-full rounded-md px-2 py-1 -mx-2 transition-colors ${isViewing ? "bg-amber-50 ring-1 ring-amber-200" : "hover:bg-muted"}`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">v{v.version_no}</span>
                  <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">{sourceTypeLabel(v.source_type)}</span>
                  {isLatest && <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">当前版本</span>}
                  {isViewing && <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700">查看中</span>}
                </div>
                <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" />{formatDate(v.created_at)}</span>
                  <span className="inline-flex items-center gap-1"><GitBranch className="h-3 w-3" />{v.generated_by === "user" ? "用户" : v.generated_by === "agent" ? "AI 生成" : "混合"}</span>
                </div>
                {v.summary_note && <p className="mt-1 text-xs text-muted-foreground truncate">{v.summary_note}</p>}
              </button>
              {showDelete && !isViewing && (
                <div className="mt-1.5 ml-0">
                  {confirmingDelete ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-red-600">确认删除？</span>
                      <button onClick={() => { deleteVersion.mutate(versionId!); setConfirmDeleteId(null); }} disabled={deleteVersion.isPending} className="text-xs font-medium text-red-600 hover:text-red-800 disabled:opacity-50">删除</button>
                      <button onClick={() => setConfirmDeleteId(null)} className="text-xs text-muted-foreground hover:text-foreground">取消</button>
                    </div>
                  ) : (
                    <button onClick={() => setConfirmDeleteId(versionId!)} className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-red-600 transition-colors"><Trash2 className="h-3 w-3" />删除</button>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
