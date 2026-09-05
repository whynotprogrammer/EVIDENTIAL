"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle, AlertTriangle, RefreshCw, Shield, Server, Database, Globe, ArrowRight } from "lucide-react";
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
    <main className="min-h-screen flex flex-col justify-between p-6 md:p-12 max-w-5xl mx-auto">
      {/* Header Bar */}
      <header className="flex items-center justify-between border-b border-hairline pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-900 border border-hairline rounded-sm text-white">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight text-white">
                EVIDENTIAL
              </h1>
            </div>
            <p className="text-xs text-mute">
              Secure Digital Investigation & Case Intelligence Platform
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-sm bg-white hover:bg-zinc-200 text-black transition-colors"
          >
            Enter Dashboard
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-sm bg-transparent hover:bg-zinc-900 text-zinc-300 border border-hairline transition-colors"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </header>

      {/* Main Status Panel */}
      <div className="my-12 space-y-8">
        <div className="space-y-2">
          <span className="text-[11px] font-mono uppercase tracking-wider text-mute">Infrastructure Status</span>
          <h2 className="text-3xl font-semibold text-white tracking-tight">
            System Foundation & Telemetry
          </h2>
          <p className="text-sm text-body max-w-2xl">
            FastAPI REST API with PostgreSQL/SQLite storage layer, cryptographic audit log, and Next.js frontend.
          </p>
        </div>

        {/* Integration Status Card */}
        <div className="bg-canvas-elevated border border-hairline rounded-md p-6">
          <div className="flex items-center justify-between border-b border-hairline pb-4 mb-5">
            <h3 className="text-sm font-medium text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-zinc-400" />
              Service & Gateway Connectivity
            </h3>
            <span className="text-xs font-mono text-mute">
              {API_BASE_URL}/health
            </span>
          </div>

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-mute">
              <RefreshCw className="w-5 h-5 animate-spin text-white" />
              <p className="text-xs">Querying system telemetry...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-sm bg-red-950/30 border border-red-900/50 flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-red-300">Connection Error</p>
                <p className="text-xs text-red-400/90 mt-1">{error}</p>
                <p className="text-[11px] text-mute mt-2 font-mono">
                  Make sure backend is running: <code className="bg-zinc-900 px-1 py-0.5 rounded text-white">uvicorn backend.app.main:app --port 8000</code>
                </p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-sm bg-canvas-subtle border border-hairline space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-mute font-medium">Service Health</span>
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <div className="text-base font-semibold text-white capitalize">
                  {health?.status}
                </div>
                <div className="text-[11px] text-mute font-mono">
                  {health?.service} v{health?.version}
                </div>
              </div>

              <div className="p-4 rounded-sm bg-canvas-subtle border border-hairline space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-mute font-medium">Database Layer</span>
                  <Database className="w-3.5 h-3.5 text-zinc-400" />
                </div>
                <div className="text-base font-semibold text-white capitalize">
                  {health?.database.status}
                </div>
                <div className="text-[11px] text-mute font-mono">
                  Engine: {health?.database.dialect}
                </div>
              </div>

              <div className="p-4 rounded-sm bg-canvas-subtle border border-hairline space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-mute font-medium">Environment</span>
                  <Globe className="w-3.5 h-3.5 text-zinc-400" />
                </div>
                <div className="text-base font-semibold text-white">
                  /api/v1
                </div>
                <div className="text-[11px] text-mute font-mono truncate">
                  Profile: {health?.environment}
                </div>
              </div>
            </div>
          )}

          {health && (
            <div className="mt-5 pt-4 border-t border-hairline flex items-center justify-end text-xs text-mute font-mono">
              <span className="text-emerald-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Operational
              </span>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
