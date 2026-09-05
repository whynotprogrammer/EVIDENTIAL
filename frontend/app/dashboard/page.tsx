"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Shield,
  FolderGit2,
  AlertCircle,
  Activity,
  CheckCircle2,
  TrendingUp,
  PlusCircle,
  ArrowRight,
  User,
  Clock,
  Database,
  Lock,
  Loader2,
} from "lucide-react";
import Navbar from "../../components/Navbar";
import CreateCaseModal from "../../components/CreateCaseModal";
import {
  getDashboardStats,
  DashboardStats,
  getCurrentUser,
  UserProfile,
  getStoredToken,
  loginUser,
  CaseItem,
  getCases,
} from "../../lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentCases, setRecentCases] = useState<CaseItem[]>([]);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      if (getStoredToken()) {
        const u = await getCurrentUser().catch(() => null);
        setUser(u);
      }
      const [statsData, casesData] = await Promise.all([
        getDashboardStats().catch(() => null),
        getCases().catch(() => []),
      ]);
      setStats(statsData);
      setRecentCases(casesData.slice(0, 5));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleQuickLogin = async (role: "officer" | "admin") => {
    setLoginLoading(true);
    try {
      if (role === "officer") {
        await loginUser("officer@evidential.gov.in", "Officer@123");
      } else {
        await loginUser("admin@evidential.gov.in", "Admin@123");
      }
      await loadData();
    } catch (err: any) {
      alert(err.message || "Login failed");
    } finally {
      setLoginLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-ink">
      <Navbar user={user} onNewCase={() => setIsCreateOpen(true)} onLogout={() => setUser(null)} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Welcome & Quick Action Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-hairline pb-5">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold tracking-tight text-white">
              Investigation Command Center
            </h1>
            <p className="text-xs text-mute">
              {user
                ? `Active Session: ${user.full_name} (${user.role}) — Badge: ${user.badge_number || "OFFICER"}`
                : "Secure forensic intelligence environment. Select identity to begin."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {!user ? (
              <>
                <button
                  onClick={() => handleQuickLogin("officer")}
                  disabled={loginLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-zinc-900 hover:bg-zinc-800 text-zinc-200 text-xs font-medium border border-hairline transition"
                >
                  <User className="w-3.5 h-3.5 text-zinc-400" />
                  Demo Investigator
                </button>
                <button
                  onClick={() => handleQuickLogin("admin")}
                  disabled={loginLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-zinc-900 hover:bg-zinc-800 border border-hairline text-zinc-200 text-xs font-medium transition"
                >
                  <Lock className="w-3.5 h-3.5 text-zinc-400" />
                  Demo Chief Admin
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsCreateOpen(true)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-sm bg-white hover:bg-zinc-200 text-black text-xs font-medium transition-colors"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                Register New Case
              </button>
            )}
          </div>
        </div>

        {/* KPI Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-sm bg-canvas-elevated border border-hairline space-y-1.5">
            <div className="flex items-center justify-between text-mute">
              <span className="text-xs font-medium">Total Cases</span>
              <FolderGit2 className="w-3.5 h-3.5 text-zinc-400" />
            </div>
            <div className="text-2xl font-semibold text-white">
              {stats?.metrics.total_cases ?? recentCases.length}
            </div>
            <p className="text-[11px] text-mute font-mono">Registry Records</p>
          </div>

          <div className="p-4 rounded-sm bg-canvas-elevated border border-hairline space-y-1.5">
            <div className="flex items-center justify-between text-mute">
              <span className="text-xs font-medium">Active Investigations</span>
              <Activity className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-semibold text-amber-400">
              {stats?.metrics.active_investigations ?? recentCases.filter((c) => c.status !== "CLOSED").length}
            </div>
            <p className="text-[11px] text-mute font-mono">Under Active Probe</p>
          </div>

          <div className="p-4 rounded-sm bg-canvas-elevated border border-hairline space-y-1.5">
            <div className="flex items-center justify-between text-mute">
              <span className="text-xs font-medium">Resolved Cases</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-semibold text-emerald-400">
              {recentCases.filter((c) => c.status === "CLOSED").length}
            </div>
            <p className="text-[11px] text-mute font-mono">Closed & Archived</p>
          </div>

          <div className="p-4 rounded-sm bg-canvas-elevated border border-hairline space-y-1.5">
            <div className="flex items-center justify-between text-mute">
              <span className="text-xs font-medium">System Telemetry</span>
              <Shield className="w-3.5 h-3.5 text-zinc-400" />
            </div>
            <div className="text-2xl font-semibold text-white">Operational</div>
            <p className="text-[11px] text-mute font-mono">All Nodes Online</p>
          </div>
        </div>

        {/* Recent Cases & Crime Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Cases Column */}
          <div className="lg:col-span-2 bg-canvas-elevated border border-hairline rounded-md p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-hairline pb-3">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-zinc-400" />
                Recent Cases
              </h2>
              <Link
                href="/cases"
                className="text-xs text-mute hover:text-white flex items-center gap-1 font-medium transition"
              >
                View All <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <div className="py-12 flex justify-center text-mute">
                <Loader2 className="w-5 h-5 animate-spin text-white" />
              </div>
            ) : recentCases.length === 0 ? (
              <div className="py-8 text-center text-xs text-mute">
                No cases registered yet. Click &quot;Register New Case&quot; above.
              </div>
            ) : (
              <div className="space-y-2">
                {recentCases.map((c) => (
                  <Link
                    key={c.id}
                    href={`/cases/${c.id}`}
                    className="flex items-center justify-between p-3 rounded-sm bg-canvas-subtle hover:bg-zinc-900/80 border border-hairline hover:border-zinc-700 transition text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-accent">{c.case_number}</span>
                        <span className="font-medium text-white">{c.title}</span>
                      </div>
                      <p className="text-[11px] text-mute">{c.crime_type} • {c.location || "Jurisdiction Wide"}</p>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-sm bg-zinc-900 text-zinc-300 border border-hairline">
                        {c.status.replace("_", " ")}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Crime Breakdown Column */}
          <div className="bg-canvas-elevated border border-hairline rounded-md p-5 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-hairline pb-3">
              <TrendingUp className="w-4 h-4 text-zinc-400" />
              Crime Breakdown
            </h2>

            {stats?.cases_by_crime_type && stats.cases_by_crime_type.length > 0 ? (
              <div className="space-y-3">
                {stats.cases_by_crime_type.map((item, idx) => (
                  <div key={idx} className="space-y-1 text-xs">
                    <div className="flex justify-between text-zinc-300">
                      <span className="truncate">{item.name}</span>
                      <span className="font-mono text-mute">{item.count}</span>
                    </div>
                    <div className="w-full bg-zinc-900 rounded-full h-1 overflow-hidden">
                      <div
                        className="bg-white h-full rounded-full"
                        style={{
                          width: `${Math.min(100, (item.count / (stats.metrics.total_cases || 1)) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-mute">
                Data will appear as cases are registered.
              </div>
            )}
          </div>
        </div>
      </main>

      <CreateCaseModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
