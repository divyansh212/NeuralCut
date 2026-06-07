export function Logo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-label="NeuralCut">
      <defs>
        <linearGradient id="ncg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f0dcb0" />
          <stop offset="0.5" stopColor="#d8b886" />
          <stop offset="1" stopColor="#8a7150" />
        </linearGradient>
        <filter id="ncglow">
          <feGaussianBlur stdDeviation="1.4" />
        </filter>
      </defs>
      <path
        d="M20 80 L20 20 L40 20 L40 55 L66 20 L80 20 L80 80 L60 80 L60 45 L34 80 Z"
        fill="none" stroke="url(#ncg)" strokeWidth="3" strokeLinejoin="round"
        filter="url(#ncglow)" opacity="0.55"
      />
      <path
        d="M20 80 L20 20 L40 20 L40 55 L66 20 L80 20 L80 80 L60 80 L60 45 L34 80 Z"
        fill="none" stroke="url(#ncg)" strokeWidth="2" strokeLinejoin="round"
      />
    </svg>
  );
}

export function Wordmark() {
  return (
    <div className="leading-none">
      <div className="font-serif text-[19px] font-bold tracking-[3px]">
        <span className="text-silver">NEURAL</span>
        <span className="text-gold">CUT</span>
      </div>
      <div className="text-[8.5px] tracking-[4px] text-gold-dim mt-[3px]">AI VIDEO EDITING</div>
    </div>
  );
}
