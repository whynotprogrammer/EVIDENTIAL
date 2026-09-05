"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Lock, Mail, AlertCircle, Loader2, KeyRound } from "lucide-react";
import { loginUser } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await loginUser(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  const setDemoCredentials = (role: "officer" | "admin") => {
    if (role === "officer") {
      setEmail("officer@evidential.gov.in");
      setPassword("Officer@123");
    } else {
      setEmail("admin@evidential.gov.in");
      setPassword("Admin@123");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0f19] p-4 text-slate-100">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 bg-blue-600/20 border border-blue-500/30 rounded-2xl text-blue-400 mb-1">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white">EVIDENTIAL</h1>
          <p className="text-xs text-slate-400">
            Secure Digital Investigation & Case Intelligence System
          </p>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-900/50 flex items-center gap-2.5 text-xs text-red-300">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Officer Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@evidential.gov.in"
                className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Security Passcode / Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-lg shadow-blue-600/20 transition disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
            Authenticate Officer
          </button>
        </form>

        <div className="pt-4 border-t border-slate-800 text-center space-y-2">
          <p className="text-[11px] text-slate-500">Demo Fast-Fill Credentials:</p>
          <div className="flex justify-center gap-2">
            <button
              onClick={() => setDemoCredentials("officer")}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] border border-slate-700"
            >
              Investigator Sen
            </button>
            <button
              onClick={() => setDemoCredentials("admin")}
              className="px-2.5 py-1 rounded-lg bg-blue-950 hover:bg-blue-900 text-blue-300 text-[11px] border border-blue-800"
            >
              Chief Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
