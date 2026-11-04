import { describe, expect, it } from "vitest";
import { parseSSE, type TwinEvent } from "./api";
import { type Message, reduce } from "./useTwin";

describe("parseSSE", () => {
  it("parses complete frames and keeps the partial one", () => {
    const got: TwinEvent[] = [];
    const rest = parseSSE(
      'event: token\r\ndata: {"type":"token","text":"Hi"}\r\n\r\nevent: token\r\ndata: {"type":"tok',
      (e) => got.push(e),
    );
    expect(got).toEqual([{ type: "token", text: "Hi" }]);
    expect(rest).toBe('event: token\r\ndata: {"type":"tok');
  });
});

describe("reduce", () => {
  const start: Message = { id: "a", role: "assistant", text: "", streaming: true, steps: [] };
  const run = (events: TwinEvent[]) => events.reduce(reduce, start);

  it("closes running steps and appends tokens", () => {
    const m = run([
      { type: "step", node: "route", status: "running" },
      { type: "step", node: "route", status: "done", ms: 12, detail: "work" },
      { type: "token", text: "Hello " },
      { type: "token", text: "there" },
    ]);
    expect(m.steps).toEqual([{ node: "route", status: "done", ms: 12, detail: "work" }]);
    expect(m.text).toBe("Hello there");
  });

  it("clears the draft on a revision and records both verdicts", () => {
    const m = run([
      { type: "token", text: "bad draft" },
      { type: "verdict", passed: false, issues: ["unsupported"] },
      { type: "reset" },
      { type: "token", text: "good" },
      { type: "verdict", passed: true, issues: [] },
      { type: "final", answer: "good", outcome: "revised", intent: "work", revisions: 1, ms: 900 },
    ]);
    expect(m.text).toBe("good");
    expect(m.verdicts?.map((v) => v.passed)).toEqual([false, true]);
    expect(m.outcome).toBe("revised");
    expect(m.streaming).toBe(false);
  });
});
