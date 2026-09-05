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
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-[10px] font-mono uppercase bg-zinc-900 border border-hairline text-zinc-300">
            <FolderGit2 className="w-3 h-3 text-zinc-400" />
            CASE
          </span>
        );
      case "DOCUMENT":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-[10px] font-mono uppercase bg-zinc-900 border border-hairline text-zinc-300">
            <FileText className="w-3 h-3 text-zinc-400" />
            DOCUMENT
          </span>
        );
      case "ENTITY":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-[10px] font-mono uppercase bg-zinc-900 border border-hairline text-zinc-300">
            <Tag className="w-3 h-3 text-zinc-400" />
            ENTITY
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-[10px] font-mono uppercase bg-zinc-900 border border-hairline text-zinc-400">
            RECORD
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-black text-ink">
      <Navbar user={user} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 border-b border-hairline pb-5">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
              <Search className="w-5 h-5 text-zinc-400" />
              Cross-Investigation Search
            </h1>
            <p className="text-xs text-mute">
              Multi-dimensional cross-evidence search across authorized cases, OCR transcripts, and extracted entities.
            </p>
          </div>
        </div>

        {/* Search Query Form */}
        <form onSubmit={handleSearch} className="mb-6 space-y-3">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-mute">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search suspect name, phone number, vehicle plate, keyword, or evidence text..."
              className="w-full pl-10 pr-24 py-2.5 bg-canvas-elevated border border-hairline rounded-md text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 transition"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-1.5 top-1.5 bottom-1.5 px-3.5 bg-white hover:bg-zinc-200 disabled:opacity-50 text-black text-xs font-medium rounded-sm transition flex items-center gap-1.5"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
              <span>Search</span>
            </button>
          </div>

          {/* Filter Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 bg-canvas-elevated border border-hairline rounded-md">
            <div>
              <label className="block text-[10px] font-mono uppercase text-mute mb-1">
                Entity Type
              </label>
              <select
                value={entityType}
                onChange={(e) => setEntityType(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200 focus:border-zinc-500 focus:outline-none"
              >
                {ENTITY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-mute mb-1">
                Crime Classification
              </label>
              <select
                value={crimeType}
                onChange={(e) => setCrimeType(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-zinc-200 focus:border-zinc-500 focus:outline-none"
              >
                {CRIME_TYPES.map((c) => (
                  <option key={c} value={c}>
                    {c.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-mute mb-1">
                Location / Jurisdiction
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Connaught Place, Mumbai..."
                className="w-full px-2.5 py-1.5 bg-zinc-950 border border-hairline rounded-sm text-xs text-white placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
              />
            </div>
          </div>
        </form>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-3 bg-red-950/30 border border-red-900/50 rounded-sm flex items-center gap-2.5 text-red-300 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Results summary */}
        {hasSearched && searchResponse && (
          <div className="mb-4 flex items-center justify-between text-xs text-mute font-mono">
            <span>
              Found <strong className="text-white">{searchResponse.total}</strong> authorized record(s)
            </span>
            <span className="text-[10px] uppercase px-1.5 py-0.5 rounded-sm bg-zinc-900 border border-hairline text-zinc-400">
              Mode: {searchResponse.search_mode}
            </span>
          </div>
        )}

        {/* Results list */}
        {results.length > 0 ? (
          <div className="space-y-2.5">
            {results.map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 bg-canvas-elevated border border-hairline rounded-md hover:border-zinc-700 transition"
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex items-center gap-2">
                    {getResultTypeBadge(item.result_type)}
                    <span className="text-xs font-mono font-medium text-accent">
                      {item.case_number}
                    </span>
                    <span className="text-zinc-600">•</span>
                    <span className="text-xs font-medium text-white">
                      {item.case_title}
                    </span>
                  </div>

                  <Link
                    href={`/cases/${item.case_id}`}
                    className="flex items-center gap-1 text-xs text-mute hover:text-white font-medium shrink-0 transition"
                  >
                    <span>View Case</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>

                {/* Match snippet */}
                <div className="mt-2 text-xs text-zinc-300 bg-zinc-950 p-2.5 rounded-sm border border-hairline font-mono">
                  <span className="text-mute text-[10px] block uppercase mb-1">
                    Matched on: {item.match_field}
                    {item.entity_type && ` • [${item.entity_type}]`}
                  </span>
                  <p className="leading-relaxed text-zinc-200">
                    {item.match_snippet}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : hasSearched && !loading ? (
          <div className="text-center py-16 border border-hairline rounded-md bg-canvas-elevated">
            <Shield className="w-8 h-8 mx-auto text-zinc-600 mb-2" />
            <h3 className="text-sm font-semibold text-white mb-1">
              No Authorized Records Found
            </h3>
            <p className="text-xs text-mute max-w-md mx-auto">
              Either no records matched your query parameters or your officer credentials do not have access to matching cases.
            </p>
          </div>
        ) : !hasSearched && (
          <div className="text-center py-16 border border-hairline rounded-md bg-canvas-elevated">
            <Search className="w-8 h-8 mx-auto text-zinc-600 mb-2" />
            <p className="text-xs text-mute">
              Enter keywords, phone numbers, vehicle registrations, or suspect names to search across authorized cases.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
