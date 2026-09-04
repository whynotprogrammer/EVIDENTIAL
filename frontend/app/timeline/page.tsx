"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  History,
  Shield,
  CalendarDays,
  Filter,
  Loader2,
  MapPin,
  FolderGit2,
  ExternalLink,
  Search,
  CheckCircle2,
  Lock,
} from "lucide-react";
import Navbar from "../../components/Navbar";
import {
  CaseItem,
  CaseTimelineResponse,
  getCases,
  getCaseTimeline,
  getCurrentUser,
  getStoredToken,
  TimelineEventItem,
  UserProfile,
} from "../../lib/api";

const EVENT_TYPE_FILTERS = [
  "ALL",
  "FIR_REGISTERED",
  "DOCUMENT_UPLOADED",
  "AI_ANALYSIS_EVENT",
  "PERSON_IDENTIFIED",
  "LOCATION_IDENTIFIED",
  "EVIDENCE_ADDED",
  "INVESTIGATION_EVENT",
  "WITNESS_STATEMENT",
  "SEIZURE",
  "ARREST",
];

export default function GlobalTimelinePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>("");
  const [timelineData, setTimelineData] = useState<CaseTimelineResponse | null>(null);
  const [events, setEvents] = useState<TimelineEventItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [casesLoading, setCasesLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [order, setOrder] = useState<"asc" | "desc">("asc");

  useEffect(() => {
    const initData = async () => {
      try {
        if (getStoredToken()) {
          const u = await getCurrentUser();
          setUser(u);
        }
        const cList = await getCases();
        setCases(cList);
        if (cList.length > 0) {
          setSelectedCaseId(String(cList[0].id));
        }
      } catch (err) {
        console.error("Failed to load initial timeline data:", err);
      } finally {
        setCasesLoading(false);
      }
    };
    initData();
  }, []);

  const fetchTimeline = async (cId: string, currentOrder: "asc" | "desc") => {
    if (!cId) return;
    setLoading(true);
    try {
      const resp = await getCaseTimeline(cId, currentOrder);
      setTimelineData(resp);
      setEvents(resp.events || []);
    } catch (err) {
      console.error("Failed to load case timeline:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCaseId) {
      fetchTimeline(selectedCaseId, order);
    }
  }, [selectedCaseId, order]);

  const filteredEvents = events.filter((e) => {
    if (typeFilter === "ALL") return true;
    return e.event_type === typeFilter;
  });

  const getEventTypeStyles = (type: string) => {
    switch (type) {
      case "FIR_REGISTERED":
        return { badge: "bg-red-950/80 border-red-800 text-red-300", dot: "bg-red-500 ring-red-950" };
      case "DOCUMENT_UPLOADED":
        return { badge: "bg-blue-950/80 border-blue-800 text-blue-300", dot: "bg-blue-500 ring-blue-950" };
      case "AI_ANALYSIS_EVENT":
        return { badge: "bg-purple-950/80 border-purple-800 text-purple-300", dot: "bg-purple-500 ring-purple-950" };
      case "PERSON_IDENTIFIED":
        return { badge: "bg-amber-950/80 border-amber-800 text-amber-300", dot: "bg-amber-500 ring-amber-950" };
      case "LOCATION_IDENTIFIED":
        return { badge: "bg-emerald-950/80 border-emerald-800 text-emerald-300", dot: "bg-emerald-500 ring-emerald-950" };
      case "EVIDENCE_ADDED":
      case "EVIDENCE_TRANSFER":
        return { badge: "bg-cyan-950/80 border-cyan-800 text-cyan-300", dot: "bg-cyan-500 ring-cyan-950" };
      default:
        return { badge: "bg-indigo-950/80 border-indigo-800 text-indigo-300", dot: "bg-indigo-500 ring-indigo-950" };
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar user={user} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="p-1.5 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400">
                <History className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-white">
                Investigation Timeline Explorer
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Chronological sequence of verified investigative events, document attachments, extractions, and official milestones.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/30 border border-emerald-800/50 text-emerald-400 text-xs font-mono">
            <Lock className="w-3.5 h-3.5" />
            <span>Pre-Retrieval Case Authorization Enforced</span>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">
              SELECT AUTHORIZED CASE
            </label>
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              disabled={casesLoading}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.case_number} • {c.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">
              EVENT TYPE FILTER
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              {EVENT_TYPE_FILTERS.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">
              CHRONOLOGICAL SORT ORDER
            </label>
            <select
              value={order}
              onChange={(e) => setOrder(e.target.value as "asc" | "desc")}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="asc">Ascending (Earliest Event First)</option>
              <option value="desc">Descending (Latest Event First)</option>
            </select>
          </div>
        </div>

        {/* Timeline Content */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-2 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p className="text-xs font-mono">Synthesizing chronological investigation events...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="border border-dashed border-slate-800 rounded-2xl p-16 text-center space-y-2 bg-slate-900/20">
            <History className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <h3 className="text-sm font-semibold text-slate-200">No Events Found</h3>
            <p className="text-xs text-slate-500">
              No events matched the selected filter criteria for this case.
            </p>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-blue-400">
                  {timelineData?.case_number}
                </span>
                <span className="text-slate-500">•</span>
                <span className="text-xs font-semibold text-white">
                  {timelineData?.case_title}
                </span>
              </div>

              <Link
                href={`/cases/${timelineData?.case_id}`}
                className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium"
              >
                <span>View Full Dossier</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>

            {/* Vertical timeline */}
            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
              {filteredEvents.map((evt, idx) => {
                const styles = getEventTypeStyles(evt.event_type);
                return (
                  <div key={evt.id || idx} className="relative group">
                    <div
                      className={`absolute -left-[27px] top-1.5 w-3 h-3 rounded-full ${styles.dot} ring-4 transition group-hover:scale-125`}
                    />

                    <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl hover:border-slate-700 transition space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${styles.badge}`}>
                            {evt.event_type.replace(/_/g, " ")}
                          </span>
                          <h3 className="text-xs font-bold text-white">
                            {evt.title}
                          </h3>
                        </div>

                        <span className="text-[11px] font-mono text-slate-400">
                          {new Date(evt.event_date).toLocaleString()}
                        </span>
                      </div>

                      {evt.description && (
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {evt.description}
                        </p>
                      )}

                      {evt.location && (
                        <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                          <MapPin className="w-3 h-3 text-red-400 shrink-0" />
                          <span>{evt.location}</span>
                        </div>
                      )}

                      <div className="pt-2 border-t border-slate-900 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-slate-500">
                        <div className="flex items-center gap-1.5">
                          <span>Source:</span>
                          <span className="text-slate-300 font-semibold">{evt.source}</span>
                          <span className="text-slate-600">({evt.source_type})</span>
                        </div>

                        {evt.source_document && (
                          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-blue-400">
                            📄 {evt.source_document}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
