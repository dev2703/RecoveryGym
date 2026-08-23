"use client";

interface Event {
  t: number;
  event: string;
  failure_type?: string;
  confidence?: number;
  policy?: string;
  success?: boolean;
}

function eventColor(event: string) {
  if (event.includes("FAILURE")) return "border-gym-danger bg-red-500/5 text-gym-danger";
  if (event.includes("RECOVERY")) return "border-gym-success bg-emerald-500/5 text-gym-success";
  return "border-gym-accent/40 bg-gym-accent/5 text-gray-200";
}

export function EventTimeline({ events }: { events: Event[] }) {
  return (
    <div className="card-static p-6">
      <h2 className="font-semibold mb-4 flex items-center gap-2">
        <span className="text-lg">📋</span>
        Event Timeline
      </h2>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {events.length === 0 && (
          <p className="text-gym-muted text-sm py-4 text-center">No events yet. Run a scenario.</p>
        )}
        {events.map((e, i) => (
          <div
            key={i}
            className={`flex gap-3 text-sm rounded-xl border-l-4 pl-4 py-2.5 transition-colors hover:bg-gym-surface/50 ${eventColor(e.event)}`}
          >
            <span className="text-gym-muted w-10 shrink-0 font-mono text-xs mt-0.5">t={e.t}</span>
            <span>
              {e.event}
              {e.failure_type && ` (${e.failure_type})`}
              {e.confidence != null && ` [${(e.confidence * 100).toFixed(0)}%]`}
              {e.success != null && (e.success ? " ✓" : " ✗")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
