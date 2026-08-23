"use client";

interface Event {
  t: number;
  event: string;
  failure_type?: string;
  confidence?: number;
  policy?: string;
  success?: boolean;
}

export function EventTimeline({ events }: { events: Event[] }) {
  return (
    <div className="bg-gym-panel rounded-lg p-4 border border-gray-800">
      <h2 className="font-semibold mb-3">Event Timeline</h2>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {events.length === 0 && <p className="text-gray-500 text-sm">No events yet. Run a scenario.</p>}
        {events.map((e, i) => (
          <div key={i} className="flex gap-3 text-sm border-l-2 border-gym-accent pl-3 py-1">
            <span className="text-gray-500 w-8">t={e.t}</span>
            <span className={
              e.event.includes("FAILURE") ? "text-gym-danger" :
              e.event.includes("RECOVERY") ? "text-gym-success" : "text-gray-300"
            }>
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
