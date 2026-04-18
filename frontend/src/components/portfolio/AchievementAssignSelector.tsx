import { useState, useRef, useEffect } from "react";
import type { WorkExperience, Education, Project } from "@/types";

interface AchievementAssignSelectorProps {
  workExperiences: WorkExperience[];
  educations?: Education[];
  projects: Project[];
  onSelect: (projectId: string, workExperienceId: string | null) => void;
  onClose: () => void;
}

export function AchievementAssignSelector({
  workExperiences,
  educations = [],
  projects,
  onSelect,
  onClose,
}: AchievementAssignSelectorProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  const projectsByWE = new Map<string, Project[]>();
  const projectsByEdu = new Map<string, Project[]>();
  const standalone: Project[] = [];
  for (const p of projects) {
    if (p.work_experience_id) {
      const list = projectsByWE.get(p.work_experience_id) ?? [];
      list.push(p);
      projectsByWE.set(p.work_experience_id, list);
    } else if (p.education_id) {
      const list = projectsByEdu.get(p.education_id) ?? [];
      list.push(p);
      projectsByEdu.set(p.education_id, list);
    } else {
      standalone.push(p);
    }
  }

  const q = search.toLowerCase();
  const filteredWEs = workExperiences.filter((we) => {
    const ps = projectsByWE.get(we.id) ?? [];
    return ps.some((p) => p.name.toLowerCase().includes(q));
  });
  const filteredEdus = educations.filter((edu) => {
    const ps = projectsByEdu.get(edu.id) ?? [];
    return ps.some((p) => p.name.toLowerCase().includes(q));
  });
  const filteredStandalone = standalone.filter((p) => p.name.toLowerCase().includes(q));

  return (
    <div ref={ref} className="absolute right-0 z-50 mt-1 w-64 rounded-md border bg-card shadow-lg">
      <div className="p-2 border-b">
        <input className="w-full rounded-md border px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-primary/50" placeholder="搜索项目..." value={search} onChange={(e) => setSearch(e.target.value)} autoFocus />
      </div>
      <div className="max-h-48 overflow-y-auto p-1">
        {filteredWEs.map((we) => {
          const ps = (projectsByWE.get(we.id) ?? []).filter((p) => p.name.toLowerCase().includes(q));
          if (ps.length === 0) return null;
          return (
            <div key={we.id}>
              <div className="px-2 py-1 text-xs font-medium text-muted-foreground">{we.company_name}</div>
              {ps.map((p) => (
                <button key={p.id} className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-muted transition-colors" onClick={() => onSelect(p.id, p.work_experience_id ?? null)}>{p.name}</button>
              ))}
            </div>
          );
        })}
        {filteredEdus.map((edu) => {
          const ps = (projectsByEdu.get(edu.id) ?? []).filter((p) => p.name.toLowerCase().includes(q));
          if (ps.length === 0) return null;
          return (
            <div key={edu.id}>
              <div className="px-2 py-1 text-xs font-medium text-muted-foreground">🎓 {edu.institution_name}</div>
              {ps.map((p) => (
                <button key={p.id} className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-muted transition-colors" onClick={() => onSelect(p.id, null)}>{p.name}</button>
              ))}
            </div>
          );
        })}
        {filteredStandalone.length > 0 && (
          <div>
            <div className="px-2 py-1 text-xs font-medium text-muted-foreground">独立项目</div>
            {filteredStandalone.map((p) => (
              <button key={p.id} className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-muted transition-colors" onClick={() => onSelect(p.id, null)}>{p.name}</button>
            ))}
          </div>
        )}
        {filteredWEs.length === 0 && filteredEdus.length === 0 && filteredStandalone.length === 0 && (
          <p className="px-2 py-3 text-xs text-muted-foreground text-center">无匹配项目</p>
        )}
      </div>
    </div>
  );
}
