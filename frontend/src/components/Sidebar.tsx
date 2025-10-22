import { ArrowUpTrayIcon, PlayCircleIcon, PowerIcon } from "@heroicons/react/24/outline";
import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const Sidebar: React.FC = () => {
  const { logout } = useAuth();

  const linkClasses = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-md px-3 py-2 transition hover:bg-slate-800/80 ${
      isActive ? "bg-slate-800 text-white" : "text-slate-300"
    }`;

  return (
    <aside className="flex w-60 flex-col bg-slate-900/80 p-4 shadow-lg">
      <div className="mb-6 text-xl font-semibold text-white">培训资料中心</div>
      <nav className="flex-1 space-y-2 text-sm">
        <NavLink to="/library" className={linkClasses}>
          <PlayCircleIcon className="h-5 w-5" />
          视频库
        </NavLink>
        <NavLink to="/upload" className={linkClasses}>
          <ArrowUpTrayIcon className="h-5 w-5" />
          上传内容
        </NavLink>
      </nav>
      <button
        onClick={logout}
        className="mt-6 inline-flex items-center justify-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-200 transition hover:bg-slate-700"
      >
        <PowerIcon className="h-5 w-5" /> 退出登录
      </button>
    </aside>
  );
};

export default Sidebar;
