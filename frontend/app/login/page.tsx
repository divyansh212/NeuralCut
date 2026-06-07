"use client";

import { useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { Logo, Wordmark } from "@/lib/Logo";

export default function Login() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function sendMagicLink() {
    setErr(null);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: typeof window !== "undefined" ? `${window.location.origin}/studio` : undefined },
    });
    if (error) setErr(error.message);
    else setSent(true);
  }

  return (
    <div>
      <header className="flex items-center px-7 py-4 border-b border-line">
        <Link href="/" className="flex items-center gap-3">
          <Logo />
          <Wordmark />
        </Link>
      </header>

      <main className="max-w-md mx-auto px-7 pt-24">
        <h1 className="text-3xl font-bold mb-2">Sign in</h1>
        <p className="text-[#9b9ea8] mb-8">Magic-link auth via Supabase. No password.</p>

        {sent ? (
          <div className="border border-gold/40 rounded-xl p-5 bg-panel text-silver">
            Check your inbox — a sign-in link is on its way to <span className="text-gold">{email}</span>.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="bg-ink border border-line rounded-lg px-4 py-3 text-silver"
            />
            <button onClick={sendMagicLink} disabled={!email}
              className="rounded-lg px-4 py-3 font-bold text-ink disabled:opacity-50"
              style={{ background: "linear-gradient(135deg,#f0dcb0,#8a7150)" }}>
              Send magic link
            </button>
            {err && <div className="text-red-400 text-sm">{err}</div>}
          </div>
        )}
      </main>
    </div>
  );
}
