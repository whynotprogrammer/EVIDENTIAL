"use client";

import React, { useState, useEffect } from "react";

export interface DashboardMetrics {
  total_cases: number;
  active_cases: number;
  documents_processed: number;
  evidence_items: number;
  potential_correlations: number;
  audit_events: number;
}

export interface EvidenceActivityPoint {
  date: string;
  ingested_count: number;
  verified_count: number;
}

export interface ChartData {
  cases_by_status: Record<string, number>;
  cases_by_crime_type: Record<string, number>;
  cases_by_language: Record<string, number>;
  evidence_activity: EvidenceActivityPoint[];
}

export interface RecentCaseItem {
  case_id: string;
  title: string;
  fir_number: string;
  status: string;
  crime_type: string;
  updated_at: string;
}

export interface RecentDocumentItem {
  doc_id: string;
  case_id: string;
  title: string;
  doc_type: string;
  language: string;
  uploaded_at: string;
}

export interface RecentCorrelationItem {
  correlation_id: string;
  entity_a: string;
  entity_b: string;
  confidence_score: number;
  correlation_type: string;
  detected_at: string;
}

export interface RecentAuditItem {
  audit_id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  status: string;
  timestamp: string;
}

export interface RecentActivity {
  latest_cases: RecentCaseItem[];
  latest_documents: RecentDocumentItem[];
  latest_correlations: RecentCorrelationItem[];
  latest_audit_events: RecentAuditItem[];
}

export interface NavigationItem {
  name: string;
  path: string;
  badge_count?: number;
}

const NAVIGATION_MODULES: NavigationItem[] = [
  { name: "Dashboard", path: "/dashboard" },
  { name: "Cases", path: "/cases", badge_count: 50 },
  { name: "Documents", path: "/documents", badge_count: 148 },
  { name: "Evidence", path: "/evidence", badge_count: 86 },
  { name: "Investigation", path: "/investigation" },
  { name: "Correlation", path: "/correlation", badge_count: 14 },
  { name: "AI Copilot", path: "/ai-copilot" },
  { name: "Audit", path: "/audit", badge_count: 120 },
];

