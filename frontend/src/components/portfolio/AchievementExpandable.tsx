import { useState } from "react";
import { ChevronDown, ChevronRight, Pencil, Loader2, FolderKanban, Trash2, Sparkles, Zap } from "lucide-react";
import { useAnalyzeAchievement, useUpdateAchievement, useDeleteAchievement } from "@/hooks/useAchievements";
import { AchievementAssignSelector } from "@/components/portfolio/AchievementAssignSelector";
import type { Achievement, WorkExperience, Education, Project } from "@/types";

interface AchievementExpandableProps {
  achievement: Achievement;
  onRemove?: () => void;
  showRemove?: boolean;
  workExperiences?: WorkExperience[];
  educations?: Education[];
  projects?: Project[];
  onInteractiveAnalysis?: (id: string, title: string) => void;
}

export function AchievementExpandable({
  achievement,
  onRemove,
  showRemove = false,
  workExperiences = [],
  educations = [],
  projects = [],
  onInteractiveAnalysis,
}: AchievementExpandableProps) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(achievement.title);
  const [editContent, setEditContent] = useState(achievement.raw_content ?? "");
  const [showMoveSelector, setShowMoveSelector] = useState(false);
  const updateAchievement = useUpdateAchievement();
  const analyzeAchievement = useAnalyzeAchievement();
  const deleteAchievement = useDeleteAchievement();

  const hasParsed = achievement.status !== "raw";
  const parsedData = achievement.parsed_data as Record<string, unknown> | null;
  const summary = (parsedData?.summary as string) ?? null;
  const canMove = showRemove && projects.length > 0;

  const handleSave = () => {
    updateAchievement.mutate(
      { id: achievement.id, data: { title: editTitle, raw_content: editContent } },
      { onSuccess: () => setEditing(false) },
    );
  };

  const handleRemove = () => {
    updateAchievement.mutate(
      { id: achievement.id, data: { project_id: null } },
      { onSuccess: () => onRemove?.() },
    );
  };

  const handleMoveToProject = (projectId: string, weId: string | null) => {
    updateAchievement.mutate(
      { id: achievement.id, data: { project_id: projectId, work_experience_id: weId } },
      { onSuccess: () => {
        setShowMoveSelector(false);
        onRemove?.();
      } },
    );
  };

  const handleDelete = () => {
    deleteAchievement.mutate(achievement.id, { onSuccess: () => onRemove?.() });
  };

  return (
    <div className="flex-1 min-w-0">
      <div
        className="flex items-center gap-2 cursor-pointer hover:bg-muted/40 rounded px-2 py-1.5 -mx-2 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
        <span className="text-sm font-medium text-foreground truncate flex-1">{achievement.title}</span>
        {achievement.importance_score > 0 && (
          <span className="inline-flex rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">{achievement.importance_score}</span>
        )}
        <span className={`inline-flex rounded px-1.5 py-0.5 text-xs ${hasParsed ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"}`}>
          {hasParsed ? "已分析" : "未分析"}
        </span>
      </div>

      {expanded && (
        <div className="border-t mt-1 px-2 py-2 space-y-2">
              {achievement.polished_content && achievement.display_format !== "raw" && (
                <div className="rounded-md border bg-muted/30 p-3 mb-2">
                  {achievement.display_format === "narrative" ? (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {achievement.polished_content.narrative}
                    </p>
                  ) : (
                    <ul className="text-sm space-y-1">
                      {achievement.polished_content.bullets.map((b, i) => (
                        <li key={i}>{b}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              {achievement.enrichment_suggestions && achievement.enrichment_suggestions.length > 0 && (
                <div className="rounded-md border border-dashed p-2 mb-2">
                  <p className="text-xs font-medium text-muted-foreground mb-1">完善建议</p>
                  {achievement.enrichment_suggestions.map((s, i) => (
                    <p key={i} className="text-xs text-muted-foreground">💡 {s.suggestion}</p>
                  ))}
                </div>
              )}
          {editing ? (
            <div className="space-y-2">
              <input className="w-full rounded-md border px-2 py-1.5 text-sm" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
              <textarea className="w-full rounded-md border px-2 py-1.5 text-sm resize-none" rows={3} value={editContent} onChange={(e) => setEditContent(e.target.value)} />
              <div className="flex gap-2 justify-end">
                <button onClick={() => setEditing(false)} className="rounded-md border px-3 py-1 text-xs hover:bg-muted transition-colors">取消</button>
                <button onClick={handleSave} disabled={updateAchievement.isPending} className="rounded-md bg-primary px-3 py-1 text-xs text-primary-foreground disabled:opacity-50">{updateAchievement.isPending ? "保存中..." : "保存"}</button>
              </div>
            </div>
          ) : (
            <>
              {hasParsed && summary && <p className="text-xs text-muted-foreground">{summary}</p>}
              {achievement.tags && achievement.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {achievement.tags.map((tag) => (<span key={tag} className="inline-flex rounded bg-indigo-50 px-1.5 py-0.5 text-xs text-indigo-700">{tag}</span>))}
                </div>
              )}
              {achievement.raw_content && <p className="text-xs text-muted-foreground/70 italic line-clamp-3">{achievement.raw_content}</p>}
            </>
          )}
          {!editing && (
            <div className="space-y-1.5 pt-1 border-t">
              {/* Row 1: AI actions (prominent) */}
              <div className="flex items-center gap-1.5">
                {!hasParsed && (
                  <button
                    onClick={() => analyzeAchievement.mutate(achievement.id)}
                    disabled={analyzeAchievement.isPending}
                    className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100 transition-colors disabled:opacity-50"
                  >
                    {analyzeAchievement.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Zap className="h-3 w-3" />}
                    快速分析
                  </button>
                )}
                {onInteractiveAnalysis && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onInteractiveAnalysis(achievement.id, achievement.title); }}
                    className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
                  >
                    <Sparkles className="h-3 w-3" />
                    互动剖析
                  </button>
                )}
                {achievement.polished_content && (
                  <div className="flex items-center gap-0.5 rounded-md border p-0.5">
                    {(["narrative", "bullets", "raw"] as const).map((fmt) => (
                      <button
                        key={fmt}
                        onClick={(e) => {
                          e.stopPropagation();
                          updateAchievement.mutate({ id: achievement.id, data: { display_format: fmt } });
                        }}
                        className={`rounded px-1.5 py-0.5 text-xs transition-colors ${
                          achievement.display_format === fmt
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-muted"
                        }`}
                      >
                        {fmt === "narrative" ? "叙事" : fmt === "bullets" ? "要点" : "原文"}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {/* Row 2: Management actions (subtle) */}
              <div className="flex items-center gap-1">
                <button onClick={() => setEditing(true)} className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" title="编辑"><Pencil className="h-3.5 w-3.5" /></button>
                {showRemove && (
                  <>
                    <button onClick={handleRemove} disabled={updateAchievement.isPending} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors disabled:opacity-50">移出项目</button>
                    {canMove && (
                      <div className="relative">
                        <button
                          onClick={() => setShowMoveSelector(!showMoveSelector)}
                          disabled={updateAchievement.isPending}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
                        >
                          <FolderKanban className="h-3 w-3" />
                          移到其他项目
                        </button>
                        {showMoveSelector && (
                          <AchievementAssignSelector
                            workExperiences={workExperiences}
                            educations={educations}
                            projects={projects.filter((p) => p.id !== achievement.project_id)}
                            onSelect={handleMoveToProject}
                            onClose={() => setShowMoveSelector(false)}
                          />
                        )}
                      </div>
                    )}
                  </>
                )}
                <button
                  onClick={handleDelete}
                  disabled={deleteAchievement.isPending}
                  className="ml-auto inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors disabled:opacity-50"
                  title="彻底删除"
                >
                  <Trash2 className="h-3 w-3" />
                  删除
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
