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
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-slate-100">
      <Navbar user={user} onNewCase={() => setIsCreateOpen(true)} onLogout={() => setUser(null)} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        {/* Welcome & Quick Action Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Investigation Command Center
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              {user
                ? `Logged in as ${user.full_name} (${user.role}) — Badge: ${user.badge_number || "OFFICER"}`
                : "Welcome to EVIDENTIAL. Please log in or select a demo identity to begin."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {!user ? (
              <>
                <button
                  onClick={() => handleQuickLogin("officer")}
                  disabled={loginLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700"
                >
                  <User className="w-3.5 h-3.5 text-blue-400" />
                  Demo Investigator
                </button>
                <button
                  onClick={() => handleQuickLogin("admin")}
                  disabled={loginLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-950/80 hover:bg-blue-900 border border-blue-800 text-blue-300 text-xs font-medium"
                >
                  <Lock className="w-3.5 h-3.5 text-blue-400" />
                  Demo Chief Admin
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsCreateOpen(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/20"
              >
                <PlusCircle className="w-4 h-4" />
                Register New Case
              </button>
            )}
          </div>
        </div>

        {/* KPI Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Total Cases</span>
              <FolderGit2 className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-black text-white">
              {stats?.metrics.total_cases ?? recentCases.length}
            </div>
            <p className="text-[11px] text-slate-500 font-mono">Registry Records</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Active Investigations</span>
              <Activity className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-black text-amber-400">
              {stats?.metrics.active_investigations ?? recentCases.filter((c) => c.status !== "CLOSED").length}
            </div>
            <p className="text-[11px] text-slate-500 font-mono">Under Active Probe</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">Resolved Cases</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400">
              {recentCases.filter((c) => c.status === "CLOSED").length}
            </div>
            <p className="text-[11px] text-slate-500 font-mono">Closed & Archived</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-medium">System Status</span>
              <Shield className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-black text-blue-400">Phase 3</div>
            <p className="text-[11px] text-slate-500 font-mono">Case Mgmt Active</p>
          </div>
        </div>

        {/* Recent Cases & Crime Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Cases Column */}
          <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-blue-400" />
                Recent Investigation Cases
              </h2>
              <Link
                href="/cases"
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
              >
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {loading ? (
              <div className="py-12 flex justify-center text-slate-500">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              </div>
            ) : recentCases.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No cases registered yet. Click &quot;Register New Case&quot; above.
              </div>
            ) : (
              <div className="space-y-2.5">
                {recentCases.map((c) => (
                  <Link
                    key={c.id}
                    href={`/cases/${c.id}`}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 hover:bg-slate-950 border border-slate-800/80 hover:border-blue-500/30 transition text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-blue-400">{c.case_number}</span>
                        <span className="font-semibold text-slate-200">{c.title}</span>
                      </div>
                      <p className="text-[11px] text-slate-400">{c.crime_type} • {c.location || "Jurisdiction Wide"}</p>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] px-2 py-0.5 rounded font-medium bg-slate-800 text-slate-300 border border-slate-700">
                        {c.status.replace("_", " ")}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Crime Breakdown Column */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <TrendingUp className="w-4 h-4 text-purple-400" />
              Crime Breakdown
            </h2>

            {stats?.cases_by_crime_type && stats.cases_by_crime_type.length > 0 ? (
              <div className="space-y-3">
                {stats.cases_by_crime_type.map((item, idx) => (
                  <div key={idx} className="space-y-1 text-xs">
                    <div className="flex justify-between text-slate-300">
                      <span className="truncate">{item.name}</span>
                      <span className="font-mono text-slate-400">{item.count}</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-blue-500 h-full rounded-full"
                        style={{
                          width: `${Math.min(100, (item.count / (stats.metrics.total_cases || 1)) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-slate-500">
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
