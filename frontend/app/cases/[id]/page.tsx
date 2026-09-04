"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  FolderGit2,
  ArrowLeft,
  Calendar,
  MapPin,
  Shield,
  Building,
  Clock,
  UserCheck,
  Edit3,
  Check,
  AlertCircle,
  Loader2,
  Save,
  Upload,
  FileText,
  Download,
  FileCheck,
  Hash,
  Copy,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  File,
  Sparkles,
  Network,
  GitFork,
  ExternalLink,
  Tag,
  History,
  CalendarDays,
  Plus,
  Compass,
} from "lucide-react";
import Navbar from "../../../components/Navbar";
import {
  CaseItem,
  DocumentItem,
  getCaseDetail,
  updateCase,
  getCurrentUser,
  UserProfile,
  getStoredToken,
  getCaseDocuments,
  uploadCaseDocument,
  downloadDocumentFile,
  processCaseDocument,
  getCaseCorrelations,
  CorrelationResult,
  getCaseTimeline,
  createTimelineEvent,
  TimelineEventItem,
} from "../../../lib/api";

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<CaseItem | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);

  // Edit mode
  const [isEditing, setIsEditing] = useState(false);
  const [editStatus, setEditStatus] = useState<string>("UNDER_INVESTIGATION");
  const [editPriority, setEditPriority] = useState<string>("HIGH");
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editLocation, setEditLocation] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Document Upload State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // AI Pipeline Processing State
  const [processingDocId, setProcessingDocId] = useState<number | null>(null);
  const [inspectDoc, setInspectDoc] = useState<DocumentItem | null>(null);
  const [inspectTab, setInspectTab] = useState<"entities" | "text" | "translation">("entities");

  // Cross-FIR Correlation State (Phase 7)
  const [correlations, setCorrelations] = useState<CorrelationResult[]>([]);
  const [correlationsLoading, setCorrelationsLoading] = useState(false);

  // Investigation Timeline State (Phase 8)
  const [timelineEvents, setTimelineEvents] = useState<TimelineEventItem[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineOrder, setTimelineOrder] = useState<"asc" | "desc">("asc");
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);
  const [milestoneTitle, setMilestoneTitle] = useState("");
  const [milestoneDesc, setMilestoneDesc] = useState("");
  const [milestoneDate, setMilestoneDate] = useState("");
  const [milestoneType, setMilestoneType] = useState("INVESTIGATION_EVENT");
  const [milestoneLocation, setMilestoneLocation] = useState("");
  const [milestoneDocId, setMilestoneDocId] = useState<string>("");
  const [creatingMilestone, setCreatingMilestone] = useState(false);

  const fetchCorrelations = async () => {
    setCorrelationsLoading(true);
    try {
      const data = await getCaseCorrelations(caseId, 0.25);
      setCorrelations(data.correlations || []);
    } catch (err: any) {
      console.error("Failed to load correlations:", err);
    } finally {
      setCorrelationsLoading(false);
    }
  };

  const fetchTimeline = async (order: "asc" | "desc" = timelineOrder) => {
    setTimelineLoading(true);
    try {
      const data = await getCaseTimeline(caseId, order);
      setTimelineEvents(data.events || []);
    } catch (err: any) {
      console.error("Failed to load timeline:", err);
    } finally {
      setTimelineLoading(false);
    }
  };

  const handleCreateMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!milestoneTitle.trim() || !milestoneDate) return;
    setCreatingMilestone(true);
    try {
      await createTimelineEvent(caseId, {
        title: milestoneTitle.trim(),
        description: milestoneDesc.trim() || undefined,
        event_date: new Date(milestoneDate).toISOString(),
        event_type: milestoneType,
        location: milestoneLocation.trim() || undefined,
        source_document_id: milestoneDocId ? Number(milestoneDocId) : undefined,
      });
      setShowMilestoneModal(false);
      setMilestoneTitle("");
      setMilestoneDesc("");
      setMilestoneLocation("");
      fetchTimeline();
    } catch (err: any) {
      alert(err.message || "Failed to record milestone");
    } finally {
      setCreatingMilestone(false);
    }
  };

  const handleProcessDoc = async (docId: number) => {
    setProcessingDocId(docId);
    setError(null);
    try {
      await processCaseDocument(docId);
      await fetchDocuments();
      await fetchCase();
      await fetchCorrelations();
      await fetchTimeline();
    } catch (err: any) {
      setError(err.message || "Failed to process document with AI pipeline");
    } finally {
      setProcessingDocId(null);
    }
  };

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

  const fetchCase = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCaseDetail(caseId);
      setCaseData(data);
      setEditStatus(data.status);
      setEditPriority(data.priority);
      setEditTitle(data.title);
      setEditDescription(data.description || "");
      setEditLocation(data.location || "");
      // Fetch documents, correlations & timeline for this case
      fetchDocuments();
      fetchCorrelations();
      fetchTimeline();
    } catch (err: any) {
      setError(err.message || "Failed to load case");
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    setDocumentsLoading(true);
    try {
      const docs = await getCaseDocuments(caseId);
      setDocuments(docs);
    } catch (err: any) {
      console.error("Failed to load documents:", err);
    } finally {
      setDocumentsLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
    fetchCase();
  }, [caseId]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateCase(caseId, {
        title: editTitle,
        description: editDescription,
        status: editStatus,
        priority: editPriority,
        location: editLocation,
      });
      setCaseData(updated);
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to update case");
    } finally {
      setSaving(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.split(".").pop()?.toLowerCase();
      const validExts = ["pdf", "jpg", "jpeg", "png"];

      if (!validExts.includes(ext || "")) {
        setUploadError("Invalid file type. Only PDF, JPG, JPEG, and PNG files are accepted.");
        setSelectedFile(null);
        return;
      }

      if (file.size > 50 * 1024 * 1024) {
        setUploadError("File size exceeds the 50MB limit.");
        setSelectedFile(null);
        return;
      }

      if (file.size === 0) {
        setUploadError("File is empty (0 bytes).");
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError("Please select an FIR document to upload.");
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const doc = await uploadCaseDocument(caseId, selectedFile, (percent) => {
        setUploadProgress(percent);
      });
      setUploadSuccess(`FIR document '${doc.original_filename}' uploaded and verified successfully!`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setTimeout(() => {
        setShowUploadModal(false);
        setUploadSuccess(null);
      }, 2000);
      fetchDocuments();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (doc: DocumentItem) => {
    try {
      await downloadDocumentFile(doc.id, doc.original_filename);
    } catch (err: any) {
      alert(err.message || "Download failed");
    }
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2500);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getProcessingStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950/80 border border-emerald-700 text-emerald-300">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            COMPLETED
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-950/80 border border-blue-700 text-blue-300">
            <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
            PROCESSING
          </span>
        );
      case "FAILED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-red-950/80 border border-red-700 text-red-300">
            <XCircle className="w-3 h-3 text-red-400" />
            FAILED
          </span>
        );
      case "PENDING":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-950/80 border border-amber-700 text-amber-300">
            <Clock className="w-3 h-3 text-amber-400" />
            PENDING
          </span>
        );
    }
  };

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

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-slate-100">
      <Navbar user={user} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center justify-between">
          <Link
            href="/cases"
            className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Case Directory
          </Link>

          {caseData && !isEditing && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition"
              >
                <Upload className="w-3.5 h-3.5" />
                Upload FIR Document
              </button>
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
              >
                <Edit3 className="w-3.5 h-3.5 text-blue-400" />
                Update Metadata
              </button>
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-900/50 flex items-center gap-3 text-xs text-red-300">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <div>
              <p className="font-semibold text-red-200">Error</p>
              <p className="mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {saveSuccess && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-900/50 flex items-center gap-2 text-xs text-emerald-300">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            Case metadata updated successfully via PATCH /api/v1/cases/{caseId}
          </div>
        )}

        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p className="text-xs">Loading case dossier...</p>
          </div>
        ) : !caseData ? (
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-12 text-center">
            <p className="text-sm text-slate-400">Case record could not be loaded.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header Card */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold px-3 py-1 rounded-lg bg-blue-950 border border-blue-800 text-blue-300">
                    {caseData.case_number}
                  </span>
                  <span className={`text-xs font-bold px-3 py-1 rounded-lg border ${getStatusBadge(caseData.status)}`}>
                    {caseData.status.replace("_", " ")}
                  </span>
                  <span className="text-xs font-bold px-3 py-1 rounded-lg border border-slate-700 bg-slate-800/80 text-slate-300">
                    Priority: {caseData.priority}
                  </span>
                </div>

                <div className="text-[11px] text-slate-400 font-mono">
                  Created: {new Date(caseData.created_at).toLocaleString()}
                </div>
              </div>

              {isEditing ? (
                <div className="space-y-4 pt-2 border-t border-slate-800">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Case Title</label>
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Description / Summary</label>
                    <textarea
                      rows={3}
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Status</label>
                      <select
                        value={editStatus}
                        onChange={(e) => setEditStatus(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                      >
                        <option value="OPEN">OPEN</option>
                        <option value="UNDER_INVESTIGATION">UNDER_INVESTIGATION</option>
                        <option value="PENDING_REVIEW">PENDING_REVIEW</option>
                        <option value="CLOSED">CLOSED</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Priority</label>
                      <select
                        value={editPriority}
                        onChange={(e) => setEditPriority(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                      >
                        <option value="LOW">LOW</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="HIGH">HIGH</option>
                        <option value="CRITICAL">CRITICAL</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Location</label>
                      <input
                        type="text"
                        value={editLocation}
                        onChange={(e) => setEditLocation(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white disabled:opacity-50"
                    >
                      {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                      Save Updates
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <h1 className="text-xl font-bold text-white tracking-tight">{caseData.title}</h1>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {caseData.description || "No detailed summary provided for this investigation."}
                  </p>
                </div>
              )}
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <Shield className="w-3.5 h-3.5 text-blue-400" />
                  Crime Type
                </span>
                <p className="text-xs font-semibold text-slate-200">{caseData.crime_type}</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <MapPin className="w-3.5 h-3.5 text-red-400" />
                  Jurisdiction / Location
                </span>
                <p className="text-xs font-semibold text-slate-200">{caseData.location || "Jurisdiction Wide"}</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <Building className="w-3.5 h-3.5 text-purple-400" />
                  Police Station
                </span>
                <p className="text-xs font-semibold text-slate-200">{caseData.police_station || "State Cell"}</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                  Incident Date
                </span>
                <p className="text-xs font-semibold text-slate-200">
                  {caseData.incident_date ? new Date(caseData.incident_date).toLocaleDateString() : "Not Specified"}
                </p>
              </div>
            </div>

            {/* Ownership & Audit Information */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400 font-mono">
              <div className="flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-blue-400" />
                <span>Assigned / Creator: <strong className="text-slate-200 font-sans">{caseData.created_by || `Officer #${caseData.assigned_officer_id}`}</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-slate-500" />
                <span>Last Updated: {new Date(caseData.updated_at).toLocaleString()}</span>
              </div>
            </div>

            {/* FIR Document Management Section (Phase 4) */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-blue-950/70 border border-blue-800/50 text-blue-400">
                    <FileCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      FIR Documents & Evidence Vault
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                        {documents.length}
                      </span>
                    </h2>
                    <p className="text-[11px] text-slate-400">
                      Immutable document storage with SHA-256 integrity validation and version tracking.
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setShowUploadModal(true)}
                  className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Upload FIR
                </button>
              </div>

              {/* Document List Table */}
              {documentsLoading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                  <p className="text-xs">Fetching registered FIR documents...</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="border border-dashed border-slate-800 rounded-xl p-8 text-center space-y-3 bg-slate-950/40">
                  <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center mx-auto text-slate-400">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-300">No FIR Documents Uploaded</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Upload an FIR scan (PDF, JPG, PNG) to securely attach immutable evidence to this case.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-blue-400 border border-slate-700 transition"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    Upload First FIR
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-mono text-[10px] tracking-wider">
                      <tr>
                        <th className="py-3 px-4">Document / File</th>
                        <th className="py-3 px-4">Size & Type</th>
                        <th className="py-3 px-4">SHA-256 Fingerprint</th>
                        <th className="py-3 px-4">Processing Status</th>
                        <th className="py-3 px-4">Upload Timestamp</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                      {documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-slate-800/40 transition">
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-2.5">
                              <div className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-blue-400">
                                <FileText className="w-4 h-4" />
                              </div>
                              <div>
                                <p className="font-semibold text-slate-200">{doc.original_filename}</p>
                                <p className="text-[10px] text-slate-500 font-mono">v{doc.versions?.length || 1} • Immutable Record #{doc.id}</p>
                              </div>
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-slate-300">
                            <span className="font-mono text-[11px]">{formatFileSize(doc.file_size_bytes)}</span>
                            <span className="block text-[10px] text-slate-500 uppercase">{doc.mime_type?.split("/")[1] || "BINARY"}</span>
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono text-[10px] bg-slate-950 border border-slate-800 px-2 py-1 rounded text-slate-400 max-w-[140px] truncate" title={doc.sha256_hash}>
                                {doc.sha256_hash.substring(0, 16)}...
                              </span>
                              <button
                                onClick={() => copyHash(doc.sha256_hash)}
                                title="Copy Full SHA-256 Hash"
                                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
                              >
                                {copiedHash === doc.sha256_hash ? (
                                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          </td>
                          <td className="py-3.5 px-4">
                            {getProcessingStatusBadge(doc.processing_status)}
                          </td>
                          <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                            {new Date(doc.created_at).toLocaleString()}
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              {doc.processing_status === "COMPLETED" ? (
                                <button
                                  onClick={() => {
                                    setInspectDoc(doc);
                                    setInspectTab("entities");
                                  }}
                                  className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-md bg-blue-950/70 hover:bg-blue-900/80 text-blue-300 border border-blue-800 transition"
                                  title="Inspect extracted entities and intelligence"
                                >
                                  <Sparkles className="w-3 h-3 text-blue-400" />
                                  Inspect AI
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleProcessDoc(doc.id)}
                                  disabled={processingDocId === doc.id || doc.processing_status === "PROCESSING"}
                                  className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-md bg-indigo-950/70 hover:bg-indigo-900/80 text-indigo-300 border border-indigo-800 transition disabled:opacity-50"
                                  title="Run Document AI Pipeline"
                                >
                                  {processingDocId === doc.id ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <Sparkles className="w-3 h-3 text-indigo-400" />
                                  )}
                                  Run AI
                                </button>
                              )}
                              <button
                                onClick={() => handleDownload(doc)}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                                title="Download original verified file"
                              >
                                <Download className="w-3 h-3 text-slate-400" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Cross-FIR Potential Correlations Section (Phase 7) */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-purple-950/70 border border-purple-800/50 text-purple-400">
                    <Network className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      Cross-FIR Potential Correlations
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-950 border border-purple-800 text-purple-300 font-mono">
                        {correlations.length} Detected
                      </span>
                    </h2>
                    <p className="text-[11px] text-slate-400">
                      Explainable multi-dimensional intelligence linking shared suspects, phone numbers, vehicles, locations, and crime patterns.
                    </p>
                  </div>
                </div>

                <button
                  onClick={fetchCorrelations}
                  disabled={correlationsLoading}
                  className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700 transition"
                >
                  {correlationsLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <GitFork className="w-3.5 h-3.5" />
                  )}
                  <span>Re-analyze Correlations</span>
                </button>
              </div>

              {/* Legal / Ethical Guardrail Notice */}
              <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl flex items-start gap-2.5 text-[11px] text-slate-400">
                <Shield className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-slate-200">Investigative Guardrail Notice:</strong> The engine identifies potential correlation links based on shared entity identifiers, spatial-temporal proximity, and semantic similarity. Automated systems never establish guilt or legal liability.
                </p>
              </div>

              {correlationsLoading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
                  <p className="text-xs">Correlating across authorized investigation dossiers...</p>
                </div>
              ) : correlations.length === 0 ? (
                <div className="border border-dashed border-slate-800 rounded-xl p-8 text-center space-y-2 bg-slate-950/40">
                  <Network className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-xs font-semibold text-slate-300">No Significant Cross-Case Correlations Detected</p>
                  <p className="text-[11px] text-slate-500 max-w-md mx-auto">
                    No other authorized cases currently share critical identifiers (phone numbers, vehicles, suspect names, locations) with this FIR.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {correlations.map((corr, idx) => {
                    const score = corr.correlation_score;
                    const scoreBadge =
                      score >= 0.70
                        ? "bg-emerald-950/80 border-emerald-700 text-emerald-300"
                        : score >= 0.40
                        ? "bg-amber-950/80 border-amber-700 text-amber-300"
                        : "bg-slate-800 border-slate-700 text-slate-300";

                    return (
                      <div
                        key={idx}
                        className="p-5 bg-slate-950/70 border border-slate-800 rounded-xl hover:border-slate-700 transition space-y-3"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-mono text-xs font-bold text-blue-400">
                                {corr.related_case.case_number}
                              </span>
                              <span className="text-slate-500">•</span>
                              <h3 className="text-sm font-semibold text-white">
                                {corr.related_case.title}
                              </h3>
                            </div>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                              {corr.related_case.crime_type}
                            </span>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className={`text-xs font-bold px-3 py-1 rounded-lg border font-mono ${scoreBadge}`}>
                              Correlation Score: {score.toFixed(2)}
                            </span>
                            <Link
                              href={`/cases/${corr.related_case.id}`}
                              className="flex items-center gap-1 text-xs font-medium text-blue-400 hover:text-blue-300 px-3 py-1 bg-blue-950/40 border border-blue-800/50 rounded-lg transition"
                            >
                              <span>Inspect Case</span>
                              <ExternalLink className="w-3 h-3" />
                            </Link>
                          </div>
                        </div>

                        {/* Matching Factors */}
                        {corr.matching_factors.length > 0 && (
                          <div className="space-y-1.5 pt-1">
                            <span className="text-[10px] font-mono uppercase text-slate-500 block">
                              Key Correlation Reasons:
                            </span>
                            <ul className="grid grid-cols-1 md:grid-cols-2 gap-1 text-xs text-slate-300">
                              {corr.matching_factors.map((factor, fIdx) => (
                                <li key={fIdx} className="flex items-center gap-1.5">
                                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 shrink-0" />
                                  <span>{factor}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Shared Entity Badges */}
                        {corr.matching_entities.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1.5 pt-1">
                            <span className="text-[10px] font-mono text-slate-500 mr-1">Shared Identifiers:</span>
                            {corr.matching_entities.map((me, meIdx) => (
                              <span
                                key={meIdx}
                                className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700 text-slate-300 font-mono"
                              >
                                <Tag className="w-3 h-3 text-purple-400" />
                                <strong className="text-purple-300">{me.entity_type}:</strong>
                                <span>{me.source_value}</span>
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Explainable Narrative Box */}
                        <div className="mt-2 bg-slate-900/60 p-3 rounded-lg border border-slate-800/60 text-xs font-mono text-slate-300 whitespace-pre-line leading-relaxed">
                          {corr.explanation}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Investigation Timeline Section (Phase 8) */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-blue-950/70 border border-blue-800/50 text-blue-400">
                    <History className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      Investigation Timeline
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-950 border border-blue-800 text-blue-300 font-mono">
                        {timelineEvents.length} Events
                      </span>
                    </h2>
                    <p className="text-[11px] text-slate-400">
                      Chronological chain-of-events synthesized from authorized FIR registration, evidence uploads, AI extractions, and investigation logs.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      const nextOrder = timelineOrder === "asc" ? "desc" : "asc";
                      setTimelineOrder(nextOrder);
                      fetchTimeline(nextOrder);
                    }}
                    className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                  >
                    <CalendarDays className="w-3.5 h-3.5 text-blue-400" />
                    <span>Order: {timelineOrder === "asc" ? "Earliest First" : "Latest First"}</span>
                  </button>

                  <button
                    onClick={() => setShowMilestoneModal(true)}
                    className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Log Milestone</span>
                  </button>
                </div>
              </div>

              {/* Source-grounded verification banner */}
              <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl flex items-center gap-2 text-[11px] text-slate-400">
                <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  <strong className="text-slate-200">Zero-Hallucination Grounding:</strong> Every timeline event is backed by an authentic source document, case record, or logged officer milestone.
                </span>
              </div>

              {/* Vertical Timeline */}
              {timelineLoading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                  <p className="text-xs">Synthesizing chronological investigation events...</p>
                </div>
              ) : timelineEvents.length === 0 ? (
                <div className="border border-dashed border-slate-800 rounded-xl p-8 text-center space-y-2 bg-slate-950/40">
                  <History className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-xs font-semibold text-slate-300">No Timeline Events Recorded</p>
                </div>
              ) : (
                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
                  {timelineEvents.map((evt, idx) => {
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

                    const styles = getEventTypeStyles(evt.event_type);

                    return (
                      <div key={evt.id || idx} className="relative group">
                        {/* Dot indicator */}
                        <div
                          className={`absolute -left-[27px] top-1.5 w-3 h-3 rounded-full ${styles.dot} ring-4 transition group-hover:scale-125`}
                        />

                        {/* Event Card */}
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

                          {/* Source Attribution Tag */}
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
              )}
            </div>
          </div>
        )}

        {/* Milestone Logging Modal */}
        {showMilestoneModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-blue-950 border border-blue-800 text-blue-400">
                    <History className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Log Official Investigation Milestone</h3>
                    <p className="text-[11px] text-slate-400">Record verified field actions, statements, or seizures</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowMilestoneModal(false)}
                  className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateMilestone} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Event Title <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={milestoneTitle}
                    onChange={(e) => setMilestoneTitle(e.target.value)}
                    placeholder="e.g. Witness Statement Recorded / Suspect Vehicle Seized"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Event Type <span className="text-red-400">*</span>
                    </label>
                    <select
                      value={milestoneType}
                      onChange={(e) => setMilestoneType(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                    >
                      <option value="INVESTIGATION_EVENT">INVESTIGATION_EVENT</option>
                      <option value="WITNESS_STATEMENT">WITNESS_STATEMENT</option>
                      <option value="SEIZURE">SEIZURE</option>
                      <option value="ARREST">ARREST</option>
                      <option value="FORENSIC_EXAM">FORENSIC_EXAM</option>
                      <option value="COURT_FILING">COURT_FILING</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Event Date & Time <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={milestoneDate}
                      onChange={(e) => setMilestoneDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Location / Jurisdictional Station
                  </label>
                  <input
                    type="text"
                    value={milestoneLocation}
                    onChange={(e) => setMilestoneLocation(e.target.value)}
                    placeholder="e.g. Cyber Crime Police Station, Delhi"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Source Document Attachment (Optional)
                  </label>
                  <select
                    value={milestoneDocId}
                    onChange={(e) => setMilestoneDocId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                  >
                    <option value="">No linked document (Direct Officer Log)</option>
                    {documents.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.original_filename} (Doc #{d.id})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Description & Narrative Notes
                  </label>
                  <textarea
                    rows={3}
                    value={milestoneDesc}
                    onChange={(e) => setMilestoneDesc(e.target.value)}
                    placeholder="Provide detailed context, witness names, or seizure memo numbers..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowMilestoneModal(false)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creatingMilestone}
                    className="flex items-center gap-1 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white disabled:opacity-50"
                  >
                    {creatingMilestone ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                    <span>Record Milestone</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-blue-950 border border-blue-800 text-blue-400">
                    <Upload className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Upload FIR Document</h3>
                    <p className="text-[11px] text-slate-400">Attach digital evidence to case {caseData?.case_number}</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (!uploading) {
                      setShowUploadModal(false);
                      setUploadError(null);
                      setUploadSuccess(null);
                    }
                  }}
                  disabled={uploading}
                  className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800 transition disabled:opacity-40"
                >
                  ✕
                </button>
              </div>

              {uploadError && (
                <div className="p-3 rounded-xl bg-red-950/50 border border-red-900/60 flex items-center gap-2.5 text-xs text-red-300">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              {uploadSuccess && (
                <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-900/60 flex items-center gap-2.5 text-xs text-emerald-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              {/* Dropzone Area */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition bg-slate-950/60 hover:bg-slate-950/90 group"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="w-12 h-12 rounded-full bg-slate-800 group-hover:bg-blue-950/70 flex items-center justify-center mx-auto text-slate-400 group-hover:text-blue-400 transition mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                {selectedFile ? (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-blue-400">{selectedFile.name}</p>
                    <p className="text-[11px] text-slate-400 font-mono">{formatFileSize(selectedFile.size)}</p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-slate-200">
                      Click to browse or drag and drop FIR scan
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Supported: PDF, JPG, JPEG, PNG (Max 50MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Upload Progress Bar */}
              {uploading && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Uploading & Computing SHA-256...</span>
                    <span className="font-mono font-semibold text-blue-400">{uploadProgress}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-200 rounded-full"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  onClick={() => setShowUploadModal(false)}
                  disabled={uploading}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!selectedFile || uploading}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-lg shadow-blue-500/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-3.5 h-3.5" />
                      Upload & Register
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Inspect AI Intelligence Modal */}
        {inspectDoc && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
              {/* Modal Header */}
              <div className="p-5 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-950 border border-blue-800 text-blue-400">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      Document AI Intelligence
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300">
                        {inspectDoc.original_filename}
                      </span>
                    </h3>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400">
                      <span>Language: <strong className="text-slate-200">{inspectDoc.detected_language || "English"}</strong> ({Math.round((inspectDoc.language_confidence || 0.95) * 100)}%)</span>
                      <span>•</span>
                      <span>OCR: <strong className="text-slate-200">{inspectDoc.ocr_engine || "Hybrid-OCR"}</strong> ({Math.round((inspectDoc.ocr_confidence || 0.90) * 100)}%)</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setInspectDoc(null)}
                  className="text-slate-400 hover:text-white text-xs px-2.5 py-1.5 rounded-lg hover:bg-slate-800 transition"
                >
                  ✕ Close
                </button>
              </div>

              {/* Tabs Navigation */}
              <div className="flex border-b border-slate-800 bg-slate-950/60 px-5 pt-2 gap-2 text-xs">
                <button
                  onClick={() => setInspectTab("entities")}
                  className={`px-4 py-2 font-medium border-b-2 transition ${
                    inspectTab === "entities"
                      ? "border-blue-500 text-blue-400 font-semibold"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Extracted Entities ({inspectDoc.entities?.length || 0})
                </button>
                <button
                  onClick={() => setInspectTab("text")}
                  className={`px-4 py-2 font-medium border-b-2 transition ${
                    inspectTab === "text"
                      ? "border-blue-500 text-blue-400 font-semibold"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Original OCR Text (Raw)
                </button>
                <button
                  onClick={() => setInspectTab("translation")}
                  className={`px-4 py-2 font-medium border-b-2 transition ${
                    inspectTab === "translation"
                      ? "border-blue-500 text-blue-400 font-semibold"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  English Translation {inspectDoc.translations?.length ? `(${inspectDoc.translations[0].source_language} → English)` : ""}
                </button>
              </div>

              {/* Tab Contents */}
              <div className="flex-1 overflow-y-auto p-5 text-xs space-y-4">
                {inspectTab === "entities" && (
                  <div className="space-y-4">
                    {!inspectDoc.entities || inspectDoc.entities.length === 0 ? (
                      <p className="text-slate-400 py-8 text-center">No entities extracted from this document.</p>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {inspectDoc.entities.map((ent, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5 hover:border-slate-700 transition"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800 text-blue-300 uppercase">
                                {ent.entity_type}
                              </span>
                              <span className="text-[10px] font-mono text-slate-500">
                                {Math.round(ent.confidence * 100)}% conf
                              </span>
                            </div>
                            <p className="text-sm font-semibold text-white tracking-wide">
                              {ent.normalized_value || ent.entity_value}
                            </p>
                            {ent.context_snippet && (
                              <p className="text-[10px] text-slate-400 italic bg-slate-900/60 p-1.5 rounded">
                                {ent.context_snippet}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {inspectTab === "text" && (
                  <div className="space-y-2">
                    <div className="p-2 rounded bg-amber-950/30 border border-amber-900/40 text-[11px] text-amber-300">
                      Immutable verbatim OCR text as extracted by {inspectDoc.ocr_engine || "OCR Engine"}. Never overwritten.
                    </div>
                    <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs whitespace-pre-wrap leading-relaxed max-h-[45vh] overflow-y-auto">
                      {inspectDoc.original_text || "No OCR text available."}
                    </pre>
                  </div>
                )}

                {inspectTab === "translation" && (
                  <div className="space-y-2">
                    {inspectDoc.translations && inspectDoc.translations.length > 0 ? (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span>Translated from <strong className="text-slate-200">{inspectDoc.translations[0].source_language}</strong> to <strong className="text-slate-200">English</strong></span>
                          <span className="font-mono text-[10px] text-slate-500">{inspectDoc.translations[0].translator_model}</span>
                        </div>
                        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs whitespace-pre-wrap leading-relaxed max-h-[45vh] overflow-y-auto">
                          {inspectDoc.translations[0].translated_text}
                        </div>
                      </div>
                    ) : inspectDoc.detected_language === "English" ? (
                      <div className="p-6 rounded-xl bg-slate-950/50 border border-slate-800 text-center text-slate-400">
                        <p className="font-semibold text-slate-300">Document language is native English.</p>
                        <p className="text-[11px] mt-1 text-slate-500">No secondary translation required for this record.</p>
                      </div>
                    ) : (
                      <p className="text-slate-400 py-8 text-center">Translation pending or not required.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
