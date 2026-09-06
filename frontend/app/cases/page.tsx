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
  const [stageFilter, setStageFilter] = useState("");
  const [districtFilter, setDistrictFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
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
        fir_stage: stageFilter || undefined,
        district: districtFilter || undefined,
        fir_year: yearFilter ? Number(yearFilter) : undefined,
        limit: 100,
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
  }, [search, stageFilter, districtFilter, yearFilter]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "OPEN":
        return "text-white bg-zinc-900 border-zinc-700";
      case "UNDER_INVESTIGATION":
        return "text-accent bg-accent-soft border-accent/30";
      case "PENDING_REVIEW":
        return "text-amber-400 bg-amber-950/40 border-amber-900/50";
      case "CLOSED":
        return "text-emerald-400 bg-emerald-950/40 border-emerald-900/50";
      default:
        return "text-zinc-400 bg-zinc-900 border-hairline";
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "CRITICAL":
        return "text-red-400 bg-red-950/30 border-red-900/50";
      case "HIGH":
        return "text-orange-400 bg-orange-950/30 border-orange-900/50";
      case "MEDIUM":
        return "text-amber-400 bg-amber-950/30 border-amber-900/50";
      default:
        return "text-zinc-400 bg-zinc-900 border-hairline";
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-ink">
      <Navbar user={user} onNewCase={() => setIsCreateOpen(true)} onLogout={() => setUser(null)} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-hairline pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <FolderGit2 className="w-5 h-5 text-zinc-400" />
              <h1 className="text-xl font-semibold tracking-tight text-white">Investigation Case Directory</h1>
            </div>
            <p className="text-xs text-mute">
              Active FIR records, digital evidence repositories, and forensic intelligence
            </p>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-sm bg-white hover:bg-zinc-200 text-black text-xs font-medium transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            Register New Case
          </button>
        </div>

        {/* Filter & Search Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 bg-canvas-elevated p-3 rounded-md border border-hairline">
          <div className="md:col-span-2 relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-mute" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search FIR source data: district, unit, crime, stage..."
              className="w-full pl-9 pr-3 py-1.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
            />
          </div>

          <div>
            <select
              value={districtFilter}
              onChange={(e) => setDistrictFilter(e.target.value)}
              className="w-full py-1.5 px-2.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200 focus:outline-none focus:border-zinc-500"
            >
              <option value="">All Districts</option>
              <option value="Bengaluru">Bengaluru</option>
              <option value="Mysuru">Mysuru</option>
              <option value="Bagalkot">Bagalkot</option>
            </select>
          </div>
          <input value={yearFilter} onChange={(e) => setYearFilter(e.target.value)} placeholder="FIR year" inputMode="numeric" className="w-full py-1.5 px-2.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200" />
          <input value={stageFilter} onChange={(e) => setStageFilter(e.target.value)} placeholder="FIR stage" className="w-full py-1.5 px-2.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200" />
        </div>

        {/* Case Cards Grid */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-2 text-mute">
            <Loader2 className="w-6 h-6 animate-spin text-white" />
            <p className="text-xs">Loading case directory...</p>
          </div>
        ) : cases.length === 0 ? (
          <div className="bg-canvas-elevated border border-hairline rounded-md p-12 text-center space-y-3">
            <FolderGit2 className="w-8 h-8 text-zinc-600 mx-auto" />
            <h3 className="text-sm font-semibold text-white">No Investigation Cases Found</h3>
            <p className="text-xs text-mute max-w-sm mx-auto">
              No cases matched your search query or filters. Click &quot;Register New Case&quot; to initialize a new FIR record.
            </p>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-sm bg-white hover:bg-zinc-200 text-black text-xs font-medium"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              Register New Case
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cases.map((c) => (
              <Link
                key={c.id}
                href={`/cases/${c.id}`}
                className="group flex flex-col justify-between bg-canvas-elevated hover:bg-zinc-900/80 border border-hairline hover:border-zinc-700 rounded-md p-4 transition-colors"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold text-white bg-zinc-900 border border-hairline px-2 py-0.5 rounded-sm">
                      {c.source_record_key ? "FIR ID: Not Available" : c.case_number}
                    </span>
                    <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-sm border ${getPriorityBadge(c.priority)}`}>
                      {c.priority}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-white group-hover:text-accent transition line-clamp-1">
                      {c.title}
                    </h3>
                    <p className="text-xs text-mute line-clamp-2 mt-1">
                      {c.description || "No case summary logged."}
                    </p>
                  </div>

                  <div className="space-y-1 pt-2 border-t border-hairline text-[11px] text-mute">
                    <div className="flex items-center gap-1.5">
                      <Shield className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                      <span className="truncate">{c.crime_type}</span>
                    </div>

                    {c.location && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                        <span className="truncate">{c.location}</span>
                      </div>
                    )}

                    {c.incident_date && (
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                        <span>Incident: {new Date(c.incident_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-hairline flex items-center justify-between">
                  <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded-sm border ${getStatusBadge(c.status)}`}>
                      {c.fir_stage || c.status.replace("_", " ")}
                  </span>
                  <span className="text-xs text-mute group-hover:text-white transition flex items-center gap-1 font-medium">
                    Open Case <ArrowRight className="w-3 h-3" />
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
