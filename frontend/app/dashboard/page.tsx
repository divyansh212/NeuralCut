'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Plus, Film, Sparkles } from 'lucide-react';
import { apiGet } from '@/lib/api';
import { createClient } from '@/lib/supabase/client';

type Project = {
  id: string;
  title: string;
  status: string;
  thumbnail_url: string | null;
  created_at: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        router.replace('/login');
        return;
      }
      try {
        const list = await apiGet<Project[]>('/projects');
        setProjects(list);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  return (
    <main className="min-h-screen bg-ink-950">
      <header className="border-b border-white/5 bg-ink-900/40">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-veedra-400 to-veedra-700">
              <Sparkles className="h-3.5 w-3.5 text-white" />
            </span>
            Veedra
          </Link>
          <Link
            href="/studio"
            className="inline-flex items-center gap-2 rounded-full bg-veedra-500 px-4 py-1.5 text-sm font-semibold text-white shadow-glow hover:bg-veedra-400"
          >
            <Plus className="h-4 w-4" /> New project
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Your projects</h1>

        {loading ? (
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map(i => (
              <div key={i} className="h-48 animate-pulse rounded-2xl bg-ink-800" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map(p => (
              <Link
                key={p.id}
                href={`/studio/${p.id}`}
                className="group overflow-hidden rounded-2xl border border-white/10 bg-ink-900 transition hover:border-veedra-500/50"
              >
                <div className="relative aspect-video w-full overflow-hidden bg-gradient-to-br from-veedra-700/40 to-veedra-900">
                  {p.thumbnail_url ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={p.thumbnail_url} alt="" className="h-full w-full object-cover" />
                  ) : (
                    <div className="grid h-full place-items-center text-veedra-300/40">
                      <Film className="h-10 w-10" />
                    </div>
                  )}
                  <span className="absolute right-2 top-2 rounded-full bg-black/50 px-2 py-0.5 text-[10px] uppercase tracking-wider">
                    {p.status}
                  </span>
                </div>
                <div className="p-4">
                  <div className="truncate text-sm font-medium group-hover:text-veedra-200">
                    {p.title}
                  </div>
                  <div className="mt-1 text-xs text-neutral-500">
                    {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="mt-16 grid place-items-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] py-20 text-center">
      <Film className="h-10 w-10 text-veedra-300" />
      <div className="mt-4 text-base font-medium">No projects yet</div>
      <p className="mt-1 max-w-sm text-sm text-neutral-400">
        Open the studio and describe your first video. Veedra will direct it for you.
      </p>
      <Link
        href="/studio"
        className="mt-6 inline-flex items-center gap-2 rounded-full bg-veedra-500 px-5 py-2 text-sm font-semibold text-white shadow-glow hover:bg-veedra-400"
      >
        <Plus className="h-4 w-4" /> Start a project
      </Link>
    </div>
  );
}
