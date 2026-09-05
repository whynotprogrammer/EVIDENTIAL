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
    <header className="border-b border-hairline bg-black/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="p-1.5 bg-zinc-900 border border-hairline rounded-sm text-white group-hover:border-zinc-700 transition">
              <Shield className="w-4 h-4" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-white">
              EVIDENTIAL
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            <Link
              href="/dashboard"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                pathname === "/dashboard" || pathname === "/"
                  ? "bg-zinc-900 text-white border border-hairline"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              Dashboard
            </Link>

            <Link
              href="/cases"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                pathname.startsWith("/cases")
                  ? "bg-zinc-900 text-white border border-hairline"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
              }`}
            >
              <FolderGit2 className="w-3.5 h-3.5" />
              Case Directory
            </Link>

            <Link
              href="/search"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                pathname.startsWith("/search")
                  ? "bg-zinc-900 text-white border border-hairline"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              Search
            </Link>

            <Link
              href="/timeline"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                pathname.startsWith("/timeline")
                  ? "bg-zinc-900 text-white border border-hairline"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Timeline
            </Link>

            <Link
              href="/ai-copilot"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                pathname.startsWith("/ai-copilot")
                  ? "bg-zinc-900 text-white border border-hairline"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-zinc-300" />
              AI Copilot
            </Link>

            <Link
              href="/audit"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium transition ${
                pathname.startsWith("/audit")
                  ? "bg-zinc-900 text-white border border-hairline"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Audit Ledger
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-2.5">
          {onNewCase && (
            <button
              onClick={onNewCase}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-sm bg-white hover:bg-zinc-200 text-black transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              New Case
            </button>
          )}

          {user ? (
            <div className="flex items-center gap-2 pl-3 border-l border-hairline">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-medium text-white">{user.full_name}</p>
                <p className="text-[10px] font-mono text-zinc-400">{user.role} • {user.badge_number || "OFFICER"}</p>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-1.5 rounded-sm bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-hairline transition"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-sm bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-hairline transition"
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
