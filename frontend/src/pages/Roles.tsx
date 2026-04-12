import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { Plus } from "lucide-react";

export function Roles() {
  return (
    <>
      <Header title="岗位目标" description="管理所有长期目标岗位" />
      <PageContainer>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">岗位列表</h3>
          <button className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            <Plus className="h-4 w-4" />
            新增岗位
          </button>
        </div>
        <div className="mt-4 rounded-lg border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            暂无岗位目标。点击「新增岗位」开始添加。
          </p>
        </div>
      </PageContainer>
    </>
  );
}
