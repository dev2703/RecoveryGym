"use client";

import { useState } from "react";
import { createBenchmark } from "@/lib/api";

const PROFILES = [
  { value: "quick", label: "Quick", episodes: "100 episodes", desc: "Fast sanity check across failure types" },
  { value: "standard", label: "Standard", episodes: "1,000 episodes", desc: "Balanced coverage for most evaluations" },
  { value: "deep", label: "Deep", episodes: "10,000 episodes", desc: "Exhaustive stress profile for publication" },
  { value: "ood", label: "OOD", episodes: "200 episodes", desc: "Held-out severity & composite failures" },
];

export default function BenchmarkPage() {
  const [profile, setProfile] = useState("quick");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = PROFILES.find((p) => p.value === profile)!;

  async function handleLaunch() {
    setLoading(true);
    setError(null);
    try {
      const bench = await createBenchmark({
        policy_id: "nominal",
        profile,
        recovery: true,
        compare_baseline: true,
      });
      window.location.href = `/reports/${bench.benchmark_id}`;
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-2xl mx-auto px-6 py-10 animate-fade-up">
      <div className="mb-8">
        <p className="section-label mb-2">Batch Evaluation</p>
        <h1 className="page-title">Stress Test</h1>
        <p className="text-gym-muted mt-2 text-sm">
          Launch a benchmark profile and get a full report with charts, exports, and fine-tuning options.
        </p>
      </div>

      <div className="card-static p-6 space-y-5">
        <h2 className="font-semibold">Choose a profile</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {PROFILES.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => setProfile(p.value)}
              className={`text-left rounded-xl border p-4 transition-all duration-200 ${
                profile === p.value
                  ? "border-gym-accent bg-gym-accent/10 shadow-glow"
                  : "border-gym-border bg-gym-surface hover:border-gym-muted/50 hover:bg-gym-panel"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold">{p.label}</span>
                {profile === p.value && (
                  <span className="h-2 w-2 rounded-full bg-gym-accent" />
                )}
              </div>
              <p className="text-xs text-gym-accent mb-1">{p.episodes}</p>
              <p className="text-xs text-gym-muted">{p.desc}</p>
            </button>
          ))}
        </div>

        <div className="rounded-xl bg-gym-surface border border-gym-border p-4">
          <p className="text-sm text-gym-muted">
            Selected: <span className="text-white font-medium">{selected.label}</span> · {selected.episodes}
          </p>
        </div>

        <button onClick={handleLaunch} disabled={loading} className="btn-primary w-full">
          {loading ? "Launching…" : "Launch Benchmark"}
        </button>

        {error && (
          <p className="text-gym-danger text-sm rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2">
            {error}
          </p>
        )}
      </div>
    </main>
  );
}
