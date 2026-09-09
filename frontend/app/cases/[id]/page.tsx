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
  Lock,
  Unlock,
  Send,
  Inbox,
  Microscope,
  FileCheck2,
  RotateCcw,
  Landmark,
  ShieldCheck,
  ShieldAlert,
  Layers,
  Eye,
  Activity,
  Scale,
} from "lucide-react";
import Navbar from "../../../components/Navbar";
import CourtPackageModal from "../../../components/CourtPackageModal";
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
  EvidenceItem,
  CustodyEventItem,
  CustodyChainResponse,
  IntegrityVerificationResult,
  CourtEvidencePackageOut,
  getLatestCourtPackage,
  getCaseEvidence,
  addCaseEvidence,
  getCustodyChain,
  sealEvidence,
  transferEvidence,
  receiveEvidence,
  startExamination,
  completeExamination,
  attachForensicReport,
  returnEvidence,
  submitToCourt,
  verifyEvidenceIntegrity,
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

  // Cross-FIR Correlation State
  const [correlations, setCorrelations] = useState<CorrelationResult[]>([]);
  const [correlationsLoading, setCorrelationsLoading] = useState(false);

  // Investigation Timeline State
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

  // Digital Chain of Custody State (Part 1)
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [showAddEvidenceModal, setShowAddEvidenceModal] = useState(false);
  const [evTitle, setEvTitle] = useState("");
  const [evDescription, setEvDescription] = useState("");
  const [evType, setEvType] = useState("DIGITAL_FILE");
  const [evLocation, setEvLocation] = useState("");
  const [evNotes, setEvNotes] = useState("");
  const [evFile, setEvFile] = useState<File | null>(null);
  const [addingEvidence, setAddingEvidence] = useState(false);

  // Custody Chain View Modal
  const [custodyChainData, setCustodyChainData] = useState<CustodyChainResponse | null>(null);
  const [loadingCustodyChain, setLoadingCustodyChain] = useState(false);
  const [showChainModal, setShowChainModal] = useState(false);

  // Integrity Verification Modal
  const [integrityData, setIntegrityData] = useState<IntegrityVerificationResult | null>(null);
  const [verifyingIntegrity, setVerifyingIntegrity] = useState(false);

  // Custody Workflow Transition Modal State
  const [activeTransition, setActiveTransition] = useState<{
    item: EvidenceItem;
    action: "SEAL" | "TRANSFER" | "RECEIVE" | "START_EXAM" | "COMPLETE_EXAM" | "REPORT" | "RETURN" | "COURT";
  } | null>(null);
  const [transField1, setTransField1] = useState("");
  const [transField2, setTransField2] = useState("");
  const [transNotes, setTransNotes] = useState("");
  const [transFile, setTransFile] = useState<File | null>(null);
  const [submittingTransition, setSubmittingTransition] = useState(false);

  // Court Evidence Package State
  const [showCourtPackageModal, setShowCourtPackageModal] = useState(false);
  const [courtPackageMode, setCourtPackageMode] = useState<"review" | "viewer">("review");
  const [latestCourtPackage, setLatestCourtPackage] = useState<CourtEvidencePackageOut | null>(null);

  const fetchLatestCourtPackage = async () => {
    try {
      const pkg = await getLatestCourtPackage(caseId);
      setLatestCourtPackage(pkg);
    } catch {
      // Package may not exist yet
    }
  };

  const fetchEvidence = async () => {
    setEvidenceLoading(true);
    try {
      const data = await getCaseEvidence(caseId);
      setEvidenceList(data);
    } catch (err: any) {
      console.error("Failed to load case evidence:", err);
    } finally {
      setEvidenceLoading(false);
    }
  };

  const handleAddEvidenceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evTitle.trim()) return;
    setAddingEvidence(true);
    try {
      const formData = new FormData();
      formData.append("title", evTitle.trim());
      if (evDescription) formData.append("description", evDescription.trim());
      formData.append("evidence_type", evType);
      if (evLocation) formData.append("collection_location", evLocation.trim());
      if (evNotes) formData.append("notes", evNotes.trim());
      if (evFile) formData.append("file", evFile);

      await addCaseEvidence(caseId, formData);
      setShowAddEvidenceModal(false);
      setEvTitle("");
      setEvDescription("");
      setEvLocation("");
      setEvNotes("");
      setEvFile(null);
      await fetchEvidence();
      await fetchTimeline();
    } catch (err: any) {
      alert(err.message || "Failed to register evidence");
    } finally {
      setAddingEvidence(false);
    }
  };

  const handleOpenChainModal = async (evidenceId: number) => {
    setShowChainModal(true);
    setLoadingCustodyChain(true);
    setCustodyChainData(null);
    try {
      const chain = await getCustodyChain(caseId, evidenceId);
      setCustodyChainData(chain);
    } catch (err: any) {
      alert(err.message || "Failed to load chain of custody");
      setShowChainModal(false);
    } finally {
      setLoadingCustodyChain(false);
    }
  };

  const handleVerifyIntegrity = async (evidenceId: number) => {
    setVerifyingIntegrity(true);
    setIntegrityData(null);
    try {
      const res = await verifyEvidenceIntegrity(caseId, evidenceId);
      setIntegrityData(res);
      await fetchEvidence();
    } catch (err: any) {
      alert(err.message || "Integrity verification failed");
    } finally {
      setVerifyingIntegrity(false);
    }
  };

  const handleExecuteTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTransition) return;
    setSubmittingTransition(true);
    const { item, action } = activeTransition;
    try {
      if (action === "SEAL") {
        await sealEvidence(caseId, item.id, { reason: transField1 || undefined, notes: transNotes || undefined });
      } else if (action === "TRANSFER") {
        await transferEvidence(caseId, item.id, { to_custodian: transField1, location: transField2 || undefined, notes: transNotes || undefined });
      } else if (action === "RECEIVE") {
        await receiveEvidence(caseId, item.id, { received_by: transField1 || undefined, location: transField2 || undefined, condition_notes: transNotes || undefined });
      } else if (action === "START_EXAM") {
        await startExamination(caseId, item.id, { examiner: transField1 || undefined, purpose: transField2 || undefined, notes: transNotes || undefined });
      } else if (action === "COMPLETE_EXAM") {
        await completeExamination(caseId, item.id, { examiner: transField1 || undefined, result_notes: transNotes || undefined });
      } else if (action === "REPORT") {
        const formData = new FormData();
        if (transField1) formData.append("report_title", transField1);
        if (transField2) formData.append("findings", transField2);
        if (transNotes) formData.append("notes", transNotes);
        if (transFile) formData.append("file", transFile);
        await attachForensicReport(caseId, item.id, formData);
      } else if (action === "RETURN") {
        await returnEvidence(caseId, item.id, { to_custodian: transField1, location: transField2 || undefined, notes: transNotes || undefined });
      } else if (action === "COURT") {
        await submitToCourt(caseId, item.id, { court_name: transField1, submission_notes: transField2 || undefined, notes: transNotes || undefined });
      }
      setActiveTransition(null);
      setTransField1("");
      setTransField2("");
      setTransNotes("");
      setTransFile(null);
      await fetchEvidence();
      await fetchTimeline();
    } catch (err: any) {
      alert(err.message || "Failed to execute custody transition");
    } finally {
      setSubmittingTransition(false);
    }
  };

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

      fetchEvidence();
      fetchDocuments();
      fetchCorrelations();
      fetchTimeline();
      fetchLatestCourtPackage();
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
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 border border-slate-700 text-slate-300">
            <Clock className="w-3 h-3 text-slate-400" />
            PENDING
          </span>
        );
    }
  };

  const getCustodyStatusBadge = (status: string) => {
    switch (status) {
      case "COLLECTED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-950/80 border border-sky-800 text-sky-300">COLLECTED</span>;
      case "SEALED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-950/80 border border-amber-800 text-amber-300">SEALED</span>;
      case "TRANSFERRED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-950/80 border border-blue-800 text-blue-300">TRANSFERRED</span>;
      case "RECEIVED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-950/80 border border-indigo-800 text-indigo-300">RECEIVED</span>;
      case "EXAMINED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-950/80 border border-purple-800 text-purple-300">EXAMINED</span>;
      case "REPORT_GENERATED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-950/80 border border-teal-800 text-teal-300">REPORT GENERATED</span>;
      case "RETURNED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-orange-950/80 border border-orange-800 text-orange-300">RETURNED</span>;
      case "COURT_SUBMITTED":
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/80 border border-emerald-700 text-emerald-300">COURT SUBMITTED</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 border border-slate-700 text-slate-300">{status}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-blue-500 selection:text-white">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/cases"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition group"
          >
            <ArrowLeft className="w-4 h-4 text-slate-500 group-hover:-translate-x-1 transition-transform" />
            Back to Case Directory
          </Link>

          {saveSuccess && (
            <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-950 border border-emerald-800 rounded-full text-xs font-semibold text-emerald-300 animate-fade-in">
              <Check className="w-3.5 h-3.5" />
              Case Dossier Updated
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-950/80 border border-red-800 flex items-center gap-3 text-xs text-red-200">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p className="text-xs font-medium">Loading case details...</p>
          </div>
        ) : !caseData ? (
          <div className="py-20 text-center space-y-3">
            <FolderGit2 className="w-12 h-12 text-slate-600 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">Case Dossier Not Found</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header Banner */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-blue-400 bg-blue-950/80 border border-blue-800/80 px-2.5 py-0.5 rounded-full">
                      {caseData.case_number}
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-slate-800 border border-slate-700 text-slate-300">
                      {caseData.status}
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-red-950/80 border border-red-800 text-red-300">
                      {caseData.priority} PRIORITY
                    </span>
                  </div>

                  {!isEditing && (
                    <div className="flex items-center justify-between gap-4">
                      <p className="text-xs text-slate-400">
                        Official FIR Investigation File • Karnataka State Police Command Network
                      </p>
                    </div>
                  )}
                </div>

                {!isEditing && (
                  <div className="flex items-center gap-2">
                    {latestCourtPackage && (
                      <button
                        onClick={() => {
                          setCourtPackageMode("viewer");
                          setShowCourtPackageModal(true);
                        }}
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition shadow-sm"
                        title="View existing Court Evidence Dossier"
                      >
                        <FileText className="w-3.5 h-3.5 text-emerald-400" />
                        View Court Package
                      </button>
                    )}

                    <button
                      onClick={() => {
                        setCourtPackageMode("review");
                        setShowCourtPackageModal(true);
                      }}
                      className="flex items-center gap-1.5 text-xs font-bold px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-md shadow-blue-900/30 transition"
                    >
                      <Scale className="w-3.5 h-3.5 text-blue-200" />
                      Generate Court Evidence Package
                    </button>

                    {user && (user.role === "ADMIN" || caseData.assigned_officer_id === user.id) && (
                      <button
                        onClick={() => setIsEditing(true)}
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                      >
                        <Edit3 className="w-3.5 h-3.5 text-blue-400" />
                        Edit Dossier
                      </button>
                    )}
                  </div>
                )}
              </div>

              {isEditing ? (
                <div className="space-y-4 pt-2 border-t border-slate-800">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Case Title</label>
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Status</label>
                      <select
                        value={editStatus}
                        onChange={(e) => setEditStatus(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                      >
                        <option value="OPEN">OPEN</option>
                        <option value="UNDER_INVESTIGATION">UNDER INVESTIGATION</option>
                        <option value="PENDING_REVIEW">PENDING REVIEW</option>
                        <option value="CLOSED">CLOSED</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                    <textarea
                      rows={3}
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            {caseData.source_record_key && (
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
                <div>
                  <h2 className="text-sm font-semibold text-white">Karnataka Police Source FIR Data</h2>
                  <p className="text-[11px] text-slate-400 mt-1">Original-source fields; unavailable values are shown as Not Available. Personnel identifiers are masked in the interface.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                  {[
                    ["District", caseData.district], ["Police unit", caseData.police_station], ["FIR year", caseData.fir_year],
                    ["FIR month", caseData.fir_month], ["FIR day", caseData.fir_day], ["FIR type", caseData.fir_type],
                    ["FIR stage", caseData.fir_stage], ["Crime group", caseData.crime_type], ["Crime head", caseData.crime_head],
                    ["Complaint mode", caseData.complaint_mode], ["Act / section", caseData.act_section], ["Place of offence", caseData.location],
                    ["Victim count", caseData.victim_count], ["Accused count", caseData.accused_count], ["Arrested count", caseData.arrested_count],
                    ["Charge-sheeted count", caseData.accused_chargesheeted_count], ["Conviction count", caseData.conviction_count],
                    ["Coordinates", caseData.latitude != null && caseData.longitude != null ? `${caseData.latitude}, ${caseData.longitude}` : undefined],
                  ].map(([label, value]) => (
                    <div key={String(label)} className="rounded-lg bg-slate-950/70 border border-slate-800 p-3">
                      <p className="text-[10px] text-slate-500 uppercase">{label}</p>
                      <p className="text-slate-200 mt-1 break-words">{value == null || value === "" ? "Not Available" : String(value)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

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

            {/* ========================================================================= */}
            {/* PART 1 — DIGITAL CHAIN OF CUSTODY SECTION */}
            {/* ========================================================================= */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-emerald-950/70 border border-emerald-800/50 text-emerald-400">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      Digital Chain of Custody & Evidence Vault
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300 font-mono">
                        {evidenceList.length} Items Registered
                      </span>
                    </h2>
                    <p className="text-[11px] text-slate-400">
                      Immutable custody ledger, cryptographic SHA-256 integrity verification, and state transition workflow.
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setShowAddEvidenceModal(true)}
                  className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 transition"
                >
                  <Plus className="w-3.5 h-3.5" />
                  + Add Evidence
                </button>
              </div>

              {/* Evidence List View */}
              {evidenceLoading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                  <p className="text-xs">Fetching chain of custody records...</p>
                </div>
              ) : evidenceList.length === 0 ? (
                <div className="border border-dashed border-slate-800 rounded-xl p-8 text-center space-y-3 bg-slate-950/40">
                  <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center mx-auto text-slate-400">
                    <Lock className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-300 tracking-wider">NO EVIDENCE REGISTERED</p>
                    <p className="text-[11px] text-slate-500 mt-0.5 max-w-md mx-auto">
                      No digital or physical evidence items have been registered into the chain of custody for this case yet.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowAddEvidenceModal(true)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    + Add Evidence
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {evidenceList.map((item) => (
                    <div
                      key={item.id}
                      className="p-5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition space-y-4"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-2.5 py-0.5 rounded-md">
                              {item.evidence_number}
                            </span>
                            {getCustodyStatusBadge(item.status)}
                            {item.is_tampered ? (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-950/80 border border-red-700 text-red-300">
                                <ShieldAlert className="w-3 h-3 text-red-400" />
                                ⚠ TAMPERED
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/80 border border-emerald-700 text-emerald-300">
                                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                                ✓ INTEGRITY VERIFIED
                              </span>
                            )}
                          </div>
                          <h3 className="text-sm font-bold text-white tracking-wide">{item.title}</h3>
                          {item.description && (
                            <p className="text-xs text-slate-300">{item.description}</p>
                          )}
                        </div>

                        {/* Top Right Info Badges */}
                        <div className="text-right space-y-1 text-xs">
                          <div className="text-[11px] text-slate-400">
                            Current Custodian: <strong className="text-slate-200">{item.current_custodian || "Unassigned"}</strong>
                          </div>
                          <div className="text-[10px] font-mono text-slate-500">
                            Type: {item.evidence_type} {item.file_size_bytes ? `• ${formatFileSize(item.file_size_bytes)}` : ""}
                          </div>
                        </div>
                      </div>

                      {/* Details Box */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                        <div>
                          <span className="text-[10px] font-mono uppercase text-slate-500 block">Collected By:</span>
                          <span className="text-slate-300 font-semibold">{item.collected_by || "Investigating Officer"}</span>
                        </div>
                        <div>
                          <span className="text-[10px] font-mono uppercase text-slate-500 block">Collection Location:</span>
                          <span className="text-slate-300">{item.collection_location || "Field Site"}</span>
                        </div>
                        <div>
                          <span className="text-[10px] font-mono uppercase text-slate-500 block">SHA-256 Hash Digest:</span>
                          <span className="font-mono text-[10px] text-emerald-400 truncate block" title={item.sha256_hash}>
                            {item.sha256_hash}
                          </span>
                        </div>
                      </div>

                      {/* Dynamic Workflow Action Buttons */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-900">
                        <div className="flex flex-wrap items-center gap-2">
                          {/* State Transition Actions */}
                          {item.status === "COLLECTED" && (
                            <button
                              onClick={() => {
                                setActiveTransition({ item, action: "SEAL" });
                                setTransField1("Evidence secured and sealed in tamper-evident bag");
                              }}
                              className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-950/80 hover:bg-amber-900 text-amber-200 border border-amber-800 transition"
                            >
                              <Lock className="w-3.5 h-3.5 text-amber-400" />
                              Seal Evidence
                            </button>
                          )}

                          {(item.status === "SEALED" || item.status === "RETURNED") && (
                            <button
                              onClick={() => {
                                setActiveTransition({ item, action: "TRANSFER" });
                                setTransField1("State Forensic Science Laboratory");
                                setTransField2("Central Evidence Repository");
                              }}
                              className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-950/80 hover:bg-blue-900 text-blue-200 border border-blue-800 transition"
                            >
                              <Send className="w-3.5 h-3.5 text-blue-400" />
                              Transfer Evidence
                            </button>
                          )}

                          {item.status === "TRANSFERRED" && (
                            <button
                              onClick={() => {
                                setActiveTransition({ item, action: "RECEIVE" });
                                setTransField1(user?.full_name || "Receiving Custodian");
                                setTransField2("Forensic Vault Desk");
                              }}
                              className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 text-indigo-200 border border-indigo-800 transition"
                            >
                              <Inbox className="w-3.5 h-3.5 text-indigo-400" />
                              Receive Evidence
                            </button>
                          )}

                          {item.status === "RECEIVED" && (
                            <button
                              onClick={() => {
                                setActiveTransition({ item, action: "START_EXAM" });
                                setTransField1(user?.full_name || "Senior Cyber Examiner");
                                setTransField2("Forensic Extraction and Cryptographic Validation");
                              }}
                              className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-purple-950/80 hover:bg-purple-900 text-purple-200 border border-purple-800 transition"
                            >
                              <Microscope className="w-3.5 h-3.5 text-purple-400" />
                              Start Examination
                            </button>
                          )}

                          {item.status === "EXAMINED" && (
                            <>
                              <button
                                onClick={() => {
                                  setActiveTransition({ item, action: "COMPLETE_EXAM" });
                                  setTransField1(user?.full_name || "Senior Examiner");
                                }}
                                className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-purple-950/80 hover:bg-purple-900 text-purple-200 border border-purple-800 transition"
                              >
                                <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />
                                Complete Examination
                              </button>
                              <button
                                onClick={() => {
                                  setActiveTransition({ item, action: "REPORT" });
                                  setTransField1("Digital Forensic Analysis Report");
                                  setTransField2("Binary structure and SHA-256 cryptographic match confirmed.");
                                }}
                                className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-teal-950/80 hover:bg-teal-900 text-teal-200 border border-teal-800 transition"
                              >
                                <FileCheck2 className="w-3.5 h-3.5 text-teal-400" />
                                Attach Forensic Report
                              </button>
                            </>
                          )}

                          {item.status === "REPORT_GENERATED" && (
                            <button
                              onClick={() => {
                                setActiveTransition({ item, action: "RETURN" });
                                setTransField1("Investigating Officer");
                                setTransField2("Police Station Vault");
                              }}
                              className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-orange-950/80 hover:bg-orange-900 text-orange-200 border border-orange-800 transition"
                            >
                              <RotateCcw className="w-3.5 h-3.5 text-orange-400" />
                              Return Evidence
                            </button>
                          )}

                          {item.status === "RETURNED" && (
                            <button
                              onClick={() => {
                                setActiveTransition({ item, action: "COURT" });
                                setTransField1("Principal District & Sessions Court");
                                setTransField2("Entered into judicial custody record.");
                              }}
                              className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-950/80 hover:bg-emerald-900 text-emerald-200 border border-emerald-800 transition"
                            >
                              <Landmark className="w-3.5 h-3.5 text-emerald-400" />
                              Submit to Court
                            </button>
                          )}

                          {item.status === "COURT_SUBMITTED" && (
                            <span className="flex items-center gap-1 text-xs font-bold text-emerald-400 px-3 py-1.5 bg-emerald-950/60 border border-emerald-800/80 rounded-lg">
                              <Landmark className="w-3.5 h-3.5" />
                              Judicial Custody Finalized
                            </span>
                          )}
                        </div>

                        {/* Always Available Action Modals */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleOpenChainModal(item.id)}
                            className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                          >
                            <History className="w-3.5 h-3.5 text-blue-400" />
                            View Chain of Custody
                          </button>

                          <button
                            onClick={() => handleVerifyIntegrity(item.id)}
                            disabled={verifyingIntegrity}
                            className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 transition disabled:opacity-50"
                          >
                            {verifyingIntegrity ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                            )}
                            Verify Integrity
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* FIR Document Management Section */}
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

            {/* Cross-FIR Potential Correlations Section */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-purple-950/70 border border-purple-800/50 text-purple-400">
                    <Network className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      Potentially Related FIRs
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-950 border border-purple-800 text-purple-300 font-mono">
                        {correlations.length} Detected
                      </span>
                    </h2>
                    <p className="text-[11px] text-slate-400">
                      Explainable similarities based only on available FIR fields, such as crime classification, jurisdiction, time, coordinates, and FIR-field similarity.
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
                  <span>Find Similar FIRs</span>
                </button>
              </div>

              <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl flex items-start gap-2.5 text-[11px] text-slate-400">
                <Shield className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-slate-200">Investigative Guardrail Notice:</strong> Similarity scores indicate potential connections only. They are not proof of a relationship, criminal involvement, guilt, or legal liability.
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
                  <p className="text-xs font-semibold text-slate-300">No sufficiently similar FIRs were found in the available dataset</p>
                  <p className="text-[11px] text-slate-500 max-w-md mx-auto">
                    No other authorized FIRs met the evidence-based similarity threshold.
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
                            <span className="text-[10px] text-slate-500 ml-2">
                              {corr.related_case.district || "Not Available"} • {corr.related_case.fir_year || "Year Not Available"}
                              {corr.related_case.crime_head ? ` • ${corr.related_case.crime_head}` : ""}
                            </span>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className={`text-xs font-bold px-3 py-1 rounded-lg border font-mono ${scoreBadge}`}>
                              Similarity Score: {(score * 100).toFixed(0)}%
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

                        <div className="mt-2 bg-slate-900/60 p-3 rounded-lg border border-slate-800/60 text-xs font-mono text-slate-300 whitespace-pre-line leading-relaxed">
                          {corr.explanation}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Investigation Timeline Section */}
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
                      Chronological chain-of-events synthesized from authorized FIR registration, evidence uploads, AI extractions, and custody transitions.
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

              <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl flex items-center gap-2 text-[11px] text-slate-400">
                <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  <strong className="text-slate-200">Zero-Hallucination Grounding:</strong> Every timeline event is backed by an authentic source document, case record, or logged custody action.
                </span>
              </div>

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
                        case "CUSTODY_CHANGE":
                          return { badge: "bg-cyan-950/80 border-cyan-800 text-cyan-300", dot: "bg-cyan-500 ring-cyan-950" };
                        default:
                          return { badge: "bg-indigo-950/80 border-indigo-800 text-indigo-300", dot: "bg-indigo-500 ring-indigo-950" };
                      }
                    };

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
              )}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODALS SECTION */}
        {/* ========================================================================= */}

        {/* 1. Add Evidence Modal */}
        {showAddEvidenceModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-emerald-950 border border-emerald-800 text-emerald-400">
                    <Plus className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Register Evidence into Chain of Custody</h3>
                    <p className="text-[11px] text-slate-400">Generates immutable SHA-256 fingerprint & initial custody log</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowAddEvidenceModal(false)}
                  className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleAddEvidenceSubmit} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Evidence Title / Identifier <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={evTitle}
                    onChange={(e) => setEvTitle(e.target.value)}
                    placeholder="e.g. Seized Mobile Handset / Hard Disk Image / CCTV Footage"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Evidence Type</label>
                    <select
                      value={evType}
                      onChange={(e) => setEvType(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                    >
                      <option value="DIGITAL_FILE">DIGITAL FILE</option>
                      <option value="PHYSICAL_ITEM">PHYSICAL ITEM</option>
                      <option value="FORENSIC_IMAGE">FORENSIC IMAGE</option>
                      <option value="MOBILE_EXTRACTION">MOBILE EXTRACTION</option>
                      <option value="DOCUMENT">DOCUMENT</option>
                      <option value="OTHER">OTHER</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Collection Location</label>
                    <input
                      type="text"
                      value={evLocation}
                      onChange={(e) => setEvLocation(e.target.value)}
                      placeholder="e.g. Crime Scene Alpha / Vault"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                  <textarea
                    rows={2}
                    value={evDescription}
                    onChange={(e) => setEvDescription(e.target.value)}
                    placeholder="Provide serial numbers, make/model, physical condition..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Upload Real Evidence File (Optional)</label>
                  <input
                    type="file"
                    onChange={(e) => setEvFile(e.target.files?.[0] || null)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Initial Custody Notes</label>
                  <input
                    type="text"
                    value={evNotes}
                    onChange={(e) => setEvNotes(e.target.value)}
                    placeholder="Seized under formal memo and sealed."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddEvidenceModal(false)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={addingEvidence}
                    className="flex items-center gap-1 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white disabled:opacity-50"
                  >
                    {addingEvidence ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
                    <span>Register Evidence</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 2. Chain of Custody Timeline Modal */}
        {showChainModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
              <div className="p-5 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-950 border border-blue-800 text-blue-400">
                    <History className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      Immutable Chain of Custody History
                      {custodyChainData && (
                        <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300">
                          {custodyChainData.evidence_number}
                        </span>
                      )}
                    </h3>
                    <p className="text-[11px] text-slate-400">Verifiable chronological audit log of all physical and digital transfers</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowChainModal(false)}
                  className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800"
                >
                  ✕ Close
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {loadingCustodyChain ? (
                  <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                    <p className="text-xs">Reading immutable custody log...</p>
                  </div>
                ) : !custodyChainData || custodyChainData.events.length === 0 ? (
                  <div className="border border-dashed border-slate-800 rounded-xl p-8 text-center space-y-2 bg-slate-950/40">
                    <p className="text-xs font-bold text-slate-300">NO CUSTODY EVENTS AVAILABLE</p>
                    <p className="text-[11px] text-slate-500">No status transitions recorded for this item yet.</p>
                  </div>
                ) : (
                  <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-3 before:bottom-3 before:w-0.5 before:bg-blue-800">
                    {custodyChainData.events.map((evt) => (
                      <div key={evt.id} className="relative group">
                        <div className="absolute -left-[27px] top-1.5 w-3 h-3 rounded-full bg-blue-500 ring-4 ring-blue-950" />
                        <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300">
                                {evt.action.replace(/_/g, " ")}
                              </span>
                              <span className="text-xs font-bold text-white">
                                {evt.previous_status ? `${evt.previous_status} → ${evt.new_status}` : evt.new_status}
                              </span>
                            </div>
                            <span className="text-[11px] font-mono text-slate-400">
                              {new Date(evt.timestamp).toLocaleString()}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 gap-2 text-xs bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                            <div>
                              <span className="text-[10px] font-mono text-slate-500 block">Who (Actor):</span>
                              <span className="text-slate-200 font-semibold">{evt.actor_name}</span>
                            </div>
                            <div>
                              <span className="text-[10px] font-mono text-slate-500 block">Where (Location):</span>
                              <span className="text-slate-200">{evt.location || "Field / Vault"}</span>
                            </div>
                            <div>
                              <span className="text-[10px] font-mono text-slate-500 block">From:</span>
                              <span className="text-slate-300">{evt.from_custodian || "N/A"}</span>
                            </div>
                            <div>
                              <span className="text-[10px] font-mono text-slate-500 block">To:</span>
                              <span className="text-slate-300">{evt.to_custodian || "N/A"}</span>
                            </div>
                          </div>

                          {evt.reason && (
                            <p className="text-xs text-slate-300">
                              <strong className="text-slate-400">Reason / Why:</strong> {evt.reason}
                            </p>
                          )}

                          <div className="pt-2 border-t border-slate-900 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-slate-500">
                            <div>
                              <span>SHA-256 Digest: </span>
                              <span className="text-emerald-400">{evt.evidence_hash.substring(0, 16)}...</span>
                            </div>
                            <div>
                              <span>Sig: </span>
                              <span className="text-blue-400">{evt.digital_signature}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 3. Real Cryptographic Integrity Verification Result Modal */}
        {integrityData && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  {integrityData.is_valid ? (
                    <div className="p-2 rounded-lg bg-emerald-950 border border-emerald-800 text-emerald-400">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                  ) : (
                    <div className="p-2 rounded-lg bg-red-950 border border-red-800 text-red-400">
                      <ShieldAlert className="w-5 h-5" />
                    </div>
                  )}
                  <div>
                    <h3 className="text-sm font-bold text-white">SHA-256 Cryptographic Verification</h3>
                    <p className="text-[11px] font-mono text-slate-400">{integrityData.evidence_number}</p>
                  </div>
                </div>
                <button
                  onClick={() => setIntegrityData(null)}
                  className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800"
                >
                  ✕
                </button>
              </div>

              {/* Status Outcome Banner */}
              <div className={`p-4 rounded-xl border flex items-center gap-3 ${
                integrityData.is_valid
                  ? "bg-emerald-950/80 border-emerald-800 text-emerald-200"
                  : "bg-red-950/80 border-red-800 text-red-200"
              }`}>
                {integrityData.is_valid ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-400 shrink-0" />
                )}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider">{integrityData.status}</h4>
                  <p className="text-[11px] mt-0.5 opacity-90">{integrityData.message}</p>
                </div>
              </div>

              {/* Hash Comparison Table */}
              <div className="space-y-2 text-xs bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase block">Original Recorded Digest:</span>
                  <span className="text-slate-300 text-[11px] break-all">{integrityData.stored_sha256}</span>
                </div>
                <div className="pt-2 border-t border-slate-900">
                  <span className="text-[10px] text-slate-500 uppercase block">Live Disk File Digest:</span>
                  <span className={`text-[11px] break-all ${integrityData.is_valid ? "text-emerald-400" : "text-red-400 font-bold"}`}>
                    {integrityData.current_sha256}
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 pt-1">
                <span>Verified by: {integrityData.verified_by}</span>
                <span>At: {new Date(integrityData.verified_at).toLocaleTimeString()}</span>
              </div>

              <div className="flex justify-end pt-2 border-t border-slate-800">
                <button
                  onClick={() => setIntegrityData(null)}
                  className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200"
                >
                  Close Verification Window
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 4. Active Workflow Transition Action Modal */}
        {activeTransition && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-blue-950 border border-blue-800 text-blue-400">
                    <Activity className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Execute Custody Action: {activeTransition.action}</h3>
                    <p className="text-[11px] font-mono text-slate-400">{activeTransition.item.evidence_number}</p>
                  </div>
                </div>
                <button
                  onClick={() => setActiveTransition(null)}
                  className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleExecuteTransition} className="space-y-3">
                {activeTransition.action === "SEAL" && (
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Reason for Sealing</label>
                    <input
                      type="text"
                      value={transField1}
                      onChange={(e) => setTransField1(e.target.value)}
                      placeholder="Evidence secured and sealed for chain of custody"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                    />
                  </div>
                )}

                {(activeTransition.action === "TRANSFER" || activeTransition.action === "RETURN") && (
                  <>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">
                        Recipient / To Custodian <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={transField1}
                        onChange={(e) => setTransField1(e.target.value)}
                        placeholder="e.g. State Forensic Lab / Inspector V. Sharma"
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Transfer Location</label>
                      <input
                        type="text"
                        value={transField2}
                        onChange={(e) => setTransField2(e.target.value)}
                        placeholder="e.g. Forensic Intake Desk / Vault 2"
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                  </>
                )}

                {activeTransition.action === "RECEIVE" && (
                  <>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Received By Custodian Name</label>
                      <input
                        type="text"
                        value={transField1}
                        onChange={(e) => setTransField1(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Receiving Location</label>
                      <input
                        type="text"
                        value={transField2}
                        onChange={(e) => setTransField2(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                  </>
                )}

                {activeTransition.action === "START_EXAM" && (
                  <>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Examiner Name</label>
                      <input
                        type="text"
                        value={transField1}
                        onChange={(e) => setTransField1(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Purpose of Examination</label>
                      <input
                        type="text"
                        value={transField2}
                        onChange={(e) => setTransField2(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                  </>
                )}

                {activeTransition.action === "COMPLETE_EXAM" && (
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Examiner Name</label>
                    <input
                      type="text"
                      value={transField1}
                      onChange={(e) => setTransField1(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                    />
                  </div>
                )}

                {activeTransition.action === "REPORT" && (
                  <>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Report Title</label>
                      <input
                        type="text"
                        value={transField1}
                        onChange={(e) => setTransField1(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Summary Findings</label>
                      <input
                        type="text"
                        value={transField2}
                        onChange={(e) => setTransField2(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Forensic Report PDF / Document File</label>
                      <input
                        type="file"
                        onChange={(e) => setTransFile(e.target.files?.[0] || null)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-800 file:text-slate-200"
                      />
                    </div>
                  </>
                )}

                {activeTransition.action === "COURT" && (
                  <>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">
                        Judicial Court Name <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={transField1}
                        onChange={(e) => setTransField1(e.target.value)}
                        placeholder="e.g. Principal Sessions Court / Special Cyber Court"
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Submission Notes</label>
                      <input
                        type="text"
                        value={transField2}
                        onChange={(e) => setTransField2(e.target.value)}
                        placeholder="Entered into official court evidence registry"
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                      />
                    </div>
                  </>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Additional Notes</label>
                  <textarea
                    rows={2}
                    value={transNotes}
                    onChange={(e) => setTransNotes(e.target.value)}
                    placeholder="Enter any additional custody notes or memo references..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setActiveTransition(null)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingTransition}
                    className="flex items-center gap-1 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white disabled:opacity-50"
                  >
                    {submittingTransition ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    <span>Confirm & Record Transition</span>
                  </button>
                </div>
              </form>
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

        {caseData && (
          <CourtPackageModal
            isOpen={showCourtPackageModal}
            onClose={() => {
              setShowCourtPackageModal(false);
              fetchLatestCourtPackage();
            }}
            caseId={caseId}
            caseNumber={caseData.case_number}
            initialMode={courtPackageMode}
            initialPackage={latestCourtPackage}
          />
        )}
      </main>
    </div>
  );
}
