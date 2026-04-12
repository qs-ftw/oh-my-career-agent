import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";

export function JDTailor() {
  return (
    <>
      <Header title="JD 定制" description="针对真实岗位JD快速生成投递版本" />
      <PageContainer>
        <div className="space-y-6">
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold">输入 JD</h3>
            <textarea
              className="mt-3 w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              rows={8}
              placeholder="粘贴岗位 JD 内容..."
            />
            <div className="mt-3 flex gap-3">
              <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                从职业资产生成
              </button>
              <button className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent">
                基于现有简历微调
              </button>
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6 text-center">
            <p className="text-muted-foreground">
              输入 JD 后，系统将自动解析并生成定制化简历和匹配度评估。
            </p>
          </div>
        </div>
      </PageContainer>
    </>
  );
}
