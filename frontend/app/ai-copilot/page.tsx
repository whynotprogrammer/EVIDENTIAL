"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Bot,
  Shield,
  Search,
  Sparkles,
  Loader2,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Lock,
  ExternalLink,
  BookOpen,
  ArrowRight,
  Send,
  UserCheck,
  Building2,
  Clock,
  Layers,
} from "lucide-react";
import Navbar from "../../components/Navbar";
import {
  CaseItem,
  CopilotCaseSummaryResponse,
  CopilotQueryResponse,
  getCases,
  getCaseCopilotSummary,
  getCurrentUser,
  getStoredToken,
  queryCopilot,
  SourceCitation,
  UserProfile,
} from "../../lib/api";

const PRESET_QUESTIONS = [
  "Summarize this case.",
  "Who are the persons mentioned?",
  "What evidence exists?",
  "What happened chronologically?",
  "Which FIRs may be related?",
  "Which documents support this answer?",
  "What locations are mentioned?",
];

interface ChatMessage {
  id: string;
  sender: "USER" | "COPILOT";
  text: string;
  timestamp: string;
  citations?: SourceCitation[];
  uncertaintyFlag?: boolean;
  confidenceLevel?: string;
  groundedScore?: number;
}

export default function AICopilotPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [summaryData, setSummaryData] = useState<CopilotCaseSummaryResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [casesLoading, setCasesLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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
          setSelectedCaseId(cList[0].id);
        }
      } catch (err) {
        console.error("Failed to load initial copilot cases:", err);
      } finally {
        setCasesLoading(false);
      }
    };
    initData();
  }, []);

  useEffect(() => {
    if (selectedCaseId) {
      loadExecutiveSummary(selectedCaseId);
    }
  }, [selectedCaseId]);

  const loadExecutiveSummary = async (cId: number) => {
    setSummaryLoading(true);
    setErrorMsg(null);
    try {
      const summary = await getCaseCopilotSummary(cId);
      setSummaryData(summary);
      // Set initial welcome assistant message
      setMessages([
        {
          id: "welcome-1",
          sender: "COPILOT",
          text: summary.summary_answer,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          citations: summary.citations,
          uncertaintyFlag: false,
          confidenceLevel: "HIGH",
        },
      ]);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load grounded case summary.");
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleSendQuestion = async (questionText: string) => {
    if (!questionText.trim() || !selectedCaseId || loading) return;

    const q = questionText.trim();
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "USER",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuestion("");
    setLoading(true);

    try {
      const resp: CopilotQueryResponse = await queryCopilot(selectedCaseId, q);
      const copilotMsg: ChatMessage = {
        id: `copilot-${Date.now()}`,
        sender: "COPILOT",
        text: resp.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        citations: resp.citations,
        uncertaintyFlag: resp.uncertainty_flag,
        confidenceLevel: resp.confidence_level,
      };
      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: any) {
      const errCopilotMsg: ChatMessage = {
        id: `copilot-err-${Date.now()}`,
        sender: "COPILOT",
        text: `Error: ${err.message || "Unable to retrieve grounded copilot response."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        uncertaintyFlag: true,
        confidenceLevel: "LOW",
      };
      setMessages((prev) => [...prev, errCopilotMsg]);
    } finally {
      setLoading(false);
    }
  };

  const selectedCase = cases.find((c) => c.id === selectedCaseId);

  return (
    <div className="min-h-screen bg-black text-ink flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-5">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-canvas-elevated border border-hairline rounded-md p-5">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <span className="p-1.5 bg-zinc-900 text-white rounded-sm border border-hairline">
                <Bot className="w-4 h-4" />
              </span>
              <h1 className="text-lg font-semibold tracking-tight text-white">
                Investigation AI Copilot
              </h1>
              <span className="px-2 py-0.5 rounded-sm text-[10px] font-mono uppercase bg-zinc-900 text-zinc-300 border border-hairline flex items-center gap-1">
                <Shield className="w-3 h-3 text-emerald-400" /> Grounded Intelligence
              </span>
            </div>
            <p className="text-xs text-mute max-w-2xl">
              Query authorized EVIDENTIAL case records with verified source citations, zero speculation, and pre-retrieval boundaries.
            </p>
          </div>

          {/* Case Selector Dropdown */}
          <div className="min-w-[260px]">
            <label className="block text-xs font-medium text-mute mb-1 flex items-center gap-1.5">
              <Lock className="w-3 h-3 text-zinc-400" /> Authorized Case File
            </label>
            {casesLoading ? (
              <div className="flex items-center gap-2 text-xs text-mute bg-zinc-950 p-2 rounded-sm border border-hairline">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" /> Loading cases...
              </div>
            ) : (
              <select
                value={selectedCaseId || ""}
                onChange={(e) => setSelectedCaseId(Number(e.target.value))}
                className="w-full bg-zinc-950 border border-hairline text-white rounded-sm px-3 py-1.5 text-xs focus:border-zinc-500 outline-none"
              >
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.case_number} — {c.title}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Security & Authorization Guardrail Banner */}
        <div className="bg-canvas-subtle border border-hairline rounded-sm p-3 text-xs text-zinc-300 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <span>
              <strong className="text-white font-medium">Pre-Retrieval Boundary Active:</strong> Copilot answers are strictly derived from records assigned to your active officer profile.
            </span>
          </div>
          <span className="px-1.5 py-0.5 bg-zinc-900 border border-hairline rounded-sm text-mute text-[10px] font-mono uppercase">
            Zero-Guilt Engine Mandate
          </span>
        </div>

        {/* Main Grid: Chat Area + Case Summary Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 flex-1">
          {/* Left 2 Cols: Copilot Interactive Chat */}
          <div className="lg:col-span-2 flex flex-col bg-canvas-elevated border border-hairline rounded-md overflow-hidden">
            {/* Quick Investigative Prompts Bar */}
            <div className="p-3.5 border-b border-hairline bg-canvas-subtle flex flex-col gap-2">
              <span className="text-xs font-medium text-mute flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-zinc-400" /> Presets & Investigative Prompts
              </span>
              <div className="flex flex-wrap gap-1.5">
                {PRESET_QUESTIONS.map((pq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendQuestion(pq)}
                    disabled={loading || !selectedCaseId}
                    className="text-xs px-2.5 py-1 rounded-sm bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-hairline hover:border-zinc-600 transition disabled:opacity-50 text-left"
                  >
                    {pq}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Transcript Container */}
            <div className="flex-1 p-5 overflow-y-auto max-h-[520px] flex flex-col gap-4">
              {summaryLoading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-2 text-mute">
                  <Loader2 className="w-6 h-6 animate-spin text-white" />
                  <p className="text-xs">Synthesizing grounded case intelligence...</p>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-16 text-mute text-xs">
                  Select a prompt above or ask a factual query about this case record.
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col gap-1.5 max-w-[88%] ${
                      msg.sender === "USER" ? "self-end items-end" : "self-start items-start"
                    }`}
                  >
                    <div className="flex items-center gap-2 text-[11px] text-mute font-mono">
                      <span>{msg.sender === "USER" ? "Officer Query" : "EVIDENTIAL Copilot"}</span>
                      <span>•</span>
                      <span>{msg.timestamp}</span>
                      {msg.sender === "COPILOT" && (
                        <>
                          <span>•</span>
                          <span
                            className={`px-1.5 py-0.2 rounded-sm text-[10px] font-mono uppercase border ${
                              msg.groundedScore !== undefined && msg.groundedScore >= 0.8
                                ? "bg-emerald-950/40 text-emerald-400 border-emerald-900/50"
                                : "bg-zinc-900 text-zinc-400 border-hairline"
                            }`}
                          >
                            {msg.groundedScore !== undefined ? `${Math.round(msg.groundedScore * 100)}% Verified` : "Processed"}
                          </span>
                        </>
                      )}
                    </div>

                    <div
                      className={`p-3.5 rounded-sm text-xs leading-relaxed ${
                        msg.sender === "USER"
                          ? "bg-white text-black font-medium"
                          : "bg-canvas-subtle border border-hairline text-zinc-200"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.text}</div>

                      {/* Uncertainty Alert */}
                      {msg.uncertaintyFlag && (
                        <div className="mt-2.5 p-2.5 bg-amber-950/30 border border-amber-900/50 rounded-sm flex items-start gap-2 text-amber-300 text-[11px]">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <strong>Uncertainty Notice:</strong>
                            <p className="text-amber-200/90 mt-0.5">
                              Information absent in authorized case data. Copilot strictly refrains from inferring unverified facts.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Source Citations */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-hairline flex flex-col gap-1.5">
                          <span className="text-[11px] font-medium text-mute flex items-center gap-1.5">
                            <BookOpen className="w-3 h-3 text-zinc-400" /> Grounded Source Citations ({msg.citations.length})
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {msg.citations.map((cit, cIdx) => (
                              <div
                                key={cIdx}
                                className="bg-zinc-950 border border-hairline rounded-sm p-2 text-xs flex flex-col gap-1"
                              >
                                <div className="flex items-center justify-between font-medium text-white">
                                  <span className="truncate">{cit.source_title}</span>
                                  <span className="px-1 py-0.2 bg-zinc-900 text-[9px] font-mono text-mute rounded-sm">
                                    {cit.source_type}
                                  </span>
                                </div>
                                {cit.document_filename && (
                                  <div className="text-[10px] text-mute flex items-center gap-1">
                                    <FileText className="w-3 h-3 text-zinc-500" />
                                    <span className="truncate">{cit.document_filename}</span>
                                  </div>
                                )}
                                {cit.snippet && (
                                  <p className="text-[10px] text-mute italic bg-black p-1 rounded-sm border border-hairline line-clamp-2">
                                    &ldquo;{cit.snippet}&rdquo;
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Input Form Bar */}
            <div className="p-3.5 bg-canvas-subtle border-t border-hairline">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendQuestion(inputQuestion);
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={inputQuestion}
                  onChange={(e) => setInputQuestion(e.target.value)}
                  placeholder={
                    selectedCase
                      ? `Query factual records for ${selectedCase.case_number}...`
                      : "Select a case to begin..."
                  }
                  disabled={loading || !selectedCaseId}
                  className="flex-1 bg-zinc-950 border border-hairline text-white rounded-sm px-3 py-2 text-xs focus:border-zinc-500 outline-none disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={loading || !inputQuestion.trim() || !selectedCaseId}
                  className="px-4 py-2 bg-white hover:bg-zinc-200 text-black font-medium text-xs rounded-sm transition-colors flex items-center gap-1.5 disabled:opacity-50 shrink-0"
                >
                  {loading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <>
                      <span>Query</span>
                      <Send className="w-3 h-3" />
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Right 1 Col: Grounded Case Profile */}
          <div className="flex flex-col gap-4">
            <div className="bg-canvas-elevated border border-hairline rounded-md p-4 flex flex-col gap-3">
              <h2 className="text-xs font-semibold text-white flex items-center justify-between border-b border-hairline pb-2.5">
                <span className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-zinc-400" /> Active Case Record
                </span>
                {selectedCase && (
                  <Link
                    href={`/cases/${selectedCase.id}`}
                    className="text-xs text-mute hover:text-white flex items-center gap-1 transition"
                  >
                    View File <ArrowRight className="w-3 h-3" />
                  </Link>
                )}
              </h2>

              {selectedCase ? (
                <div className="flex flex-col gap-3 text-xs">
                  <div>
                    <span className="text-[11px] font-mono text-mute block mb-0.5">FIR ID & Title</span>
                    <p className="font-semibold text-white text-xs">{selectedCase.case_number}</p>
                    <p className="text-zinc-400 text-[11px]">{selectedCase.title}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-hairline">
                    <div className="bg-zinc-950 p-2 rounded-sm border border-hairline">
                      <span className="text-mute block text-[10px] font-mono">Crime Type</span>
                      <span className="font-medium text-zinc-200 text-xs truncate block">{selectedCase.crime_type}</span>
                    </div>
                    <div className="bg-zinc-950 p-2 rounded-sm border border-hairline">
                      <span className="text-mute block text-[10px] font-mono">Status</span>
                      <span className="font-medium text-zinc-200 text-xs">{selectedCase.status}</span>
                    </div>
                  </div>

                  {summaryData && (
                    <div className="flex flex-col gap-2.5 pt-2.5 border-t border-hairline">
                      <span className="font-medium text-mute text-xs flex items-center gap-1.5">
                        <Layers className="w-3 h-3 text-zinc-400" /> Evidence Inventory Metrics
                      </span>

                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-zinc-950 p-2 rounded-sm border border-hairline">
                          <span className="text-base font-semibold text-white block">
                            {summaryData.persons_identified.length}
                          </span>
                          <span className="text-[10px] text-mute font-mono">Persons</span>
                        </div>
                        <div className="bg-zinc-950 p-2 rounded-sm border border-hairline">
                          <span className="text-base font-semibold text-white block">
                            {summaryData.evidence_count}
                          </span>
                          <span className="text-[10px] text-mute font-mono">Evidence</span>
                        </div>
                        <div className="bg-zinc-950 p-2 rounded-sm border border-hairline">
                          <span className="text-base font-semibold text-white block">
                            {summaryData.timeline_events_count}
                          </span>
                          <span className="text-[10px] text-mute font-mono">Events</span>
                        </div>
                      </div>

                      {summaryData.persons_identified.length > 0 && (
                        <div className="pt-1.5">
                          <span className="text-[10px] font-mono text-mute block mb-1">
                            Identified Entities
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {summaryData.persons_identified.map((name, i) => (
                              <span
                                key={i}
                                className="px-1.5 py-0.5 bg-zinc-900 text-zinc-300 border border-hairline rounded-sm text-[10px] font-mono"
                              >
                                {name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-mute">No authorized case selected.</p>
              )}
            </div>

            {/* Zero-Guilt Policy Notice */}
            <div className="bg-canvas-elevated border border-hairline rounded-md p-3.5 text-xs text-mute flex flex-col gap-1.5">
              <span className="font-medium text-zinc-300 flex items-center gap-1.5 text-xs">
                <AlertTriangle className="w-3.5 h-3.5 text-zinc-400" /> Zero-Guilt System Policy
              </span>
              <p className="text-[11px] leading-relaxed">
                EVIDENTIAL AI Investigation Copilot never asserts legal guilt or speculative culpability. Responses provide objective factual summaries of authorized forensic evidence.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
