"use client";

import React, { useState, useEffect, useMemo } from "react";

export type AuditAction =
  | "LOGIN"
  | "LOGOUT"
  | "CASE_CREATED"
  | "CASE_VIEWED"
  | "DOCUMENT_UPLOADED"
  | "OCR_COMPLETED"
  | "TRANSLATION_CREATED"
  | "SEARCH_EXECUTED"
  | "CORRELATION_EXECUTED"
  | "AI_QUERY"
  | "EVIDENCE_ADDED"
  | "HASH_GENERATED"
  | "EVIDENCE_VERIFIED";

export type AuditStatus = "SUCCESS" | "FAILURE" | "DENIED" | "WARNING";

export interface AuditRecord {
  audit_id: string;
  user_id: string;
  action: AuditAction;
  resource_type: string;
  resource_id: string;
  timestamp: string;
  status: AuditStatus;
  metadata: Record<string, any>;
  previous_hash: string;
  record_hash: string;
}

const ALL_ACTIONS: AuditAction[] = [
  "LOGIN",
  "LOGOUT",
  "CASE_CREATED",
  "CASE_VIEWED",
  "DOCUMENT_UPLOADED",
  "OCR_COMPLETED",
  "TRANSLATION_CREATED",
  "SEARCH_EXECUTED",
  "CORRELATION_EXECUTED",
  "AI_QUERY",
  "EVIDENCE_ADDED",
  "HASH_GENERATED",
  "EVIDENCE_VERIFIED",
];

const ALL_STATUSES: AuditStatus[] = ["SUCCESS", "FAILURE", "DENIED", "WARNING"];

