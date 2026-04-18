import { useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { WorkExperienceModal } from "@/components/portfolio/WorkExperienceModal";
import { EducationModal } from "@/components/portfolio/EducationModal";
import { ProjectModal } from "@/components/portfolio/ProjectModal";
import { AchievementAssignSelector } from "@/components/portfolio/AchievementAssignSelector";
import { AchievementCreateModal } from "@/components/portfolio/AchievementCreateModal";
import {
  useWorkExperiences,
  useCreateWorkExperience,
  useUpdateWorkExperience,
  useDeleteWorkExperience,
} from "@/hooks/useWorkExperiences";
import {
  useEducations,
  useCreateEducation,
  useUpdateEducation,
  useDeleteEducation,
} from "@/hooks/useEducations";
import {
  useProjects,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
} from "@/hooks/useProjects";
import { useAchievements, useUpdateAchievement, useDeleteAchievement, useCreateAchievement } from "@/hooks/useAchievements";
import {
  Plus,
  Building2,
  GraduationCap,
  FolderKanban,
  Trophy,
  Loader2,
  FileText,
  ChevronDown,
  ChevronRight,
  Pencil,
  Trash2,
  Calendar,
  MapPin,
} from "lucide-react";
import type { WorkExperience, Education, Project } from "@/types";

function formatDate(date: string | null): string {
  if (!date) return "至今";
  return new Date(date).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
  });
}

