"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Search,
  Shield,
  FileText,
  Tag,
  FolderGit2,
  Filter,
  Loader2,
  AlertCircle,
  ExternalLink,
  Lock,
  ArrowRight,
} from "lucide-react";
import Navbar from "../../components/Navbar";
import {
  searchInvestigation,
  SearchResponse,
  SearchResultItem,
  UserProfile,
  getCurrentUser,
  getStoredToken,
} from "../../lib/api";

const ENTITY_TYPES = [
  "ALL",
  "PERSON",
  "PHONE",
  "EMAIL",
  "LOCATION",
  "DATE",
  "VEHICLE",
  "POLICE_STATION",
  "CASE_NUMBER",
  "CRIME_TYPE",
  "LAW_SECTION",
  "ORGANIZATION",
];

const CRIME_TYPES = [
  "ALL",
  "CYBER_CRIME",
  "FINANCIAL_FRAUD",
  "NARCOTICS",
  "HOMICIDE",
  "KIDNAPPING",
  "TERRORISM",
  "THEFT_ROBBERY",
  "ASSAULT",
  "FORGERY",
  "OTHER",
];

export default function SearchPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState("ALL");
  const [crimeType, setCrimeType] = useState("ALL");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        if (getStoredToken()) {
          const u = await getCurrentUser();
          setUser(u);
        }
      } catch {
        // Not logged in
      }
    };
    fetchUser();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() && entityType === "ALL" && crimeType === "ALL" && !location.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const resp = await searchInvestigation({
        q: query.trim() || undefined,
        entity_type: entityType !== "ALL" ? entityType : undefined,
        crime_type: crimeType !== "ALL" ? crimeType : undefined,
        location: location.trim() || undefined,
      });
      setSearchResponse(resp);
      setResults(resp.results);
      setHasSearched(true);
    } catch (err: any) {
      setError(err.message || "Investigation search failed");
    } finally {
      setLoading(false);
    }
  };

  const getResultTypeBadge = (type: string) => {
    switch (type) {
      case "CASE":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-blue-950/70 border border-blue-800 text-blue-300 font-mono">
            <FolderGit2 className="w-3 h-3" /> CASE RECORD
          </span>
        );
      case "DOCUMENT":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-purple-950/70 border border-purple-800 text-purple-300 font-mono">
            <FileText className="w-3 h-3" /> DOCUMENT EVIDENCE
          </span>
        );
      case "ENTITY":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-950/70 border border-emerald-800 text-emerald-300 font-mono">
            <Tag className="w-3 h-3" /> EXTRACTED ENTITY
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar user={user} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header banner */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="p-1.5 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400">
                <Search className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-white">
                Investigation Search
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Multi-dimensional cross-evidence search across authorized cases, OCR transcripts, and extracted entities.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/30 border border-emerald-800/50 text-emerald-400 text-xs font-mono">
            <Lock className="w-3.5 h-3.5" />
            <span>Pre-Retrieval Authorization Enforced</span>
          </div>
        </div>

        {/* Search Query Form */}
        <form onSubmit={handleSearch} className="mb-8 space-y-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500">
              <Search className="w-5 h-5" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search suspect name, phone number, vehicle plate, keyword, or evidence text..."
              className="w-full pl-12 pr-28 py-3.5 bg-slate-900/90 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/80 transition"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-2 top-2 bottom-2 px-5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-lg shadow-blue-600/20 transition flex items-center gap-1.5"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              <span>Search</span>
            </button>
          </div>

          {/* Filter Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 bg-slate-900/40 border border-slate-800/60 rounded-xl">
            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                ENTITY TYPE
              </label>
              <select
                value={entityType}
                onChange={(e) => setEntityType(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                {ENTITY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                CRIME CLASSIFICATION
              </label>
              <select
                value={crimeType}
                onChange={(e) => setCrimeType(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                {CRIME_TYPES.map((c) => (
                  <option key={c} value={c}>
                    {c.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                LOCATION / POLICE JURISDICTION
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Connaught Place, Mumbai..."
                className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </form>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-950/40 border border-red-800/50 rounded-xl flex items-center gap-3 text-red-300 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results summary */}
        {hasSearched && searchResponse && (
          <div className="mb-4 flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>
              Found <strong className="text-white">{searchResponse.total}</strong> authorized result(s)
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
              Mode: {searchResponse.search_mode}
            </span>
          </div>
        )}

        {/* Results list */}
        {results.length > 0 ? (
          <div className="space-y-3">
            {results.map((item, idx) => (
              <div
                key={idx}
                className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex items-center gap-2">
                    {getResultTypeBadge(item.result_type)}
                    <span className="text-xs font-mono text-blue-400">
                      {item.case_number}
                    </span>
                    <span className="text-slate-500">•</span>
                    <span className="text-xs font-semibold text-white">
                      {item.case_title}
                    </span>
                  </div>

                  <Link
                    href={`/cases/${item.case_id}`}
                    className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium shrink-0"
                  >
                    <span>View Case</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>

                {/* Match snippet */}
                <div className="mt-2 text-xs text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800/60 font-mono">
                  <span className="text-slate-500 text-[10px] block uppercase mb-1">
                    Matched on: {item.match_field}
                    {item.entity_type && ` • [${item.entity_type}]`}
                  </span>
                  <p className="leading-relaxed">
                    {item.match_snippet}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : hasSearched && !loading ? (
          <div className="text-center py-16 border border-dashed border-slate-800 rounded-2xl bg-slate-900/20">
            <Shield className="w-12 h-12 mx-auto text-slate-600 mb-3" />
            <h3 className="text-base font-semibold text-slate-200 mb-1">
              No Authorized Records Found
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Either no records matched your query parameters or your officer credentials do not have access to matching cases.
            </p>
          </div>
        ) : !hasSearched && (
          <div className="text-center py-16 border border-slate-900 rounded-2xl bg-slate-900/10">
            <Search className="w-10 h-10 mx-auto text-slate-600 mb-2" />
            <p className="text-xs text-slate-400">
              Enter keywords, phone numbers, vehicle registrations, or suspect names to search across authorized cases.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
