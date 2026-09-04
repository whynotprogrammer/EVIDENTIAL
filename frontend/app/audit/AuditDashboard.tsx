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
      case "SEARCH_EXECUTED":
      case "CORRELATION_EXECUTED":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "DOCUMENT_UPLOADED":
      case "OCR_COMPLETED":
      case "TRANSLATION_CREATED":
        return "bg-amber-100 text-amber-800 border-amber-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusBadge = (status: AuditStatus) => {
    switch (status) {
      case "SUCCESS":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-green-100 text-green-700">SUCCESS</span>;
      case "FAILURE":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-red-100 text-red-700">FAILURE</span>;
      case "DENIED":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-100 text-rose-800">DENIED</span>;
      case "WARNING":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">WARNING</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto font-sans bg-gray-50 min-h-screen">
      {/* Header & Cryptographic Status */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-gray-200 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">EVIDENTIAL Audit Trail Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Immutable application activity ledger with cryptographic hash verification.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium border ${
              chainValid
                ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                : "bg-red-50 text-red-800 border-red-300"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${chainValid ? "bg-emerald-500" : "bg-red-500"}`} />
            {chainValid ? "Cryptographic Chain Verified" : "Chain Integrity Tampered"}
          </div>
          <button
            onClick={fetchAuditData}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Multi-Criteria Filter Bar */}
      <div className="mt-6 bg-white p-4 rounded-xl shadow-sm border border-gray-200">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">Filter Records</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {/* User Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">User</label>
            <input
              type="text"
              placeholder="e.g. INV-101"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="w-full text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Action Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Action</label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="w-full text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
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
            <label className="block text-xs font-medium text-gray-600 mb-1">Date</label>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Resource Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Resource</label>
            <input
              type="text"
              placeholder="Type or ID (e.g. CASE, EVID)"
              value={resourceFilter}
              onChange={(e) => setResourceFilter(e.target.value)}
              className="w-full text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
            >
              <option value="">All Statuses</option>
              {ALL_STATUSES.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Filter Action Buttons */}
        <div className="mt-3 flex items-center justify-between pt-2 border-t border-gray-100">
          <span className="text-xs text-gray-500">
            Showing {records.length} matching events
          </span>
          <div className="flex gap-2">
            <button
              onClick={clearFilters}
              className="px-3 py-1 text-xs text-gray-600 hover:text-gray-900 border border-gray-300 rounded hover:bg-gray-100 transition"
            >
              Reset Filters
            </button>
            <button
              onClick={fetchAuditData}
              className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Audit ID</th>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Resource</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Chain Hash</th>
                <th className="px-4 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {records.map((rec) => (
                <tr key={rec.audit_id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{rec.audit_id}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
                    {rec.timestamp.replace("T", " ").substring(0, 19)}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">{rec.user_id}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded border ${getActionColor(rec.action)}`}>
                      {rec.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-700">
                    <span className="font-semibold text-gray-600">{rec.resource_type}:</span> {rec.resource_id}
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(rec.status)}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-400" title={rec.record_hash}>
                    {rec.record_hash ? rec.record_hash.substring(0, 8) + "..." : "N/A"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setSelectedRecord(rec)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
              {records.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">
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
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 border border-gray-200">
            <div className="flex items-center justify-between pb-3 border-b border-gray-200">
              <h3 className="text-base font-bold text-gray-900">Audit Record Details</h3>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>
            <div className="mt-4 space-y-2 text-sm">
              <div>
                <span className="text-xs text-gray-500">Audit ID:</span>
                <p className="font-mono text-xs font-semibold text-gray-800">{selectedRecord.audit_id}</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-xs text-gray-500">User ID:</span>
                  <p className="font-semibold text-gray-800">{selectedRecord.user_id}</p>
                </div>
                <div>
                  <span className="text-xs text-gray-500">Action:</span>
                  <p className="font-semibold text-gray-800">{selectedRecord.action}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-xs text-gray-500">Resource:</span>
                  <p className="text-xs text-gray-800 font-mono">
                    {selectedRecord.resource_type} / {selectedRecord.resource_id}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-gray-500">Timestamp:</span>
                  <p className="text-xs text-gray-800">{selectedRecord.timestamp}</p>
                </div>
              </div>
              <div>
                <span className="text-xs text-gray-500">Previous Chain Hash:</span>
                <p className="font-mono text-xs text-gray-600 break-all">{selectedRecord.previous_hash}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">Record Hash:</span>
                <p className="font-mono text-xs text-gray-600 break-all">{selectedRecord.record_hash}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">Metadata Payload:</span>
                <pre className="bg-gray-100 p-2.5 rounded text-xs overflow-x-auto text-gray-800">
                  {JSON.stringify(selectedRecord.metadata, null, 2)}
                </pre>
              </div>
            </div>
            <div className="mt-5 text-right">
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-800 text-xs font-semibold rounded"
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
