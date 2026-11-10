// Client for the Ashariri API. Chat responses arrive as Server-Sent Events over a POST,
// which EventSource can't do, so the stream is read and parsed by hand.

export type NodeName = "route" | "decline" | "recall" | "retrieve" | "respond" | "guard" | "fallback" | "remember";

export type Source = {
  id: number;
  title: string;
  source: string;
  url: string;
  snippet: string;
  vector_rank: number | null;
  keyword_rank: number | null;
};

export type TwinEvent =
  | { type: "step"; node: NodeName; status: "running" | "done" | "skipped"; ms?: number; detail?: string }
  | { type: "token"; text: string }
  | { type: "reset" }
  | { type: "replace"; text: string }
  | { type: "sources"; sources: Source[] }
  | { type: "verdict"; passed: boolean; issues: string[] }
  | { type: "final"; answer: string; outcome: string; intent: string | null; revisions: number; ms: number }
  | { type: "error"; message: string };

export type Memory = { id: number; kind: "fact" | "episode"; text: string; created_at: string };

export type Persona = {
  name: string;
  short_name: string;
  role: string;
  avatar: string;
  tagline: string;
  greeting: string;
  suggestions: string[];
};

export type Health = { status: string; llm: string; model: string; store: string; embedder: string; passages: number };

export type Turn = { role: "user" | "assistant"; content: string };

/** Split an SSE byte stream into parsed `data:` payloads. Returns the unconsumed remainder. */
export function parseSSE(buffer: string, emit: (event: TwinEvent) => void): string {
  const frames = buffer.split(/\r?\n\r?\n/);
  const rest = frames.pop() ?? "";
  for (const frame of frames) {
    const data = frame
      .split(/\r?\n/)
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (data) emit(JSON.parse(data) as TwinEvent);
  }
  return rest;
}

export async function streamChat(
  body: { message: string; session_id: string; history: Turn[]; remember: boolean },
  onEvent: (event: TwinEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`Chat failed (${res.status})`);
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer = parseSSE(buffer + value, onEvent);
  }
  parseSSE(buffer + "\n\n", onEvent);
}

const json = async <T>(res: Response): Promise<T> => {
  if (!res.ok) throw new Error(`${res.url} -> ${res.status}`);
  return (await res.json()) as T;
};

export const getHealth = () => fetch("/api/health").then(json<Health>);
export const getPersona = () => fetch("/api/persona").then(json<Persona>);
export const getMemories = (sid: string) => fetch(`/api/memory/${sid}`).then(json<Memory[]>);
export const forgetMemories = (sid: string) =>
  fetch(`/api/memory/${sid}`, { method: "DELETE" }).then(json<{ forgotten: number }>);
