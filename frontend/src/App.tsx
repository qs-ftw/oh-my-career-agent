import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "@/components/layout/Sidebar";
import { Dashboard } from "@/pages/Dashboard";
import { Roles } from "@/pages/Roles";
import { RoleDetail } from "@/pages/RoleDetail";
import { ResumeDetail } from "@/pages/ResumeDetail";
import { Achievements } from "@/pages/Achievements";
import { GapBoard } from "@/pages/GapBoard";
import { JDTailor } from "@/pages/JDTailor";
import { Resumes } from "@/pages/Resumes";
import { Suggestions } from "@/pages/Suggestions";
import { Profile } from "@/pages/Profile";

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
              <Route path="/achievements" element={<Achievements />} />
              <Route path="/gaps" element={<GapBoard />} />
              <Route path="/jd-tailor" element={<JDTailor />} />
              <Route path="/suggestions" element={<Suggestions />} />
              <Route path="/profile" element={<Profile />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
