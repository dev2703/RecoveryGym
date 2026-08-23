"use client";

import { useEffect, useState } from "react";
import { createRun, createBenchmark, getHealth } from "@/lib/api";
import type { HealthInfo, RunResult } from "@/lib/types";
import { ReactorPanel } from "@/components/ReactorPanel";
import { SimPanel } from "@/components/SimPanel";
import { EventTimeline } from "@/components/EventTimeline";

const FAILURES = ["OBJECT_SLIP", "GRASP_MISS", "TARGET_SHIFT", "ACTUATOR_DEVIATION", "SENSOR_NOISE", "OCCLUSION", "OBSTACLE_APPEARS", "COMPOSITE_FAILURE"];

export default function PlaygroundPage() {
  const [policyId, setPolicyId] = useState("nominal");
  const [failureType, setFailureType] = useState("OBJECT_SLIP");
  const [seed, setSeed] = useState(42);
  const [recovery, setRecovery] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthInfo | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function handleRun() {
    setLoading(true);
    setError(null);
    setResult(null);
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
  const reactorPreviews = result?.counterfactual?.frame_previews ?? [];
  const hasReactorVideo = reactorPreviews.length > 0;
  const hasReactorAttempt = Boolean(result?.counterfactual || result?.counterfactual_error);
  const wamMode = health?.wam_mode ?? "reactor";
  const reactorModel = health?.reactor_model ?? "reactor/lingbot-world-2";

  return (
    <main className="max-w-6xl mx-auto px-6 py-10 space-y-8 animate-fade-up">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="section-label mb-2">Interactive Lab</p>
          <h1 className="page-title">Playground</h1>
          <p className="text-gym-muted mt-2 text-sm max-w-lg">
            Configure a failure, run an episode, and watch recovery unfold in real time.
          </p>
        </div>
        {health && (
          <div className="flex flex-wrap gap-2">
            <span className="badge-accent">{health.wam_mode}</span>
            <span className="badge-muted">{health.reactor_model.split("/").pop()}</span>
          </div>
        )}
      </div>

      <ReactorPanel
        counterfactual={result?.counterfactual}
        error={result?.counterfactual_error ?? null}
        wamMode={wamMode}
        reactorModel={reactorModel}
        loading={loading}
        hasRun={Boolean(result) || loading}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="card-static p-6 space-y-4">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-gym-accent animate-pulse" />
              Scenario Config
            </h2>

            <div>
              <label className="block text-sm text-gym-muted mb-1.5">Policy</label>
              <select value={policyId} onChange={(e) => setPolicyId(e.target.value)} className="select-field">
                <option value="nominal">Nominal (scripted)</option>
                <option value="smolvla">SmolVLA (zero-shot)</option>
                <option value="smolvla_ft">SmolVLA fine-tuned (HF)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gym-muted mb-1.5">Failure type</label>
              <select value={failureType} onChange={(e) => setFailureType(e.target.value)} className="select-field">
                {FAILURES.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gym-muted mb-1.5">Seed</label>
              <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="input-field" />
            </div>

            <label className="flex items-center gap-3 text-sm cursor-pointer group">
              <input
                type="checkbox"
                checked={recovery}
                onChange={(e) => setRecovery(e.target.checked)}
                className="h-4 w-4 rounded border-gym-border bg-gym-surface accent-gym-accent"
              />
              <span className="group-hover:text-gym-accent transition-colors">Enable recovery</span>
            </label>

            <div className="flex flex-wrap gap-3 pt-2">
              <button onClick={handleRun} disabled={loading} className="btn-primary !py-2.5 !px-5">
                {loading ? "Running…" : "Run Episode"}
              </button>
              <button onClick={handleStressTest} disabled={loading} className="btn-outline !py-2.5 !px-5">
                Stress Test
              </button>
            </div>
            {error && (
              <p className="text-gym-danger text-sm rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2">
                {error}
              </p>
            )}
          </div>

          {!hasReactorVideo && !hasReactorAttempt && !loading && <SimPanel state={finalState} />}
        </div>

        <div className="space-y-4">
          {result && (
            <>
              <div className="card-static p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gym-accent/5 rounded-full blur-3xl group-hover:bg-gym-accent/10 transition-colors" />
                <p className="section-label mb-1">Recovery Score</p>
                <p className="stat-value">{(result.recovery_score * 100).toFixed(1)}%</p>
              </div>

              <div className="card-static p-6">
                <h2 className="font-semibold mb-3">Recovery Plan</h2>
                <div className="flex flex-wrap gap-2">
                  {(result.recovery_plan || []).map((p: string, i: number) => (
                    <span key={i} className="badge-accent">{p}</span>
                  ))}
                  {(result.recovery_plan || []).length === 0 && (
                    <span className="text-gym-muted text-sm">No recovery steps recorded.</span>
                  )}
                </div>
              </div>

              <EventTimeline events={events} />

              {hasReactorVideo && (
                <div className="card-static p-6">
                  <h2 className="font-semibold text-sm mb-3">Sim Telemetry</h2>
                  <SimPanel state={finalState} />
                </div>
              )}
            </>
          )}

          {!result && !loading && (
            <div className="card p-8 text-center">
              <p className="text-4xl mb-3 animate-float inline-block">🤖</p>
              <p className="text-gym-muted text-sm">
                Configure a scenario and hit <span className="text-gym-accent font-medium">Run Episode</span> to see results here.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
