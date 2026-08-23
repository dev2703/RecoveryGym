"use client";

import { useState } from "react";
import { createBenchmark } from "@/lib/api";

export default function BenchmarkPage() {
  const [profile, setProfile] = useState("quick");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <main className="max-w-xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold mb-6">Stress Test</h1>
      <div className="bg-gym-panel rounded-lg p-6 border border-gray-800 space-y-4">
        <label className="block text-sm text-gray-400">Profile</label>
        <select value={profile} onChange={(e) => setProfile(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2">
          <option value="quick">Quick (100 episodes)</option>
          <option value="standard">Standard (1,000 episodes)</option>
          <option value="deep">Deep (10,000 episodes)</option>
          <option value="ood">OOD (200 episodes)</option>
        </select>
        <button onClick={handleLaunch} disabled={loading} className="w-full bg-gym-accent text-black py-3 rounded font-medium disabled:opacity-50">
          {loading ? "Launching..." : "Launch Benchmark"}
        </button>
        {error && <p className="text-gym-danger text-sm">{error}</p>}
      </div>
    </main>
  );
}
