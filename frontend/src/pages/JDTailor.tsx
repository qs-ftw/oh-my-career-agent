import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import { useJDParse, useJDTailor } from "@/hooks/useJD";
import type { JDParsed, JDTailorResult } from "@/types";

const STEPS = [
  { num: 1, label: "输入 JD" },
  { num: 2, label: "解析结果" },
  { num: 3, label: "选择模式" },
  { num: 4, label: "定制结果" },
];

const RECOMMENDATION_MAP: Record<string, { label: string; color: string }> = {
  apply_now: { label: "建议投递", color: "bg-green-100 text-green-800 border-green-200" },
  tune_then_apply: { label: "微调后投递", color: "bg-blue-100 text-blue-800 border-blue-200" },
  fill_gap_first: { label: "补齐差距后投递", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  not_recommended: { label: "暂不建议投递", color: "bg-red-100 text-red-800 border-red-200" },
};

export function JDTailor() {
  const [step, setStep] = useState(1);
  const [jdText, setJdText] = useState("");
  const [parsedResult, setParsedResult] = useState<JDParsed | null>(null);
  const [mode, setMode] = useState<"generate_new" | "tune_existing">("generate_new");
  const [tailorResult, setTailorResult] = useState<JDTailorResult | null>(null);

  const parseMutation = useJDParse();
  const tailorMutation = useJDTailor();

  const handleParse = async () => {
    if (!jdText.trim()) return;
    try {
      const result = await parseMutation.mutateAsync(jdText);
      setParsedResult(result);
      setStep(2);
    } catch {
      // Error handled by mutation state
    }
  };

  const handleTailor = async () => {
    if (!jdText.trim()) return;
    try {
      const result = await tailorMutation.mutateAsync({
        raw_jd: jdText,
        mode,
      });
      setTailorResult(result);
      setStep(4);
    } catch {
      // Error handled by mutation state
    }
  };

  return (
    <>
      <Header title="JD 定制" description="针对真实岗位JD快速生成投递版本" />
      <PageContainer>
        <div className="space-y-6">
          {/* Stepper */}
          <div className="flex items-center gap-2">
            {STEPS.map((s, i) => (
              <div key={s.num} className="flex items-center gap-2">
                <button
                  onClick={() => {
                    if (s.num < step || (s.num === 2 && parsedResult) || (s.num === 4 && tailorResult))
                      setStep(s.num);
                  }}
                  className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                    step === s.num
                      ? "bg-primary text-primary-foreground"
                      : step > s.num
                        ? "bg-primary/10 text-primary"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  <span className="flex h-5 w-5 items-center justify-center rounded-full text-xs">
                    {step > s.num ? "✓" : s.num}
                  </span>
                  {s.label}
                </button>
                {i < STEPS.length - 1 && (
                  <div className={`h-px w-8 ${step > s.num ? "bg-primary" : "bg-muted"}`} />
                )}
              </div>
            ))}
          </div>

          {/* Step 1: Input JD */}
          {step === 1 && (
            <div className="rounded-lg border bg-card p-6">
              <h3 className="font-semibold">粘贴岗位描述</h3>
              <textarea
                className="mt-3 w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                rows={10}
                placeholder="粘贴完整的岗位 JD 内容，包括职位要求、技能要求、职责描述等..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
              <div className="mt-3 flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  {jdText.length > 0 ? `${jdText.length} 字` : "最少输入 10 个字符"}
                </p>
                <button
                  onClick={handleParse}
                  disabled={jdText.length < 10 || parseMutation.isPending}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {parseMutation.isPending ? (
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                      解析中...
                    </span>
                  ) : (
                    "解析 JD"
                  )}
                </button>
              </div>
              {parseMutation.isError && (
                <p className="mt-2 text-sm text-red-500">解析失败，请重试</p>
              )}
            </div>
          )}

          {/* Step 2: Parsed Results */}
          {step === 2 && parsedResult && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-card p-6">
                <h3 className="mb-4 font-semibold">解析结果</h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">职位名称</p>
                    <p className="mt-1 text-lg font-medium">{parsedResult.role_name || "未识别"}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">必备技能</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {parsedResult.required_skills.map((skill, i) => (
                        <span key={i} className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                          {skill}
                        </span>
                      ))}
                      {parsedResult.required_skills.length === 0 && (
                        <span className="text-sm text-muted-foreground">未识别</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">加分技能</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {parsedResult.bonus_items.map((item, i) => (
                        <span key={i} className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                          {item}
                        </span>
                      ))}
                      {parsedResult.bonus_items.length === 0 && (
                        <span className="text-sm text-muted-foreground">未识别</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">关键词</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {parsedResult.keywords.map((kw, i) => (
                        <span key={i} className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
                >
                  返回修改
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                >
                  下一步：选择模式
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Mode Selection */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-card p-6">
                <h3 className="mb-4 font-semibold">选择定制模式</h3>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setMode("generate_new")}
                    className={`rounded-lg border p-4 text-left transition-colors ${
                      mode === "generate_new"
                        ? "border-primary bg-primary/5 ring-1 ring-primary"
                        : "hover:bg-accent"
                    }`}
                  >
                    <p className="font-medium">从职业资产生成</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      基于你的所有成果和技能，从头生成一份针对该 JD 的简历
                    </p>
                  </button>
                  <button
                    onClick={() => setMode("tune_existing")}
                    className={`rounded-lg border p-4 text-left transition-colors ${
                      mode === "tune_existing"
                        ? "border-primary bg-primary/5 ring-1 ring-primary"
                        : "hover:bg-accent"
                    }`}
                  >
                    <p className="font-medium">基于现有简历微调</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      在现有简历基础上，根据 JD 优化关键词和重点
                    </p>
                  </button>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setStep(2)}
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
                >
                  返回
                </button>
                <button
                  onClick={handleTailor}
                  disabled={tailorMutation.isPending}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {tailorMutation.isPending ? (
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                      定制中（10-30秒）...
                    </span>
                  ) : (
                    "开始定制"
                  )}
                </button>
              </div>
              {tailorMutation.isError && (
                <p className="text-sm text-red-500">定制失败，请重试</p>
              )}
            </div>
          )}

          {/* Step 4: Results */}
          {step === 4 && tailorResult && (
            <div className="space-y-4">
              {/* Scores */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: "能力匹配度", score: tailorResult.ability_match_score },
                  { label: "简历表达度", score: tailorResult.resume_match_score },
                  { label: "投递准备度", score: tailorResult.readiness_score },
                ].map((item) => (
                  <div key={item.label} className="rounded-lg border bg-card p-4 text-center">
                    <p className="text-sm text-muted-foreground">{item.label}</p>
                    <div className="mt-2">
                      <span className={`text-2xl font-bold ${item.score >= 0.7 ? "text-green-600" : item.score >= 0.4 ? "text-yellow-600" : "text-red-600"}`}>
                        {Math.round(item.score * 100)}%
                      </span>
                    </div>
                    <div className="mt-2 h-2 w-full rounded-full bg-muted">
                      <div
                        className={`h-full rounded-full transition-all ${
                          item.score >= 0.7 ? "bg-green-500" : item.score >= 0.4 ? "bg-yellow-500" : "bg-red-500"
                        }`}
                        style={{ width: `${item.score * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Recommendation */}
              {tailorResult.recommendation && (
                <div className={`rounded-lg border p-4 ${RECOMMENDATION_MAP[tailorResult.recommendation]?.color || "bg-gray-100 text-gray-800"}`}>
                  <p className="font-medium">
                    投递建议：{RECOMMENDATION_MAP[tailorResult.recommendation]?.label || tailorResult.recommendation}
                  </p>
                </div>
              )}

              {/* Resume Preview */}
              <div className="rounded-lg border bg-card p-6">
                <h3 className="mb-4 font-semibold">定制简历预览</h3>
                {tailorResult.resume && (
                  <div className="space-y-4">
                    {tailorResult.resume.summary && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">职业摘要</p>
                        <p className="mt-1 text-sm">{tailorResult.resume.summary}</p>
                      </div>
                    )}
                    {tailorResult.resume.skills && tailorResult.resume.skills.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">核心技能</p>
                        <div className="mt-1 flex flex-wrap gap-1.5">
                          {(Array.isArray(tailorResult.resume.skills) ? tailorResult.resume.skills : []).map(
                            (skill: string | Record<string, unknown>, i: number) => (
                              <span key={i} className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                                {typeof skill === "string" ? skill : JSON.stringify(skill)}
                              </span>
                            )
                          )}
                        </div>
                      </div>
                    )}
                    {tailorResult.resume.highlights && tailorResult.resume.highlights.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">亮点</p>
                        <ul className="mt-1 space-y-1">
                          {tailorResult.resume.highlights.map((h: string | Record<string, unknown>, i: number) => (
                            <li key={i} className="text-sm">
                              • {typeof h === "string" ? h : JSON.stringify(h)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Missing Items & Optimization Notes */}
              <div className="grid grid-cols-2 gap-4">
                {tailorResult.missing_items && tailorResult.missing_items.length > 0 && (
                  <div className="rounded-lg border bg-card p-4">
                    <p className="font-medium text-red-700">缺失项</p>
                    <ul className="mt-2 space-y-1">
                      {tailorResult.missing_items.map((item: string, i: number) => (
                        <li key={i} className="text-sm text-red-600">• {item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {tailorResult.optimization_notes && tailorResult.optimization_notes.length > 0 && (
                  <div className="rounded-lg border bg-card p-4">
                    <p className="font-medium text-yellow-700">优化建议</p>
                    <ul className="mt-2 space-y-1">
                      {tailorResult.optimization_notes.map((note: string, i: number) => (
                        <li key={i} className="text-sm text-yellow-600">• {note}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setStep(1);
                    setJdText("");
                    setParsedResult(null);
                    setTailorResult(null);
                  }}
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
                >
                  重新开始
                </button>
              </div>
            </div>
          )}
        </div>
      </PageContainer>
    </>
  );
}