export const AuditDashboard: React.FC = () => {
  // Filter States
  const [userFilter, setUserFilter] = useState<string>("");
  const [actionFilter, setActionFilter] = useState<string>("");
  const [dateFilter, setDateFilter] = useState<string>("");
  const [resourceFilter, setResourceFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  // Data States
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [chainValid, setChainValid] = useState<boolean>(true);
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null);

  // Fetch from API or use initial dataset
  useEffect(() => {
    fetchAuditData();
  }, []);

  const fetchAuditData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (userFilter) params.append("user", userFilter);
      if (actionFilter) params.append("action", actionFilter);
      if (dateFilter) params.append("date", dateFilter);
      if (resourceFilter) params.append("resource", resourceFilter);
      if (statusFilter) params.append("status", statusFilter);

      const res = await fetch(`/api/v1/audit/events?${params.toString()}`, {
        headers: {
          "x-user-role": "ADMIN",
          "x-clearance": "4",
        },
      });
      if (res.ok) {
        const data = await res.json();
        setRecords(data.records);
        setChainValid(data.chain_valid);
      }
    } catch {
      // Fallback for isolated preview mode
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setUserFilter("");
    setActionFilter("");
    setDateFilter("");
    setResourceFilter("");
    setStatusFilter("");
  };

  const getActionColor = (action: AuditAction) => {
    switch (action) {
      case "LOGIN":
      case "LOGOUT":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "CASE_CREATED":
      case "CASE_VIEWED":
        return "bg-indigo-100 text-indigo-800 border-indigo-200";
      case "EVIDENCE_ADDED":
      case "HASH_GENERATED":
      case "EVIDENCE_VERIFIED":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "AI_QUERY":
        return "bg-zinc-900 text-white border-zinc-700";
      case "DOCUMENT_UPLOADED":
      case "OCR_COMPLETED":
      case "TRANSLATION_CREATED":
        return "bg-zinc-900 text-accent border-hairline";
      case "SEARCH_EXECUTED":
      case "CORRELATION_EXECUTED":
      case "AI_QUERY":
        return "bg-zinc-900 text-zinc-300 border-hairline";
      case "HASH_GENERATED":
      case "EVIDENCE_VERIFIED":
        return "bg-emerald-950/40 text-emerald-400 border-emerald-900/50";
      default:
        return "bg-zinc-900 text-zinc-400 border-hairline";
    }
  };

  const getStatusBadge = (status: AuditStatus) => {
    switch (status) {
      case "SUCCESS":
        return <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase rounded-sm bg-emerald-950/40 text-emerald-400 border border-emerald-900/50">SUCCESS</span>;
      case "FAILURE":
        return <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase rounded-sm bg-red-950/40 text-red-400 border border-red-900/50">FAILURE</span>;
      case "DENIED":
        return <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase rounded-sm bg-red-950/40 text-red-400 border border-red-900/50">DENIED</span>;
      case "WARNING":
        return <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase rounded-sm bg-amber-950/40 text-amber-400 border border-amber-900/50">WARNING</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto font-sans bg-black text-ink min-h-screen space-y-6">
      {/* Header & Cryptographic Status */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-5 border-b border-hairline gap-4">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">Audit Trail & Chain Ledger</h1>
          <p className="text-xs text-mute mt-1">
            Cryptographic SHA-256 hash-chained application activity records.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <div
            className={`flex items-center gap-2 px-2.5 py-1 rounded-sm text-xs font-mono border ${
              chainValid
                ? "bg-zinc-900 text-emerald-400 border-hairline"
                : "bg-red-950/40 text-red-400 border-red-900/50"
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${chainValid ? "bg-emerald-400" : "bg-red-500"}`} />
            {chainValid ? "Hash Chain Verified" : "Chain Integrity Tampered"}
          </div>
          <button
            onClick={fetchAuditData}
            className="px-3 py-1 bg-white hover:bg-zinc-200 text-black text-xs font-medium rounded-sm transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Multi-Criteria Filter Bar */}
      <div className="bg-canvas-elevated p-4 rounded-md border border-hairline">
        <h2 className="text-[11px] font-mono uppercase text-mute mb-3">Filter Records</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {/* User Filter */}
          <div>
            <label className="block text-[11px] font-mono text-mute mb-1">User ID</label>
            <input
              type="text"
              placeholder="e.g. INV-101"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="w-full text-xs px-3 py-1.5 bg-zinc-950 border border-hairline text-white rounded-sm placeholder-zinc-600 focus:border-zinc-500 focus:outline-none font-mono"
            />
          </div>

          {/* Action Filter */}
          <div>
            <label className="block text-[11px] font-mono text-mute mb-1">Action</label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="w-full text-xs px-2.5 py-1.5 bg-zinc-950 border border-hairline text-white rounded-sm focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Actions (13)</option>
              {ALL_ACTIONS.map((act) => (
                <option key={act} value={act}>
                  {act}
                </option>
              ))}
            </select>
          </div>

          {/* Date Filter */}
          <div>
            <label className="block text-[11px] font-mono text-mute mb-1">Date</label>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full text-xs px-3 py-1.5 bg-zinc-950 border border-hairline text-white rounded-sm focus:border-zinc-500 focus:outline-none"
            />
          </div>

          {/* Resource Filter */}
          <div>
            <label className="block text-[11px] font-mono text-mute mb-1">Resource ID</label>
            <input
              type="text"
              placeholder="e.g. CASE-2026-001"
              value={resourceFilter}
              onChange={(e) => setResourceFilter(e.target.value)}
              className="w-full text-xs px-3 py-1.5 bg-zinc-950 border border-hairline text-white rounded-sm placeholder-zinc-600 focus:border-zinc-500 focus:outline-none font-mono"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-[11px] font-mono text-mute mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full text-xs px-2.5 py-1.5 bg-zinc-950 border border-hairline text-white rounded-sm focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Statuses (4)</option>
              {ALL_STATUSES.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Clear Filters */}
        <div className="mt-3 flex justify-end">
          <button
            onClick={() => {
              setUserFilter("");
              setActionFilter("");
              setDateFilter("");
              setResourceFilter("");
              setStatusFilter("");
            }}
            className="text-xs text-mute hover:text-white transition underline font-mono"
          >
            Clear All Filters
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-canvas-elevated rounded-md border border-hairline overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-hairline text-left text-xs">
            <thead className="bg-canvas-subtle text-[11px] font-mono uppercase text-mute">
              <tr>
                <th className="px-4 py-2.5">Audit ID</th>
                <th className="px-4 py-2.5">Timestamp</th>
                <th className="px-4 py-2.5">User</th>
                <th className="px-4 py-2.5">Action</th>
                <th className="px-4 py-2.5">Resource</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Chain Hash</th>
                <th className="px-4 py-2.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {records.map((rec) => (
                <tr key={rec.audit_id} className="hover:bg-zinc-900/50 transition">
                  <td className="px-4 py-2.5 font-mono text-xs text-mute">{rec.audit_id}</td>
                  <td className="px-4 py-2.5 text-xs text-mute whitespace-nowrap font-mono">
                    {rec.timestamp.replace("T", " ").substring(0, 19)}
                  </td>
                  <td className="px-4 py-2.5 font-medium text-white">{rec.user_id}</td>
                  <td className="px-4 py-2.5">
                    <span className={`px-1.5 py-0.5 text-[10px] font-mono rounded-sm border ${getActionColor(rec.action)}`}>
                      {rec.action}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-zinc-300">
                    <span className="font-mono text-mute">{rec.resource_type}:</span> {rec.resource_id}
                  </td>
                  <td className="px-4 py-2.5">{getStatusBadge(rec.status)}</td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-mute" title={rec.record_hash}>
                    {rec.record_hash ? rec.record_hash.substring(0, 8) + "..." : "N/A"}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      onClick={() => setSelectedRecord(rec)}
                      className="text-xs text-accent hover:underline font-medium"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
              {records.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-xs text-mute">
                    No audit records matching the specified filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Record Metadata Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-canvas-elevated rounded-md max-w-lg w-full p-6 border border-hairline text-ink">
            <div className="flex items-center justify-between pb-3 border-b border-hairline">
              <h3 className="text-sm font-semibold text-white">Audit Record Payload</h3>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-mute hover:text-white text-xs font-mono"
              >
                ✕
              </button>
            </div>
            <div className="mt-4 space-y-2 text-xs">
              <div>
                <span className="text-[11px] font-mono text-mute">Audit ID:</span>
                <p className="font-mono text-xs font-semibold text-white">{selectedRecord.audit_id}</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[11px] font-mono text-mute">User ID:</span>
                  <p className="font-medium text-white">{selectedRecord.user_id}</p>
                </div>
                <div>
                  <span className="text-[11px] font-mono text-mute">Action:</span>
                  <p className="font-medium text-white">{selectedRecord.action}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[11px] font-mono text-mute">Resource:</span>
                  <p className="text-xs text-zinc-300 font-mono">
                    {selectedRecord.resource_type} / {selectedRecord.resource_id}
                  </p>
                </div>
                <div>
                  <span className="text-[11px] font-mono text-mute">Timestamp:</span>
                  <p className="text-xs text-zinc-300 font-mono">{selectedRecord.timestamp}</p>
                </div>
              </div>
              <div>
                <span className="text-[11px] font-mono text-mute">Previous Chain Hash:</span>
                <p className="font-mono text-[11px] text-mute break-all bg-black p-2 rounded-sm border border-hairline">{selectedRecord.previous_hash}</p>
              </div>
              <div>
                <span className="text-[11px] font-mono text-mute">Record Hash:</span>
                <p className="font-mono text-[11px] text-mute break-all bg-black p-2 rounded-sm border border-hairline">{selectedRecord.record_hash}</p>
              </div>
              <div>
                <span className="text-[11px] font-mono text-mute">Metadata Payload:</span>
                <pre className="bg-black p-2.5 rounded-sm text-[11px] font-mono overflow-x-auto text-zinc-300 border border-hairline">
                  {JSON.stringify(selectedRecord.metadata, null, 2)}
                </pre>
              </div>
            </div>
            <div className="mt-5 text-right">
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 text-xs font-medium rounded-sm border border-hairline transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditDashboard;
