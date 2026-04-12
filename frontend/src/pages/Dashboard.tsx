import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { Target, FileText, BarChart3, Trophy, Bell } from "lucide-react";

const stats = [
  { label: "目标岗位", value: "0", icon: Target, color: "text-blue-500" },
  { label: "活跃简历", value: "0", icon: FileText, color: "text-green-500" },
  { label: "高优 Gap", value: "0", icon: BarChart3, color: "text-orange-500" },
  { label: "最近成果", value: "0", icon: Trophy, color: "text-purple-500" },
  { label: "待确认建议", value: "0", icon: Bell, color: "text-red-500" },
];

export function Dashboard() {
  return (
    <>
      <Header title="仪表盘" description="查看职业资产整体状态" />
      <PageContainer>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-lg border bg-card p-4"
            >
              <div className="flex items-center gap-2">
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
                <span className="text-sm text-muted-foreground">
                  {stat.label}
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold">{stat.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-lg border bg-card p-6">
          <h3 className="font-semibold">岗位概览</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            暂无岗位目标。点击左侧「岗位目标」开始添加。
          </p>
        </div>

        <div className="mt-4 rounded-lg border bg-card p-6">
          <h3 className="font-semibold">最近动态</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            暂无动态。开始使用 CareerAgent 后，这里会展示最近的成果、更新建议和 Gap 变化。
          </p>
        </div>
      </PageContainer>
    </>
  );
}
