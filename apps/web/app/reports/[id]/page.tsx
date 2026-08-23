"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { getBenchmark, generateDataset, startTraining, runComparison } from "@/lib/api";
import type {
  BenchmarkResult,
  ComparisonResult,
  DatasetInfo,
  TrainingInfo,
} from "@/lib/types";

const CHART_THEME = {
  grid: "#3f3f46",
  text: "#a1a1aa",
  tooltip: { background: "#27272a", border: "1px solid #3f3f46", borderRadius: "12px" },
  accent: "#FEF08A",
  purple: "#a78bfa",
};

export default function ReportPage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<BenchmarkResult | null>(null);
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null);
  const [trainingInfo, setTrainingInfo] = useState<TrainingInfo | null>(null);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    async function poll() {
      try {
        const d = await getBenchmark(id);
        if (!active) return;
        setData(d);
        if (d.status === "running" || d.status === "queued") {
          setTimeout(poll, 2000);
        }
      } catch (e: any) {
        if (active) setError(e.message);
      }
    }
    poll();
    return () => {
      active = false;
    };
  }, [id]);

  useEffect(() => {
    if (!trainingInfo?.training_id || trainingInfo.status !== "queued_modal") return;
    let active = true;
    async function pollTraining() {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/v1/training/${trainingInfo!.training_id}`);
        if (!res.ok) return;
        const info = await res.json();
        if (!active) return;
        setTrainingInfo(info);
        if (info.comparison) setComparison(info.comparison);
        if (info.status === "queued_modal") setTimeout(pollTraining, 5000);
      } catch {
        /* keep last known status */
      }
    }
    pollTraining();
    return () => {
      active = false;
    };
  }, [trainingInfo?.training_id, trainingInfo?.status]);

  async function handleDownload() {
    setBusy(true);
    try {
      const info = await generateDataset(id);
      setDatasetInfo(info);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleFineTune() {
    setBusy(true);
    try {
      const info = await startTraining(id, {
        runTraining: true,
        pushDataset: true,
        steps: 500,
      });
      setTrainingInfo(info);
      if (info.comparison) setComparison(info.comparison);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleCompare() {
    setBusy(true);
    try {
      const result = await runComparison(10, 6);
      setComparison(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (error && !data) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-16 text-center">
        <p className="text-gym-danger rounded-xl bg-red-500/10 border border-red-500/20 px-6 py-4 inline-block">{error}</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-16 flex flex-col items-center gap-4">
        <div className="h-10 w-10 rounded-full border-2 border-gym-accent border-t-transparent animate-spin" />
        <p className="text-gym-muted">Loading report…</p>
      </main>
    );
  }

  const metrics = data.metrics || {};
  const baseline = data.baseline_metrics || {};
  const chartData = [
    { name: "Baseline", value: (baseline.final_success_rate || 0) * 100 },
    { name: "Rule Recovery", value: (metrics.final_success_rate || 0) * 100 },
    { name: "OOD Recovery", value: (metrics.ood_recovery_success || 0) * 100 },
  ];

  const methodLabels: Record<string, string> = {
    baseline: "No recovery",
    rule: "Rule recovery",
    smolvla_zeroshot: "SmolVLA zero-shot",
    smolvla_finetuned: "SmolVLA fine-tuned",
  };

  const compareChart = (comparison?.summary_table || []).map((row) => ({
    name: methodLabels[row.method] || row.method,
    Known: row.known_success_pct,
    OOD: row.ood_success_pct,
  }));

  const isRunning = data.status === "running" || data.status === "queued";

  const statCards = [
    { label: "Nominal Success", val: metrics.nominal_success_rate, color: "from-emerald-500/10" },
    { label: "Stress Success", val: metrics.final_success_rate, color: "from-gym-accent/10" },
    { label: "Recovery Success", val: metrics.recovery_success_rate, color: "from-violet-500/10" },
    { label: "OOD Recovery", val: metrics.ood_recovery_success, color: "from-cyan-500/10" },
  ];

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 space-y-8 animate-fade-up">
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div>
          <p className="section-label mb-2">Benchmark Report</p>
          <h1 className="page-title">Results</h1>
          <p className="text-gym-muted text-sm mt-1 font-mono">{id}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`badge ${isRunning ? "badge-accent animate-pulse" : "badge-muted"}`}>
            {data.status}
          </span>
          <span className="stat-value">{(metrics.robustness_score || 0).toFixed(1)}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map(({ label, val, color }) => (
          <div key={label} className="card-static p-5 relative overflow-hidden group">
            <div className={`absolute inset-0 bg-gradient-to-br ${color} to-transparent opacity-50 group-hover:opacity-100 transition-opacity`} />
            <p className="text-xs text-gym-muted relative">{label}</p>
            <p className="text-2xl font-bold relative mt-1">{(((val as number) || 0) * 100).toFixed(0)}%</p>
          </div>
        ))}
      </div>

      <div className="card-static p-6 h-72">
        <h2 className="font-semibold mb-4">Baseline vs Recovery</h2>
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke={CHART_THEME.text} tick={{ fontSize: 12 }} />
            <YAxis stroke={CHART_THEME.text} unit="%" />
            <Tooltip contentStyle={CHART_THEME.tooltip} />
            <Bar dataKey="value" fill={CHART_THEME.accent} radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {compareChart.length > 0 && (
        <div className="card-static p-6 h-80">
          <h2 className="font-semibold mb-1">Method Comparison</h2>
          <p className="text-xs text-gym-muted mb-4">Known vs held-out OOD — real episode rates only</p>
          <ResponsiveContainer width="100%" height="80%">
            <BarChart data={compareChart}>
              <XAxis dataKey="name" stroke={CHART_THEME.text} tick={{ fontSize: 11 }} />
              <YAxis stroke={CHART_THEME.text} unit="%" />
              <Tooltip contentStyle={CHART_THEME.tooltip} />
              <Legend />
              <Bar dataKey="Known" fill={CHART_THEME.accent} radius={[6, 6, 0, 0]} />
              <Bar dataKey="OOD" fill={CHART_THEME.purple} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="card-static p-5 text-sm text-gym-muted">
        <p>OOD split: severity 0.6–0.8 held out · composite failures held out · split by scenario</p>
        <p className="mt-1">
          Episodes: <span className="text-white font-medium">{data.episodes_completed}/{data.episodes_total}</span>
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <button onClick={handleDownload} disabled={busy} className="btn-primary !py-2.5 !px-5">
          {busy ? "Exporting…" : "Export & Push to Hugging Face"}
        </button>
        <button onClick={handleFineTune} disabled={busy} className="btn-secondary !py-2.5 !px-5">
          {busy ? "Running…" : "Fine-tune + Compare"}
        </button>
        <button onClick={handleCompare} disabled={busy} className="btn-outline !py-2.5 !px-5">
          Run Method Comparison
        </button>
      </div>

      {datasetInfo && (
        <div className="card-static p-5 text-sm space-y-1 border-gym-success/30">
          <p className="text-gym-success font-medium">Dataset exported</p>
          <p className="text-gym-muted">{datasetInfo.dataset_path} ({datasetInfo.format})</p>
          {datasetInfo.summary && (
            <p className="text-gym-muted">
              {datasetInfo.summary.count} episodes · {datasetInfo.summary.with_action_chunks} with action chunks
            </p>
          )}
          {datasetInfo.hf_upload && (
            <p>
              Hugging Face:{" "}
              <a href={datasetInfo.hf_upload.url} className="text-gym-accent hover:underline" target="_blank" rel="noreferrer">
                {datasetInfo.hf_upload.repo_id}
              </a>{" "}
              ({datasetInfo.hf_upload.rows} rows)
            </p>
          )}
        </div>
      )}
      {trainingInfo && (
        <div className="card-static p-5 text-sm text-gym-muted space-y-1">
          <p>
            Training: <span className="text-gym-accent font-medium">{trainingInfo.training_id}</span> — {trainingInfo.status}
          </p>
          {trainingInfo.status === "queued_modal" && (
            <p className="text-xs">GPU job running on Modal (LoRA fine-tune, ~10–30 min). Poll every 5s…</p>
          )}
          {trainingInfo.message && <p>{trainingInfo.message}</p>}
        </div>
      )}
      {error && (
        <p className="text-gym-danger text-sm rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2">{error}</p>
      )}
    </main>
  );
}
