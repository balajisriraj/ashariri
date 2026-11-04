import type { Source } from "../api";
import type { Message } from "../useTwin";
import { AgentGraph } from "./AgentGraph";

const NODE_LABEL: Record<string, string> = {
  route: "Routed the question",
  decline: "Declined politely",
  recall: "Recalled memory",
  retrieve: "Searched my sources",
  respond: "Drafted the reply",
  guard: "Reviewed the draft",
  fallback: "Fell back to a safe answer",
  remember: "Updated memory",
};

const OUTCOME: Record<string, string> = {
  answered: "Answered first time",
  revised: "Answered after self-correction",
  declined: "Declined at the boundary",
  fallback: "Fell back safely",
};

export function Inspector({ message, highlight }: { message: Message | undefined; highlight: number | null }) {
  if (!message) {
    return (
      <div className="inspector empty">
        <AgentGraph steps={[]} finished={false} />
        <p className="hint">
          Ask something and watch the agent work: how it routes the question, what it retrieves, the review its draft
          has to pass, and what it chooses to remember.
        </p>
      </div>
    );
  }
  const steps = message.steps ?? [];
  let respondCount = 0;
  let verdictIndex = 0;
  return (
    <div className="inspector">
      <AgentGraph steps={steps} finished={!message.streaming} />
      {message.outcome && (
        <div className="outcome">
          <span className={`pill ${message.outcome}`}>{OUTCOME[message.outcome] ?? message.outcome}</span>
          {message.intent && <span className="pill quiet">intent · {message.intent}</span>}
          {message.ms !== undefined && <span className="pill quiet">{(message.ms / 1000).toFixed(1)}s</span>}
        </div>
      )}
      <ol className="timeline">
        {steps.map((s, i) => {
          const isRevision = s.node === "respond" && respondCount++ > 0;
          const verdict = s.node === "guard" && s.status === "done" ? message.verdicts?.[verdictIndex++] : undefined;
          return (
            <li key={i} className={`t-${s.status} ${verdict && !verdict.passed ? "t-fail" : ""}`}>
              <span className="dot" />
              <div>
                <b>{isRevision ? "Revised the reply" : NODE_LABEL[s.node]}</b>
                <span className="meta">
                  {s.status === "running" ? "working…" : s.detail}
                  {s.ms !== undefined && ` · ${s.ms} ms`}
                </span>
                {verdict && !verdict.passed && (
                  <ul className="issues">
                    {verdict.issues.map((issue) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      {message.sources && message.sources.length > 0 && <Sources sources={message.sources} highlight={highlight} />}
    </div>
  );
}

function Sources({ sources, highlight }: { sources: Source[]; highlight: number | null }) {
  return (
    <section className="sources">
      <h3>
        Sources <span>hybrid search · reciprocal rank fusion</span>
      </h3>
      {sources.map((s) => (
        <a
          key={s.id}
          id={`src-${s.id}`}
          className={`source ${highlight === s.id ? "hl" : ""}`}
          href={s.url || undefined}
          target="_blank"
          rel="noreferrer"
        >
          <span className="num">{s.id}</span>
          <div>
            <b>{s.title}</b>
            <p>{s.snippet}</p>
            <span className="ranks">
              <i title="Rank in vector (semantic) search">{s.vector_rank ? `semantic #${s.vector_rank}` : "semantic -"}</i>
              <i title="Rank in keyword (BM25) search">{s.keyword_rank ? `keyword #${s.keyword_rank}` : "keyword -"}</i>
            </span>
          </div>
        </a>
      ))}
    </section>
  );
}
