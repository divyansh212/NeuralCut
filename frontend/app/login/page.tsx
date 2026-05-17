'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Sparkles, Mail } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [err, setErr] = useState<string>();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('sending');
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: `${window.location.origin}/dashboard` },
      });
      if (error) throw error;
      setStatus('sent');
    } catch (e: any) {
      setErr(e.message);
      setStatus('error');
    }
  }

  return (
    <main className="bg-veedra-aura grid min-h-screen place-items-center px-6">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-10 flex items-center justify-center gap-2 text-xl font-semibold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-veedra-400 to-veedra-700 shadow-glow">
            <Sparkles className="h-4 w-4 text-white" />
          </span>
          Veedra
        </Link>

        <div className="rounded-2xl border border-white/10 bg-ink-900/60 p-8">
          <h1 className="text-xl font-semibold">Sign in</h1>
          <p className="mt-1 text-sm text-neutral-400">
            We&apos;ll email you a magic link.
          </p>

          {status === 'sent' ? (
            <div className="mt-8 rounded-xl border border-veedra-500/30 bg-veedra-500/10 p-4 text-sm">
              Check <span className="font-medium">{email}</span> for a sign-in link.
            </div>
          ) : (
            <form onSubmit={onSubmit} className="mt-6 space-y-3">
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-2.5 h-5 w-5 text-neutral-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full rounded-xl border border-white/10 bg-ink-800/80 py-2.5 pl-10 pr-3 text-sm outline-none ring-veedra-500/40 focus:ring-2"
                />
              </div>
              <button
                disabled={status === 'sending'}
                className="w-full rounded-xl bg-veedra-500 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:bg-veedra-400 disabled:opacity-60"
              >
                {status === 'sending' ? 'Sending...' : 'Send magic link'}
              </button>
              {err && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
                  {err}
                </div>
              )}
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
