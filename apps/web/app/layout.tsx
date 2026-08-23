import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecoveryGym — Make your robot sweat",
  description: "Robustness and recovery evaluation platform for robot policies",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="border-b border-gray-800 bg-gym-panel px-6 py-3 flex gap-6 text-sm">
          <a href="/" className="font-bold text-gym-accent">RecoveryGym</a>
          <a href="/playground" className="text-gray-300 hover:text-white">Playground</a>
          <a href="/benchmark" className="text-gray-300 hover:text-white">Benchmark</a>
        </nav>
        {children}
      </body>
    </html>
  );
}
