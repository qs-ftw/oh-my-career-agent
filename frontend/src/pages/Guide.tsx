import { useNavigate } from "react-router-dom";
import {
  UserCircle,
  Briefcase,
  Target,
  Trophy,
  BarChart3,
  FileText,
  CheckCircle2,
  Circle,
  ArrowRight,
  Sparkles,
  Upload,
} from "lucide-react";
import { useProfileCompleteness } from "@/hooks/useProfile";
import { useWorkExperiences } from "@/hooks/useWorkExperiences";
import { useProjects } from "@/hooks/useProjects";
import { useAchievements } from "@/hooks/useAchievements";
import { useRoles } from "@/hooks/useRoles";
import { useListResumes } from "@/hooks/useResumes";

interface StepStatus {
  done: boolean;
  detail: string;
}

function useStepStatuses(): StepStatus[] {
  const { data: completeness } = useProfileCompleteness();
  const { data: workExperiences = [] } = useWorkExperiences();
  const { data: projects = [] } = useProjects();
  const { data: achievements = [] } = useAchievements();
  const { data: rolesResp } = useRoles();
  const { data: resumes = [] } = useListResumes();

  const roles = rolesResp?.items ?? [];

  return [
    {
      done: (completeness?.completeness_pct ?? 0) >= 60,
      detail: (completeness?.completeness_pct ?? 0) > 0
        ? `完善度 ${completeness!.completeness_pct}%`
        : "尚未开始",
    },
    {
      done: workExperiences.length > 0 || projects.length > 0,
      detail: `${workExperiences.length} 段经历 · ${projects.length} 个项目`,
    },
    {
      done: roles.length > 0,
      detail: roles.length > 0 ? `${roles.length} 个目标岗位` : "尚未添加",
    },
    {
      done: achievements.length > 0,
      detail: achievements.length > 0 ? `${achievements.length} 条成果` : "尚未录入",
    },
    {
      done: roles.length > 0,
      detail: roles.length > 0 ? `${roles.length} 个岗位可查看` : "先添加目标岗位",
    },
    {
      done: resumes.length > 0,
      detail: resumes.length > 0 ? `${resumes.length} 份简历` : "尚未生成",
    },
  ];
}

const steps = [
  {
    icon: UserCircle,
    title: "完善候选人画像",
    desc: "上传简历 PDF 自动提取个人信息，或手动填写姓名、联系方式、专业技能等基础资料。",
    tip: "导入简历一键搞定，省去手动填写",
    tipIcon: Upload,
    href: "/profile",
    color: "text-blue-500",
    bg: "bg-blue-50",
  },
  {
    icon: Briefcase,
    title: "构建职业履历",
    desc: "添加工作经历、教育背景和项目。每段经历下可关联多个项目，每个项目可录入具体成果。",
    tip: "支持在教育/工作经历下管理项目",
    tipIcon: Sparkles,
    href: "/portfolio",
    color: "text-violet-500",
    bg: "bg-violet-50",
  },
  {
    icon: Target,
    title: "设定目标岗位",
    desc: "创建你想投递的岗位方向（如后端工程师、AI 工程师）。系统会为每个岗位建立独立的能力模型。",
    tip: "可粘贴 JD 快速创建",
    tipIcon: Sparkles,
    href: "/roles",
    color: "text-orange-500",
    bg: "bg-orange-50",
  },
  {
    icon: Trophy,
    title: "录入工作成果",
    desc: "将项目中的关键产出整理为成果记录。每条成果会自动分析并匹配到相关岗位。",
    tip: "在 Claude Code 中运行 /check-work 一键从代码生成成果",
    tipIcon: Sparkles,
    href: "/portfolio",
    color: "text-emerald-500",
    bg: "bg-emerald-50",
  },
  {
    icon: BarChart3,
    title: "查看 Gap 分析",
    desc: "系统对比你的职业资产和目标岗位要求，生成结构化的能力差距报告，明确提升方向。",
    tip: "新增成果后 Gap 会自动更新",
    tipIcon: Sparkles,
    href: "/gaps",
    color: "text-amber-500",
    bg: "bg-amber-50",
  },
  {
    icon: FileText,
    title: "定制简历",
    desc: "在目标岗位卡片上点击「定制简历」，系统自动匹配你最相关的经历和成果，生成投递就绪的简历版本。",
    tip: "生成后自动跳转到简历详情页",
    tipIcon: Sparkles,
    href: "/roles",
    color: "text-rose-500",
    bg: "bg-rose-50",
  },
];

export function Guide() {
  const navigate = useNavigate();
  const statuses = useStepStatuses();
  const totalDone = statuses.filter((s) => s.done).length;
  const progressPct = Math.round((totalDone / steps.length) * 100);

  return (
    <div className="overflow-y-auto p-6 max-w-3xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold">新手指南</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          六步完成从信息录入到简历生成的完整流程
        </p>
        {/* Progress bar */}
        <div className="mt-4 flex items-center gap-3">
          <div className="h-2 flex-1 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <span className="text-xs font-medium text-muted-foreground">
            {totalDone}/{steps.length} 已完成
          </span>
        </div>
      </div>

      {/* Steps */}
      <div className="relative space-y-4">
        {/* Connecting line */}
        <div className="absolute left-5 top-6 bottom-6 w-px bg-border" />

        {steps.map((step, i) => {
          const status = statuses[i];
          const Icon = step.icon;
          const TipIcon = step.tipIcon;

          return (
            <div
              key={i}
              className="relative flex gap-4"
            >
              {/* Step indicator */}
              <div className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 ${
                status.done
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-background text-muted-foreground"
              }`}>
                {status.done ? (
                  <CheckCircle2 className="h-5 w-5" />
                ) : (
                  <span className="text-sm font-semibold">{i + 1}</span>
                )}
              </div>

              {/* Card */}
              <div
                className={`group flex-1 rounded-lg border bg-card p-4 transition-shadow hover:shadow-sm ${
                  status.done ? "opacity-80" : ""
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-md ${step.bg}`}>
                      <Icon className={`h-4 w-4 ${step.color}`} />
                    </div>
                    <div>
                      <h3 className="font-medium text-sm">{step.title}</h3>
                      <p className="text-xs text-muted-foreground">{status.detail}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate(step.href)}
                    className="flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium text-primary opacity-0 group-hover:opacity-100 hover:bg-primary/10 transition-all"
                  >
                    前往
                    <ArrowRight className="h-3 w-3" />
                  </button>
                </div>

                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  {step.desc}
                </p>

                {/* Tip badge */}
                <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-primary/5 px-2 py-0.5 text-xs text-primary">
                  <TipIcon className="h-3 w-3" />
                  {step.tip}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
