import type { NodeName } from "../api";
import type { Step } from "../useTwin";

// The same graph the backend compiles (backend/ashariri/graph.py), drawn so each node lights up as it runs.
const NODES: { id: NodeName | "end"; label: string; sub: string; x: number; y: number; kind: string }[] = [
  { id: "route", label: "Route", sub: "intent · tone", x: 56, y: 110, kind: "agent" },
  { id: "decline", label: "Decline", sub: "boundary", x: 168, y: 36, kind: "guard" },
  { id: "recall", label: "Recall", sub: "memory", x: 168, y: 110, kind: "store" },
  { id: "retrieve", label: "Retrieve", sub: "hybrid search", x: 280, y: 110, kind: "store" },
  { id: "respond", label: "Respond", sub: "in my voice", x: 392, y: 110, kind: "agent" },
  { id: "guard", label: "Review", sub: "rules + judge", x: 504, y: 110, kind: "guard" },
  { id: "fallback", label: "Fallback", sub: "safe answer", x: 504, y: 188, kind: "guard" },
  { id: "remember", label: "Remember", sub: "consented", x: 616, y: 110, kind: "store" },
  { id: "end", label: "Reply", sub: "", x: 616, y: 36, kind: "io" },
];

const EDGES: [string, string][] = [
  ["route", "decline"],
  ["route", "recall"],
  ["recall", "retrieve"],
  ["retrieve", "respond"],
  ["respond", "guard"],
  ["guard", "remember"],
  ["guard", "fallback"],
  ["fallback", "remember"],
  ["decline", "end"],
  ["remember", "end"],
];

const at = (id: string) => NODES.find((n) => n.id === id)!;

type State = "idle" | "running" | "done" | "skipped";

export function AgentGraph({ steps, finished }: { steps: Step[]; finished: boolean }) {
  const state = (id: string): State => {
    if (id === "end") return finished && steps.length ? "done" : "idle";
    const mine = steps.filter((s) => s.node === id);
    return mine.length ? mine[mine.length - 1].status : "idle";
  };
  const visited = (id: string) => state(id) === "done" || state(id) === "running";
  const revised = steps.filter((s) => s.node === "respond" && s.status !== "skipped").length > 1;

  return (
    <svg className="graph" viewBox="0 0 672 224" role="img" aria-label="Agent graph: which steps ran for this answer">
      <defs>
        <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0 0L8 4L0 8z" fill="currentColor" />
        </marker>
      </defs>
      {EDGES.map(([a, b]) => {
        const p = at(a), q = at(b);
        const lit = visited(a) && (visited(b) || (b === "end" && finished));
        const x1 = p.x + (q.x > p.x ? 46 : 0), x2 = q.x - (q.x > p.x ? 46 : 0);
        const y1 = p.y + (q.y > p.y ? 18 : q.y < p.y ? -18 : 0), y2 = q.y + (q.y > p.y ? -18 : q.y < p.y ? 18 : 0);
        return (
          <line key={a + b} x1={x1} y1={y1} x2={x2} y2={y2} className={`edge ${lit ? "lit" : ""}`} markerEnd="url(#arrow)" />
        );
      })}
      <path
        d={`M ${at("guard").x - 20} ${at("guard").y - 20} C ${at("guard").x - 30} 52, ${at("respond").x + 30} 52, ${at("respond").x + 20} ${at("respond").y - 20}`}
        className={`edge loop ${revised ? "lit" : ""}`}
        markerEnd="url(#arrow)"
      />
      <text x={(at("guard").x + at("respond").x) / 2} y={62} className="edge-label">
        revise
      </text>
      {NODES.map((n) => (
        <g key={n.id} className={`node ${n.kind} ${state(n.id)}`} transform={`translate(${n.x - 46} ${n.y - 18})`}>
          <rect width="92" height="36" rx="11" />
          <text x="46" y={n.sub ? 15 : 22} className="label">
            {n.label}
          </text>
          {n.sub && (
            <text x="46" y="28" className="sub">
              {n.sub}
            </text>
          )}
        </g>
      ))}
    </svg>
  );
}
