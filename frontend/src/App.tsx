import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "@/components/layout/Sidebar";
import { Dashboard } from "@/pages/Dashboard";
import { Roles } from "@/pages/Roles";
import { RoleDetail } from "@/pages/RoleDetail";
import { ResumeDetail } from "@/pages/ResumeDetail";
import { GapBoard } from "@/pages/GapBoard";
import { Guide } from "@/pages/Guide";
import { Resumes } from "@/pages/Resumes";
import { Profile } from "@/pages/Profile";
import { CareerPortfolio } from "@/pages/CareerPortfolio";
import { Overview } from "@/pages/CareerPortfolio/Overview";
import { CompanyDetail } from "@/pages/CareerPortfolio/CompanyDetail";
import { ProjectDetail } from "@/pages/CareerPortfolio/ProjectDetail";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-screen">
          <Sidebar />
          <div className="flex flex-1 flex-col overflow-hidden">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/roles" element={<Roles />} />
              <Route path="/roles/:id" element={<RoleDetail />} />
              <Route path="/resumes" element={<Resumes />} />
              <Route path="/resumes/:id" element={<ResumeDetail />} />
              <Route path="/gaps" element={<GapBoard />} />
              <Route path="/guide" element={<Guide />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/portfolio" element={<CareerPortfolio />}>
                <Route index element={<Overview />} />
                <Route path="project/:projectId" element={<ProjectDetail />} />
                <Route path=":weId" element={<CompanyDetail />} />
                <Route path=":weId/:projectId" element={<ProjectDetail />} />
              </Route>
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
