import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { useResume, useUpdateResume, useResumeVersions } from "@/hooks/useResumes";
import type { ResumeContent } from "@/types";
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
} from "lucide-react";

// ── Main Component ────────────────────────────────────

export function ResumeDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: resume, isLoading, isError } = useResume(id ?? "");
  const { data: versions } = useResumeVersions(id ?? "");

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

  return (
    <>
      <Header title={resume.resume_name} description="查看、编辑简历内容" />
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
          <span className="text-foreground font-medium">{resume.resume_name}</span>
        </nav>

        {/* Two-column layout */}
        <div className="mt-6 grid gap-6 lg:grid-cols-[3fr_2fr]">
          {/* Left Column — Content Editor */}
          <div className="space-y-5">
            <SummarySection resume={resume} />
            <SkillsSection resume={resume} />
            <ExperiencesSection resume={resume} />
            <ProjectsSection resume={resume} />
            <HighlightsSection resume={resume} />
            <MetricsSection resume={resume} />
            <InterviewPointsSection resume={resume} />
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
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}
                  >
                    {statusLabel}
                  </span>
                </InfoField>
                <InfoField label="版本号">
                  <span className="text-sm font-medium">v{resume.current_version_no}</span>
                </InfoField>
                <InfoField label="创建时间">
                  <span className="text-sm text-muted-foreground">
                    {formatDate(resume.created_at)}
                  </span>
                </InfoField>
                <InfoField label="更新时间">
                  <span className="text-sm text-muted-foreground">
                    {formatDate(resume.updated_at)}
                  </span>
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
                <ScoreBar
                  label="完成度"
                  value={resume.completeness_score}
                  colorClass="bg-blue-500"
                />
                <ScoreBar
                  label="匹配度"
                  value={resume.match_score}
                  colorClass="bg-emerald-500"
                />
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
                  <VersionTimeline versions={versions} />
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

// ── Helper components ─────────────────────────────────

function InfoField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <div>{children}</div>
    </div>
  );
}

