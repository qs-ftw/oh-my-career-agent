import { Outlet } from "react-router-dom";
import { Header } from "@/components/layout/Header";

export function CareerPortfolio() {
  return (
    <>
      <Header title="职业履历" description="按公司、项目、成果三层结构管理你的职业经历" />
      <Outlet />
    </>
  );
}
