import Link from 'next/link';
import { ArrowRight, Sparkles, Wand2, Mic, Film, Eye, Zap } from 'lucide-react';

export default function LandingPage() {
  return (
    <main className="bg-veedra-aura min-h-screen">
      {/* ─── Nav ─────────────────────────────────────────────────── */}
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <Link href="/" className="flex items-center gap-2 text-xl font-semibold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-veedra-400 to-veedra-700 shadow-glow">
            <Sparkles className="h-4 w-4 text-white" />
          </span>
          Veedra
        </Link>
        <div className="flex items-center gap-3 text-sm">
          <Link href="/login" className="text-neutral-300 hover:text-white">
            Sign in
          </Link>
          <Link
            href="/signup"
            className="rounded-full bg-white px-4 py-1.5 font-medium text-ink-950 hover:bg-neutral-100"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* ─── Hero ────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 pt-16 pb-24 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-300">
          <span className="h-1.5 w-1.5 rounded-full bg-veedra-400" />
          AI directors, voices, and editors. One conversation.
        </div>
        <h1 className="mt-6 text-balance text-5xl font-semibold leading-[1.05] sm:text-7xl">
          Describe it. <br />
          <span className="bg-gradient-to-br from-veedra-200 via-veedra-400 to-veedra-600 bg-clip-text text-transparent">
            Veedra films it.
          </span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg text-neutral-300">
          A conversational video studio that turns prompts into finished shorts —
          script, visuals, voiceover, and edit, all directed by a chat with an AI agent.
        </p>
        <div className="mt-10 flex items-center justify-center gap-3">
          <Link
            href="/studio"
            className="group inline-flex items-center gap-2 rounded-full bg-veedra-500 px-6 py-3 text-sm font-semibold text-white shadow-glow hover:bg-veedra-400"
          >
            Open the studio
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
          </Link>
          <a
            href="#how"
            className="rounded-full border border-white/10 bg-white/5 px-6 py-3 text-sm font-semibold text-neutral-200 hover:bg-white/10"
          >
            How it works
          </a>
        </div>
      </section>

      {/* ─── Demo strip ──────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6">
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-ink-900/60 p-2 shadow-glow">
          <div className="rounded-2xl bg-grid p-10">
            <div className="rounded-xl border border-white/10 bg-ink-800/80 p-6 text-left text-sm">
              <div className="text-veedra-200/80">you</div>
              <div className="mt-1">
                make a 30-second explainer about how solar panels work, friendly tone, vertical
              </div>
              <div className="mt-4 text-veedra-200/80">veedra</div>
              <div className="mt-1 text-neutral-300">
                Drafting 4 scenes... generating visuals... synthesizing voice... composing.
              </div>
              <div className="mt-4 grid grid-cols-4 gap-3">
                {[1, 2, 3, 4].map(i => (
                  <div
                    key={i}
                    className="aspect-[9/16] rounded-lg bg-gradient-to-br from-veedra-700/40 to-veedra-900/40 ring-1 ring-white/5"
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features ────────────────────────────────────────────── */}
      <section id="how" className="mx-auto mt-32 max-w-6xl px-6">
        <h2 className="text-center text-3xl font-semibold sm:text-4xl">
          A studio that thinks alongside you
        </h2>
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(f => (
            <div
              key={f.title}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 transition hover:bg-white/[0.05]"
            >
              <f.icon className="h-6 w-6 text-veedra-300" />
              <div className="mt-4 text-base font-semibold">{f.title}</div>
              <div className="mt-1 text-sm text-neutral-400">{f.body}</div>
            </div>
          ))}
        </div>
      </section>

      <footer className="mx-auto mt-32 max-w-6xl px-6 py-12 text-xs text-neutral-500">
        © {new Date().getFullYear()} Veedra · Conversational video for everyone.
      </footer>
    </main>
  );
}

const FEATURES = [
  {
    icon: Wand2,
    title: 'Prompt → finished video',
    body: 'One sentence in, an edited short out. The agent decomposes, drafts, and renders.',
  },
  {
    icon: Film,
    title: 'Scene-by-scene editing',
    body: 'Swap any visual, rewrite any line, change voice. Re-render only what changed.',
  },
  {
    icon: Mic,
    title: 'Real voices, multi-language',
    body: 'ElevenLabs voices out of the box. Bring your own clone, mix narration and dialog.',
  },
  {
    icon: Eye,
    title: 'Video understanding',
    body: 'Drop in a clip, ask questions, pull moments out by description. ViMax-style agent.',
  },
  {
    icon: Sparkles,
    title: 'Story templates',
    body: 'Explainer, story, ad, recap — start from a template that already knows the beats.',
  },
  {
    icon: Zap,
    title: 'Streamed agent trace',
    body: 'Watch the director think. Every step is visible and reproducible.',
  },
];
