import Link from "next/link";

export default function Home() {
  return (
    <main className="max-w-4xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-bold mb-2">RecoveryGym</h1>
      <p className="text-xl text-gym-accent mb-6">Make your robot sweat.</p>
      <p className="text-gray-400 mb-8 max-w-2xl">
        Learn when a policy fails, what kind of failure it was, and whether a recovery policy can bring the task back.
        Upload a policy, break it thousands of ways, measure failure, recover, adapt, and compare.
      </p>
      <div className="flex gap-4">
        <Link href="/playground" className="bg-gym-accent text-black px-6 py-3 rounded font-medium hover:opacity-90">
          Open Playground
        </Link>
        <Link href="/benchmark" className="border border-gray-600 px-6 py-3 rounded hover:border-gym-accent">
          Run Benchmark
        </Link>
      </div>
    </main>
  );
}
