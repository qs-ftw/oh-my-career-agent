import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";

export function Suggestions() {
  return (
    <>
      <Header
        title="更新建议"
        description="统一管理所有 Agent 生成的待确认更新建议"
      />
      <PageContainer>
        <div className="rounded-lg border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            暂无待确认的更新建议。录入成果或更新岗位后，Agent 会自动生成建议。
          </p>
        </div>
      </PageContainer>
    </>
  );
}
