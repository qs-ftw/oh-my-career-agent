import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { useListResumes, useDeleteResume } from "@/hooks/useResumes";
import { FileText, Loader2, AlertTriangle, Trash2 } from "lucide-react";

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  active: { label: "生效中", color: "bg-green-100 text-green-700" },
  draft: { label: "草稿", color: "bg-yellow-100 text-yellow-700" },
  archived: { label: "已归档", color: "bg-gray-100 text-gray-500" },
};

const TYPE_MAP: Record<string, string> = {
  master: "主简历",
  customized: "定制简历",
};

export function Resumes() {
  const navigate = useNavigate();
  const { data: resumes, isLoading, isError } = useListResumes();
  const deleteResume = useDeleteResume();
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <>
        <Header title="简历管理" description="管理所有简历版本" />
        <PageContainer>
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">加载中...</span>
          </div>
        </PageContainer>
      </>
    );
  }

  if (isError) {
    return (
      <>
        <Header title="简历管理" description="管理所有简历版本" />
        <PageContainer>
          <div className="flex items-center justify-center rounded-lg border border-red-200 bg-red-50 p-12">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="ml-2 text-red-600">加载失败，请稍后重试</span>
          </div>
        </PageContainer>
      </>
    );
  }

  return (
    <>
      <Header title="简历管理" description="管理所有简历版本" />
      <PageContainer>
        {!resumes || resumes.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-lg border bg-card p-12">
            <FileText className="h-12 w-12 text-muted-foreground/40" />
            <p className="mt-4 text-lg font-medium text-muted-foreground">暂无简历</p>
            <p className="mt-1 text-sm text-muted-foreground">
              先创建一个岗位目标，系统会自动生成对应的主简历
            </p>
            <button
              onClick={() => navigate("/roles")}
              className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              前往岗位目标
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {resumes.map((resume) => {
              const status = STATUS_MAP[resume.status] ?? {
                label: resume.status,
                color: "bg-gray-100 text-gray-500",
              };
              return (
                <div
                  key={resume.id}
                  className="flex flex-col rounded-lg border bg-card p-5 text-left transition-colors hover:bg-accent"
                >
                  {/* Clickable card body */}
                  <div
                    className="cursor-pointer flex-1"
                    onClick={() => navigate(`/resumes/${resume.id}`)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-base font-semibold">
                          {resume.resume_name}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {TYPE_MAP[resume.resume_type] ?? resume.resume_type}
                        </p>
                      </div>
                      <span
                        className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${status.color}`}
                      >
                        {status.label}
                      </span>
                    </div>
                    {resume.content.summary && (
                      <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
                        {resume.content.summary}
                      </p>
                    )}
                    <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
                      <span>v{resume.current_version_no}</span>
                      {resume.completeness_score > 0 && (
                        <span>完成度 {Math.round(resume.completeness_score)}%</span>
                      )}
                      {resume.match_score > 0 && (
                        <span>匹配度 {Math.round(resume.match_score)}%</span>
                      )}
                    </div>
                    {resume.content.skills && resume.content.skills.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {resume.content.skills.slice(0, 5).map((skill) => (
                          <span
                            key={skill}
                            className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700"
                          >
                            {skill}
                          </span>
                        ))}
                        {resume.content.skills.length > 5 && (
                          <span className="px-1.5 py-0.5 text-xs text-muted-foreground">
                            +{resume.content.skills.length - 5}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  {/* Delete button */}
                  <div className="mt-3 pt-3 border-t flex items-center justify-end">
                    {confirmDeleteId === resume.id ? (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-red-600">确认删除？</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteResume.mutate(resume.id);
                            setConfirmDeleteId(null);
                          }}
                          disabled={deleteResume.isPending}
                          className="text-xs font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
                        >
                          删除
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfirmDeleteId(null);
                          }}
                          className="text-xs text-muted-foreground hover:text-foreground"
                        >
                          取消
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmDeleteId(resume.id);
                        }}
                        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-red-600 transition-colors"
                      >
                        <Trash2 className="h-3 w-3" />
                        删除
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </PageContainer>
    </>
  );
}
