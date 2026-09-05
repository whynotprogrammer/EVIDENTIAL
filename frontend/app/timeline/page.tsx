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
        return { badge: "bg-red-950/30 border-red-900/50 text-red-400", dot: "bg-red-400" };
      case "DOCUMENT_UPLOADED":
        return { badge: "bg-zinc-900 border-hairline text-zinc-300", dot: "bg-zinc-400" };
      case "AI_ANALYSIS_EVENT":
        return { badge: "bg-zinc-900 border-hairline text-accent", dot: "bg-accent" };
      case "PERSON_IDENTIFIED":
        return { badge: "bg-amber-950/30 border-amber-900/50 text-amber-400", dot: "bg-amber-400" };
      case "LOCATION_IDENTIFIED":
        return { badge: "bg-emerald-950/30 border-emerald-900/50 text-emerald-400", dot: "bg-emerald-400" };
      case "EVIDENCE_ADDED":
      case "EVIDENCE_TRANSFER":
        return { badge: "bg-zinc-900 border-hairline text-white", dot: "bg-white" };
      default:
        return { badge: "bg-zinc-900 border-hairline text-mute", dot: "bg-zinc-500" };
    }
  };

  return (
    <div className="min-h-screen bg-black text-ink flex flex-col font-sans">
      <Navbar user={user} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-hairline pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-zinc-400" />
              <h1 className="text-xl font-semibold tracking-tight text-white">
                Investigation Timeline Explorer
              </h1>
            </div>
            <p className="text-xs text-mute">
              Chronological sequence of verified investigative events, document attachments, extractions, and official milestones.
            </p>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 bg-canvas-elevated border border-hairline rounded-md">
          <div>
            <label className="block text-[10px] font-mono uppercase text-mute mb-1">
              Select Authorized Case
            </label>
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              disabled={casesLoading}
              className="w-full px-2.5 py-1.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200 focus:border-zinc-500 focus:outline-none"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.case_number} • {c.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-mute mb-1">
              Event Type Filter
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-2.5 py-1.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200 focus:border-zinc-500 focus:outline-none"
            >
              {EVENT_TYPE_FILTERS.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-mute mb-1">
              Sort Order
            </label>
            <select
              value={order}
              onChange={(e) => setOrder(e.target.value as "asc" | "desc")}
              className="w-full px-2.5 py-1.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200 focus:border-zinc-500 focus:outline-none"
            >
              <option value="asc">Ascending (Earliest Event First)</option>
              <option value="desc">Descending (Latest Event First)</option>
            </select>
          </div>
        </div>

        {/* Timeline Content */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-2 text-mute">
            <Loader2 className="w-6 h-6 animate-spin text-white" />
            <p className="text-xs font-mono">Synthesizing chronological investigation events...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="border border-hairline rounded-md p-16 text-center space-y-2 bg-canvas-elevated">
            <History className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
            <h3 className="text-sm font-semibold text-white">No Events Found</h3>
            <p className="text-xs text-mute">
              No events matched the selected filter criteria for this case.
            </p>
          </div>
        ) : (
          <div className="bg-canvas-elevated border border-hairline rounded-md p-5 space-y-5">
            <div className="flex items-center justify-between border-b border-hairline pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-semibold text-accent">
                  {timelineData?.case_number}
                </span>
                <span className="text-zinc-600">•</span>
                <span className="text-xs font-medium text-white">
                  {timelineData?.case_title}
                </span>
              </div>

              <Link
                href={`/cases/${timelineData?.case_id}`}
                className="flex items-center gap-1 text-xs text-mute hover:text-white font-medium transition"
              >
                <span>View Full File</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>

            {/* Vertical timeline */}
            <div className="relative pl-6 space-y-5 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-hairline">
              {filteredEvents.map((evt, idx) => {
                const styles = getEventTypeStyles(evt.event_type);
                return (
                  <div key={evt.id || idx} className="relative group">
                    <div
                      className={`absolute -left-[27px] top-1.5 w-2 h-2 rounded-full ${styles.dot}`}
                    />

                    <div className="p-3.5 bg-canvas-subtle border border-hairline rounded-sm hover:border-zinc-700 transition space-y-1.5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-mono uppercase px-1.5 py-0.2 rounded-sm border ${styles.badge}`}>
                            {evt.event_type.replace(/_/g, " ")}
                          </span>
                          <h3 className="text-xs font-semibold text-white">
                            {evt.title}
                          </h3>
                        </div>

                        <span className="text-[10px] font-mono text-mute">
                          {new Date(evt.event_date).toLocaleString()}
                        </span>
                      </div>

                      {evt.description && (
                        <p className="text-xs text-zinc-300 leading-relaxed">
                          {evt.description}
                        </p>
                      )}

                      {evt.location && (
                        <div className="flex items-center gap-1.5 text-[11px] text-mute">
                          <MapPin className="w-3 h-3 text-zinc-400 shrink-0" />
                          <span>{evt.location}</span>
                        </div>
                      )}

                      <div className="pt-2 border-t border-hairline flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-mute">
                        <div className="flex items-center gap-1.5">
                          <span>Source:</span>
                          <span className="text-zinc-300 font-medium">{evt.source}</span>
                          <span className="text-zinc-600">({evt.source_type})</span>
                        </div>

                        {evt.source_document && (
                          <span className="px-1.5 py-0.2 rounded-sm bg-zinc-900 border border-hairline text-zinc-300">
                            {evt.source_document}
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
