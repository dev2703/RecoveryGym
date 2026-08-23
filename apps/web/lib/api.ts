export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getHealth() {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createRun(body: Record<string, unknown>) {
  const res = await fetch(`${API_URL}/v1/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createBenchmark(body: Record<string, unknown>) {
  const res = await fetch(`${API_URL}/v1/benchmarks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getBenchmark(id: string) {
  const res = await fetch(`${API_URL}/v1/benchmarks/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generateDataset(benchmarkId: string, pushToHub = true) {
  const res = await fetch(`${API_URL}/v1/datasets/${benchmarkId}/generate?push_to_hf=${pushToHub}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function startTraining(
  benchmarkId: string,
  options?: { runTraining?: boolean; pushDataset?: boolean; steps?: number }
) {
  const res = await fetch(`${API_URL}/v1/training`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      benchmark_id: benchmarkId,
      run_training: options?.runTraining ?? false,
      push_dataset: options?.pushDataset ?? true,
      steps: options?.steps ?? 500,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runComparison(known = 10, ood = 6) {
  const res = await fetch(`${API_URL}/v1/experiments/compare?known_episodes=${known}&ood_episodes=${ood}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
