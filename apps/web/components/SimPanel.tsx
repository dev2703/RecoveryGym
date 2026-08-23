"use client";

interface SimPanelProps {
  state: {
    ee_x?: number;
    ee_y?: number;
    object_x?: number;
    object_y?: number;
    target_x?: number;
    target_y?: number;
    grasped?: boolean;
  };
}

export function SimPanel({ state }: SimPanelProps) {
  const scale = 300;
  const toSvg = (x = 0.5, y = 0.5) => ({ cx: x * scale + 20, cy: (1 - y) * scale + 20 });

  const ee = toSvg(state.ee_x, state.ee_y);
  const obj = toSvg(state.object_x, state.object_y);
  const tgt = toSvg(state.target_x, state.target_y);

  return (
    <div className="card-static p-6">
      <h2 className="font-semibold mb-3 flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-gym-cyan" />
        Simulation
      </h2>
      <svg width={340} height={340} className="bg-gym-surface rounded-2xl border border-gym-border">
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#3f3f46" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="340" height="340" fill="url(#grid)" />
        <rect x={tgt.cx - 20} y={tgt.cy - 20} width={40} height={40} fill="none" stroke="#FEF08A" strokeWidth={2} strokeDasharray="4" rx="4" />
        <circle cx={obj.cx} cy={obj.cy} r={12} fill={state.grasped ? "#4ade80" : "#f97316"} className="drop-shadow-lg" />
        <circle cx={ee.cx} cy={ee.cy} r={8} fill="#a78bfa" />
        <line x1={ee.cx} y1={ee.cy} x2={obj.cx} y2={obj.cy} stroke="#52525b" strokeWidth={1.5} strokeDasharray="3" />
      </svg>
      <div className="grid grid-cols-2 gap-2 mt-3">
        {[
          ["EE", `(${state.ee_x?.toFixed(2)}, ${state.ee_y?.toFixed(2)})`],
          ["Object", `(${state.object_x?.toFixed(2)}, ${state.object_y?.toFixed(2)})`],
          ["Target", `(${state.target_x?.toFixed(2)}, ${state.target_y?.toFixed(2)})`],
          ["Grasped", state.grasped ? "yes ✓" : "no"],
        ].map(([label, val]) => (
          <div key={label} className="rounded-lg bg-gym-surface border border-gym-border px-3 py-2 text-xs">
            <span className="text-gym-muted">{label}: </span>
            <span className="text-white font-medium">{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
