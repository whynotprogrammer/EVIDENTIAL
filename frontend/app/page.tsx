"use client";

import { useEffect, useState } from "react";
import { CheckCircle, AlertTriangle, RefreshCw, Shield, Server, Database, Globe } from "lucide-react";
import { checkBackendHealth, HealthResponse, API_BASE_URL } from "../lib/api";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkBackendHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend service");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <main className="min-h-screen flex flex-col justify-between p-6 md:p-12 max-w-6xl mx-auto">
      {/* Header Bar */}
      <header className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400">
            <Shield className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              EVIDENTIAL
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/60 border border-blue-700 text-blue-300 font-mono">
                PHASE 1: FOUNDATION
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Secure Digital Investigation & Case Intelligence Platform
            </p>
          </div>
        </div>

        <button
          onClick={fetchHealth}
          disabled={loading}
          className="flex items-center gap-2 text-xs font-medium px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Check Live Status
        </button>
      </header>

      {/* Main Status Panel */}
      <div className="my-10 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            System Foundation & Architecture
          </h2>
          <p className="text-sm text-slate-400">
            FastAPI REST backend with API v1 routing, PostgreSQL database layer, secure CORS, and Next.js frontend integration.
          </p>
        </div>

        {/* Integration Status Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
            <h3 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-400" />
              Backend & Database Connectivity
            </h3>
            <span className="text-xs font-mono text-slate-500">
              Endpoint: {API_BASE_URL}/health
            </span>
          </div>

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
              <p className="text-sm">Pinging backend health endpoint...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-900/50 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-300">Connection Error</p>
                <p className="text-xs text-red-400/90 mt-1">{error}</p>
                <p className="text-xs text-slate-400 mt-2 font-mono">
                  Make sure backend is running: <code className="bg-slate-800 px-1.5 py-0.5 rounded">uvicorn backend.app.main:app --port 8000</code>
                </p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-medium">Service Status</span>
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-lg font-bold text-emerald-400 capitalize">
                  {health?.status}
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Service: {health?.service} (v{health?.version})
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-medium">Database Layer</span>
                  <Database className="w-4 h-4 text-blue-400" />
                </div>
                <div className="text-lg font-bold text-blue-400 capitalize">
                  {health?.database.status}
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Dialect: {health?.database.dialect}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-medium">API Version</span>
                  <Globe className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="text-lg font-bold text-cyan-400">
                  /api/v1
                </div>
                <div className="text-[11px] text-slate-400 font-mono truncate">
                  Environment: {health?.environment}
                </div>
              </div>
            </div>
          )}

          {health && (
            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-500 font-mono">
              <span>Timestamp: {health.timestamp}</span>
              <span className="text-emerald-500 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Integration Verified
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 pt-6 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500">
        <div>EVIDENTIAL — Phase 1 Acceptance Test & Baseline</div>
        <div className="mt-2 md:mt-0 font-mono">FastAPI 0.115 • Next.js 14 • PostgreSQL / SQLite</div>
      </footer>
    </main>
  );
}
