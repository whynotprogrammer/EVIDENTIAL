"use client";

import React, { useState, useEffect } from "react";
import {
  Scale,
  ShieldCheck,
  ShieldAlert,
  FileCheck2,
  FileText,
  Clock,
  Printer,
  X,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Fingerprint,
  Hash,
  Copy,
  ExternalLink,
  ChevronRight,
  User,
  Building,
  Calendar,
  Lock,
  FileSignature,
  Award,
  Layers,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import {
  CourtPackageReadiness,
  CourtEvidencePackageOut,
  getCourtPackageReadiness,
  generateCourtPackage,
  getLatestCourtPackage,
} from "../lib/api";

interface CourtPackageModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string | number;
  caseNumber: string;
  initialMode?: "review" | "viewer";
  initialPackage?: CourtEvidencePackageOut | null;
}

export default function CourtPackageModal({
  isOpen,
  onClose,
  caseId,
  caseNumber,
  initialMode = "review",
  initialPackage = null,
}: CourtPackageModalProps) {
  const [mode, setMode] = useState<"review" | "viewer">(initialMode);
  const [readiness, setReadiness] = useState<CourtPackageReadiness | null>(null);
  const [currentPackage, setCurrentPackage] = useState<CourtEvidencePackageOut | null>(initialPackage);
  const [loading, setLoading] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("all");

  useEffect(() => {
    if (isOpen) {
      setMode(initialMode);
      if (initialPackage) {
        setCurrentPackage(initialPackage);
      }
      loadReadiness();
    }
  }, [isOpen, caseId, initialMode, initialPackage]);

  const loadReadiness = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getCourtPackageReadiness(caseId);
      setReadiness(res);
      // Also check if existing package exists if not supplied
      if (!initialPackage) {
        const latest = await getLatestCourtPackage(caseId);
        if (latest) {
          setCurrentPackage(latest);
        }
      }
    } catch (err: any) {
      console.error("Failed to load court package readiness:", err);
      setError(err.message || "Failed to load readiness data");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);
      const pkg = await generateCourtPackage(caseId);
      setCurrentPackage(pkg);
      setMode("viewer");
      // Refresh readiness for metrics sync
      loadReadiness();
    } catch (err: any) {
      console.error("Error generating package:", err);
      setError(err.message || "Failed to generate court evidence package");
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4 print:p-0 print:static print:bg-white print:overflow-visible">
      <div className="relative w-full max-w-5xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] print:max-h-none print:border-none print:shadow-none print:rounded-none print:bg-white print:text-black">
        
        {/* Modal Top Header (Hidden on Print) */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90 print:hidden">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-950/80 border border-blue-800/80 text-blue-400">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100 tracking-wide">
                  COURT EVIDENCE PACKAGE
                </h2>
                <span className="font-mono text-xs px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-800">
                  {caseNumber}
                </span>
                {currentPackage && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full font-bold bg-emerald-950/80 border border-emerald-700 text-emerald-300">
                    {currentPackage.status}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Section 65B Indian Evidence Act, 1872 • Section 63 Bharatiya Sakshya Adhiniyam, 2023 Compliant
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {currentPackage && mode === "review" && (
              <button
                onClick={() => setMode("viewer")}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition"
              >
                <FileText className="w-3.5 h-3.5 text-blue-400" />
                View Generated Package
              </button>
            )}

            {currentPackage && mode === "viewer" && (
              <button
                onClick={() => setMode("review")}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition"
              >
                <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
                Review Readiness
              </button>
            )}

            {mode === "viewer" && currentPackage && (
              <button
                onClick={handlePrint}
                className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white flex items-center gap-1.5 shadow-lg shadow-blue-900/30 transition"
              >
                <Printer className="w-3.5 h-3.5" />
                Download PDF / Print
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition ml-2"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="overflow-y-auto flex-1 p-6 space-y-6 print:p-0 print:overflow-visible print:space-y-4">
          
          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/80 text-red-300 text-xs flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p className="text-xs font-medium tracking-wide">Evaluating Case Readiness & Integrity...</p>
            </div>
          ) : mode === "review" && readiness ? (
            /* ========================================================= */
            /* MODE: REVIEW / READINESS CHECKLIST                        */
            /* ========================================================= */
            <div className="space-y-6">
              
              {/* Summary Readiness Status Banner */}
              <div className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                readiness.is_package_complete
                  ? "bg-emerald-950/20 border-emerald-800/60"
                  : "bg-amber-950/20 border-amber-800/60"
              }`}>
                <div className="flex items-start gap-3">
                  {readiness.is_package_complete ? (
                    <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                      {readiness.is_package_complete
                        ? "Dossier Fully Complete & Court Ready"
                        : "Partial Case Dossier (Ready for Packaging with Notices)"}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      {readiness.is_package_complete
                        ? "All statutory evidence, forensic hashes, FIR links, custody logs, and audit trails are verified."
                        : `Notice: ${readiness.missing_sections.length} section(s) currently contain no records (${readiness.missing_sections.join(
                            ", "
                          )}). Package will be certified as 'PACKAGE INCOMPLETE' with explicit statutory disclaimers.`}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white flex items-center gap-2 shadow-lg shadow-blue-900/30 disabled:opacity-50 transition"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generating Package...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 text-blue-200" />
                        Generate Package
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Dynamic Metrics Counters */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Evidence Registered
                  </span>
                  <span className="text-xl font-bold font-mono text-blue-400 mt-1 block">
                    {readiness.preview.evidence_register.count}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {readiness.preview.evidence_register.available ? "Hardware / Digital Items" : "No items logged"}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Custody Transfers
                  </span>
                  <span className="text-xl font-bold font-mono text-emerald-400 mt-1 block">
                    {readiness.preview.chain_of_custody.total_events}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {readiness.preview.chain_of_custody.available ? "Cryptographically Signed" : "No transfers recorded"}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Timeline Milestones
                  </span>
                  <span className="text-xl font-bold font-mono text-purple-400 mt-1 block">
                    {readiness.preview.investigation_timeline.count}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {readiness.preview.investigation_timeline.available ? "Logged Case Events" : "No milestones logged"}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Audit Verification
                  </span>
                  <span className="text-xl font-bold font-mono text-amber-400 mt-1 block">
                    {readiness.preview.audit_certificate.total_audit_events}
                  </span>
                  <span className="text-[10px] text-slate-500">Immutable Audit Entries</span>
                </div>
              </div>

              {/* 11-Section Dynamic Readiness Checklist */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-blue-400" />
                  11-Point Statutory Dossier Checklist
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Item 1 */}
                  <ChecklistItem
                    title="1. Case Summary"
                    status={readiness.case_summary_status}
                    details={`Case #${readiness.case_number} • ${readiness.preview.case_summary.crime_type}`}
                    isAvailable={true}
                  />

                  {/* Item 2 */}
                  <ChecklistItem
                    title="2. First Information Report (FIR)"
                    status={readiness.fir_status}
                    details={
                      readiness.preview.fir.available
                        ? `FIR #${readiness.preview.fir.fir_number || "Logged"} • ${readiness.preview.fir.linked_documents.length} Linked Documents`
                        : "No FIR document or metadata registered for this case"
                    }
                    isAvailable={readiness.preview.fir.available}
                  />

                  {/* Item 3 */}
                  <ChecklistItem
                    title="3. Witness Statements"
                    status={readiness.witness_statements_status}
                    details={
                      readiness.preview.witness_statements.available
                        ? `${readiness.preview.witness_statements.count} Recorded Statements in Dossier`
                        : "No formal witness statements recorded in timeline or evidence"
                    }
                    isAvailable={readiness.preview.witness_statements.available}
                  />

                  {/* Item 4 */}
                  <ChecklistItem
                    title="4. Evidence Register"
                    status={readiness.evidence_register_status}
                    details={
                      readiness.preview.evidence_register.available
                        ? `${readiness.preview.evidence_register.count} Registered Hardware / Digital Evidence Items`
                        : "No physical/digital evidence items registered in case locker"
                    }
                    isAvailable={readiness.preview.evidence_register.available}
                  />

                  {/* Item 5 */}
                  <ChecklistItem
                    title="5. Forensic Examination Reports"
                    status={readiness.forensic_reports_status}
                    details={
                      readiness.preview.forensic_reports.available
                        ? `${readiness.preview.forensic_reports.count} Certified Digital Forensics Reports Attached`
                        : "No forensic lab reports attached to registered items"
                    }
                    isAvailable={readiness.preview.forensic_reports.available}
                  />

                  {/* Item 6 */}
                  <ChecklistItem
                    title="6. Comprehensive Investigation Timeline"
                    status={readiness.investigation_timeline_status}
                    details={
                      readiness.preview.investigation_timeline.available
                        ? `${readiness.preview.investigation_timeline.count} Chronological Milestones Logged`
                        : "No timeline milestones registered"
                    }
                    isAvailable={readiness.preview.investigation_timeline.available}
                  />

                  {/* Item 7 */}
                  <ChecklistItem
                    title="7. Digital Chain of Custody"
                    status={readiness.chain_of_custody_status}
                    details={
                      readiness.preview.chain_of_custody.available
                        ? `${readiness.preview.chain_of_custody.total_events} Total Custody Handover Events Recorded`
                        : "No custody events logged"
                    }
                    isAvailable={readiness.preview.chain_of_custody.available}
                  />

                  {/* Item 8 */}
                  <ChecklistItem
                    title="8. Evidence Integrity Certificates"
                    status={readiness.integrity_certificates_status}
                    details={
                      readiness.preview.integrity_certificates.available
                        ? readiness.preview.integrity_certificates.all_valid
                          ? "All item SHA-256 digests verify 100% untampered"
                          : "Warning: Integrity discrepancies detected"
                        : "No evidence items available for cryptographic hashing"
                    }
                    isAvailable={readiness.preview.integrity_certificates.available}
                  />

                  {/* Item 9 */}
                  <ChecklistItem
                    title="9. Cryptographic Digital Signatures"
                    status={readiness.digital_signatures_status}
                    details={
                      readiness.preview.digital_signatures.available
                        ? `${readiness.preview.digital_signatures.total_signatures} Authorized Officer / Custodian Signatures`
                        : "No digital signatures captured in custody chain"
                    }
                    isAvailable={readiness.preview.digital_signatures.available}
                  />

                  {/* Item 10 */}
                  <ChecklistItem
                    title="10. Chain of Custody Audit Certificate"
                    status={readiness.audit_certificate_status}
                    details={`${readiness.preview.audit_certificate.total_audit_events} Immutable Events Certified under Sec 65B/63`}
                    isAvailable={true}
                  />

                  {/* Item 11 */}
                  <ChecklistItem
                    title="11. Cryptographic Package Verification & Hash"
                    status="Generated on Compilation"
                    details="Unique Canonical SHA-256 master package digest calculated upon assembly"
                    isAvailable={true}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={generating}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white flex items-center gap-2 shadow-lg shadow-blue-900/30 disabled:opacity-50 transition"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Generating Package...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 text-blue-200" />
                      Generate Package
                    </>
                  )}
                </button>
              </div>

            </div>
          ) : currentPackage ? (
            /* ========================================================= */
            /* MODE: VIEWER / COURT-READY EVIDENCE PACKAGE               */
            /* ========================================================= */
            <div className="space-y-6 print:space-y-4 print:text-black">
              
              {/* Package Identification Card */}
              <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 shadow-xl space-y-4 print:border-black print:bg-white print:p-4 print:rounded-none">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-blue-400 bg-blue-950/90 px-3 py-1 rounded-lg border border-blue-800/80 print:bg-white print:text-black print:border-black">
                        {currentPackage.package_id}
                      </span>
                      <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${
                        currentPackage.status === "COURT_READY"
                          ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:text-black print:border-black"
                          : "bg-amber-950/80 border-amber-700 text-amber-300 print:text-black print:border-black"
                      }`}>
                        {currentPackage.status}
                      </span>
                      {currentPackage.is_complete ? (
                        <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-emerald-950/60 border border-emerald-800 text-emerald-300 print:hidden">
                          ✓ Complete Dossier
                        </span>
                      ) : (
                        <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-amber-950/60 border border-amber-800 text-amber-300 print:hidden">
                          ⚠ Incomplete / Partial
                        </span>
                      )}
                    </div>
                    <h1 className="text-lg font-bold text-slate-100 tracking-wide mt-2 print:text-black">
                      OFFICIAL COURT EVIDENCE DOSSIER
                    </h1>
                    <p className="text-xs text-slate-400 print:text-slate-600">
                      Generated: {new Date(currentPackage.created_at).toLocaleString()} • Compiled By: {currentPackage.generated_by_name}
                    </p>
                  </div>

                  <div className="text-right space-y-1">
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider block font-semibold print:text-slate-600">
                      Legal Statute Reference
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-200 block print:text-black">
                      Sec. 65B IEA / Sec. 63 BSA
                    </span>
                    <span className="text-[10px] text-slate-400 block print:text-slate-600">
                      Government of India • Forensic Division
                    </span>
                  </div>
                </div>

                {/* Package Cryptographic SHA-256 Digest Bar */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 print:border-black print:bg-white">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <Fingerprint className="w-4 h-4 text-blue-400 shrink-0 print:text-black" />
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider shrink-0 print:text-black">
                      Master Package Hash (SHA-256):
                    </span>
                    <span className="font-mono text-xs text-blue-300 font-bold truncate select-all print:text-black">
                      {currentPackage.package_hash}
                    </span>
                  </div>

                  <button
                    onClick={() => handleCopy(currentPackage.package_hash)}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition shrink-0 print:hidden"
                  >
                    {copiedHash === currentPackage.package_hash ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Copy Hash
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Section 1: Executive Case Summary */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <Building className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 1: Case Summary
                  </h3>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Case Identifier</span>
                    <span className="font-semibold text-slate-200 print:text-black">
                      {currentPackage.package_data.case_summary.case_number}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Crime Classification</span>
                    <span className="font-semibold text-slate-200 print:text-black">
                      {currentPackage.package_data.case_summary.crime_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Priority & Status</span>
                    <span className="font-semibold text-slate-200 print:text-black">
                      {currentPackage.package_data.case_summary.priority} • {currentPackage.package_data.case_summary.status}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Investigating Officer</span>
                    <span className="font-semibold text-slate-200 print:text-black">
                      {currentPackage.package_data.case_summary.assigned_officer || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Police Station & District</span>
                    <span className="font-semibold text-slate-200 print:text-black">
                      {currentPackage.package_data.case_summary.police_station || "HQ"}, {currentPackage.package_data.case_summary.district || "State"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Applicable Acts / Sections</span>
                    <span className="font-semibold text-slate-200 font-mono print:text-black">
                      {currentPackage.package_data.case_summary.act_section || "Information Technology Act / BNS"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Incident Date</span>
                    <span className="font-semibold text-slate-200 print:text-black">
                      {currentPackage.package_data.case_summary.incident_date || "Recorded in Dossier"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">FIR Year</span>
                    <span className="font-semibold text-slate-200 print:text-black">
                      {currentPackage.package_data.case_summary.fir_year || "Current"}
                    </span>
                  </div>
                </div>

                {currentPackage.package_data.case_summary.title && (
                  <div className="pt-2 border-t border-slate-800/80 print:border-slate-300">
                    <span className="text-[11px] text-slate-400 block print:text-slate-600">Dossier Matter Title</span>
                    <p className="text-xs text-slate-200 font-medium mt-0.5 print:text-black">
                      {currentPackage.package_data.case_summary.title}
                    </p>
                  </div>
                )}
              </div>

              {/* Section 2: First Information Report (FIR) */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <FileText className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 2: First Information Report (FIR)
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.fir.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.fir.available ? "VERIFIED ATTACHED" : "NO FIR AVAILABLE"}
                  </span>
                </div>

                {currentPackage.package_data.fir.available ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                      <div>
                        <span className="text-[11px] text-slate-400 block print:text-slate-600">FIR Number</span>
                        <span className="font-semibold text-slate-200 print:text-black">
                          {currentPackage.package_data.fir.fir_number || "Logged in Case File"}
                        </span>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-400 block print:text-slate-600">FIR Stage</span>
                        <span className="font-semibold text-slate-200 print:text-black">
                          {currentPackage.package_data.fir.fir_stage || "Under Investigation"}
                        </span>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-400 block print:text-slate-600">Station & District</span>
                        <span className="font-semibold text-slate-200 print:text-black">
                          {currentPackage.package_data.fir.police_station || "HQ Station"}, {currentPackage.package_data.fir.district || "State"}
                        </span>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-400 block print:text-slate-600">Complaint Mode</span>
                        <span className="font-semibold text-slate-200 print:text-black">
                          {currentPackage.package_data.fir.complaint_mode || "Official Submission"}
                        </span>
                      </div>
                    </div>

                    {currentPackage.package_data.fir.linked_documents.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block print:text-slate-600">
                          Linked FIR Documents & Evidentiary Scans:
                        </span>
                        <div className="space-y-1.5">
                          {currentPackage.package_data.fir.linked_documents.map((doc) => (
                            <div
                              key={doc.document_id}
                              className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs print:border-black print:bg-white"
                            >
                              <div className="flex items-center gap-2">
                                <FileCheck2 className="w-4 h-4 text-blue-400 shrink-0 print:text-black" />
                                <span className="font-medium text-slate-200 print:text-black">{doc.filename}</span>
                              </div>
                              <span className="font-mono text-[11px] text-slate-400 select-all print:text-black">
                                SHA-256: {doc.file_hash}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <EmptySectionMessage message="NO FIR AVAILABLE: No FIR document or structured FIR metadata has been registered for this case dossier." />
                )}
              </div>

              {/* Section 3: Witness Statements */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <User className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 3: Witness Statements
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.witness_statements.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.witness_statements.available
                      ? `${currentPackage.package_data.witness_statements.count} STATEMENTS`
                      : "NO WITNESS STATEMENTS AVAILABLE"}
                  </span>
                </div>

                {currentPackage.package_data.witness_statements.available ? (
                  <div className="space-y-3">
                    {currentPackage.package_data.witness_statements.statements.map((stmt, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs print:border-black print:bg-white"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-200 print:text-black">{stmt.witness_name}</span>
                          <span className="text-[11px] text-slate-400 print:text-slate-600">
                            Recorded: {new Date(stmt.statement_date).toLocaleString()} • By: {stmt.recorded_by}
                          </span>
                        </div>
                        <p className="text-slate-300 print:text-black">{stmt.summary}</p>
                        {stmt.document_hash && (
                          <div className="font-mono text-[10px] text-slate-400 print:text-slate-600">
                            Signed Transcript Hash: {stmt.document_hash}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptySectionMessage message="NO WITNESS STATEMENTS AVAILABLE: No formal witness examinations or recorded statements are currently on file for this case." />
                )}
              </div>

              {/* Section 4: Evidence Register */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <Layers className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 4: Evidence Register
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.evidence_register.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.evidence_register.available
                      ? `${currentPackage.package_data.evidence_register.count} REGISTERED ITEMS`
                      : "NO EVIDENCE REGISTERED"}
                  </span>
                </div>

                {currentPackage.package_data.evidence_register.available ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 print:border-black print:text-black">
                          <th className="py-2 px-2 font-semibold">Evidence #</th>
                          <th className="py-2 px-2 font-semibold">Item & Type</th>
                          <th className="py-2 px-2 font-semibold">Current Status</th>
                          <th className="py-2 px-2 font-semibold">Custodian / Location</th>
                          <th className="py-2 px-2 font-semibold font-mono">Original SHA-256 Digest</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/80 print:divide-black">
                        {currentPackage.package_data.evidence_register.items.map((item) => (
                          <tr key={item.evidence_id} className="text-slate-300 print:text-black">
                            <td className="py-2.5 px-2 font-mono font-bold text-blue-400 print:text-black">
                              {item.evidence_number}
                            </td>
                            <td className="py-2.5 px-2">
                              <span className="font-semibold block text-slate-200 print:text-black">{item.title}</span>
                              <span className="text-[10px] text-slate-400 print:text-slate-600">{item.evidence_type}</span>
                            </td>
                            <td className="py-2.5 px-2">
                              <span className="font-bold text-[11px] text-slate-300 print:text-black">{item.custody_status}</span>
                            </td>
                            <td className="py-2.5 px-2 text-[11px]">
                              <span className="block text-slate-200 print:text-black">{item.current_custodian}</span>
                              <span className="text-slate-400 print:text-slate-600">{item.storage_location}</span>
                            </td>
                            <td className="py-2.5 px-2 font-mono text-[10px] text-slate-400 select-all print:text-black">
                              {item.original_sha256}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptySectionMessage message="NO EVIDENCE REGISTERED: No physical or digital evidence has been cataloged in the evidence locker for this case." />
                )}
              </div>

              {/* Section 5: Forensic Reports */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <FileCheck2 className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 5: Forensic Examination Reports
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.forensic_reports.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.forensic_reports.available
                      ? `${currentPackage.package_data.forensic_reports.count} REPORTS ATTACHED`
                      : "NO FORENSIC REPORTS AVAILABLE"}
                  </span>
                </div>

                {currentPackage.package_data.forensic_reports.available ? (
                  <div className="space-y-3">
                    {currentPackage.package_data.forensic_reports.reports.map((rep, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs print:border-black print:bg-white"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-blue-400 print:text-black">
                            {rep.evidence_number} — {rep.evidence_title}
                          </span>
                          <span className="text-[11px] text-slate-400 print:text-slate-600">
                            Attached: {new Date(rep.attached_at).toLocaleString()} • Examiner: {rep.attached_by}
                          </span>
                        </div>
                        <p className="text-slate-300 font-medium print:text-black">
                          Report File: {rep.report_filename}
                        </p>
                        {rep.summary && <p className="text-slate-400 print:text-slate-600">{rep.summary}</p>}
                        <div className="font-mono text-[10px] text-slate-400 select-all print:text-black">
                          Cryptographic Lab Digest (SHA-256): {rep.report_hash}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptySectionMessage message="NO FORENSIC REPORTS AVAILABLE: No digital forensics lab examination reports or extraction certificates have been uploaded." />
                )}
              </div>

              {/* Section 6: Investigation Timeline */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <Clock className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 6: Investigation Timeline
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.investigation_timeline.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.investigation_timeline.available
                      ? `${currentPackage.package_data.investigation_timeline.count} EVENTS`
                      : "NO TIMELINE EVENTS RECORDED"}
                  </span>
                </div>

                {currentPackage.package_data.investigation_timeline.available ? (
                  <div className="space-y-2">
                    {currentPackage.package_data.investigation_timeline.events.map((ev) => (
                      <div
                        key={ev.id}
                        className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-3 text-xs print:border-black print:bg-white"
                      >
                        <span className="font-mono text-[11px] text-slate-400 shrink-0 mt-0.5 print:text-slate-600">
                          {new Date(ev.event_date).toLocaleString()}
                        </span>
                        <div className="space-y-0.5 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-200 print:text-black">{ev.title}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono print:border-black print:text-black">
                              {ev.event_type}
                            </span>
                          </div>
                          <p className="text-slate-400 print:text-slate-700">{ev.description}</p>
                          {ev.location && (
                            <span className="text-[10px] text-slate-500 block print:text-slate-600">
                              Location: {ev.location}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptySectionMessage message="NO TIMELINE EVENTS RECORDED: No investigative sequence or procedural milestones have been logged for this case." />
                )}
              </div>

              {/* Section 7: Digital Chain of Custody */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <ShieldCheck className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 7: Digital Chain of Custody
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.chain_of_custody.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.chain_of_custody.available
                      ? `${currentPackage.package_data.chain_of_custody.total_events} TOTAL EVENTS`
                      : "NO CUSTODY EVENTS AVAILABLE"}
                  </span>
                </div>

                {currentPackage.package_data.chain_of_custody.available ? (
                  <div className="space-y-4">
                    {currentPackage.package_data.chain_of_custody.items.map((itemChain) => (
                      <div
                        key={itemChain.evidence_id}
                        className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3 text-xs print:border-black print:bg-white"
                      >
                        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 print:border-black">
                          <span className="font-mono font-bold text-blue-400 print:text-black">
                            {itemChain.evidence_number} — {itemChain.title}
                          </span>
                          <span className="text-[11px] text-slate-400 print:text-slate-600">
                            Current Status: {itemChain.current_status} • Custodian: {itemChain.current_custodian || "Locker"}
                          </span>
                        </div>

                        <div className="space-y-2">
                          {itemChain.events.map((ev, idx) => (
                            <div
                              key={idx}
                              className="p-2 rounded-lg bg-slate-900/60 border border-slate-800/80 text-[11px] space-y-1 print:border-black print:bg-white"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-slate-200 print:text-black">{ev.action}</span>
                                <span className="text-slate-400 print:text-slate-600">{new Date(ev.when).toLocaleString()}</span>
                              </div>
                              <div className="text-slate-400 print:text-slate-700">
                                Handler: {ev.who} {ev.to_custodian ? `→ Transferred To: ${ev.to_custodian}` : ""}
                                {ev.where ? ` • Location: ${ev.where}` : ""}
                              </div>
                              <div className="font-mono text-[10px] text-slate-500 print:text-black truncate">
                                Evidence Digest: {ev.evidence_hash}
                              </div>
                              {ev.digital_signature && (
                                <div className="font-mono text-[10px] text-blue-400 print:text-black truncate">
                                  Signature: {ev.digital_signature}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptySectionMessage message="NO CUSTODY EVENTS AVAILABLE: No custody transfers, seizures, or chain-of-custody transactions have been logged." />
                )}
              </div>

              {/* Section 8: Evidence Integrity Certificates */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <Award className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 8: Evidence Integrity Certificates
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.integrity_certificates.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.integrity_certificates.available
                      ? currentPackage.package_data.integrity_certificates.all_valid
                        ? "ALL VALID & UNTAMPERED"
                        : "ATTENTION REQUIRED"
                      : "NO INTEGRITY CERTIFICATES"}
                  </span>
                </div>

                {currentPackage.package_data.integrity_certificates.available ? (
                  <div className="space-y-3">
                    {currentPackage.package_data.integrity_certificates.certificates.map((cert) => (
                      <div
                        key={cert.evidence_id}
                        className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs print:border-black print:bg-white"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-blue-400 print:text-black">
                            {cert.evidence_number} — {cert.title}
                          </span>
                          <span className={`font-bold px-2 py-0.5 rounded text-[10px] ${
                            cert.is_valid
                              ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800 print:border-black print:text-black"
                              : "bg-red-950/80 text-red-300 border border-red-800 print:border-black print:text-black"
                          }`}>
                            {cert.status}
                          </span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-[11px]">
                          <div className="p-2 rounded bg-slate-900/80 border border-slate-800 print:border-black print:bg-white">
                            <span className="text-[10px] text-slate-400 block print:text-slate-600">Original Acquisition SHA-256</span>
                            <span className="text-slate-200 select-all break-all print:text-black">{cert.original_sha256}</span>
                          </div>
                          <div className="p-2 rounded bg-slate-900/80 border border-slate-800 print:border-black print:bg-white">
                            <span className="text-[10px] text-slate-400 block print:text-slate-600">Verification SHA-256</span>
                            <span className="text-slate-200 select-all break-all print:text-black">{cert.current_sha256}</span>
                          </div>
                        </div>
                        <p className="text-[11px] text-slate-400 italic print:text-slate-700">
                          "{cert.integrity_declaration}"
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptySectionMessage message="NO INTEGRITY CERTIFICATES: No evidence records exist to generate cryptographic integrity verification certificates." />
                )}
              </div>

              {/* Section 9: Cryptographic Digital Signatures */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <FileSignature className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 9: Cryptographic Digital Signatures
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentPackage.package_data.digital_signatures.available
                      ? "bg-emerald-950/80 border-emerald-700 text-emerald-300 print:border-black print:text-black"
                      : "bg-slate-800 border-slate-700 text-slate-400 print:border-black print:text-black"
                  }`}>
                    {currentPackage.package_data.digital_signatures.available
                      ? `${currentPackage.package_data.digital_signatures.total_signatures} SIGNATURES`
                      : "NO SIGNATURES AVAILABLE"}
                  </span>
                </div>

                {currentPackage.package_data.digital_signatures.available ? (
                  <div className="space-y-2">
                    {currentPackage.package_data.digital_signatures.signatures.map((sig, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs print:border-black print:bg-white"
                      >
                        <div>
                          <span className="font-bold text-slate-200 block print:text-black">
                            {sig.signer_name} ({sig.signer_role})
                          </span>
                          <span className="text-[11px] text-slate-400 print:text-slate-600">
                            Subject: {sig.item_type} #{sig.item_identifier} • {new Date(sig.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <div className="font-mono text-[10px] text-blue-400 select-all print:text-black">
                          Digest: {sig.signature_hash} ({sig.algorithm})
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptySectionMessage message="NO DIGITAL SIGNATURES AVAILABLE: No cryptographic digital signatures have been affixed to custody events in this case." />
                )}
              </div>

              {/* Section 10: Formal Chain of Custody Audit Certificate */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-blue-900/60 space-y-4 print:border-black print:bg-white print:p-4 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 print:border-black">
                  <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <ShieldCheck className="w-5 h-5 text-blue-400 print:text-black" />
                    Section 10: Formal Chain of Custody Audit Certificate
                  </h3>
                  <span className="font-mono text-[11px] text-slate-400 print:text-black">
                    Certificate ID: {currentPackage.package_data.audit_certificate.certificate_id}
                  </span>
                </div>

                <div className="text-xs text-slate-300 space-y-3 leading-relaxed print:text-black">
                  <p className="font-medium text-slate-200 print:text-black">
                    {currentPackage.package_data.audit_certificate.integrity_declaration}
                  </p>
                  <p className="text-slate-400 print:text-slate-700">
                    Statutory Compliance:{" "}
                    <strong className="text-slate-200 print:text-black">
                      {currentPackage.package_data.audit_certificate.legal_statute_reference}
                    </strong>
                  </p>
                  <div className="pt-3 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-3 gap-3 print:border-black">
                    <div>
                      <span className="text-[10px] text-slate-500 block print:text-slate-600">Total Audit Events Verified</span>
                      <span className="font-bold text-emerald-400 text-sm print:text-black">
                        {currentPackage.package_data.audit_certificate.total_audit_events} Events
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block print:text-slate-600">Chain Verification Status</span>
                      <span className="font-bold text-slate-200 text-sm print:text-black">
                        {currentPackage.package_data.audit_certificate.chain_of_custody_status}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block print:text-slate-600">Certified Officer</span>
                      <span className="font-bold text-slate-200 text-sm print:text-black">
                        {currentPackage.package_data.audit_certificate.certified_by}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 11: Cryptographic Package Verification & Hash */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 print:border-black print:bg-white print:p-3 print:rounded-none">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 print:border-black">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 print:text-black">
                    <Lock className="w-4 h-4 text-blue-400 print:text-black" />
                    Section 11: Master Cryptographic Package Verification
                  </h3>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-700 text-emerald-300 print:border-black print:text-black">
                    SEALED & HASHED
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <p className="text-slate-400 print:text-slate-700">
                    The entire court evidence package above has been serialized into canonical JSON and signed with a cryptographic SHA-256 hash. Any alteration to any entry in this package will invalidate the hash verification.
                  </p>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-blue-300 break-all select-all print:border-black print:bg-white print:text-black">
                    {currentPackage.package_hash}
                  </div>
                </div>
              </div>

              {/* Bottom Actions (Hidden on Print) */}
              <div className="pt-4 border-t border-slate-800 flex items-center justify-between print:hidden">
                <div className="text-[11px] text-slate-500">
                  Evidence Package ID: <span className="font-mono text-slate-400">{currentPackage.package_id}</span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                  >
                    Close
                  </button>
                  <button
                    onClick={handlePrint}
                    className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white flex items-center gap-1.5 shadow-lg shadow-blue-900/30 transition"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    Download PDF / Print
                  </button>
                </div>
              </div>

            </div>
          ) : null}

        </div>
      </div>
    </div>
  );
}

function ChecklistItem({
  title,
  status,
  details,
  isAvailable,
}: {
  title: string;
  status: string;
  details: string;
  isAvailable: boolean;
}) {
  return (
    <div
      className={`p-3 rounded-xl border transition flex items-start gap-3 ${
        isAvailable
          ? "bg-slate-900/70 border-slate-800 hover:border-slate-700"
          : "bg-slate-950/60 border-slate-900/90"
      }`}
    >
      <div className="mt-0.5">
        {isAvailable ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-amber-400" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold text-slate-200 truncate">{title}</span>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0 ${
              isAvailable
                ? "bg-emerald-950/80 border-emerald-800 text-emerald-300"
                : "bg-amber-950/80 border-amber-800 text-amber-300"
            }`}
          >
            {status}
          </span>
        </div>
        <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{details}</p>
      </div>
    </div>
  );
}

function EmptySectionMessage({ message }: { message: string }) {
  return (
    <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-400 flex items-center gap-2.5 print:border-black print:bg-white print:text-slate-600">
      <AlertTriangle className="w-4 h-4 text-amber-400/80 shrink-0 print:text-black" />
      <span>{message}</span>
    </div>
  );
}
