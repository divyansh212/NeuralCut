import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Veedra · AI video studio',
  description:
    'Conversational AI video creation. Describe it, Veedra directs the scenes, voices, and edit.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-ink-950 text-neutral-200 antialiased">
        {children}
      </body>
    </html>
  );
}
