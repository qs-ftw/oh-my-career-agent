import { useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { WorkExperienceModal } from "@/components/portfolio/WorkExperienceModal";
import { ProjectModal } from "@/components/portfolio/ProjectModal";
import { AchievementExpandable } from "@/components/portfolio/AchievementExpandable";
import { AchievementAssignSelector } from "@/components/portfolio/AchievementAssignSelector";
import { useWorkExperiences, useUpdateWorkExperience, useDeleteWorkExperience } from "@/hooks/useWorkExperiences";
import { useProjects, useCreateProject, useUpdateProject, useDeleteProject } from "@/hooks/useProjects";
import { useAchievements, useUpdateAchievement } from "@/hooks/useAchievements";
import { ChevronRight, Pencil, Trash2, Plus, FolderKanban, Calendar, MapPin } from "lucide-react";
import type { WorkExperience, Project } from "@/types";

function formatDate(date: string | null): string {
  if (!date) return "至今";
  return new Date(date).toLocaleDateString("zh-CN", { year: "numeric", month: "short" });
}

export function CompanyDetail() {
  const { weId } = useParams<{ weId: string }>();
  const navigate = useNavigate();

  // ── Data hooks ──────────────────────────────────────────
  const { data: workExperiences = [], isLoading: weLoading } = useWorkExperiences();
  const { data: projects = [], isLoading: projLoading } = useProjects();
  const { data: achievements = [], isLoading: achLoading } = useAchievements();

  const updateWE = useUpdateWorkExperience();
  const deleteWE = useDeleteWorkExperience();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const updateAchievement = useUpdateAchievement();

  // ── Modal state ─────────────────────────────────────────
  const [editWE, setEditWE] = useState<WorkExperience | null>(null);
  const [showWEModal, setShowWEModal] = useState(false);
  const [editProject, setEditProject] = useState<Project | null>(null);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [assigningAchId, setAssigningAchId] = useState<string | null>(null);

  // ── Derived data ────────────────────────────────────────
  const we = useMemo(
    () => workExperiences.find((w) => w.id === weId) ?? null,
    [workExperiences, weId]
  );

  const weProjects = useMemo(
    () => projects.filter((p) => p.work_experience_id === weId),
    [projects, weId]
  );

  const weAchievements = useMemo(
    () =>
      achievements.filter(
        (a) => a.work_experience_id === weId && !a.project_id
      ),
    [achievements, weId]
  );

  // ── Callbacks ───────────────────────────────────────────
  const handleEditWE = (w: WorkExperience) => {
    setEditWE(w);
    setShowWEModal(true);
  };

  const handleDeleteWE = () => {
    if (confirm("确定删除此工作经历？相关项目将变为独立项目。")) {
      deleteWE.mutate(weId!, {
        onSuccess: () => navigate("/portfolio"),
      });
    }
  };

  const handleWESubmit = (data: Record<string, unknown>) => {
    updateWE.mutate(
      { id: editWE!.id, data },
      { onSuccess: () => setShowWEModal(false) }
    );
  };

  const handleCreateProject = () => {
    setEditProject(null);
    setShowProjectModal(true);
  };

  const handleEditProject = (p: Project) => {
    setEditProject(p);
    setShowProjectModal(true);
  };

  const handleDeleteProject = (id: string) => {
    if (confirm("确定删除此项目？")) {
      deleteProject.mutate(id);
    }
  };

  const handleProjectSubmit = (data: Record<string, unknown>) => {
    if (editProject) {
      updateProject.mutate(
        { id: editProject.id, data },
        { onSuccess: () => setShowProjectModal(false) }
      );
    } else {
      createProject.mutate(data, {
        onSuccess: () => setShowProjectModal(false),
      });
    }
  };

  const handleAssign = (achId: string, projectId: string, weId: string | null) => {
    updateAchievement.mutate(
      { id: achId, data: { project_id: projectId, work_experience_id: weId } },
      { onSuccess: () => setAssigningAchId(null) }
    );
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

  if (!we) {
    return (
      <PageContainer>
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <p>工作经历不存在</p>
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
        <span className="text-foreground font-medium">{we.company_name}</span>
      </nav>

      {/* ── Company info card ─────────────────────────── */}
      <div className="rounded-lg border bg-card p-5">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-semibold">{we.company_name}</h1>
            <p className="mt-1 text-muted-foreground">{we.role_title}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {formatDate(we.start_date)} - {formatDate(we.end_date)}
              </span>
              {we.location && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" />
                  {we.location}
                </span>
              )}
            </div>
            {we.description && (
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                {we.description}
              </p>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleEditWE(we)}
              className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="编辑"
            >
              <Pencil className="h-4 w-4" />
            </button>
            <button
              onClick={handleDeleteWE}
              className="rounded p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
              title="删除"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Project list ──────────────────────────────── */}
      <div className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <FolderKanban className="h-5 w-5" />
            项目
            <span className="text-sm font-normal text-muted-foreground">
              ({weProjects.length})
            </span>
          </h2>
          <button
            onClick={handleCreateProject}
            className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            新增项目
          </button>
        </div>

        {weProjects.length === 0 ? (
          <p className="py-4 text-sm text-muted-foreground">暂无项目</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {weProjects.map((p) => {
              const pAchievements = achievements.filter(
                (a) => a.project_id === p.id
              );
              return (
                <div
                  key={p.id}
                  onClick={() => navigate(`/portfolio/${weId}/${p.id}`)}
                  className="group cursor-pointer rounded-lg border bg-card p-4 transition-shadow hover:shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <h3 className="font-medium">{p.name}</h3>
                    <div
                      className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => handleEditProject(p)}
                        className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                        title="编辑项目"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteProject(p.id)}
                        className="rounded p-1 text-muted-foreground hover:text-destructive transition-colors"
                        title="删除项目"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  {p.description && (
                    <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                      {p.description}
                    </p>
                  )}
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    {p.tech_stack && p.tech_stack.length > 0 && (
                      <>
                        {p.tech_stack.map((tech) => (
                          <span
                            key={tech}
                            className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                          >
                            {tech}
                          </span>
                        ))}
                      </>
                    )}
                    <span className="ml-auto text-xs text-muted-foreground">
                      {pAchievements.length} 条成果
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── WE-level achievements ──────────────────────── */}
      <div className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">
          工作成果
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({weAchievements.length})
          </span>
        </h2>
        {weAchievements.length === 0 ? (
          <p className="py-4 text-sm text-muted-foreground">暂无工作成果</p>
        ) : (
          <div className="space-y-2">
            {weAchievements.map((ach) => (
              <div
                key={ach.id}
                className="relative flex items-start gap-3 rounded-lg border bg-card px-4 py-3"
              >
                <AchievementExpandable achievement={ach} />
                <div className="relative shrink-0 pt-1">
                  <button
                    onClick={() =>
                      setAssigningAchId(
                        assigningAchId === ach.id ? null : ach.id
                      )
                    }
                    className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium hover:bg-muted transition-colors"
                  >
                    <FolderKanban className="h-3 w-3" />
                    归档到项目
                  </button>
                  {assigningAchId === ach.id && (
                    <AchievementAssignSelector
                      workExperiences={workExperiences}
                      projects={projects}
                      onSelect={(projectId, weId) =>
                        handleAssign(ach.id, projectId, weId)
                      }
                      onClose={() => setAssigningAchId(null)}
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Modals ────────────────────────────────────── */}
      {showWEModal && (
        <WorkExperienceModal
          title="编辑工作经历"
          initial={editWE ?? undefined}
          onSubmit={handleWESubmit}
          onClose={() => setShowWEModal(false)}
          isSubmitting={updateWE.isPending}
        />
      )}

      {showProjectModal && (
        <ProjectModal
          title={editProject ? "编辑项目" : "新增项目"}
          initial={editProject ?? undefined}
          defaultWorkExperienceId={weId}
          onSubmit={handleProjectSubmit}
          onClose={() => setShowProjectModal(false)}
          isSubmitting={createProject.isPending || updateProject.isPending}
        />
      )}
    </PageContainer>
  );
}
