"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { Logo, Wordmark } from "@/lib/Logo";

const API = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const STAGES = [
  { key: "script", label: "Script Agent", sub: "decompose prompt into scenes" },
  { key: "visuals", label: "Visual Agent", sub: "render frames per scene · parallel" },
  { key: "voice", label: "Voice Agent", sub: "synthesize narration · parallel" },
  { key: "compose", label: "Compositor", sub: "ffmpeg assembly" },
];

type Evt = { stage: string; status: string; detail?: any };

export default function Studio() {
  const [prompt, setPrompt] = useState("a lighthouse waking up at dawn over a stormy sea");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [events, setEvents] = useState<Evt[]>([]);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [authed, setAuthed] = useState<boolean | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setAuthed(!!data.session));
  }, []);
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [events]);

  const stageState = (key: string): "idle" | "start" | "done" => {
    let s: "idle" | "start" | "done" = "idle";
    for (const e of events) {
      if (e.stage === key && e.status === "start") s = "start";
      if (e.stage === key && e.status === "done") s = "done";
    }
    return s;
  };

  async function generate() {
    setEvents([]); setVideoUrl(null); setStatus("queued");
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) { setStatus("idle"); setAuthed(false); return; }

    const res = await fetch(`${API}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${session.access_token}` },
      body: JSON.stringify({ prompt }),
    });
    if (!res.ok) { setStatus("failed"); return; }
    const { job_id } = await res.json();
    setJobId(job_id);
    setStatus("running");

    // fetch + ReadableStream SSE reader (token passed as query param, validated
    // server-side; the stream endpoint also confirms job ownership).
    const streamRes = await fetch(`${API}/jobs/${job_id}/stream?token=${encodeURIComponent(session.access_token)}`);
    const reader = streamRes.body!.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop() || "";
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const evt: Evt = JSON.parse(line.slice(5).trim());
        setEvents((prev) => [...prev, evt]);
        if (evt.stage === "done") { setVideoUrl(evt.detail?.url); setStatus("done"); }
        if (evt.status === "failed") setStatus("failed");
      }
    }
  }

  const busy = status === "queued" || status === "running";

  return (
    <div>
      <header className="flex justify-between items-center px-7 py-4 border-b border-line sticky top-0 bg-ink/80 backdrop-blur z-10">
        <Link href="/" className="flex items-center gap-3"><Logo /><Wordmark /></Link>
        <Link href="/dashboard" className="border border-line text-[#7e8290] rounded-md px-4 py-[7px] text-[13px]">Dashboard</Link>
      </header>

      {authed === false && (
        <div className="max-w-5xl mx-auto px-5 pt-5">
          <div className="border border-gold/40 rounded-lg p-4 bg-panel text-silver text-sm">
            You need to <Link href="/login" className="text-gold underline">sign in</Link> — the API rejects unauthenticated requests (no auth bypass).
          </div>
        </div>
      )}

      <main className="grid gap-4 p-5" style={{ gridTemplateColumns: "minmax(300px,1fr) minmax(280px,0.9fr)" }}>
        {/* LEFT: prompt + pipeline + result */}
        <section className="flex flex-col gap-4">
          <div className="bg-panel border border-line rounded-xl p-4">
            <div className="text-gold-dim tracking-[3px] text-[10.5px] font-mono mb-3">PROMPT</div>
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} disabled={busy}
              placeholder="Describe your video…"
              className="w-full min-h-[96px] bg-ink border border-line rounded-lg p-3 text-sm text-silver resize-y" />
            <button onClick={generate} disabled={busy}
              className="w-full mt-3 rounded-lg py-3 font-bold text-ink disabled:opacity-60 disabled:cursor-not-allowed"
              style={{ background: busy ? "#1a1a20" : "linear-gradient(135deg,#f0dcb0,#8a7150)", color: busy ? "#8a7150" : "#050507" }}>
              {busy ? "Generating…" : "Generate Video"}
            </button>
            {jobId && (
              <div className="flex justify-between items-center mt-3">
                <span className="font-mono text-xs text-[#7e8290]">{jobId.slice(0, 13)}</span>
                <StatusPill status={status} />
              </div>
            )}
          </div>

          <div className="bg-panel border border-line rounded-xl p-4">
            <div className="text-gold-dim tracking-[3px] text-[10.5px] font-mono mb-3">PIPELINE</div>
            <div className="flex flex-col gap-2.5">
              {STAGES.map((st) => <StageBar key={st.key} label={st.label} sub={st.sub} state={stageState(st.key)} />)}
            </div>
          </div>

          {videoUrl && (
            <div className="bg-panel border border-line rounded-xl p-4">
              <div className="text-gold-dim tracking-[3px] text-[10.5px] font-mono mb-3">RENDER</div>
              <video src={videoUrl} controls className="w-full rounded-lg border border-line" />
              <div className="font-mono text-[11.5px] text-gold mt-2 break-all">{videoUrl}</div>
            </div>
          )}
        </section>

        {/* RIGHT: live event stream */}
        <section>
          <div className="bg-panel border border-line rounded-xl p-4 h-full flex flex-col">
            <div className="text-gold-dim tracking-[3px] text-[10.5px] font-mono mb-3">
              LIVE STREAM <span className="font-normal">· job:{jobId?.slice(0, 8) || "—"}</span>
            </div>
            <div ref={logRef} className="flex-1 min-h-[320px] max-h-[520px] overflow-y-auto bg-ink border border-line rounded-lg p-3 font-mono text-xs leading-7">
              {events.length === 0 && <div className="text-[#4a4d56] italic">SUBSCRIBE job:&lt;id&gt; — awaiting events…</div>}
              {events.map((e, i) => (
                <div key={i} className="whitespace-pre-wrap break-words">
                  <span className="text-gold-dim">›</span>{" "}
                  <span className="text-gold">{e.stage}</span>
                  <span className="text-silver"> — {e.status}</span>
                  {e.detail && <span className="text-[#7e8290]"> {JSON.stringify(e.detail)}</span>}
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, { c: string; t: string }> = {
    idle: { c: "#7e8290", t: "IDLE" },
    queued: { c: "#7e8290", t: "QUEUED" },
    running: { c: "#d8b886", t: "RUNNING" },
    done: { c: "#6fcf97", t: "DONE" },
    failed: { c: "#eb5757", t: "FAILED" },
  };
  const m = map[status] || map.idle;
  return (
    <span className="inline-flex items-center gap-1.5 border rounded-full px-2.5 py-[3px] text-[10.5px] font-mono tracking-wide"
      style={{ color: m.c, borderColor: m.c + "55" }}>
      <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: m.c }} />{m.t}
    </span>
  );
}

function StageBar({ label, sub, state }: { label: string; sub: string; state: "idle" | "start" | "done" }) {
  const active = state === "start", done = state === "done";
  return (
    <div className="flex items-center gap-3 border rounded-lg px-3 py-2.5 transition-colors"
      style={{ borderColor: active ? "#d8b88666" : done ? "#6fcf9755" : "#1c1c22" }}>
      <span className={"w-2.5 h-2.5 rounded-full flex-shrink-0 " + (active ? "animate-pulse2" : "")}
        style={{ background: done ? "#6fcf97" : active ? "#d8b886" : "#2a2a32", boxShadow: active ? "0 0 10px #d8b886" : "none" }} />
      <div className="flex-1">
        <div className="text-[13px] font-semibold" style={{ color: done || active ? "#cfd2d8" : "#5a5d68" }}>{label}</div>
        <div className="text-[11px] text-[#5a5d68]">{sub}</div>
      </div>
      <span className="text-[10px] tracking-wide" style={{ color: done ? "#6fcf97" : active ? "#d8b886" : "#3a3d46" }}>
        {done ? "DONE" : active ? "···" : "IDLE"}
      </span>
    </div>
  );
}
