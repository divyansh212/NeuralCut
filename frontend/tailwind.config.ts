import type { Config } from 'tailwindcss';

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: { 950: '#07070a', 900: '#0d0d12', 800: '#15151c', 700: '#22222c' },
        veedra: {
          50:  '#f1ecff',
          100: '#e3d7ff',
          200: '#c8b0ff',
          300: '#a989ff',
          400: '#8a62ff',
          500: '#6a3bff',
          600: '#5326e0',
          700: '#3f1aab',
          800: '#2c1278',
          900: '#1c0a4f',
        },
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        display: ['ui-sans-serif', 'system-ui'],
      },
      boxShadow: {
        glow: '0 0 80px -10px rgba(106, 59, 255, 0.35)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
} satisfies Config;
