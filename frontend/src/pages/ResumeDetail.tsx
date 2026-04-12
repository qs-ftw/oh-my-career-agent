import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";

export function ResumeDetail() {
  return (
    <>
      <Header title="简历详情" description="查看、编辑和确认岗位主简历" />
      <PageContainer>
        <div className="rounded-lg border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            请从岗位详情中选择一份简历查看。
          </p>
        </div>
      </PageContainer>
    </>
  );
}
