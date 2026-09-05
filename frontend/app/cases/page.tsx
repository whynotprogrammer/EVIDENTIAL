"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderGit2,
  Search,
  PlusCircle,
  Filter,
  Shield,
  Calendar,
  MapPin,
  Clock,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import Navbar from "../../components/Navbar";
import CreateCaseModal from "../../components/CreateCaseModal";
import { CaseItem, getCases, getCurrentUser, UserProfile, getStoredToken } from "../../lib/api";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const fetchUserData = async () => {
    try {
      if (getStoredToken()) {
        const u = await getCurrentUser();
        setUser(u);
      }
    } catch {
      // Unauthenticated
    }
  };

  const fetchCasesData = async () => {
    setLoading(true);
    try {
      const data = await getCases({
        search: search.trim() || undefined,
        status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  useEffect(() => {
    fetchCasesData();
  }, [search, statusFilter]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "UNDER_INVESTIGATION":
        return "bg-amber-950/60 border-amber-800 text-amber-300";
      case "OPEN":
        return "bg-blue-950/60 border-blue-800 text-blue-300";
      case "PENDING_REVIEW":
        return "bg-purple-950/60 border-purple-800 text-purple-300";
      case "CLOSED":
        return "bg-emerald-950/60 border-emerald-800 text-emerald-300";
      default:
        return "bg-slate-800 border-slate-700 text-slate-300";
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "CRITICAL":
        return "text-red-400 bg-red-950/50 border-red-900";
      case "HIGH":
        return "text-orange-400 bg-orange-950/50 border-orange-900";
      case "MEDIUM":
        return "text-yellow-400 bg-yellow-950/50 border-yellow-900";
      default:
        return "text-slate-400 bg-slate-900 border-slate-800";
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-slate-100">
      <Navbar user={user} onNewCase={() => setIsCreateOpen(true)} onLogout={() => setUser(null)} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <FolderGit2 className="w-6 h-6 text-blue-400" />
              <h1 className="text-2xl font-bold tracking-tight text-white">Investigation Case Directory</h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Active FIR records, digital evidence repositories, and case intelligence
            </p>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/20 transition"
          >
            <PlusCircle className="w-4 h-4" />
            Register New Case
          </button>
        </div>

        {/* Filter & Search Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <div className="md:col-span-3 relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search across case number, title, description, location, crime type..."
              className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
            />
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-2 px-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="UNDER_INVESTIGATION">UNDER INVESTIGATION</option>
              <option value="PENDING_REVIEW">PENDING REVIEW</option>
              <option value="CLOSED">CLOSED</option>
            </select>
          </div>
        </div>

        {/* Case Cards Grid */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p className="text-xs">Loading case directory...</p>
          </div>
        ) : cases.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
            <FolderGit2 className="w-12 h-12 text-slate-600 mx-auto" />
            <h3 className="text-base font-semibold text-slate-300">No Investigation Cases Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No cases matched your search query or filters. Click &quot;Register New Case&quot; to initialize a new FIR file.
            </p>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
            >
              <PlusCircle className="w-4 h-4" />
              Register New Case
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cases.map((c) => (
              <Link
                key={c.id}
                href={`/cases/${c.id}`}
                className="group flex flex-col justify-between bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-blue-500/40 rounded-2xl p-5 shadow-lg transition duration-200"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-blue-400 bg-blue-950/60 border border-blue-800 px-2 py-0.5 rounded-md">
                      {c.case_number}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getPriorityBadge(c.priority)}`}>
                      {c.priority}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-white group-hover:text-blue-300 transition line-clamp-1">
                      {c.title}
                    </h3>
                    <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                      {c.description || "No case summary logged."}
                    </p>
                  </div>

                  <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Shield className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span className="truncate">{c.crime_type}</span>
                    </div>

                    {c.location && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="truncate">{c.location}</span>
                      </div>
                    )}

                    {c.incident_date && (
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span>Incident: {new Date(c.incident_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${getStatusBadge(c.status)}`}>
                    {c.status.replace("_", " ")}
                  </span>
                  <span className="text-xs text-blue-400 group-hover:translate-x-1 transition flex items-center gap-1 font-medium">
                    Open Case <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>

      <CreateCaseModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={fetchCasesData}
      />
    </div>
  );
}
