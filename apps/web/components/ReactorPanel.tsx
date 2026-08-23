"use client";

import { useEffect, useMemo, useState } from "react";
import type { CounterfactualResult } from "@/lib/types";

interface ReactorPanelProps {
  counterfactual?: CounterfactualResult | null;
  error?: string | null;
  wamMode?: string;
  reactorModel?: string;
  loading?: boolean;
  hasRun?: boolean;
}

export function ReactorPanel({
  counterfactual,
  error,
  wamMode = "reactor",
  reactorModel = "reactor/lingbot-world-2",
  loading = false,
  hasRun = false,
}: ReactorPanelProps) {
  const previews = counterfactual?.frame_previews ?? [];
  const [frameIdx, setFrameIdx] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    setFrameIdx(0);
    setPlaying(true);
  }, [counterfactual?.frame_count, counterfactual?.model, previews.length]);

  useEffect(() => {
    if (!playing || previews.length <= 1) return;
    const timer = setInterval(() => {
      setFrameIdx((idx) => (idx + 1) % previews.length);
    }, 120);
    return () => clearInterval(timer);
  }, [playing, previews.length]);

  const activeFrame = previews[frameIdx];
  const referenceSrc = useMemo(
    () =>
      counterfactual?.reference_image_b64
        ? `data:image/png;base64,${counterfactual.reference_image_b64}`
        : null,
    [counterfactual?.reference_image_b64]
  );
  const frameSrc = activeFrame ? `data:image/jpeg;base64,${activeFrame.jpeg_b64}` : null;
  const hasVideo = previews.length > 0;
  const generatedOffWire =
    !hasVideo &&
    hasRun &&
    !error &&
    (counterfactual?.frame_count ?? 0) > 0 &&
    Boolean(counterfactual?.generation_started);

  return (
    <div className="card-static p-6 space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h2 className="font-semibold text-lg flex items-center gap-2">
          <span className="text-xl">🎬</span>
          Reactor · LingBot World
        </h2>
        <span className="badge-accent">
          {wamMode} · {reactorModel.split("/").pop()}
        </span>
      </div>

      {loading && (
        <div className="aspect-video bg-gym-surface rounded-2xl flex flex-col items-center justify-center gap-3 border border-gym-border">
          <div className="h-8 w-8 rounded-full border-2 border-gym-accent border-t-transparent animate-spin" />
          <p className="text-gym-muted text-sm">Generating counterfactual rollout…</p>
        </div>
      )}

      {!loading && error && (
        <div className="aspect-video bg-gym-surface rounded-2xl flex items-center justify-center p-6 text-center border border-red-500/30">
          <p className="text-sm text-gym-danger">{error}</p>
        </div>
      )}

      {!loading && !error && !hasRun && (
        <div className="aspect-video bg-gym-surface rounded-2xl flex flex-col items-center justify-center p-8 text-center gap-3 border border-gym-border border-dashed">
          <span className="text-4xl opacity-50">📹</span>
          <p className="text-gym-muted text-sm max-w-sm">Run an episode to generate a Reactor counterfactual.</p>
          {wamMode === "mock" && (
            <p className="text-xs text-gym-muted/70">API is in mock WAM mode — deploy with REACTOR_API_KEY for live video.</p>
          )}
        </div>
      )}

      {!loading && !error && hasRun && generatedOffWire && (
        <div className="aspect-video bg-gym-surface rounded-2xl flex flex-col items-center justify-center p-6 text-center gap-2 border border-amber-500/30">
          <p className="text-amber-300 text-sm font-medium">
            LingBot generated {counterfactual?.frame_count} frames
          </p>
          <p className="text-xs text-gym-muted max-w-md">
            The world model ran successfully, but video previews did not reach the browser. Redeploy the Modal API to pick up the latest Reactor client.
          </p>
        </div>
      )}

      {!loading && !error && hasRun && !hasVideo && !generatedOffWire && !referenceSrc && (
        <div className="aspect-video bg-gym-surface rounded-2xl flex items-center justify-center p-4 text-center border border-gym-border">
          <p className="text-sm text-gym-muted">No counterfactual video returned for this run.</p>
        </div>
      )}

      {!loading && !error && (referenceSrc || frameSrc) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {referenceSrc && (
            <div>
              <p className="text-xs text-gym-muted mb-2 font-medium uppercase tracking-wide">Scene input</p>
              <img src={referenceSrc} alt="Reactor scene input" className="w-full rounded-xl border border-gym-border bg-gym-surface" />
            </div>
          )}
          {frameSrc && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gym-muted font-medium uppercase tracking-wide">
                  Counterfactual · {frameIdx + 1}/{previews.length}
                </p>
                <button
                  type="button"
                  onClick={() => setPlaying((p) => !p)}
                  className="badge-accent cursor-pointer hover:bg-gym-accent/25 transition-colors"
                >
                  {playing ? "⏸ Pause" : "▶ Play"}
                </button>
              </div>
              <img src={frameSrc} alt={`Reactor frame ${frameIdx + 1}`} className="w-full rounded-xl border-2 border-gym-accent/40 bg-gym-surface shadow-glow" />
            </div>
          )}
        </div>
      )}

      {counterfactual && (hasVideo || generatedOffWire || counterfactual.prompt) && (
        <div className="text-xs text-gym-muted space-y-1 border-t border-gym-border pt-3">
          {counterfactual.prompt && (
            <p>
              <span className="text-gym-muted/70">Prompt:</span>{" "}
              {counterfactual.prompt.slice(0, 140)}
              {counterfactual.prompt.length > 140 ? "…" : ""}
            </p>
          )}
          <p>
            {counterfactual.frame_count ?? previews.length} frames
            {counterfactual.generation_started && " · generation started"}
            {counterfactual.chunk_complete && " · chunk complete"}
          </p>
        </div>
      )}
    </div>
  );
}
