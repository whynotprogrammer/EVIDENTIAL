"use client";

import { useState } from "react";
import { X, Plus, AlertCircle, Loader2 } from "lucide-react";
import { CaseCreatePayload, createCase } from "../lib/api";

interface CreateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateCaseModal({ isOpen, onClose, onSuccess }: CreateCaseModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<CaseCreatePayload>({
    case_number: `FIR-${new Date().getFullYear()}-DL-${Math.floor(1000 + Math.random() * 9000)}`,
    title: "",
    description: "",
    crime_type: "Cyber Financial Fraud",
    priority: "HIGH",
    status: "UNDER_INVESTIGATION",
    location: "",
    police_station: "Central Cyber Crime Cell",
    district: "New Delhi",
    state: "Delhi",
    incident_date: new Date().toISOString().split("T")[0],
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.case_number || !formData.crime_type) {
      setError("Please fill in all mandatory case details.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await createCase({
        ...formData,
        incident_date: formData.incident_date ? new Date(formData.incident_date).toISOString() : undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to register case");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-canvas-elevated border border-hairline rounded-md max-w-2xl w-full p-6 overflow-y-auto max-h-[90vh]">
        <div className="flex items-center justify-between border-b border-hairline pb-4 mb-5">
          <div>
            <h2 className="text-base font-semibold text-white">Register Investigation Case</h2>
            <p className="text-xs text-mute">Initialize a new FIR record into the secure case registry</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-sm hover:bg-zinc-900 text-zinc-400 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-sm bg-red-950/30 border border-red-900/50 flex items-center gap-2 text-xs text-red-300">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-zinc-300 font-medium mb-1">Case Number / FIR ID *</label>
              <input
                type="text"
                required
                value={formData.case_number}
                onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
                placeholder="e.g. FIR-2024-WB-0412"
              />
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">Crime Classification *</label>
              <select
                value={formData.crime_type}
                onChange={(e) => setFormData({ ...formData, crime_type: e.target.value })}
                className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white focus:outline-none focus:border-zinc-500"
              >
                <option value="Cyber Financial Fraud">Cyber Financial Fraud</option>
                <option value="Ransomware & Extortion">Ransomware & Extortion</option>
                <option value="Critical Infrastructure Attack">Critical Infrastructure Attack</option>
                <option value="Unauthorized Server Intrusion">Unauthorized Server Intrusion</option>
                <option value="Data Exfiltration & Espionage">Data Exfiltration & Espionage</option>
                <option value="Armed Robbery & Theft">Armed Robbery & Theft</option>
                <option value="Narcotics Trafficking">Narcotics Trafficking</option>
                <option value="Identity Theft / SIM Swap">Identity Theft / SIM Swap</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-zinc-300 font-medium mb-1">Case Title *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500"
              placeholder="e.g. Unauthorized Corporate Banking Server Intrusion"
            />
          </div>

          <div>
            <label className="block text-zinc-300 font-medium mb-1">Incident Description</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500"
              placeholder="Provide a concise summary of the reported incident, modus operandi, and initial observations..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-zinc-300 font-medium mb-1">Investigation Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white focus:outline-none focus:border-zinc-500"
              >
                <option value="OPEN">OPEN</option>
                <option value="UNDER_INVESTIGATION">UNDER_INVESTIGATION</option>
                <option value="PENDING_REVIEW">PENDING_REVIEW</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">Priority Level</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white focus:outline-none focus:border-zinc-500"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">Incident Date</label>
              <input
                type="date"
                value={formData.incident_date}
                onChange={(e) => setFormData({ ...formData, incident_date: e.target.value })}
                className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white focus:outline-none focus:border-zinc-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-zinc-300 font-medium mb-1">Incident Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500"
                placeholder="e.g. Sector 62, Cyber Hub, Noida"
              />
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">Police Station / Cell</label>
              <input
                type="text"
                value={formData.police_station}
                onChange={(e) => setFormData({ ...formData, police_station: e.target.value })}
                className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500"
                placeholder="e.g. Cyber Crime Special Cell"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-hairline">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-sm bg-transparent hover:bg-zinc-900 text-zinc-300 border border-hairline transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-sm bg-white hover:bg-zinc-200 text-black font-medium transition disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              Create Case
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
