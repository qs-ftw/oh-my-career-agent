import { useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { ProjectModal } from "@/components/portfolio/ProjectModal";
import { AchievementExpandable } from "@/components/portfolio/AchievementExpandable";
import { InteractiveAnalysisPanel } from "@/components/portfolio/InteractiveAnalysisPanel";
import { useWorkExperiences } from "@/hooks/useWorkExperiences";
import { useProjects, useUpdateProject, useDeleteProject } from "@/hooks/useProjects";
import { useAchievements, useCreateAchievement } from "@/hooks/useAchievements";
import { ChevronRight, Pencil, Trash2, Plus, Calendar, ExternalLink } from "lucide-react";
import type { Project } from "@/types";

function formatDate(date: string | null): string {
  if (!date) return "至今";
  return new Date(date).toLocaleDateString("zh-CN", { year: "numeric", month: "short" });
}

export function ProjectDetail() {
  const { weId, projectId } = useParams<{ weId: string; projectId: string }>();
  const navigate = useNavigate();

  // ── Data hooks ──────────────────────────────────────────
  const { data: workExperiences = [], isLoading: weLoading } = useWorkExperiences();
  const { data: projects = [], isLoading: projLoading } = useProjects();
  const { data: achievements = [], isLoading: achLoading } = useAchievements();

  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const createAchievement = useCreateAchievement();

  // ── Modal state ─────────────────────────────────────────
  const [editProject, setEditProject] = useState<Project | null>(null);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showCreateAch, setShowCreateAch] = useState(false);
  const [achTitle, setAchTitle] = useState("");
  const [achContent, setAchContent] = useState("");
  const [analysisAchId, setAnalysisAchId] = useState<string | null>(null);
  const [analysisAchTitle, setAnalysisAchTitle] = useState("");

  // ── Derived data ────────────────────────────────────────
  const we = useMemo(
    () => workExperiences.find((w) => w.id === weId) ?? null,
    [workExperiences, weId]
  );

  const project = useMemo(
    () => projects.find((p) => p.id === projectId) ?? null,
    [projects, projectId]
  );

  const parentLabel = we ? we.company_name : "独立项目";

  const projectAchievements = useMemo(
    () => achievements.filter((a) => a.project_id === projectId),
    [achievements, projectId]
  );

  // ── Callbacks ───────────────────────────────────────────
  const handleEditProject = () => {
    if (project) {
      setEditProject(project);
      setShowProjectModal(true);
    }
  };

  const handleDeleteProject = () => {
    if (confirm("确定删除此项目？")) {
      deleteProject.mutate(projectId!, {
        onSuccess: () => navigate(weId ? `/portfolio/${weId}` : "/portfolio"),
      });
    }
  };

  const handleProjectSubmit = (data: Record<string, unknown>) => {
    updateProject.mutate(
      { id: editProject!.id, data },
      { onSuccess: () => setShowProjectModal(false) }
    );
  };

  const handleCreateAch = () => {
    if (!achTitle.trim()) return;
    createAchievement.mutate(
      {
        title: achTitle.trim(),
        raw_content: achContent.trim(),
        project_id: projectId!,
        work_experience_id: weId ?? null,
        source_type: "manual",
      },
      {
        onSuccess: () => {
          setAchTitle("");
          setAchContent("");
          setShowCreateAch(false);
        },
      }
    );
  };

  const handleInteractiveAnalysis = (achId: string, title: string) => {
    setAnalysisAchId(achId);
    setAnalysisAchTitle(title);
  };

  // ── Loading state ───────────────────────────────────────
  const isLoading = weLoading || projLoading || achLoading;

  if (isLoading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          加载中...
        </div>
      </PageContainer>
    );
  }

  if (!project) {
    return (
      <PageContainer>
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <p>项目不存在</p>
          <Link to="/portfolio" className="mt-2 text-primary hover:underline">
            返回履历列表
          </Link>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* ── Breadcrumb ────────────────────────────────── */}
      <nav className="mb-6 flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link to="/portfolio" className="hover:text-foreground transition-colors">
          职业履历
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        {weId ? (
          <Link to={`/portfolio/${weId}`} className="hover:text-foreground transition-colors">
            {parentLabel}
          </Link>
        ) : (
          <span>{parentLabel}</span>
        )}
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-foreground font-medium">{project.name}</span>
      </nav>

      {/* ── Project info card ─────────────────────────── */}
      <div className="rounded-lg border bg-card p-5">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h2 className="text-xl font-semibold">{project.name}</h2>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              {(project.start_date || project.end_date) && (
                <span className="inline-flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {formatDate(project.start_date)} - {formatDate(project.end_date)}
                </span>
              )}
              {project.url && (
                <a
                  href={project.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-primary hover:underline"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  {project.url}
                </a>
              )}
            </div>
            {project.description && (
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
                {project.description}
              </p>
            )}
            {project.tech_stack && project.tech_stack.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {project.tech_stack.map((tech) => (
                  <span
                    key={tech}
                    className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleEditProject}
              className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="编辑"
            >
              <Pencil className="h-4 w-4" />
            </button>
            <button
              onClick={handleDeleteProject}
              className="rounded p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
              title="删除"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Achievement list ──────────────────────────── */}
      <div className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            项目成果
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({projectAchievements.length})
            </span>
          </h2>
          <button
            onClick={() => setShowCreateAch(true)}
            className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            新增成果
          </button>
        </div>

        {projectAchievements.length === 0 && !showCreateAch ? (
          <p className="py-4 text-sm text-muted-foreground">暂无项目成果</p>
        ) : (
          <div className="space-y-2">
            {projectAchievements.map((ach) => (
              <div
                key={ach.id}
                className="flex items-start rounded-lg border bg-card px-4 py-3"
              >
                <AchievementExpandable achievement={ach} showRemove={true} workExperiences={workExperiences} projects={projects} onInteractiveAnalysis={handleInteractiveAnalysis} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Create achievement form ───────────────────── */}
      {showCreateAch && (
        <div className="mt-4 rounded-lg border bg-card p-4 space-y-3">
          <input
            type="text"
            placeholder="成果标题"
            value={achTitle}
            onChange={(e) => setAchTitle(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
          />
          <textarea
            placeholder="成果内容（可选）"
            value={achContent}
            onChange={(e) => setAchContent(e.target.value)}
            rows={3}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setShowCreateAch(false);
                setAchTitle("");
                setAchContent("");
              }}
              className="rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleCreateAch}
              disabled={!achTitle.trim() || createAchievement.isPending}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {createAchievement.isPending ? "创建中..." : "创建"}
            </button>
          </div>
        </div>
      )}

      {/* ── Edit project modal ────────────────────────── */}
      {showProjectModal && (
        <ProjectModal
          title="编辑项目"
          initial={editProject ?? undefined}
          defaultWorkExperienceId={weId}
          onSubmit={handleProjectSubmit}
          onClose={() => setShowProjectModal(false)}
          isSubmitting={updateProject.isPending}
        />
      )}

      {analysisAchId && (
        <InteractiveAnalysisPanel
          achievementId={analysisAchId}
          achievementTitle={analysisAchTitle}
          onClose={() => { setAnalysisAchId(null); setAnalysisAchTitle(""); }}
        />
      )}
    </PageContainer>
  );
}
