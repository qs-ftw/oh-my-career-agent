import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Target,
  FileText,
  Trophy,
  BarChart3,
  FileSearch,
  Bell,
  UserCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "仪表盘", icon: LayoutDashboard },
  { to: "/roles", label: "岗位目标", icon: Target },
  { to: "/resumes", label: "简历管理", icon: FileText },
  { to: "/achievements", label: "成果中心", icon: Trophy },
  { to: "/gaps", label: "Gap 看板", icon: BarChart3 },
  { to: "/jd-tailor", label: "JD 定制", icon: FileSearch },
  { to: "/suggestions", label: "更新建议", icon: Bell },
  { to: "/profile", label: "候选人画像", icon: UserCircle },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-60 flex-col border-r bg-card">
      <div className="flex h-14 items-center border-b px-4">
        <h1 className="text-lg font-semibold text-primary">CareerAgent</h1>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t p-4 text-xs text-muted-foreground">
        CareerAgent v0.1.0
      </div>
    </aside>
  );
}
