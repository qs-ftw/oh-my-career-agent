import { useState } from "react";
import { useStories } from "@/hooks/useStories";

const THEMES = ["全部", "general", "leadership", "technical", "problem_solving", "collaboration"];

export function StoryBank() {
  const [theme, setTheme] = useState<string | undefined>(undefined);
  const [sourceType, setSourceType] = useState<string | undefined>(undefined);

  const selectedTheme = theme === "全部" ? undefined : theme;
  const { data, isLoading } = useStories(selectedTheme, sourceType);

  if (isLoading) {
    return <div className="p-6 text-muted-foreground">加载中...</div>;
  }

  const stories = data?.items ?? [];

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">故事库</h2>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">主题</label>
          <select
            className="rounded-md border px-3 py-1.5 text-sm"
            value={theme ?? "全部"}
            onChange={(e) => setTheme(e.target.value)}
          >
            {THEMES.map((t) => (
              <option key={t} value={t}>{t === "全部" ? "全部" : t}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">来源</label>
          <select
            className="rounded-md border px-3 py-1.5 text-sm"
            value={sourceType ?? "全部"}
            onChange={(e) => setSourceType(e.target.value === "全部" ? undefined : e.target.value)}
          >
            <option value="全部">全部</option>
            <option value="achievement">成果</option>
            <option value="jd_task">JD任务</option>
          </select>
        </div>
      </div>

      {/* Story list */}
      {stories.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          暂无故事。通过成果分析或JD任务生成面试故事。
        </div>
      ) : (
        <div className="space-y-4">
          {stories.map((story) => (
            <div key={story.id} className="rounded-lg border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{story.title}</h3>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-accent px-2 py-0.5 text-xs">
                    {story.theme}
                  </span>
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-xs">
                    {story.source_type}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {(story.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              {story.story_json && (
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Boolean(story.story_json.situation) && (
                    <div>
                      <span className="font-medium text-muted-foreground">情境: </span>
                      {String(story.story_json.situation).slice(0, 100)}
                    </div>
                  )}
                  {Boolean(story.story_json.task) && (
                    <div>
                      <span className="font-medium text-muted-foreground">任务: </span>
                      {String(story.story_json.task).slice(0, 100)}
                    </div>
                  )}
                  {Boolean(story.story_json.action) && (
                    <div>
                      <span className="font-medium text-muted-foreground">行动: </span>
                      {String(story.story_json.action).slice(0, 100)}
                    </div>
                  )}
                  {Boolean(story.story_json.result) && (
                    <div>
                      <span className="font-medium text-muted-foreground">结果: </span>
                      {String(story.story_json.result).slice(0, 100)}
                    </div>
                  )}
                </div>
              )}
              {story.best_for_json.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {story.best_for_json.map((tag, i) => (
                    <span key={i} className="rounded bg-muted px-1.5 py-0.5 text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
