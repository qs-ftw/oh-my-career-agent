import { NavLink, Link } from "react-router-dom";
import {
  LayoutDashboard,
  Target,
  FileText,
  BarChart3,
  UserCircle,
  Briefcase,
  Map,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "仪表盘", icon: LayoutDashboard },
  { to: "/profile", label: "候选人画像", icon: UserCircle },
  { to: "/portfolio", label: "职业履历", icon: Briefcase },
  { to: "/roles", label: "岗位目标", icon: Target },
  { to: "/resumes", label: "简历管理", icon: FileText },
  { to: "/gaps", label: "Gap 看板", icon: BarChart3 },
  { to: "/guide", label: "新手指南", icon: Map },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-60 flex-col border-r bg-card">
      <div className="flex h-14 items-center border-b px-4">
        <Link to="/" className="group flex items-center gap-2 hover:opacity-80 transition-opacity">
          <span className="text-base font-semibold text-primary tracking-tight leading-none">Oh My Career</span>
          <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-widest text-primary leading-none">agent</span>
        </Link>
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
        ohmycareer v0.1.0
      </div>
    </aside>
  );
}
