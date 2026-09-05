"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, FolderGit2, LayoutDashboard, PlusCircle, LogOut, User, History } from "lucide-react";
import { UserProfile, removeStoredToken } from "../lib/api";

interface NavbarProps {
  user?: UserProfile | null;
  onNewCase?: () => void;
  onLogout?: () => void;
}

export default function Navbar({ user, onNewCase, onLogout }: NavbarProps) {
  const pathname = usePathname();

  const handleLogout = () => {
    removeStoredToken();
    if (onLogout) onLogout();
    window.location.href = "/";
  };

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="p-2 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400 group-hover:border-blue-400 transition">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold tracking-tight text-white flex items-center gap-2">
                EVIDENTIAL
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950 border border-blue-800 text-blue-300 font-mono">
                  SECURE OSINT
                </span>
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            <Link
              href="/dashboard"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                pathname === "/dashboard" || pathname === "/"
                  ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              Dashboard
            </Link>

            <Link
              href="/cases"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                pathname.startsWith("/cases")
                  ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <FolderGit2 className="w-3.5 h-3.5" />
              Case Directory
            </Link>

            <Link
              href="/search"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                pathname.startsWith("/search")
                  ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              Investigation Search
            </Link>

            <Link
              href="/timeline"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                pathname.startsWith("/timeline")
                  ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Timeline
            </Link>

            <Link
              href="/ai-copilot"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                pathname.startsWith("/ai-copilot")
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-indigo-400" />
              AI Copilot
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {onNewCase && (
            <button
              onClick={onNewCase}
              className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 transition"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              New Case
            </button>
          )}

          {user ? (
            <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-medium text-slate-200">{user.full_name}</p>
                <p className="text-[10px] font-mono text-slate-400">{user.role} • {user.badge_number || "OFFICER"}</p>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-2 rounded-lg bg-slate-900 hover:bg-red-950/50 hover:text-red-400 text-slate-400 border border-slate-800 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800"
            >
              <User className="w-3.5 h-3.5" />
              Officer Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