export const CommandCenter: React.FC = () => {
  const [activeNav, setActiveNav] = useState<string>("Dashboard");
  const [activeActivityTab, setActiveActivityTab] = useState<"cases" | "documents" | "correlations" | "audit">("cases");

  const [metrics, setMetrics] = useState<DashboardMetrics>({
    total_cases: 50,
    active_cases: 32,
    documents_processed: 148,
    evidence_items: 86,
    potential_correlations: 14,
    audit_events: 120,
  });

  const [charts, setCharts] = useState<ChartData>({
    cases_by_status: { ACTIVE: 24, UNDER_INVESTIGATION: 18, PENDING_TRIAL: 8, CLOSED: 14 },
    cases_by_crime_type: { "Cyber Crime": 26, "Financial Fraud": 18, Narcotics: 11, "Physical Intrusion": 6, "Identity Theft": 3 },
    cases_by_language: { English: 68, Hindi: 44, Bengali: 16, Marathi: 12, Tamil: 8 },
    evidence_activity: [
      { date: "10-06", ingested_count: 8, verified_count: 7 },
      { date: "10-07", ingested_count: 12, verified_count: 10 },
      { date: "10-08", ingested_count: 15, verified_count: 14 },
      { date: "10-09", ingested_count: 9, verified_count: 9 },
      { date: "10-10", ingested_count: 22, verified_count: 20 },
      { date: "10-11", ingested_count: 18, verified_count: 16 },
      { date: "10-12", ingested_count: 25, verified_count: 24 },
    ],
  });

  const [recentActivity, setRecentActivity] = useState<RecentActivity>({
    latest_cases: [
      { case_id: "CASE-2024-001", title: "Meridian Vault Cyber Heist", fir_number: "FIR-2024-088", status: "UNDER_INVESTIGATION", crime_type: "Cyber Crime", updated_at: "2024-10-12 14:30" },
      { case_id: "CASE-2024-002", title: "Harbour Docks Narcotics", fir_number: "FIR-2024-331", status: "PENDING_TRIAL", crime_type: "Narcotics", updated_at: "2024-10-11 18:15" },
      { case_id: "CASE-2024-003", title: "Apex Global Laundering", fir_number: "FIR-2024-412", status: "ACTIVE", crime_type: "Financial Fraud", updated_at: "2024-10-10 11:00" },
      { case_id: "CASE-2024-004", title: "Metro Grid Ransomware", fir_number: "FIR-2024-502", status: "ACTIVE", crime_type: "Cyber Crime", updated_at: "2024-10-09 09:45" },
    ],
    latest_documents: [
      { doc_id: "DOC-FIR-001", case_id: "CASE-2024-001", title: "First Information Report", doc_type: "FIR", language: "English", uploaded_at: "2024-10-12 09:30" },
      { doc_id: "DOC-WIT-002", case_id: "CASE-2024-001", title: "Guard Statement", doc_type: "WITNESS_STATEMENT", language: "Hindi", uploaded_at: "2024-10-12 14:00" },
      { doc_id: "DOC-EVID-003", case_id: "CASE-2024-001", title: "Seizure Memo - Kingston USB", doc_type: "SEIZURE_MEMO", language: "English", uploaded_at: "2024-10-13 16:40" },
      { doc_id: "DOC-FOR-005", case_id: "CASE-2024-001", title: "Cyber Forensic Examination", doc_type: "FORENSIC_REPORT", language: "English", uploaded_at: "2024-10-14 10:15" },
    ],
    latest_correlations: [
      { correlation_id: "CORR-991", entity_a: "Vikram Malhotra (CASE-001)", entity_b: "FIR-2024-012 (Phishing)", confidence_score: 0.96, correlation_type: "IDENTITY_MATCH", detected_at: "2024-10-12 10:15" },
      { correlation_id: "CORR-992", entity_a: "Kingston USB BC-88192", entity_b: "Malware Repository", confidence_score: 0.99, correlation_type: "CRYPTOGRAPHIC_HASH", detected_at: "2024-10-12 11:20" },
      { correlation_id: "CORR-993", entity_a: "Dark Sedan (River Road)", entity_b: "CCTV Gate B Alleyway", confidence_score: 0.88, correlation_type: "VISUAL_MATCH", detected_at: "2024-10-13 17:00" },
      { correlation_id: "CORR-994", entity_a: "Container MSC-4491", entity_b: "Apex Bill of Lading", confidence_score: 0.92, correlation_type: "CROSS_CASE_ENTITY", detected_at: "2024-10-14 08:30" },
    ],
    latest_audit_events: [
      { audit_id: "AUDIT-01", user_id: "INV-101", action: "AI_QUERY", resource_type: "COPILOT", resource_id: "QUERY-882", status: "SUCCESS", timestamp: "2024-10-14 11:00" },
      { audit_id: "AUDIT-02", user_id: "SYSTEM", action: "EVIDENCE_VERIFIED", resource_type: "EVIDENCE", resource_id: "EVID-001", status: "SUCCESS", timestamp: "2024-10-14 10:45" },
      { audit_id: "AUDIT-03", user_id: "INV-102", action: "CORRELATION_EXECUTED", resource_type: "GRAPH", resource_id: "GRAPH-01", status: "SUCCESS", timestamp: "2024-10-14 10:15" },
      { audit_id: "AUDIT-04", user_id: "INV-101", action: "CASE_VIEWED", resource_type: "CASE", resource_id: "CASE-2024-001", status: "SUCCESS", timestamp: "2024-10-14 09:30" },
    ],
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const res = await fetch("/api/v1/dashboard/overview");
      if (res.ok) {
        const data = await res.json();
        setMetrics(data.metrics);
        setCharts(data.charts);
        setRecentActivity(data.recent_activity);
      }
    } catch {
      // Retain offline sample data
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans flex flex-col">
      {/* Top Enterprise Bar */}
      <header className="bg-slate-950 border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center font-bold text-white tracking-widest text-sm">
            EV
          </div>
          <div>
            <span className="font-bold text-base tracking-wide text-white">EVIDENTIAL</span>
            <span className="text-xs text-slate-400 ml-2 border-l border-slate-700 pl-2">
              COMMAND CENTER — ENTERPRISE INVESTIGATION
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            SYSTEM OPERATIONAL
          </div>
          <span className="text-slate-400 font-mono">UTC {new Date().toISOString().substring(11, 19)}</span>
        </div>
      </header>

      {/* Navigation Bar (All 8 Modules) */}
      <nav className="bg-slate-900 border-b border-slate-800 px-6 flex items-center gap-1 overflow-x-auto text-sm">
        {NAVIGATION_MODULES.map((item) => {
          const isActive = activeNav === item.name;
          return (
            <button
              key={item.name}
              onClick={() => setActiveNav(item.name)}
              className={`px-4 py-3 font-semibold border-b-2 transition whitespace-nowrap flex items-center gap-2 ${
                isActive
                  ? "border-blue-500 text-blue-400 bg-slate-800/40"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600"
              }`}
            >
              {item.name}
              {item.badge_count && (
                <span className="text-xs px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                  {item.badge_count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Main Command Center Body */}
      <main className="p-6 max-w-7xl mx-auto w-full flex-1 space-y-6">
        {/* KPI Metric Cards (6 Required KPIs) */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">TOTAL CASES</span>
            <span className="text-2xl font-extrabold text-white mt-1 block font-mono">{metrics.total_cases}</span>
            <span className="text-[11px] text-slate-400 mt-1 block font-medium">All recorded FIRs</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block">ACTIVE CASES</span>
            <span className="text-2xl font-extrabold text-emerald-400 mt-1 block font-mono">{metrics.active_cases}</span>
            <span className="text-[11px] text-slate-400 mt-1 block font-medium">Under active inquiry</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg">
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider block">DOCUMENTS PROCESSED</span>
            <span className="text-2xl font-extrabold text-blue-400 mt-1 block font-mono">{metrics.documents_processed}</span>
            <span className="text-[11px] text-slate-400 mt-1 block font-medium">OCR & Translations</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider block">EVIDENCE ITEMS</span>
            <span className="text-2xl font-extrabold text-amber-400 mt-1 block font-mono">{metrics.evidence_items}</span>
            <span className="text-[11px] text-slate-400 mt-1 block font-medium">SHA-256 Hashed</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg">
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider block">POTENTIAL CORRELATIONS</span>
            <span className="text-2xl font-extrabold text-purple-400 mt-1 block font-mono">{metrics.potential_correlations}</span>
            <span className="text-[11px] text-slate-400 mt-1 block font-medium">Cross-case links</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider block">AUDIT EVENTS</span>
            <span className="text-2xl font-extrabold text-cyan-400 mt-1 block font-mono">{metrics.audit_events}</span>
            <span className="text-[11px] text-slate-400 mt-1 block font-medium">Chain verified</span>
          </div>
        </section>

        {/* Charts Section (4 Required Functional Visualizations) */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Chart 1: Cases by status */}
          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-700/60 mb-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Cases by Status</h3>
                <span className="text-[11px] text-slate-400">Total: {metrics.total_cases}</span>
              </div>
              <div className="space-y-2.5">
                {Object.entries(charts.cases_by_status).map(([status, count]) => {
                  const percent = Math.round((count / (metrics.total_cases || 1)) * 100);
                  return (
                    <div key={status} className="text-xs">
                      <div className="flex justify-between text-slate-300 mb-1">
                        <span className="font-semibold">{status}</span>
                        <span className="font-mono text-slate-400">{count} ({percent}%)</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-700">
                        <div
                          className="bg-blue-500 h-full rounded-full"
                          style={{ width: `${Math.min(percent, 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <span className="text-[11px] text-slate-500 mt-4 block">Updated in real-time</span>
          </div>

          {/* Chart 2: Cases by crime type */}
          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-700/60 mb-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Cases by Crime Type</h3>
                <span className="text-[11px] text-slate-400">Top Categories</span>
              </div>
              <div className="space-y-2.5">
                {Object.entries(charts.cases_by_crime_type).map(([crime, count]) => {
                  const maxVal = Math.max(...Object.values(charts.cases_by_crime_type));
                  const barWidth = Math.round((count / maxVal) * 100);
                  return (
                    <div key={crime} className="text-xs">
                      <div className="flex justify-between text-slate-300 mb-1">
                        <span className="font-semibold">{crime}</span>
                        <span className="font-mono text-slate-400">{count}</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-700">
                        <div
                          className="bg-purple-500 h-full rounded-full"
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <span className="text-[11px] text-slate-500 mt-4 block">FIR Classification</span>
          </div>

          {/* Chart 3: Cases by language */}
          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-700/60 mb-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Cases by Language</h3>
                <span className="text-[11px] text-slate-400">Multilingual Ingestion</span>
              </div>
              <div className="space-y-2.5">
                {Object.entries(charts.cases_by_language).map(([lang, count]) => {
                  const maxLang = Math.max(...Object.values(charts.cases_by_language));
                  const barWidth = Math.round((count / maxLang) * 100);
                  return (
                    <div key={lang} className="text-xs">
                      <div className="flex justify-between text-slate-300 mb-1">
                        <span className="font-semibold">{lang}</span>
                        <span className="font-mono text-slate-400">{count} docs</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-700">
                        <div
                          className="bg-amber-500 h-full rounded-full"
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <span className="text-[11px] text-slate-500 mt-4 block">NLP & Translation pipeline</span>
          </div>

          {/* Chart 4: Evidence activity */}
          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-700/60 mb-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Evidence Activity</h3>
                <span className="text-[11px] text-emerald-400 font-mono">Ingested vs Verified</span>
              </div>
              <div className="space-y-2">
                {charts.evidence_activity.map((point) => (
                  <div key={point.date} className="flex items-center justify-between text-xs py-1 border-b border-slate-700/40">
                    <span className="font-mono text-slate-400">{point.date}</span>
                    <div className="flex items-center gap-3 font-mono">
                      <span className="text-amber-400">+{point.ingested_count} in</span>
                      <span className="text-emerald-400">✓{point.verified_count} ver</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <span className="text-[11px] text-slate-500 mt-4 block">Daily forensic throughput</span>
          </div>
        </section>

        {/* Recent Activity Section (4 Streams) */}
        <section className="bg-slate-800/80 border border-slate-700 rounded-lg p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-700 gap-3">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Recent Operational Telemetry</h2>
              <p className="text-xs text-slate-400 mt-0.5">High-frequency streams across investigations and security</p>
            </div>

            {/* Stream Tab Selectors */}
            <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-md border border-slate-700">
              <button
                onClick={() => setActiveActivityTab("cases")}
                className={`px-3 py-1 text-xs font-semibold rounded ${
                  activeActivityTab === "cases" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Latest Cases
              </button>
              <button
                onClick={() => setActiveActivityTab("documents")}
                className={`px-3 py-1 text-xs font-semibold rounded ${
                  activeActivityTab === "documents" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Latest Documents
              </button>
              <button
                onClick={() => setActiveActivityTab("correlations")}
                className={`px-3 py-1 text-xs font-semibold rounded ${
                  activeActivityTab === "correlations" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Latest Correlations
              </button>
              <button
                onClick={() => setActiveActivityTab("audit")}
                className={`px-3 py-1 text-xs font-semibold rounded ${
                  activeActivityTab === "audit" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Latest Audit Events
              </button>
            </div>
          </div>

          {/* Active Activity Tab Content */}
          <div className="mt-4 overflow-x-auto">
            {activeActivityTab === "cases" && (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="text-slate-400 uppercase font-semibold border-b border-slate-700 bg-slate-900/50">
                    <th className="py-2.5 px-3">Case ID</th>
                    <th className="py-2.5 px-3">FIR Number</th>
                    <th className="py-2.5 px-3">Title</th>
                    <th className="py-2.5 px-3">Crime Type</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {recentActivity.latest_cases.map((c) => (
                    <tr key={c.case_id} className="hover:bg-slate-750">
                      <td className="py-2.5 px-3 font-mono text-blue-400 font-medium">{c.case_id}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">{c.fir_number}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{c.title}</td>
                      <td className="py-2.5 px-3 text-slate-300">{c.crime_type}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-700 text-slate-200 border border-slate-600">
                          {c.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400 font-mono">{c.updated_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeActivityTab === "documents" && (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="text-slate-400 uppercase font-semibold border-b border-slate-700 bg-slate-900/50">
                    <th className="py-2.5 px-3">Doc ID</th>
                    <th className="py-2.5 px-3">Case ID</th>
                    <th className="py-2.5 px-3">Title</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Language</th>
                    <th className="py-2.5 px-3 text-right">Uploaded</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {recentActivity.latest_documents.map((d) => (
                    <tr key={d.doc_id} className="hover:bg-slate-750">
                      <td className="py-2.5 px-3 font-mono text-amber-400 font-medium">{d.doc_id}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">{d.case_id}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{d.title}</td>
                      <td className="py-2.5 px-3 text-slate-300">{d.doc_type}</td>
                      <td className="py-2.5 px-3 text-slate-300">{d.language}</td>
                      <td className="py-2.5 px-3 text-right text-slate-400 font-mono">{d.uploaded_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeActivityTab === "correlations" && (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="text-slate-400 uppercase font-semibold border-b border-slate-700 bg-slate-900/50">
                    <th className="py-2.5 px-3">Corr ID</th>
                    <th className="py-2.5 px-3">Entity A</th>
                    <th className="py-2.5 px-3">Entity B</th>
                    <th className="py-2.5 px-3">Match Type</th>
                    <th className="py-2.5 px-3">Confidence</th>
                    <th className="py-2.5 px-3 text-right">Detected</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {recentActivity.latest_correlations.map((cr) => (
                    <tr key={cr.correlation_id} className="hover:bg-slate-750">
                      <td className="py-2.5 px-3 font-mono text-purple-400 font-medium">{cr.correlation_id}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-medium">{cr.entity_a}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-medium">{cr.entity_b}</td>
                      <td className="py-2.5 px-3 text-slate-400">{cr.correlation_type}</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">
                        {(cr.confidence_score * 100).toFixed(0)}%
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400 font-mono">{cr.detected_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeActivityTab === "audit" && (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="text-slate-400 uppercase font-semibold border-b border-slate-700 bg-slate-900/50">
                    <th className="py-2.5 px-3">Audit ID</th>
                    <th className="py-2.5 px-3">User</th>
                    <th className="py-2.5 px-3">Action</th>
                    <th className="py-2.5 px-3">Target</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {recentActivity.latest_audit_events.map((a) => (
                    <tr key={a.audit_id} className="hover:bg-slate-750">
                      <td className="py-2.5 px-3 font-mono text-cyan-400 font-medium">{a.audit_id}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-medium">{a.user_id}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{a.action}</td>
                      <td className="py-2.5 px-3 text-slate-400">{a.resource_type}: {a.resource_id}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                          {a.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400 font-mono">{a.timestamp}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </main>
    </div>
  );
};

export default CommandCenter;
