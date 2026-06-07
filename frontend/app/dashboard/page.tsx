"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { Logo, Wordmark } from "@/lib/Logo";

const API = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type Job = { id: string; prompt: string; status: string; output_url?: string; created_at: string };

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [needAuth, setNeedAuth] = useState(false);

  useEffect(() => {
    (async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { setNeedAuth(true); setLoading(false); return; }
      const res = await fetch(`${API}/jobs`, { headers: { Authorization: `Bearer ${session.access_token}` } });
      if (res.ok) setJobs(await res.json());
      setLoading(false);
    })();
  }, []);

  return (
    <div>
      <header className="flex justify-between items-center px-7 py-4 border-b border-line">
        <Link href="/" className="flex items-center gap-3"><Logo /><Wordmark /></Link>
        <Link href="/studio" className="border border-gold/40 text-gold rounded-md px-4 py-[7px] text-[13px]">New video</Link>
      </header>

      <main className="max-w-4xl mx-auto px-7 pt-10">
        <h1 className="text-2xl font-bold mb-6">Your projects</h1>
        {needAuth && (
          <div className="border border-gold/40 rounded-lg p-4 bg-panel text-silver text-sm">
            Please <Link href="/login" className="text-gold underline">sign in</Link> to see your jobs.
          </div>
        )}
        {loading && !needAuth && <div className="text-[#7e8290]">Loading…</div>}
        {!loading && !needAuth && jobs.length === 0 && (
          <div className="text-[#7e8290]">No jobs yet. <Link href="/studio" className="text-gold underline">Create one.</Link></div>
        )}
        <div className="flex flex-col gap-3">
          {jobs.map((j) => (
            <div key={j.id} className="bg-panel border border-line rounded-xl p-4 flex justify-between items-center gap-4">
              <div className="min-w-0">
                <div className="text-silver text-sm truncate">{j.prompt}</div>
                <div className="text-gold-dim text-[11px] font-mono mt-1">{j.id.slice(0, 8)} · {new Date(j.created_at).toLocaleString()}</div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="font-mono text-[10.5px] tracking-wide" style={{
                  color: j.status === "done" ? "#6fcf97" : j.status === "failed" ? "#eb5757" : "#d8b886",
                }}>{j.status.toUpperCase()}</span>
                {j.output_url && <a href={j.output_url} target="_blank" className="text-gold text-xs underline">view</a>}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
