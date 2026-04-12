import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";

const columns = [
  { key: "open", label: "未开始" },
  { key: "in_progress", label: "进行中" },
  { key: "closed", label: "已完成" },
];

export function GapBoard() {
  return (
    <>
      <Header title="Gap 看板" description="帮助理解自己离每个岗位还差什么" />
      <PageContainer>
        <div className="grid gap-4 md:grid-cols-3">
          {columns.map((col) => (
            <div key={col.key} className="rounded-lg border bg-card">
              <div className="border-b px-4 py-3">
                <h4 className="text-sm font-semibold">{col.label}</h4>
              </div>
              <div className="p-4 text-center text-sm text-muted-foreground">
                暂无 Gap
              </div>
            </div>
          ))}
        </div>
      </PageContainer>
    </>
  );
}
