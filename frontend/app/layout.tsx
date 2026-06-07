import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuralCut · AI Video Editing",
  description: "Type a prompt. Watch the director think. A multi-agent text-to-video studio.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
