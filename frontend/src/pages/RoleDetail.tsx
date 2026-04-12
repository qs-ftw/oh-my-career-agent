import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";

export function RoleDetail() {
  return (
    <>
      <Header title="岗位详情" description="查看岗位完整职业资产情况" />
      <PageContainer>
        <div className="rounded-lg border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            请从岗位列表中选择一个岗位查看详情。
          </p>
        </div>
      </PageContainer>
    </>
  );
}
