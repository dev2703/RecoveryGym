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
    <div className="bg-gym-panel rounded-lg p-4 border border-gray-800">
      <h2 className="font-semibold mb-2">Simulation</h2>
      <svg width={340} height={340} className="bg-gray-900 rounded">
        <rect x={tgt.cx - 20} y={tgt.cy - 20} width={40} height={40} fill="none" stroke="#22d3ee" strokeWidth={2} strokeDasharray="4" />
        <circle cx={obj.cx} cy={obj.cy} r={12} fill={state.grasped ? "#4ade80" : "#f97316"} />
        <circle cx={ee.cx} cy={ee.cy} r={8} fill="#a78bfa" />
        <line x1={ee.cx} y1={ee.cy} x2={obj.cx} y2={obj.cy} stroke="#374151" strokeWidth={1} />
      </svg>
      <div className="grid grid-cols-2 gap-2 mt-2 text-xs text-gray-400">
        <span>EE: ({state.ee_x?.toFixed(2)}, {state.ee_y?.toFixed(2)})</span>
        <span>Object: ({state.object_x?.toFixed(2)}, {state.object_y?.toFixed(2)})</span>
        <span>Target: ({state.target_x?.toFixed(2)}, {state.target_y?.toFixed(2)})</span>
        <span>Grasped: {state.grasped ? "yes" : "no"}</span>
      </div>
    </div>
  );
}
