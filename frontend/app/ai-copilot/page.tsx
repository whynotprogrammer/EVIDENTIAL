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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-xl p-6 backdrop-blur">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="p-2 bg-indigo-600/20 text-indigo-400 rounded-lg border border-indigo-500/30">
                <Bot className="w-6 h-6" />
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                EVIDENTIAL AI Investigation Copilot
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <Shield className="w-3.5 h-3.5" /> Grounded Intelligence
              </span>
            </div>
            <p className="text-sm text-slate-400 max-w-3xl">
              Query authorized EVIDENTIAL case records with zero hallucination, strict prompt-injection defense,
              pre-retrieval access control, and verifiable source citations.
            </p>
          </div>

          {/* Case Selector Dropdown */}
          <div className="min-w-[280px]">
            <label className="block text-xs font-medium text-slate-400 mb-1.5 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-indigo-400" /> Authorized Active Case
            </label>
            {casesLoading ? (
              <div className="flex items-center gap-2 text-sm text-slate-400 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" /> Loading authorized cases...
              </div>
            ) : (
              <select
                value={selectedCaseId || ""}
                onChange={(e) => setSelectedCaseId(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
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
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 rounded-lg p-3.5 text-xs text-slate-300 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>
              <strong>Pre-Retrieval Authorization Boundary Active:</strong> Copilot answers are strictly derived from case records assigned to your officer profile.
            </span>
          </div>
          <span className="px-2 py-0.5 bg-slate-900 border border-slate-700 rounded text-slate-400 text-[11px] font-mono">
            Zero-Guilt Engine Mandate
          </span>
        </div>

        {/* Main Grid: Chat Area + Case Summary Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
          {/* Left 2 Cols: Copilot Interactive Chat */}
          <div className="lg:col-span-2 flex flex-col bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            {/* Quick Investigative Prompts Bar */}
            <div className="p-4 border-b border-slate-800 bg-slate-900/90 flex flex-col gap-2">
              <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Presets & Investigative Prompts
              </span>
              <div className="flex flex-wrap gap-2">
                {PRESET_QUESTIONS.map((pq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendQuestion(pq)}
                    disabled={loading || !selectedCaseId}
                    className="text-xs px-3 py-1.5 rounded-full bg-slate-800 hover:bg-indigo-600/30 hover:text-indigo-200 text-slate-300 border border-slate-700 hover:border-indigo-500/50 transition-all disabled:opacity-50 text-left"
                  >
                    {pq}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Transcript Container */}
            <div className="flex-1 p-6 overflow-y-auto max-h-[560px] flex flex-col gap-5">
              {summaryLoading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
                  <p className="text-sm">Synthesizing grounded case intelligence...</p>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-16 text-slate-500">
                  <Bot className="w-12 h-12 mx-auto mb-3 text-slate-600" />
                  <p className="text-sm">Select an authorized case and submit your inquiry.</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col gap-2 max-w-[90%] ${
                      msg.sender === "USER" ? "ml-auto items-end" : "mr-auto items-start"
                    }`}
                  >
                    <div className="flex items-center gap-2 text-xs text-slate-400 px-1">
                      {msg.sender === "USER" ? (
                        <>
                          <span>You</span>
                          <span>•</span>
                          <span>{msg.timestamp}</span>
                        </>
                      ) : (
                        <>
                          <Bot className="w-3.5 h-3.5 text-indigo-400" />
                          <span className="font-semibold text-indigo-300">EVIDENTIAL Copilot</span>
                          <span>•</span>
                          <span>{msg.timestamp}</span>
                          {msg.confidenceLevel && (
                            <span
                              className={`ml-1 px-1.5 py-0.2 text-[10px] font-mono rounded ${
                                msg.confidenceLevel === "HIGH"
                                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                  : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                              }`}
                            >
                              {msg.confidenceLevel} CONFIDENCE
                            </span>
                          )}
                        </>
                      )}
                    </div>

                    <div
                      className={`p-4 rounded-xl text-sm leading-relaxed ${
                        msg.sender === "USER"
                          ? "bg-indigo-600 text-white rounded-tr-none shadow-md"
                          : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none"
                      }`}
                    >
                      {/* Message Text formatted */}
                      <div className="whitespace-pre-wrap font-sans">{msg.text}</div>

                      {/* Uncertainty Fallback Alert Banner if flagged */}
                      {msg.uncertaintyFlag && (
                        <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-2.5 text-amber-300 text-xs">
                          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <strong>Explicit Uncertainty Notice:</strong>
                            <p className="text-amber-200/90 mt-0.5">
                              Information absent in authorized case data. Copilot strictly refrains from inferring or hallucinating facts beyond verified records.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Verifiable Source Citations Cards */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-col gap-2">
                          <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                            <BookOpen className="w-3.5 h-3.5 text-indigo-400" /> Grounded Source Citations ({msg.citations.length})
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {msg.citations.map((cit, cIdx) => (
                              <div
                                key={cIdx}
                                className="bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs flex flex-col gap-1 hover:border-indigo-500/40 transition-colors"
                              >
                                <div className="flex items-center justify-between font-semibold text-indigo-300">
                                  <span className="truncate">{cit.source_title}</span>
                                  <span className="px-1.5 py-0.5 bg-slate-800 text-[10px] font-mono text-slate-400 rounded">
                                    {cit.source_type}
                                  </span>
                                </div>
                                {cit.document_filename && (
                                  <div className="text-[11px] text-slate-400 flex items-center gap-1">
                                    <FileText className="w-3 h-3 text-slate-500" />
                                    <span className="truncate">{cit.document_filename}</span>
                                  </div>
                                )}
                                {cit.snippet && (
                                  <p className="text-[11px] text-slate-400 italic bg-slate-950/60 p-1.5 rounded border border-slate-850 line-clamp-2">
                                    "{cit.snippet}"
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
            <div className="p-4 bg-slate-900 border-t border-slate-800">
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
                      ? `Ask a grounded question about ${selectedCase.case_number}...`
                      : "Select a case to begin..."
                  }
                  disabled={loading || !selectedCaseId}
                  className="flex-1 bg-slate-950 border border-slate-700 text-white rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={loading || !inputQuestion.trim() || !selectedCaseId}
                  className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <span>Query</span>
                      <Send className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Right 1 Col: Grounded Executive Case Intelligence Panel */}
          <div className="flex flex-col gap-4">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
              <h2 className="text-sm font-bold text-white flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-400" /> Authorized Case Profile
                </span>
                {selectedCase && (
                  <Link
                    href={`/cases/${selectedCase.id}`}
                    className="text-xs text-indigo-400 hover:underline flex items-center gap-1"
                  >
                    View Details <ArrowRight className="w-3 h-3" />
                  </Link>
                )}
              </h2>

              {selectedCase ? (
                <div className="flex flex-col gap-3 text-xs">
                  <div>
                    <span className="text-slate-400 block mb-0.5">Case Number & Title</span>
                    <p className="font-bold text-white text-sm">{selectedCase.case_number}</p>
                    <p className="text-slate-300">{selectedCase.title}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                    <div className="bg-slate-950 p-2.5 rounded border border-slate-850">
                      <span className="text-slate-500 block text-[10px]">Crime Classification</span>
                      <span className="font-semibold text-indigo-300">{selectedCase.crime_type}</span>
                    </div>
                    <div className="bg-slate-950 p-2.5 rounded border border-slate-850">
                      <span className="text-slate-500 block text-[10px]">Status</span>
                      <span className="font-semibold text-emerald-400">{selectedCase.status}</span>
                    </div>
                  </div>

                  {summaryData && (
                    <div className="flex flex-col gap-3 pt-3 border-t border-slate-800/80">
                      <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-indigo-400" /> Evidence Inventory Metrics
                      </span>

                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-slate-950 p-2 rounded border border-slate-800">
                          <span className="text-lg font-bold text-white block">
                            {summaryData.persons_identified.length}
                          </span>
                          <span className="text-[10px] text-slate-400">Persons</span>
                        </div>
                        <div className="bg-slate-950 p-2 rounded border border-slate-800">
                          <span className="text-lg font-bold text-white block">
                            {summaryData.evidence_count}
                          </span>
                          <span className="text-[10px] text-slate-400">Evidence</span>
                        </div>
                        <div className="bg-slate-950 p-2 rounded border border-slate-800">
                          <span className="text-lg font-bold text-white block">
                            {summaryData.timeline_events_count}
                          </span>
                          <span className="text-[10px] text-slate-400">Events</span>
                        </div>
                      </div>

                      {summaryData.persons_identified.length > 0 && (
                        <div className="pt-2">
                          <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                            Identified Persons in Record
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {summaryData.persons_identified.map((name, i) => (
                              <span
                                key={i}
                                className="px-2 py-0.5 bg-indigo-950/60 text-indigo-300 border border-indigo-800/40 rounded text-[11px]"
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
                <p className="text-xs text-slate-500">No authorized case selected.</p>
              )}
            </div>

            {/* Guilt Prevention Mandate Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 flex flex-col gap-2">
              <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" /> Zero-Guilt System Policy
              </span>
              <p className="leading-relaxed">
                EVIDENTIAL AI Investigation Copilot never asserts legal guilt, culpability, or outputs statements like "Person X committed the crime."
                All responses provide objective factual summaries of authorized evidence.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