function ScoreBar({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: number;
  colorClass: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold">{value}%</span>
      </div>
      <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all ${colorClass}`}
          style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
        />
      </div>
    </div>
  );
}

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function sourceTypeLabel(sourceType: string) {
  switch (sourceType) {
    case "achievement":
      return "成就分析";
    case "jd":
      return "JD 解析";
    case "manual_edit":
      return "手动编辑";
    default:
      return sourceType;
  }
}

// ── Section Wrapper with Edit Mode ────────────────────

function EditableSection({
  icon,
  title,
  editingKey,
  currentKey,
  onEdit,
  onCancel,
  onSave,
  isSaving,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  editingKey: string;
  currentKey: string;
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
  isSaving: boolean;
  children: React.ReactNode;
}) {
  const isEditing = editingKey === currentKey;

  return (
    <section className="rounded-lg border bg-card p-5">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-base font-semibold">
          {icon}
          {title}
        </h3>
        {isEditing ? (
          <div className="flex items-center gap-2">
            <button
              onClick={onCancel}
              className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium hover:bg-muted transition-colors"
            >
              <X className="h-3 w-3" />
              取消
            </button>
            <button
              onClick={onSave}
              disabled={isSaving}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isSaving ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Save className="h-3 w-3" />
              )}
              保存
            </button>
          </div>
        ) : (
          <button
            onClick={onEdit}
            className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium hover:bg-muted transition-colors"
          >
            <Pencil className="h-3 w-3" />
            编辑
          </button>
        )}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

// ── Summary Section ───────────────────────────────────

function SummarySection({ resume }: { resume: { id: string; content: ResumeContent } }) {
  const updateResume = useUpdateResume();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const SECTION_KEY = "summary";

  const handleEdit = () => {
    setDraft(resume.content.summary ?? "");
    setEditingKey(SECTION_KEY);
  };

  const handleCancel = () => {
    setEditingKey(null);
    setDraft("");
  };

  const handleSave = () => {
    updateResume.mutate(
      {
        id: resume.id,
        data: {
          content: { summary: draft },
        },
      },
      { onSuccess: () => setEditingKey(null) }
    );
  };

  const isEditing = editingKey === SECTION_KEY;

  return (
    <EditableSection
      icon={<User className="h-4 w-4 text-primary" />}
      title="个人摘要"

      editingKey={editingKey ?? ""}
      currentKey={SECTION_KEY}
      onEdit={handleEdit}
      onCancel={handleCancel}
      onSave={handleSave}
      isSaving={updateResume.isPending}
    >
      {isEditing ? (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={5}
          className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
          placeholder="输入个人摘要..."
        />
      ) : (
        <p className="text-sm whitespace-pre-wrap leading-relaxed">
          {resume.content.summary || (
            <span className="text-muted-foreground italic">暂无个人摘要</span>
          )}
        </p>
      )}
    </EditableSection>
  );
}

// ── Skills Section ────────────────────────────────────

function SkillsSection({ resume }: { resume: { id: string; content: ResumeContent } }) {
  const updateResume = useUpdateResume();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [draft, setDraft] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState("");

  const SECTION_KEY = "skills";

  const handleEdit = () => {
    setDraft([...(resume.content.skills ?? [])]);
    setEditingKey(SECTION_KEY);
  };

  const handleCancel = () => {
    setEditingKey(null);
    setDraft([]);
    setNewSkill("");
  };

  const handleSave = () => {
    updateResume.mutate(
      {
        id: resume.id,
        data: {
          content: { skills: draft },
        },
      },
      { onSuccess: () => setEditingKey(null) }
    );
  };

  const addSkill = () => {
    const trimmed = newSkill.trim();
    if (trimmed && !draft.includes(trimmed)) {
      setDraft([...draft, trimmed]);
      setNewSkill("");
    }
  };

  const removeSkill = (skill: string) => {
    setDraft(draft.filter((s) => s !== skill));
  };

  const isEditing = editingKey === SECTION_KEY;

  return (
    <EditableSection
      icon={<Wrench className="h-4 w-4 text-primary" />}
      title="核心技能"

      editingKey={editingKey ?? ""}
      currentKey={SECTION_KEY}
      onEdit={handleEdit}
      onCancel={handleCancel}
      onSave={handleSave}
      isSaving={updateResume.isPending}
    >
      {isEditing ? (
        <div>
          <div className="flex flex-wrap gap-1.5">
            {draft.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center gap-1 rounded-md bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700"
              >
                {skill}
                <button
                  onClick={() => removeSkill(skill)}
                  className="hover:text-blue-900 transition-colors"
                >
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
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addSkill();
                }
              }}
              className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="输入技能名称，按 Enter 添加"
            />
            <button
              onClick={addSkill}
              className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
            >
              <Plus className="h-3 w-3" />
              添加
            </button>
          </div>
        </div>
      ) : (
        <div>
          {resume.content.skills && resume.content.skills.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {resume.content.skills.map((skill) => (
                <span
                  key={skill}
                  className="rounded-md bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700"
                >
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无核心技能</p>
          )}
        </div>
      )}
    </EditableSection>
  );
}

// ── Experiences Section (read-only) ───────────────────

function ExperiencesSection({ resume }: { resume: { content: ResumeContent } }) {
  const experiences = resume.content.experiences ?? [];

  return (
    <section className="rounded-lg border bg-card p-5">
      <h3 className="flex items-center gap-2 text-base font-semibold">
        <Building2 className="h-4 w-4 text-primary" />
        工作经历
      </h3>
      <div className="mt-4">
        {experiences.length > 0 ? (
          <div className="space-y-3">
            {experiences.map((exp, idx) => (
              <ExperienceCard key={idx} entry={exp} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground italic">暂无工作经历</p>
        )}
      </div>
    </section>
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
          {company && (
            <p className="text-sm font-semibold">{company}</p>
          )}
          {title && (
            <p className="text-sm text-muted-foreground">{title}</p>
          )}
        </div>
        {period && (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            {period}
          </span>
        )}
      </div>
      {description && (
        <p className="mt-2 text-sm whitespace-pre-wrap leading-relaxed">{description}</p>
      )}
    </div>
  );
}

// ── Projects Section (read-only) ──────────────────────

function ProjectsSection({ resume }: { resume: { content: ResumeContent } }) {
  const projects = resume.content.projects ?? [];

  return (
    <section className="rounded-lg border bg-card p-5">
      <h3 className="flex items-center gap-2 text-base font-semibold">
        <FolderGit2 className="h-4 w-4 text-primary" />
        项目经历
      </h3>
      <div className="mt-4">
        {projects.length > 0 ? (
          <div className="space-y-3">
            {projects.map((proj, idx) => (
              <ProjectCard key={idx} entry={proj} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground italic">暂无项目经历</p>
        )}
      </div>
    </section>
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
          {name && (
            <p className="text-sm font-semibold">{name}</p>
          )}
          {role && (
            <p className="text-sm text-muted-foreground">{role}</p>
          )}
        </div>
        {period && (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            {period}
          </span>
        )}
      </div>
      {description && (
        <p className="mt-2 text-sm whitespace-pre-wrap leading-relaxed">{description}</p>
      )}
      {techStack && techStack.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {techStack.map((tech) => (
            <span
              key={tech}
              className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
            >
              {tech}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Highlights Section ────────────────────────────────

function HighlightsSection({ resume }: { resume: { id: string; content: ResumeContent } }) {
  const updateResume = useUpdateResume();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [draft, setDraft] = useState<string[]>([]);
  const [newItem, setNewItem] = useState("");

  const SECTION_KEY = "highlights";

  const handleEdit = () => {
    setDraft([...(resume.content.highlights ?? [])]);
    setEditingKey(SECTION_KEY);
  };

  const handleCancel = () => {
    setEditingKey(null);
    setDraft([]);
    setNewItem("");
  };

  const handleSave = () => {
    updateResume.mutate(
      {
        id: resume.id,
        data: {
          content: { highlights: draft },
        },
      },
      { onSuccess: () => setEditingKey(null) }
    );
  };

  const addItem = () => {
    const trimmed = newItem.trim();
    if (trimmed) {
      setDraft([...draft, trimmed]);
      setNewItem("");
    }
  };

  const removeItem = (index: number) => {
    setDraft(draft.filter((_, i) => i !== index));
  };

  const isEditing = editingKey === SECTION_KEY;

  return (
    <EditableSection
      icon={<Lightbulb className="h-4 w-4 text-primary" />}
      title="技术亮点"

      editingKey={editingKey ?? ""}
      currentKey={SECTION_KEY}
      onEdit={handleEdit}
      onCancel={handleCancel}
      onSave={handleSave}
      isSaving={updateResume.isPending}
    >
      {isEditing ? (
        <div>
          <ul className="space-y-2">
            {draft.map((item, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 rounded-md border px-3 py-2 text-sm"
              >
                <span className="mt-0.5 shrink-0 text-primary">&bull;</span>
                <span className="flex-1">{item}</span>
                <button
                  onClick={() => removeItem(idx)}
                  className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addItem();
                }
              }}
              className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="输入亮点，按 Enter 添加"
            />
            <button
              onClick={addItem}
              className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
            >
              <Plus className="h-3 w-3" />
              添加
            </button>
          </div>
        </div>
      ) : (
        <div>
          {resume.content.highlights && resume.content.highlights.length > 0 ? (
            <ul className="space-y-1.5">
              {resume.content.highlights.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <span className="mt-1 shrink-0 text-primary">&bull;</span>
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无技术亮点</p>
          )}
        </div>
      )}
    </EditableSection>
  );
}

// ── Metrics Section (read-only) ───────────────────────

function MetricsSection({ resume }: { resume: { content: ResumeContent } }) {
  const metrics = resume.content.metrics ?? [];

  return (
    <section className="rounded-lg border bg-card p-5">
      <h3 className="flex items-center gap-2 text-base font-semibold">
        <BarChart3 className="h-4 w-4 text-primary" />
        量化指标
      </h3>
      <div className="mt-4">
        {metrics.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {metrics.map((metric, idx) => (
              <MetricCard key={idx} metric={metric} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground italic">暂无量化指标</p>
        )}
      </div>
    </section>
  );
}

function MetricCard({ metric }: { metric: Record<string, unknown> }) {
  const label = (metric.label as string) ?? (metric.name as string) ?? (metric.title as string) ?? "";
  const value = (metric.value as string) ?? (metric.metric as string) ?? "";
  const description = (metric.description as string) ?? (metric.context as string) ?? "";

  return (
    <div className="rounded-md border p-3">
      {label && (
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
      )}
      {value && (
        <p className="mt-1 text-sm font-semibold text-primary">{value}</p>
      )}
      {description && (
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

// ── Interview Points Section ──────────────────────────

function InterviewPointsSection({ resume }: { resume: { id: string; content: ResumeContent } }) {
  const updateResume = useUpdateResume();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [draft, setDraft] = useState<string[]>([]);
  const [newItem, setNewItem] = useState("");

  const SECTION_KEY = "interview_points";

  const handleEdit = () => {
    setDraft([...(resume.content.interview_points ?? [])]);
    setEditingKey(SECTION_KEY);
  };

  const handleCancel = () => {
    setEditingKey(null);
    setDraft([]);
    setNewItem("");
  };

  const handleSave = () => {
    updateResume.mutate(
      {
        id: resume.id,
        data: {
          content: { interview_points: draft },
        },
      },
      { onSuccess: () => setEditingKey(null) }
    );
  };

  const addItem = () => {
    const trimmed = newItem.trim();
    if (trimmed) {
      setDraft([...draft, trimmed]);
      setNewItem("");
    }
  };

  const removeItem = (index: number) => {
    setDraft(draft.filter((_, i) => i !== index));
  };

  const isEditing = editingKey === SECTION_KEY;

  return (
    <EditableSection
      icon={<MessageSquare className="h-4 w-4 text-primary" />}
      title="面试展开点"

      editingKey={editingKey ?? ""}
      currentKey={SECTION_KEY}
      onEdit={handleEdit}
      onCancel={handleCancel}
      onSave={handleSave}
      isSaving={updateResume.isPending}
    >
      {isEditing ? (
        <div>
          <ul className="space-y-2">
            {draft.map((item, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 rounded-md border px-3 py-2 text-sm"
              >
                <span className="mt-0.5 shrink-0 text-primary">&bull;</span>
                <span className="flex-1">{item}</span>
                <button
                  onClick={() => removeItem(idx)}
                  className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addItem();
                }
              }}
              className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="输入面试展开点，按 Enter 添加"
            />
            <button
              onClick={addItem}
              className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
            >
              <Plus className="h-3 w-3" />
              添加
            </button>
          </div>
        </div>
      ) : (
        <div>
          {resume.content.interview_points && resume.content.interview_points.length > 0 ? (
            <ul className="space-y-1.5">
              {resume.content.interview_points.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <span className="mt-1 shrink-0 text-primary">&bull;</span>
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground italic">暂无面试展开点</p>
          )}
        </div>
      )}
    </EditableSection>
  );
}

// ── Version Timeline ──────────────────────────────────

function VersionTimeline({ versions }: { versions: { version_no: number; created_at: string; source_type: string; summary_note?: string; generated_by: string }[] }) {
  const sorted = [...versions].sort((a, b) => b.version_no - a.version_no);

  return (
    <div className="relative space-y-0">
      {sorted.map((v, idx) => (
        <div key={v.version_no} className="relative flex gap-3 pb-4">
          {/* Timeline line */}
          {idx < sorted.length - 1 && (
            <div className="absolute left-[11px] top-6 bottom-0 w-px bg-border" />
          )}
          {/* Timeline dot */}
          <div className="mt-1 shrink-0">
            <div className="h-[22px] w-[22px] rounded-full border-2 border-primary bg-primary/10 flex items-center justify-center">
              <div className="h-2 w-2 rounded-full bg-primary" />
            </div>
          </div>
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">v{v.version_no}</span>
              <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {sourceTypeLabel(v.source_type)}
              </span>
            </div>
            <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDate(v.created_at)}
              </span>
              <span className="inline-flex items-center gap-1">
                <GitBranch className="h-3 w-3" />
                {v.generated_by === "user"
                  ? "用户"
                  : v.generated_by === "agent"
                    ? "AI 生成"
                    : "混合"}
              </span>
            </div>
            {v.summary_note && (
              <p className="mt-1 text-xs text-muted-foreground truncate">
                {v.summary_note}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
