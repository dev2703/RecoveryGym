"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/playground", label: "Playground" },
  { href: "/benchmark", label: "Benchmark" },
];

export function Nav() {
  const pathname = usePathname();

  function linkClass(href: string) {
    const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
    return active ? "nav-pill-active" : "nav-pill";
  }

  return (
    <header className="sticky top-0 z-50 border-b border-gym-border/60 bg-gym-bg/80 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gym-accent text-lg font-black text-black shadow-glow transition-transform group-hover:scale-105">
            R
          </span>
          <span className="text-base font-bold tracking-tight text-white group-hover:text-gym-accent transition-colors">
            RecoveryGym
          </span>
        </Link>

        <div className="hidden sm:flex items-center gap-1 rounded-full border border-gym-border bg-gym-surface/80 p-1">
          {links.map(({ href, label }) => (
            <Link key={href} href={href} className={linkClass(href)}>
              {label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <Link href="/playground" className="btn-primary hidden sm:inline-flex !py-2 !px-5 !text-xs">
            Run Episode
          </Link>
          <div className="flex sm:hidden gap-1">
            {links.map(({ href, label }) => (
              <Link key={href} href={href} className={linkClass(href)}>
                {label}
              </Link>
            ))}
          </div>
        </div>
      </nav>
    </header>
  );
}
