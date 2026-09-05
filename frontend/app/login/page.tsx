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
    <div className="min-h-screen flex items-center justify-center bg-black p-4 text-ink">
      <div className="max-w-sm w-full bg-canvas-elevated border border-hairline rounded-md p-7 space-y-6">
        <div className="space-y-2">
          <div className="inline-flex p-2 bg-zinc-900 border border-hairline rounded-sm text-white mb-1">
            <Shield className="w-5 h-5" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Officer Authentication</h1>
          <p className="text-xs text-mute">
            EVIDENTIAL Digital Investigation & Intelligence System
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-sm bg-red-950/30 border border-red-900/50 flex items-center gap-2 text-xs text-red-300">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-zinc-300 font-medium mb-1">Officer Email Address</label>
            <div className="relative">
              <Mail className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-mute" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@evidential.gov.in"
                className="w-full pl-9 pr-3 py-2 bg-zinc-950 border border-hairline rounded-sm text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-zinc-300 font-medium mb-1">Security Passcode / Password</label>
            <div className="relative">
              <Lock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-mute" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-zinc-950 border border-hairline rounded-sm text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-sm bg-white hover:bg-zinc-200 text-black font-medium text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <KeyRound className="w-3.5 h-3.5" />}
            Authenticate Officer
          </button>
        </form>

        <div className="pt-4 border-t border-hairline text-center space-y-2">
          <p className="text-[11px] text-mute">Demo Credentials:</p>
          <div className="flex justify-center gap-2">
            <button
              onClick={() => setDemoCredentials("officer")}
              className="px-2.5 py-1 rounded-sm bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-[11px] border border-hairline transition"
            >
              Investigator Sen
            </button>
            <button
              onClick={() => setDemoCredentials("admin")}
              className="px-2.5 py-1 rounded-sm bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-[11px] border border-hairline transition"
            >
              Chief Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
