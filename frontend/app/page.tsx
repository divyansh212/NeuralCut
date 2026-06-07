import Link from "next/link";
import { Logo, Wordmark } from "@/lib/Logo";

const STAGES = [
  { label: "Script Agent", sub: "decompose prompt into scenes" },
  { label: "Visual Agent", sub: "render frames per scene · parallel" },
  { label: "Voice Agent", sub: "synthesize narration · parallel" },
  { label: "Compositor", sub: "ffmpeg-style assembly" },
];

export default function Landing() {
  return (
    <div>
      <header className="flex justify-between items-center px-7 py-4 border-b border-line sticky top-0 bg-ink/80 backdrop-blur z-10">
        <div className="flex items-center gap-3">
          <Logo />
          <Wordmark />
        </div>
        <Link href="/login" className="border border-gold/40 text-gold rounded-md px-4 py-[7px] text-[13px] tracking-wide">
          Sign in
        </Link>
      </header>

      <main className="max-w-3xl mx-auto px-7 pt-16 pb-24">
        <div className="animate-rise text-gold-dim tracking-[5px] text-[11px] font-mono">
          MULTI-AGENT · TEXT → VIDEO
        </div>
        <h1 className="animate-rise text-5xl leading-[1.08] font-bold tracking-tight mt-4 mb-5" style={{ animationDelay: "80ms" }}>
          Type a prompt.<br />
          <span className="text-gold">Watch the director think.</span>
        </h1>
        <p className="animate-rise text-[#9b9ea8] text-[17px] leading-relaxed max-w-xl mb-8" style={{ animationDelay: "160ms" }}>
          A script agent decomposes your idea into scenes. Visual and voice agents run in
          parallel. An ffmpeg compositor assembles the cut. You watch every stage stream live
          over Redis pub/sub.
        </p>
        <div className="animate-rise flex gap-3 flex-wrap" style={{ animationDelay: "240ms" }}>
          <Link href="/studio" className="rounded-lg px-6 py-3 text-[15px] font-bold tracking-wide text-ink"
            style={{ background: "linear-gradient(135deg,#f0dcb0,#8a7150)" }}>
            Enter the Studio →
          </Link>
          <Link href="/login" className="rounded-lg px-6 py-3 text-[15px] border border-line text-silver">
            Sign in
          </Link>
        </div>

        <div className="animate-rise mt-14" style={{ animationDelay: "320ms" }}>
          <div className="text-gold-dim tracking-[4px] text-[11px] font-mono mb-4">THE PIPELINE</div>
          <div className="flex items-stretch gap-2 flex-wrap">
            {STAGES.map((s, i) => (
              <div key={s.label} className="flex items-stretch gap-2">
                <div className="flex-1 min-w-[150px] border border-line rounded-xl px-4 py-3.5 bg-panel">
                  <div className="text-silver font-semibold text-sm">{s.label}</div>
                  <div className="text-[#6b6e78] text-[11.5px] mt-1">{s.sub}</div>
                </div>
                {i < STAGES.length - 1 && <div className="text-gold-dim self-center text-lg">→</div>}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
