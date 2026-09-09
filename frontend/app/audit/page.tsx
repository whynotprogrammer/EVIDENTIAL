"use client";

import React, { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import { AuditDashboard } from "./AuditDashboard";
import { getCurrentUser, getStoredToken, UserProfile } from "../../lib/api";

export default function AuditPage() {
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    if (getStoredToken()) {
      getCurrentUser().then(setUser).catch(() => {});
    }
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-black text-ink">
      <Navbar user={user} />
      <main className="flex-1">
        <AuditDashboard />
      </main>
    </div>
  );
}
