import {
  Bot,
  FileText,
  LayoutDashboard,
  LogOut,
  Sparkles,
} from "lucide-react";
import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router";
import { useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../../hooks/useAuth";

export default function AppLayout() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  function handleLogout() {
    localStorage.removeItem("access_token");

    queryClient.clear();

    navigate("/login");
  }

  const linkClass = ({
    isActive,
  }: {
    isActive: boolean;
  }) =>
    [
      "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition",
      isActive
        ? "bg-blue-600 !text-white shadow-md shadow-blue-200"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
    ].join(" ");

  return (
    <div className="min-h-screen bg-[#fff8f5] md:flex">
      <aside className="border-b border-slate-200/80 bg-white md:sticky md:top-0 md:min-h-screen md:w-72 md:border-b-0 md:border-r">
        <div className="flex items-center gap-3 p-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ff7a59] via-[#ff5f6d] to-[#ff2f7d] text-white shadow-lg shadow-orange-200">
            <Sparkles size={19} />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">
              AI Document
            </p>
            <h1 className="mt-0.5 text-base font-semibold text-slate-900">
              Intelligence Platform
            </h1>
          </div>
        </div>

        <nav className="flex gap-2 overflow-x-auto px-4 pb-4 md:block md:space-y-2">
          
          <NavLink
            to="/dashboard"
            className={linkClass}
          >
            <LayoutDashboard size={18} />
            Dashboard
          </NavLink>

          <NavLink
            to="/documents"
            className={linkClass}
          >
            <FileText size={18} />
            Documents
          </NavLink>

          <NavLink
            to="/chat"
            className={linkClass}
          >
            <Bot size={18} />
            AI Chat
          </NavLink>

        </nav>

        <div className="border-t border-slate-200 p-4 md:absolute md:bottom-0 md:w-72">
          <div className="mb-3 flex items-center gap-3 rounded-2xl bg-slate-50 p-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
              {(user?.name ?? "U").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">
                {user?.name ?? "User"}
              </p>
              <p className="truncate text-xs text-slate-500">
                {user?.email}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-slate-600 transition hover:bg-blue-50 hover:text-blue-700"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1 bg-[radial-gradient(circle_at_top_right,_rgba(255,224,214,0.7),_transparent_30rem)]">
        <Outlet />
      </main>
    </div>
  );
}
