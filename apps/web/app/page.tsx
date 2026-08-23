import Link from "next/link";

const FAILURES = [
  { label: "SLIP", color: "bg-orange-500" },
  { label: "MISS", color: "bg-red-500" },
  { label: "SHIFT", color: "bg-amber-400" },
  { label: "NOISE", color: "bg-violet-500" },
  { label: "OCCL", color: "bg-sky-500" },
  { label: "COMP", color: "bg-rose-500" },
  { label: "DEV", color: "bg-emerald-500" },
  { label: "OBS", color: "bg-indigo-500" },
  { label: "GRIP", color: "bg-pink-500" },
  { label: "DRIFT", color: "bg-teal-500" },
  { label: "DROP", color: "bg-yellow-500" },
  { label: "JAM", color: "bg-purple-600" },
];

const FEATURES = [
  {
    title: "Break it thousands of ways",
    desc: "Inject OBJECT_SLIP, GRASP_MISS, OCCLUSION, and composite failures across deterministic seeds.",
    icon: "💥",
    accent: "from-orange-500/20 to-red-500/10",
  },
  {
    title: "Watch recovery in action",
    desc: "Reactor counterfactual rollouts and live sim telemetry show exactly how a policy recovers.",
    icon: "🎬",
    accent: "from-violet-500/20 to-purple-500/10",
  },
  {
    title: "Benchmark & fine-tune",
    desc: "Run stress profiles, export datasets to Hugging Face, and compare baseline vs fine-tuned policies.",
    icon: "📊",
    accent: "from-cyan-500/20 to-blue-500/10",
  },
  {
    title: "Measure what matters",
    desc: "Robustness score, OOD recovery rate, and method comparison charts — all in one report.",
    icon: "🎯",
    accent: "from-emerald-500/20 to-green-500/10",
  },
];

const iconGrid = [...FAILURES, ...FAILURES];

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="relative mx-auto max-w-5xl px-6 pt-16 pb-8 text-center animate-fade-up">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-gym-border bg-gym-surface/60 px-4 py-1.5 text-xs text-gym-muted">
          <span className="flex -space-x-1.5">
            {["🤖", "⚡", "🔧"].map((e, i) => (
              <span key={i} className="flex h-5 w-5 items-center justify-center rounded-full bg-gym-panel text-[10px] ring-2 ring-gym-bg">
                {e}
              </span>
            ))}
          </span>
          Supporting robotics researchers worldwide
        </div>

        <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight tracking-tight md:text-6xl">
          Make your robot{" "}
          <span className="gradient-text">sweat.</span>
        </h1>

        <p className="mx-auto mt-5 max-w-2xl text-lg text-gym-muted leading-relaxed">
          Learn when a policy fails, what kind of failure it was, and whether a recovery policy can bring the task back.
          Upload a policy, break it, measure, recover, adapt, and compare.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link href="/playground" className="btn-primary">
            Open Playground
          </Link>
          <Link href="/benchmark" className="btn-secondary">
            Run Benchmark
          </Link>
        </div>
      </section>

      {/* Icon marquee — Page Flows style */}
      <section className="relative overflow-hidden py-10">
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-24 bg-gradient-to-r from-gym-bg to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-24 bg-gradient-to-l from-gym-bg to-transparent" />
        <div className="flex animate-marquee gap-4 whitespace-nowrap">
          {iconGrid.map(({ label, color }, i) => (
            <div
              key={`${label}-${i}`}
              className={`squircle h-16 w-16 shrink-0 text-xs ${color}`}
            >
              {label}
            </div>
          ))}
        </div>
      </section>

      {/* Trusted strip */}
      <section className="mx-auto max-w-4xl px-6 py-8 text-center">
        <p className="section-label mb-4">Trusted evaluation pipeline</p>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-gym-muted/70">
          {["Reactor WAM", "SmolVLA", "Modal GPU", "Hugging Face", "LeRobot"].map((name) => (
            <span key={name} className="text-sm font-semibold tracking-wide">{name}</span>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-5xl px-6 py-16">
        <h2 className="page-title text-center mb-3">Why RecoveryGym?</h2>
        <p className="text-center text-gym-muted mb-12 max-w-xl mx-auto">
          Real-world failure injection, counterfactual video, and measurable recovery — all in one playground.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {FEATURES.map(({ title, desc, icon, accent }) => (
            <div
              key={title}
              className="card group p-6 cursor-default"
            >
              <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${accent} text-2xl transition-transform group-hover:scale-110`}>
                {icon}
              </div>
              <h3 className="text-lg font-semibold mb-2 group-hover:text-gym-accent transition-colors">{title}</h3>
              <p className="text-sm text-gym-muted leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-3xl px-6 py-16 text-center">
        <div className="card-static p-10 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-gym-accent/5 via-transparent to-gym-purple/5 pointer-events-none" />
          <h2 className="text-2xl font-bold mb-3 relative">Ready to stress-test?</h2>
          <p className="text-gym-muted mb-6 relative">
            Launch a single episode in the playground or fire off a full benchmark profile.
          </p>
          <div className="flex flex-wrap justify-center gap-3 relative">
            <Link href="/playground" className="btn-primary">Try Playground</Link>
            <Link href="/benchmark" className="btn-outline">Explore Benchmarks</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
