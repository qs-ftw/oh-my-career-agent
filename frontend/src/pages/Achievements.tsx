import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { Plus } from "lucide-react";

export function Achievements() {
  return (
    <>
      <Header title="成果中心" description="管理所有沉淀下来的成果资产" />
      <PageContainer>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">成果列表</h3>
          <button className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            <Plus className="h-4 w-4" />
            新增成果
          </button>
        </div>
        <div className="mt-4 rounded-lg border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            暂无成果记录。点击「新增成果」开始录入你的工作成果。
          </p>
        </div>
      </PageContainer>
    </>
  );
}
