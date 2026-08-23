import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Nav } from "@/components/Nav";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RecoveryGym — Make your robot sweat",
  description: "Robustness and recovery evaluation platform for robot policies",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans">
        <Nav />
        {children}
        <footer className="mt-20 border-t border-gym-border/40 py-10 text-center text-sm text-gym-muted">
          <p>RecoveryGym · Stress-test policies · Recover · Adapt · Compare</p>
        </footer>
      </body>
    </html>
  );
}
