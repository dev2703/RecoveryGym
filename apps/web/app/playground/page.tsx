"use client";

import { useState } from "react";
import { createRun, createBenchmark } from "@/lib/api";
import { SimPanel } from "@/components/SimPanel";
import { EventTimeline } from "@/components/EventTimeline";

const FAILURES = ["OBJECT_SLIP", "GRASP_MISS", "TARGET_SHIFT", "ACTUATOR_DEVIATION", "SENSOR_NOISE", "OCCLUSION", "OBSTACLE_APPEARS", "COMPOSITE_FAILURE"];

export default function PlaygroundPage() {
  const [policyId, setPolicyId] = useState("nominal");
  const [failureType, setFailureType] = useState("OBJECT_SLIP");
  const [seed, setSeed] = useState(42);
  const [recovery, setRecovery] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const data = await createRun({
        policy_id: policyId,
        task_id: "pick_place_v1",
        failure: { type: failureType, seed, time: 30.0, severity: 0.5, deterministic: true },
        recovery,
        seed,
      });
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleStressTest() {
    setLoading(true);
    setError(null);
    try {
      const bench = await createBenchmark({ policy_id: policyId, profile: "quick", episodes: 20, recovery: true });
      window.location.href = `/reports/${bench.benchmark_id}`;
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const finalState = result?.final_state || {};
  const events = result?.events || [];

  return (
    <main className="max-w-6xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Playground</h1>

        <div className="bg-gym-panel rounded-lg p-4 space-y-3 border border-gray-800">
          <label className="block text-sm text-gray-400">Policy</label>
          <select value={policyId} onChange={(e) => setPolicyId(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2">
            <option value="nominal">Nominal (scripted)</option>
            <option value="smolvla">SmolVLA (stub)</option>
          </select>

          <label className="block text-sm text-gray-400">Failure type</label>
          <select value={failureType} onChange={(e) => setFailureType(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2">
            {FAILURES.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>

          <label className="block text-sm text-gray-400">Seed</label>
          <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2" />

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={recovery} onChange={(e) => setRecovery(e.target.checked)} />
            Enable recovery
          </label>

          <div className="flex gap-2 pt-2">
            <button onClick={handleRun} disabled={loading} className="bg-gym-accent text-black px-4 py-2 rounded font-medium disabled:opacity-50">
              {loading ? "Running..." : "Run"}
            </button>
            <button onClick={handleStressTest} disabled={loading} className="border border-gym-accent text-gym-accent px-4 py-2 rounded disabled:opacity-50">
              Stress Test
            </button>
          </div>
          {error && <p className="text-gym-danger text-sm">{error}</p>}
        </div>

        <SimPanel state={finalState} />
      </div>

      <div className="space-y-4">
        {result && (
          <>
            <div className="bg-gym-panel rounded-lg p-4 border border-gray-800">
              <h2 className="font-semibold mb-2">Recovery Score</h2>
              <p className="text-3xl text-gym-accent">{(result.recovery_score * 100).toFixed(1)}</p>
            </div>

            <div className="bg-gym-panel rounded-lg p-4 border border-gray-800">
              <h2 className="font-semibold mb-2">Recovery Plan</h2>
              <div className="flex flex-wrap gap-2">
                {(result.recovery_plan || []).map((p: string, i: number) => (
                  <span key={i} className="bg-gray-800 px-2 py-1 rounded text-xs">{p}</span>
                ))}
              </div>
            </div>

            <EventTimeline events={events} />

            {result.counterfactual && (
              <div className="bg-gym-panel rounded-lg p-4 border border-gray-800">
                <h2 className="font-semibold mb-1 text-gym-accent">WAM Counterfactual</h2>
                <p className="text-xs text-gray-400">Provider: {result.counterfactual.provider || "wam"}</p>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
