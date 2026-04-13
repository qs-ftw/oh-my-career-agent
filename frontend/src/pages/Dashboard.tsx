import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { Target, FileText, BarChart3, Trophy, Bell, BookOpen } from "lucide-react";
import { useDashboardStats, useRecentJdDecisions } from "@/hooks/useDashboard";

const RECOMMENDATION_MAP: Record<string, { label: string; color: string }> = {
  apply_now: { label: "建议投递", color: "text-green-600" },
  tune_then_apply: { label: "微调后投递", color: "text-blue-600" },
  fill_gap_first: { label: "补齐差距", color: "text-yellow-600" },
  not_recommended: { label: "不建议", color: "text-red-600" },
};

export function Dashboard() {
  const { data: stats, isLoading } = useDashboardStats();
  const { data: jdDecisions } = useRecentJdDecisions();

  const statCards = [
    { label: "目标岗位", value: stats?.role_count ?? 0, icon: Target, color: "text-blue-500" },
    { label: "活跃简历", value: stats?.resume_count ?? 0, icon: FileText, color: "text-green-500" },
    { label: "高优 Gap", value: stats?.high_priority_gap_count ?? 0, icon: BarChart3, color: "text-orange-500" },
    { label: "最近成果", value: stats?.recent_achievement_count ?? 0, icon: Trophy, color: "text-purple-500" },
    { label: "待确认建议", value: stats?.pending_suggestion_count ?? 0, icon: Bell, color: "text-red-500" },
    { label: "面试故事", value: stats?.story_count ?? 0, icon: BookOpen, color: "text-teal-500" },
  ];

  return (
    <>
      <Header title="仪表盘" description="查看职业资产整体状态" />
      <PageContainer>
        {isLoading ? (
          <div className="text-sm text-muted-foreground">加载中...</div>
        ) : (
          <>
            {/* Stats grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              {statCards.map((stat) => (
                <div key={stat.label} className="rounded-lg border bg-card p-4">
                  <div className="flex items-center gap-2">
                    <stat.icon className={`h-4 w-4 ${stat.color}`} />
                    <span className="text-sm text-muted-foreground">{stat.label}</span>
                  </div>
                  <p className="mt-2 text-2xl font-bold">{stat.value}</p>
                </div>
              ))}
            </div>

            {/* Recent JD Decisions */}
            <div className="mt-6 rounded-lg border bg-card p-6">
              <h3 className="font-semibold">最近 JD 决策</h3>
              {jdDecisions && jdDecisions.length > 0 ? (
                <div className="mt-3 space-y-3">
                  {jdDecisions.map((decision) => (
                    <div key={decision.task_id} className="flex items-center justify-between rounded-md border p-3">
                      <div className="flex items-center gap-3">
                        <span className={`text-sm font-medium ${RECOMMENDATION_MAP[decision.recommendation]?.color || ""}`}>
                          {RECOMMENDATION_MAP[decision.recommendation]?.label || decision.recommendation}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>能力匹配: {Math.round(decision.ability_match_score * 100)}%</span>
                        <span>简历匹配: {Math.round(decision.resume_match_score * 100)}%</span>
                        <span>{decision.created_at ? new Date(decision.created_at).toLocaleDateString("zh-CN") : ""}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">
                  暂无 JD 决策。使用 JD 定制功能后，决策会显示在这里。
                </p>
              )}
            </div>

            {/* Quick links */}
            <div className="mt-4 rounded-lg border bg-card p-6">
              <h3 className="font-semibold">快速开始</h3>
              <div className="mt-3 grid grid-cols-3 gap-3">
                <a href="/roles" className="rounded-lg border p-4 text-sm hover:bg-accent transition-colors">
                  <p className="font-medium">添加岗位目标</p>
                  <p className="mt-1 text-muted-foreground">定义你想要的岗位方向</p>
                </a>
                <a href="/achievements" className="rounded-lg border p-4 text-sm hover:bg-accent transition-colors">
                  <p className="font-medium">录入成果</p>
                  <p className="mt-1 text-muted-foreground">记录项目成果和里程碑</p>
                </a>
                <a href="/jd-tailor" className="rounded-lg border p-4 text-sm hover:bg-accent transition-colors">
                  <p className="font-medium">JD 定制</p>
                  <p className="mt-1 text-muted-foreground">针对真实JD生成定制简历</p>
                </a>
              </div>
            </div>
          </>
        )}
      </PageContainer>
    </>
  );
}
