import { useCallback, useRef, useState } from "react";
import { type NodeName, type Source, streamChat, type TwinEvent } from "./api";

export type Step = { node: NodeName; status: "running" | "done" | "skipped"; ms?: number; detail?: string };

export type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  streaming?: boolean;
  steps?: Step[];
  sources?: Source[];
  verdicts?: { passed: boolean; issues: string[] }[];
  outcome?: string;
  intent?: string | null;
  ms?: number;
  error?: boolean;
};

const SESSION_KEY = "ashariri.session";

export function sessionId(): string {
  let sid = localStorage.getItem(SESSION_KEY);
  if (!sid) {
    sid = crypto.randomUUID().replaceAll("-", "");
    localStorage.setItem(SESSION_KEY, sid);
  }
  return sid;
}

/** Fold one streamed event into the assistant message it belongs to. */
export function reduce(msg: Message, event: TwinEvent): Message {
  switch (event.type) {
    case "step": {
      const steps = [...(msg.steps ?? [])];
      const open = steps.findLastIndex((s) => s.node === event.node && s.status === "running");
      const step: Step = { node: event.node, status: event.status, ms: event.ms, detail: event.detail };
      if (open >= 0 && event.status !== "running") steps[open] = { ...steps[open], ...step };
      else steps.push(step);
      return { ...msg, steps };
    }
    case "token":
      return { ...msg, text: msg.text + event.text };
    case "reset":
      return { ...msg, text: "" };
    case "replace":
      return { ...msg, text: event.text };
    case "sources":
      return { ...msg, sources: event.sources };
    case "verdict":
      return { ...msg, verdicts: [...(msg.verdicts ?? []), { passed: event.passed, issues: event.issues }] };
    case "final":
      return { ...msg, text: event.answer, outcome: event.outcome, intent: event.intent, ms: event.ms, streaming: false };
    case "error":
      return { ...msg, text: event.message, error: true, streaming: false };
  }
}

export function useTwin(remember: boolean, onTurnDone?: () => void) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const abort = useRef<AbortController | null>(null);
  const busy = messages.some((m) => m.streaming);

  const send = useCallback(
    async (text: string) => {
      const question = text.trim();
      if (!question || busy) return;
      const history = messages
        .filter((m) => !m.error && m.text)
        .slice(-8)
        .map((m) => ({ role: m.role, content: m.text }));
      const id = crypto.randomUUID();
      setMessages((ms) => [
        ...ms,
        { id: `${id}-q`, role: "user", text: question },
        { id, role: "assistant", text: "", streaming: true, steps: [] },
      ]);
      setSelected(id);
      abort.current = new AbortController();
      const update = (event: TwinEvent) =>
        setMessages((ms) => ms.map((m) => (m.id === id ? reduce(m, event) : m)));
      try {
        await streamChat({ message: question, session_id: sessionId(), history, remember }, update, abort.current.signal);
      } catch (err) {
        if ((err as Error).name !== "AbortError") update({ type: "error", message: "I couldn't reach my brain just now. Is the API running?" });
      } finally {
        setMessages((ms) => ms.map((m) => (m.id === id && m.streaming ? { ...m, streaming: false } : m)));
        onTurnDone?.();
      }
    },
    [busy, messages, remember, onTurnDone],
  );

  const stop = useCallback(() => abort.current?.abort(), []);
  const clear = useCallback(() => {
    abort.current?.abort();
    setMessages([]);
    setSelected(null);
  }, []);

  return { messages, send, stop, clear, busy, selected, setSelected };
}
