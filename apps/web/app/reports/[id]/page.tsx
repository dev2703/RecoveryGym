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

  async function handleDownload() {
    try {
      const info = await generateDataset(id);
      setDatasetInfo(info);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function handleFineTune() {
    setBusy(true);
    try {
      const info = await startTraining(id);
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

  if (error && !data) return <main className="p-8 text-gym-danger">{error}</main>;
  if (!data) return <main className="p-8 text-gray-400">Loading report...</main>;

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

  return (
    <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Benchmark Report</h1>
          <p className="text-gray-400 text-sm">
            {id} · {data.status}
          </p>
        </div>
        <span className="text-3xl font-bold text-gym-accent">{(metrics.robustness_score || 0).toFixed(1)}</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          ["Nominal Success", metrics.nominal_success_rate],
          ["Stress Success", metrics.final_success_rate],
          ["Recovery Success", metrics.recovery_success_rate],
          ["OOD Recovery", metrics.ood_recovery_success],
        ].map(([label, val]) => (
          <div key={label as string} className="bg-gym-panel rounded-lg p-4 border border-gray-800">
            <p className="text-xs text-gray-400">{label}</p>
            <p className="text-xl font-semibold">{(((val as number) || 0) * 100).toFixed(0)}%</p>
          </div>
        ))}
      </div>

      <div className="bg-gym-panel rounded-lg p-4 border border-gray-800 h-64">
        <h2 className="font-semibold mb-4">Baseline vs Recovery</h2>
        <ResponsiveContainer width="100%" height="80%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" unit="%" />
            <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
            <Bar dataKey="value" fill="#22d3ee" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {compareChart.length > 0 && (
        <div className="bg-gym-panel rounded-lg p-4 border border-gray-800 h-72">
          <h2 className="font-semibold mb-2">Method Comparison (measured)</h2>
          <p className="text-xs text-gray-500 mb-3">Known vs held-out OOD — real episode rates only</p>
          <ResponsiveContainer width="100%" height="75%">
            <BarChart data={compareChart}>
              <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 11 }} />
              <YAxis stroke="#9ca3af" unit="%" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
              <Legend />
              <Bar dataKey="Known" fill="#22d3ee" />
              <Bar dataKey="OOD" fill="#a78bfa" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-gym-panel rounded-lg p-4 border border-gray-800 text-sm text-gray-400">
        <p>OOD split: severity 0.6–0.8 held out · composite failures held out · split by scenario</p>
        <p className="mt-1">
          Episodes: {data.episodes_completed}/{data.episodes_total}
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <button onClick={handleDownload} className="bg-gym-accent text-black px-4 py-2 rounded font-medium">
          Export & Push to Hugging Face
        </button>
        <button
          onClick={handleFineTune}
          disabled={busy}
          className="border border-gray-600 px-4 py-2 rounded hover:border-gym-accent disabled:opacity-50"
        >
          {busy ? "Running..." : "Fine-tune + Compare"}
        </button>
        <button
          onClick={handleCompare}
          disabled={busy}
          className="border border-gym-accent text-gym-accent px-4 py-2 rounded disabled:opacity-50"
        >
          Run Method Comparison
        </button>
      </div>

      {datasetInfo && (
        <div className="text-sm text-gym-success space-y-1">
          <p>Dataset exported: {datasetInfo.dataset_path} ({datasetInfo.format})</p>
          {datasetInfo.summary && (
            <p className="text-gray-400">
              {datasetInfo.summary.count} episodes · {datasetInfo.summary.with_action_chunks} with action chunks
            </p>
          )}
          {datasetInfo.hf_upload && (
            <p>
              Hugging Face:{" "}
              <a href={datasetInfo.hf_upload.url} className="underline text-gym-accent" target="_blank" rel="noreferrer">
                {datasetInfo.hf_upload.repo_id}
              </a>{" "}
              ({datasetInfo.hf_upload.rows} rows)
            </p>
          )}
        </div>
      )}
      {trainingInfo && (
        <div className="text-sm text-gray-400">
          Training: {trainingInfo.training_id} — {trainingInfo.message}
        </div>
      )}
      {error && <p className="text-gym-danger text-sm">{error}</p>}
    </main>
  );
}