export function Overview() {
  const navigate = useNavigate();

  // ── Data hooks ──────────────────────────────────────────
  const { data: workExperiences = [], isLoading: weLoading } =
    useWorkExperiences();
  const { data: educations = [], isLoading: eduLoading } = useEducations();
  const { data: projects = [], isLoading: projLoading } = useProjects();
  const { data: achievements = [], isLoading: achLoading } = useAchievements();

  const createWE = useCreateWorkExperience();
  const updateWE = useUpdateWorkExperience();
  const deleteWE = useDeleteWorkExperience();
  const createEdu = useCreateEducation();
  const updateEdu = useUpdateEducation();
  const deleteEdu = useDeleteEducation();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const updateAchievement = useUpdateAchievement();
  const deleteAchievement = useDeleteAchievement();
  const createAchievement = useCreateAchievement();

  // ── Modal state ─────────────────────────────────────────
  const [editWE, setEditWE] = useState<WorkExperience | null>(null);
  const [showWEModal, setShowWEModal] = useState(false);
  const [editEdu, setEditEdu] = useState<Education | null>(null);
  const [showEduModal, setShowEduModal] = useState(false);
  const [editProject, setEditProject] = useState<Project | null>(null);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showAchCreateModal, setShowAchCreateModal] = useState(false);

  // Track which WE cards are expanded (all expanded by default)
  const [expandedWEs, setExpandedWEs] = useState<Set<string>>(() => {
    // Auto-expand all on first render — will be populated once data loads
    return new Set();
  });
  const [expandedEdus, setExpandedEdus] = useState<Set<string>>(() => new Set());
  const [initialExpandDone, setInitialExpandDone] = useState(false);

  // Orphan achievement assign selector state
  const [assigningAchId, setAssigningAchId] = useState<string | null>(null);

  // ── Derived data ────────────────────────────────────────
  const projectsByWE = useMemo(() => {
    const map = new Map<string, Project[]>();
    for (const p of projects) {
      if (p.work_experience_id) {
        const list = map.get(p.work_experience_id) ?? [];
        list.push(p);
        map.set(p.work_experience_id, list);
      }
    }
    return map;
  }, [projects]);

  const projectsByEdu = useMemo(() => {
    const map = new Map<string, Project[]>();
    for (const p of projects) {
      if (p.education_id && !p.work_experience_id) {
        const list = map.get(p.education_id) ?? [];
        list.push(p);
        map.set(p.education_id, list);
      }
    }
    return map;
  }, [projects]);

  const standaloneProjects = useMemo(
    () => projects.filter((p) => !p.work_experience_id && !p.education_id),
    [projects]
  );

  const orphanAchievements = useMemo(
    () =>
      achievements.filter(
        (a) => !a.project_id && !a.work_experience_id
      ),
    [achievements]
  );

  // Auto-expand all company and education cards on first load
  useMemo(() => {
    if (!initialExpandDone && (workExperiences.length > 0 || educations.length > 0)) {
      const allWEIds = new Set(workExperiences.map((we) => we.id));
      const allEduIds = new Set(educations.map((e) => e.id));
      setExpandedWEs(allWEIds);
      setExpandedEdus(allEduIds);
      setInitialExpandDone(true);
    }
  }, [workExperiences, educations, initialExpandDone]);

  // ── Callbacks ───────────────────────────────────────────
  const toggleWE = useCallback((weId: string) => {
    setExpandedWEs((prev) => {
      const next = new Set(prev);
      if (next.has(weId)) {
        next.delete(weId);
      } else {
        next.add(weId);
      }
      return next;
    });
  }, []);

  const handleCreateWE = useCallback(() => {
    setEditWE(null);
    setShowWEModal(true);
  }, []);

  const handleEditWE = useCallback((we: WorkExperience) => {
    setEditWE(we);
    setShowWEModal(true);
  }, []);

  const handleDeleteWE = useCallback(
    (id: string) => {
      if (confirm("确定删除此工作经历？相关项目将变为独立项目。")) {
        deleteWE.mutate(id);
      }
    },
    [deleteWE]
  );

  const toggleEdu = useCallback((eduId: string) => {
    setExpandedEdus((prev) => {
      const next = new Set(prev);
      if (next.has(eduId)) {
        next.delete(eduId);
      } else {
        next.add(eduId);
      }
      return next;
    });
  }, []);

  const handleCreateEdu = useCallback(() => {
    setEditEdu(null);
    setShowEduModal(true);
  }, []);

  const handleEditEdu = useCallback((edu: Education) => {
    setEditEdu(edu);
    setShowEduModal(true);
  }, []);

  const handleDeleteEdu = useCallback(
    (id: string) => {
      if (confirm("确定删除此教育经历？相关项目和成果将被一并删除。")) {
        deleteEdu.mutate(id);
      }
    },
    [deleteEdu]
  );

  const handleEduSubmit = useCallback(
    (data: Record<string, unknown>) => {
      if (editEdu) {
        updateEdu.mutate(
          { id: editEdu.id, data },
          { onSuccess: () => setShowEduModal(false) }
        );
      } else {
        createEdu.mutate(data, {
          onSuccess: () => setShowEduModal(false),
        });
      }
    },
    [editEdu, updateEdu, createEdu]
  );

  const handleWESubmit = useCallback(
    (data: Record<string, unknown>) => {
      if (editWE) {
        updateWE.mutate(
          { id: editWE.id, data },
          { onSuccess: () => setShowWEModal(false) }
        );
      } else {
        createWE.mutate(data, {
          onSuccess: () => setShowWEModal(false),
        });
      }
    },
    [editWE, updateWE, createWE]
  );

  const handleCreateProject = useCallback(() => {
    setEditProject(null);
    setShowProjectModal(true);
  }, []);

  const handleEditProject = useCallback(
    (p: Project) => {
      setEditProject(p);
      setShowProjectModal(true);
    },
    []
  );

  const handleDeleteProject = useCallback(
    (id: string) => {
      if (confirm("确定删除此项目？")) {
        deleteProject.mutate(id);
      }
    },
    [deleteProject]
  );

  const handleProjectSubmit = useCallback(
    (data: Record<string, unknown>) => {
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
    },
    [editProject, updateProject, createProject]
  );

  const handleAssign = useCallback(
    (achId: string, projectId: string, weId: string | null) => {
      updateAchievement.mutate(
        { id: achId, data: { project_id: projectId, work_experience_id: weId } },
        { onSuccess: () => setAssigningAchId(null) }
      );
    },
    [updateAchievement]
  );

  // ── Loading state ───────────────────────────────────────
  const isLoading = weLoading || eduLoading || projLoading || achLoading;

  if (isLoading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">加载中...</span>
        </div>
      </PageContainer>
    );
  }

  // ── Stats ───────────────────────────────────────────────
  const stats = {
    companies: workExperiences.length,
    educations: educations.length,
    projects: projects.length,
    achievements: achievements.length,
  };

  return (
    <PageContainer>
      {/* ── Sticky Toolbar ──────────────────────────────── */}
      <div className="sticky top-0 z-10 -mx-6 -mt-6 mb-6 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <Building2 className="h-4 w-4" />
              {stats.companies} 家公司
            </span>
            <span className="inline-flex items-center gap-1">
              <GraduationCap className="h-4 w-4" />
              {stats.educations} 段教育
            </span>
            <span className="inline-flex items-center gap-1">
              <FolderKanban className="h-4 w-4" />
              {stats.projects} 个项目
            </span>
            <span className="inline-flex items-center gap-1">
              <Trophy className="h-4 w-4" />
              {stats.achievements} 条成果
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAchCreateModal(true)}
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
            >
              <Plus className="h-4 w-4" />
              新增成果
            </button>
            <button
              onClick={handleCreateProject}
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
            >
              <Plus className="h-4 w-4" />
              新增项目
            </button>
            <button
              onClick={handleCreateEdu}
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
            >
              <Plus className="h-4 w-4" />
              新增教育经历
            </button>
            <button
              onClick={handleCreateWE}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              新增工作经历
            </button>
          </div>
        </div>
      </div>

      {/* ── Company Cards ───────────────────────────────── */}
      {workExperiences.length === 0 && standaloneProjects.length === 0 && orphanAchievements.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <FileText className="h-12 w-12 mb-3" />
          <p>暂无工作经历，点击上方按钮开始添加</p>
        </div>
      )}

      <div className="space-y-3">
        {workExperiences.map((we) => {
          const weProjects = projectsByWE.get(we.id) ?? [];
          const isExpanded = expandedWEs.has(we.id);

          return (
            <div
              key={we.id}
              className="rounded-lg border bg-card transition-shadow hover:shadow-sm"
            >
              {/* Compact header */}
              <div className="flex items-center gap-3 px-4 py-3">
                <button
                  onClick={() => toggleWE(we.id)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </button>

                <button
                  onClick={() => navigate(`/portfolio/${we.id}`)}
                  className="font-medium text-foreground hover:text-primary transition-colors"
                >
                  {we.company_name}
                </button>

                <span className="text-sm text-muted-foreground">
                  {we.role_title}
                </span>

                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  {formatDate(we.start_date)} - {formatDate(we.end_date)}
                </span>

                {we.location && (
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="h-3 w-3" />
                    {we.location}
                  </span>
                )}

                <span className="text-xs text-muted-foreground">
                  {weProjects.length} 个项目
                </span>

                <div className="ml-auto flex items-center gap-1">
                  <button
                    onClick={() => handleEditWE(we)}
                    className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                    title="编辑"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => handleDeleteWE(we.id)}
                    className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                    title="删除"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {/* Expanded project list */}
              {isExpanded && (
                <div className="border-t px-4 py-2">
                  {weProjects.length === 0 ? (
                    <p className="py-2 text-sm text-muted-foreground">
                      暂无项目
                    </p>
                  ) : (
                    <div className="space-y-1">
                      {weProjects.map((p) => (
                        <div
                          key={p.id}
                          className="group flex items-center gap-2 rounded px-2 py-1.5 hover:bg-muted/50 transition-colors"
                        >
                          <button
                            onClick={() =>
                              navigate(
                                `/portfolio/${we.id}/${p.id}`
                              )
                            }
                            className="text-sm font-medium hover:text-primary transition-colors"
                          >
                            {p.name}
                          </button>
                          {p.tech_stack && p.tech_stack.length > 0 && (
                            <div className="flex items-center gap-1">
                              {p.tech_stack.slice(0, 4).map((tech) => (
                                <span
                                  key={tech}
                                  className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                                >
                                  {tech}
                                </span>
                              ))}
                              {p.tech_stack.length > 4 && (
                                <span className="text-xs text-muted-foreground">
                                  +{p.tech_stack.length - 4}
                                </span>
                              )}
                            </div>
                          )}
                          <div className="ml-auto flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleEditProject(p)}
                              className="rounded p-1 text-muted-foreground hover:text-foreground transition-colors"
                              title="编辑项目"
                            >
                              <Pencil className="h-3 w-3" />
                            </button>
                            <button
                              onClick={() => handleDeleteProject(p.id)}
                              className="rounded p-1 text-muted-foreground hover:text-destructive transition-colors"
                              title="删除项目"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Education Cards ─────────────────────────────── */}
      {educations.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            <GraduationCap className="h-5 w-5" />
            教育经历
          </h2>
          <div className="space-y-3">
            {educations.map((edu) => {
              const eduProjects = projectsByEdu.get(edu.id) ?? [];
              const isExpanded = expandedEdus.has(edu.id);

              return (
                <div
                  key={edu.id}
                  className="rounded-lg border bg-card transition-shadow hover:shadow-sm"
                >
                  <div className="flex items-center gap-3 px-4 py-3">
                    <button
                      onClick={() => toggleEdu(edu.id)}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </button>

                    <GraduationCap className="h-4 w-4 text-muted-foreground shrink-0" />

                    <span className="font-medium text-foreground">
                      {edu.institution_name}
                    </span>

                    {edu.degree && (
                      <span className="text-sm text-muted-foreground">
                        {edu.degree}
                      </span>
                    )}

                    {edu.field_of_study && (
                      <span className="text-sm text-muted-foreground">
                        {edu.field_of_study}
                      </span>
                    )}

                    <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {formatDate(edu.start_date)} - {formatDate(edu.end_date)}
                    </span>

                    {edu.gpa && (
                      <span className="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">
                        GPA: {edu.gpa}
                      </span>
                    )}

                    <span className="text-xs text-muted-foreground">
                      {eduProjects.length} 个项目
                    </span>

                    <div className="ml-auto flex items-center gap-1">
                      <button
                        onClick={() => handleEditEdu(edu)}
                        className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                        title="编辑"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteEdu(edu.id)}
                        className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                        title="删除"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t px-4 py-2">
                      {edu.description && (
                        <p className="text-sm text-muted-foreground mb-2">
                          {edu.description}
                        </p>
                      )}
                      {eduProjects.length === 0 ? (
                        <p className="py-2 text-sm text-muted-foreground">
                          暂无项目
                        </p>
                      ) : (
                        <div className="space-y-1">
                          {eduProjects.map((p) => (
                            <div
                              key={p.id}
                              className="group flex items-center gap-2 rounded px-2 py-1.5 hover:bg-muted/50 transition-colors"
                            >
                              <span className="text-sm font-medium">{p.name}</span>
                              {p.tech_stack && p.tech_stack.length > 0 && (
                                <div className="flex items-center gap-1">
                                  {p.tech_stack.slice(0, 4).map((tech) => (
                                    <span
                                      key={tech}
                                      className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                                    >
                                      {tech}
                                    </span>
                                  ))}
                                  {p.tech_stack.length > 4 && (
                                    <span className="text-xs text-muted-foreground">
                                      +{p.tech_stack.length - 4}
                                    </span>
                                  )}
                                </div>
                              )}
                              <div className="ml-auto flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                  onClick={() => handleEditProject(p)}
                                  className="rounded p-1 text-muted-foreground hover:text-foreground transition-colors"
                                  title="编辑项目"
                                >
                                  <Pencil className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={() => handleDeleteProject(p.id)}
                                  className="rounded p-1 text-muted-foreground hover:text-destructive transition-colors"
                                  title="删除项目"
                                >
                                  <Trash2 className="h-3 w-3" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Standalone Projects ─────────────────────────── */}
      {standaloneProjects.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            <FolderKanban className="h-5 w-5" />
            独立项目
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {standaloneProjects.map((p) => {
              const pAchievements = achievements.filter(
                (a) => a.project_id === p.id
              );
              return (
                <div
                  key={p.id}
                  onClick={() => navigate(`/portfolio/project/${p.id}`)}
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
        </div>
      )}

      {/* ── Orphaned Achievements ───────────────────────── */}
      {orphanAchievements.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            <Trophy className="h-5 w-5" />
            未归档成果
            <span className="text-sm font-normal text-muted-foreground">
              ({orphanAchievements.length})
            </span>
          </h2>
          <div className="space-y-2">
            {orphanAchievements.map((ach) => (
              <div
                key={ach.id}
                className="group relative flex items-center gap-3 rounded-lg border bg-card px-4 py-3 hover:shadow-sm transition-shadow"
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{ach.title}</p>
                  {ach.raw_content && (
                    <p className="mt-0.5 text-sm text-muted-foreground line-clamp-1">
                      {ach.raw_content}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1.5 relative">
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
                      educations={educations}
                      projects={projects}
                      onSelect={(projectId, weId) =>
                        handleAssign(ach.id, projectId, weId)
                      }
                      onClose={() => setAssigningAchId(null)}
                    />
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteAchievement.mutate(ach.id);
                    }}
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Modals ──────────────────────────────────────── */}
      {showWEModal && (
        <WorkExperienceModal
          title={editWE ? "编辑工作经历" : "新增工作经历"}
          initial={editWE ?? undefined}
          onSubmit={handleWESubmit}
          onClose={() => setShowWEModal(false)}
          isSubmitting={createWE.isPending || updateWE.isPending}
        />
      )}

      {showEduModal && (
        <EducationModal
          title={editEdu ? "编辑教育经历" : "新增教育经历"}
          initial={editEdu ?? undefined}
          onSubmit={handleEduSubmit}
          onClose={() => setShowEduModal(false)}
          isSubmitting={createEdu.isPending || updateEdu.isPending}
        />
      )}

      {showProjectModal && (
        <ProjectModal
          title={editProject ? "编辑项目" : "新增项目"}
          initial={editProject ?? undefined}
          defaultWorkExperienceId={null}
          onSubmit={handleProjectSubmit}
          onClose={() => setShowProjectModal(false)}
          isSubmitting={createProject.isPending || updateProject.isPending}
        />
      )}

      {showAchCreateModal && (
        <AchievementCreateModal
          workExperiences={workExperiences}
          educations={educations}
          projects={projects}
          onClose={() => setShowAchCreateModal(false)}
          onSubmit={(data) => {
            createAchievement.mutate(data, {
              onSuccess: () => setShowAchCreateModal(false),
            });
          }}
          isSubmitting={createAchievement.isPending}
        />
      )}
    </PageContainer>
  );
}
