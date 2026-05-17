'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Sparkles, Film } from 'lucide-react';
import { apiGet } from '@/lib/api';

type Project = {
  id: string; title: string; status: string;
  final_url: string | null; thumbnail_url: string | null;
};
type Scene = {
  idx: number; narration: string; visual_url: string | null; voice_url: string | null;
};

export default function ProjectPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project>();
  const [scenes, setScenes] = useState<Scene[]>([]);

  useEffect(() => {
    (async () => {
      setProject(await apiGet<Project>(`/projects/${params.projectId}`));
      setScenes(await apiGet<Scene[]>(`/projects/${params.projectId}/scenes`));
    })();
  }, [params.projectId]);

  return (
    <main className="min-h-screen bg-ink-950">
      <header className="border-b border-white/5 bg-ink-900/40 px-6 py-4">
        <Link href="/dashboard" className="flex items-center gap-2 text-sm font-semibold">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-veedra-400 to-veedra-700">
            <Sparkles className="h-3.5 w-3.5 text-white" />
          </span>
          {project?.title ?? 'Loading...'}
        </Link>
      </header>

      <section className="mx-auto max-w-5xl px-6 py-8">
        {project?.final_url ? (
          <video controls src={project.final_url}
            className="aspect-video w-full rounded-2xl bg-black shadow-glow" />
        ) : (
          <div className="grid aspect-video w-full place-items-center rounded-2xl border border-white/10 bg-ink-900 text-neutral-500">
            <div className="text-center">
              <Film className="mx-auto h-10 w-10" />
              <div className="mt-3 text-sm">Status: {project?.status}</div>
            </div>
          </div>
        )}

        <h2 className="mt-10 text-lg font-semibold">Scenes</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {scenes.map(sc => (
            <div key={sc.idx} className="overflow-hidden rounded-xl border border-white/10 bg-ink-900">
              {sc.visual_url ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={sc.visual_url} alt="" className="aspect-video w-full object-cover" />
              ) : (
                <div className="aspect-video w-full bg-gradient-to-br from-veedra-700/20 to-veedra-900" />
              )}
              <div className="border-t border-white/5 p-3 text-xs text-neutral-300">
                {sc.narration}
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
