'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Sparkles, Send, Loader2, Film, Mic, Wand2, CheckCircle2, XCircle,
} from 'lucide-react';
import { apiPost, apiSSE, apiGet } from '@/lib/api';
import { createClient } from '@/lib/supabase/client';
import { cn } from '@/lib/utils';

type ChatItem =
  | { kind: 'user'; text: string }
  | { kind: 'agent'; step: string; role: string; content: any };

type Scene = {
  idx: number;
  narration: string;
  visual_prompt: string;
  visual_url?: string;
  voice_url?: string;
  duration_s: number;
};

export default function StudioPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [aspect, setAspect] = useState<'16:9' | '9:16' | '1:1'>('9:16');
  const [tone, setTone] = useState('friendly explainer');
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [chat, setChat] = useState<ChatItem[]>([]);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [finalUrl, setFinalUrl] = useState<string>();
  const [error, setError] = useState<string>();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    (async () => {
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      if (!data.session) router.replace('/login');
    })();
  }, [router]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [chat.length]);

  async function start() {
    if (!prompt.trim() || running) return;
    setRunning(true);
    setError(undefined);
    setFinalUrl(undefined);
    setScenes([]);
    setProgress(2);
    setChat(c => [...c, { kind: 'user', text: prompt }]);

    try {
      const { job_id, project_id } = await apiPost<{
        job_id: string; project_id: string;
      }>('/agent/run', { prompt, style: { aspect, tone, scenes: 4 } });

      await apiSSE(`/agent/stream/${job_id}`, ({ event, data }) => {
        if (event !== 'agent') return;
        setChat(c => [...c, { kind: 'agent', ...data }]);

        // bump progress based on step
        const bump: Record<string, number> = {
          script: 15, visual: 55, voice: 80, compose: 95, done: 100,
        };
        if (bump[data.step]) setProgress(p => Math.max(p, bump[data.step]));

        if (data.step === 'script' && Array.isArray(data.content.scenes)) {
          setScenes(data.content.scenes);
        }
        if (data.step === 'done') {
          setFinalUrl(data.content.final_url);
          // refresh scenes with URLs filled in
          apiGet<Scene[]>(`/projects/${project_id}/scenes`).then(setScenes);
        }
        if (data.step === 'error') setError(data.content.error || 'failed');
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="grid min-h-screen grid-cols-1 bg-ink-950 lg:grid-cols-[420px_1fr]">
      {/* ─── Left: chat / agent trace ──────────────────────────── */}
      <aside className="flex h-screen flex-col border-r border-white/5 bg-ink-900/40">
        <header className="flex items-center justify-between border-b border-white/5 px-5 py-4">
          <Link href="/dashboard" className="flex items-center gap-2 text-sm font-semibold">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-veedra-400 to-veedra-700">
              <Sparkles className="h-3.5 w-3.5 text-white" />
            </span>
            Veedra Studio
          </Link>
          {running && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-veedra-500/15 px-2 py-0.5 text-xs text-veedra-200">
              <Loader2 className="h-3 w-3 animate-spin" /> {progress}%
            </span>
          )}
        </header>

        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-5">
          {chat.length === 0 && (
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 text-sm text-neutral-400">
              Describe the video you want. The agent will draft a script, generate visuals
              and voice, then compose the final cut. Each step streams here.
            </div>
          )}
          {chat.map((m, i) => <ChatRow key={i} item={m} />)}
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
              <XCircle className="h-4 w-4" /> {error}
            </div>
          )}
        </div>

        <div className="border-t border-white/5 p-4">
          <div className="mb-2 flex gap-2 text-xs">
            <Pill label="9:16" active={aspect === '9:16'} onClick={() => setAspect('9:16')} />
            <Pill label="16:9" active={aspect === '16:9'} onClick={() => setAspect('16:9')} />
            <Pill label="1:1" active={aspect === '1:1'} onClick={() => setAspect('1:1')} />
            <input
              value={tone}
              onChange={e => setTone(e.target.value)}
              placeholder="tone"
              className="ml-auto w-32 rounded-full border border-white/10 bg-ink-800 px-3 py-1 text-xs outline-none focus:border-veedra-500/50"
            />
          </div>
          <div className="flex gap-2">
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) start();
              }}
              placeholder="A 30-second explainer about how solar panels work, vertical, friendly tone..."
              rows={3}
              className="flex-1 resize-none rounded-xl border border-white/10 bg-ink-800/80 p-3 text-sm outline-none ring-veedra-500/40 focus:ring-2"
            />
            <button
              onClick={start}
              disabled={running || !prompt.trim()}
              className="grid h-auto place-items-center rounded-xl bg-veedra-500 px-4 text-white shadow-glow transition hover:bg-veedra-400 disabled:opacity-50"
            >
              {running ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </div>
          <div className="mt-2 text-[10px] text-neutral-500">
            ⌘/Ctrl + Enter to send
          </div>
        </div>
      </aside>

      {/* ─── Right: preview ────────────────────────────────────── */}
      <section className="flex h-screen flex-col">
        <header className="border-b border-white/5 px-6 py-4">
          <div className="text-sm text-neutral-400">Preview</div>
        </header>

        <div className="flex-1 overflow-y-auto p-6">
          {finalUrl ? (
            <div className="mx-auto max-w-3xl">
              <video
                key={finalUrl}
                controls
                src={finalUrl}
                className="aspect-video w-full rounded-2xl bg-black shadow-glow"
              />
              <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                <CheckCircle2 className="h-3.5 w-3.5" /> Rendered
              </div>
            </div>
          ) : (
            <div
              className={cn(
                'grid gap-4',
                aspect === '9:16' && 'grid-cols-2 sm:grid-cols-4',
                aspect === '16:9' && 'grid-cols-1 sm:grid-cols-2',
                aspect === '1:1' && 'grid-cols-2 sm:grid-cols-3',
              )}
            >
              {(scenes.length ? scenes : Array.from({ length: 4 }).map((_, i) => ({
                idx: i, narration: '', visual_prompt: '', visual_url: undefined,
                voice_url: undefined, duration_s: 4,
              }))).map(sc => (
                <ScenePreview key={sc.idx} scene={sc as Scene} aspect={aspect} />
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function Pill({
  label, active, onClick,
}: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'rounded-full px-3 py-1 transition',
        active
          ? 'bg-veedra-500 text-white'
          : 'border border-white/10 bg-ink-800 text-neutral-300 hover:bg-ink-700',
      )}
    >
      {label}
    </button>
  );
}

function ChatRow({ item }: { item: ChatItem }) {
  if (item.kind === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-veedra-500/20 px-4 py-2 text-sm text-veedra-50">
          {item.text}
        </div>
      </div>
    );
  }
  const Icon = ICONS[item.step] ?? Sparkles;
  return (
    <div className="flex gap-3">
      <div className="mt-1 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-veedra-500/10 text-veedra-300">
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="flex-1 rounded-xl border border-white/5 bg-white/[0.03] p-3 text-xs">
        <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-wider text-neutral-500">
          {item.step} · {item.role}
        </div>
        <div className="text-neutral-200">{summarize(item)}</div>
      </div>
    </div>
  );
}

const ICONS: Record<string, any> = {
  script: Wand2, visual: Film, voice: Mic, compose: Sparkles, done: CheckCircle2,
  error: XCircle,
};

function summarize(item: Extract<ChatItem, { kind: 'agent' }>): string {
  const c = item.content ?? {};
  if (typeof c.message === 'string') return c.message;
  if (item.step === 'visual' || item.step === 'voice') {
    return `scene ${c.scene + 1} · ${c.status}`;
  }
  if (item.step === 'done') return `Render ready · ${c.scene_count} scenes`;
  return JSON.stringify(c).slice(0, 220);
}

function ScenePreview({ scene, aspect }: { scene: Scene; aspect: string }) {
  const ratio = aspect === '9:16' ? 'aspect-[9/16]' : aspect === '1:1' ? 'aspect-square' : 'aspect-video';
  return (
    <div className="overflow-hidden rounded-xl border border-white/10 bg-ink-900">
      <div className={cn('relative w-full bg-gradient-to-br from-veedra-700/20 to-veedra-900', ratio)}>
        {scene.visual_url ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img src={scene.visual_url} alt="" className="h-full w-full object-cover" />
        ) : scene.visual_prompt ? (
          <div className="absolute inset-0 grid place-items-center p-4 text-center text-xs text-veedra-200/70">
            generating...
          </div>
        ) : (
          <div className="absolute inset-0 grid place-items-center text-veedra-500/30">
            <Film className="h-8 w-8" />
          </div>
        )}
        <span className="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-[10px]">
          {scene.idx + 1}
        </span>
      </div>
      {scene.narration && (
        <div className="border-t border-white/5 p-3 text-[11px] leading-relaxed text-neutral-300">
          {scene.narration}
        </div>
      )}
    </div>
  );
}
